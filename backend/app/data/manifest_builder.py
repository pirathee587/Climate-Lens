"""Deterministic artifact generation with an explicit human-review gate."""

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, HttpUrl, field_validator

from app.schemas.common import NonEmpty
from app.schemas.repository import (
    BoundaryModel,
    NormalizedMonthlyRecord,
    ProvenanceReview,
    SnapshotDescriptor,
    SnapshotManifest,
)
from app.schemas.source import RegionDescriptor, VariableDescriptor
from app.services.snapshot_validation import monthly_periods

CSV_COLUMNS = (
    "region_id",
    "period",
    "precipitation_total_mm",
    "valid_fraction",
    "quality_flag",
)
MAX_SOURCE_BYTES = 10_000_000
MAX_MONTHS = 2400


class ImportRecipe(BoundaryModel):
    """Metadata from actual source attributes; no inferred product or unit defaults."""

    snapshot_id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$")]
    collection_id: Literal["GPM_3IMERGM_07"]
    version_label: Annotated[str, Field(pattern=r"^V07[A-Z]?$", strict=True)]
    run_type: Literal["Final"]
    source_url: HttpUrl
    granule_ids_or_export_reference: Annotated[
        tuple[NonEmpty, ...], Field(min_length=1)
    ]
    retrieved_at_utc: AwareDatetime
    original_variable_name: NonEmpty
    original_units: Literal["mm/hr", "mm", "mm/month"]
    region: RegionDescriptor
    display_name: NonEmpty
    description: NonEmpty
    # External exports must already contain their documented regional spatial average.
    spatial_aggregation: NonEmpty
    spatial_method: Literal["externally_area_averaged"]
    source_metadata_reference: HttpUrl
    license_or_usage_notes: NonEmpty
    period_column: NonEmpty
    value_column: NonEmpty
    period_format: Literal["%Y-%m", "%Y-%m-%d"] = "%Y-%m"
    valid_fraction_column: NonEmpty | None = None
    quality_flag_column: NonEmpty | None = None
    skip_header_lines: Annotated[int, Field(strict=True, ge=0, le=100)] = 0
    fill_values: tuple[float, ...] = ()
    missing_tokens: tuple[str, ...] = ("",)

    @field_validator("source_url", "source_metadata_reference")
    @classmethod
    def public_reference(cls, value: HttpUrl) -> HttpUrl:
        return SnapshotManifest.public_source_reference(value)


def canonical_json(value: dict) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()


def normalized_csv(rows: tuple[NormalizedMonthlyRecord, ...]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: "" if value is None else value
                for key, value in row.model_dump().items()
            }
        )
    return output.getvalue().encode()


def build_artifacts(
    recipe: ImportRecipe,
    raw_source: bytes,
    rows: tuple[NormalizedMonthlyRecord, ...],
    review: ProvenanceReview | None = None,
) -> tuple[bytes, dict, SnapshotManifest | None]:
    if len(raw_source) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds size limit")
    rows = tuple(
        NormalizedMonthlyRecord.model_validate(row.model_dump()) for row in rows
    )
    if any(row.region_id != recipe.region.id for row in rows):
        raise ValueError("source region mismatch")
    periods = [row.period for row in rows]
    if periods != sorted(set(periods)):
        raise ValueError("duplicate or unordered periods")
    if review is not None:
        review = ProvenanceReview.model_validate(review.model_dump())
    if not rows or len(rows) > MAX_MONTHS:
        raise ValueError("monthly record limit exceeded or source is empty")
    if recipe.region.id not in {"jaffna_area", "colombo_area"}:
        raise ValueError("unsupported region ID")
    first, last = rows[0].period, rows[-1].period
    span = (int(last[:4]) - int(first[:4])) * 12 + int(last[5:]) - int(first[5:]) + 1
    if span > MAX_MONTHS:
        raise ValueError("coverage span exceeds monthly resource limit")
    if recipe.retrieved_at_utc.date().isoformat() < last + "-01":
        raise ValueError("retrieval predates observations")
    # Even unreviewed imports must satisfy existing catalog and geometry contracts.
    variable = VariableDescriptor(
        id="precipitation",
        display_name=recipe.display_name,
        description=recipe.description,
        source_dataset_id=recipe.collection_id,
        source_version=recipe.version_label,
        source_run=recipe.run_type,
        aggregation_units="mm",
        time_resolution="monthly",
        supported=True,
        first_available_period=first,
        last_available_period=last,
    )
    snapshot = normalized_csv(rows)
    conversion = (
        "rate_mm_per_hour * 24 * actual_Gregorian_days_in_month"
        if recipe.original_units == "mm/hr"
        else "already_accumulated_no_conversion"
    )
    manifest_data = {
        key: recipe.model_dump(mode="json")[key]
        for key in [
            "snapshot_id",
            "collection_id",
            "version_label",
            "run_type",
            "source_url",
            "granule_ids_or_export_reference",
            "retrieved_at_utc",
            "original_variable_name",
            "original_units",
            "spatial_aggregation",
            "license_or_usage_notes",
        ]
    }
    manifest_data.update(
        time_start=first,
        time_end=last,
        normalization_units="mm/month",
        rate_to_total_conversion=conversion,
        missing_data_policy="preserve-missing-exclude-incomplete-years",
        input_sha256=hashlib.sha256(raw_source).hexdigest(),
        output_sha256=hashlib.sha256(snapshot).hexdigest(),
        processing_script_or_steps=(
            "terratrend-imerg-import-v1; source CSV mapping stored in recipe; "
            "stable period sort; duplicate rejection; "
        )
        + conversion,
        review=review.model_dump(mode="json") if review is not None else None,
    )
    manifest = (
        SnapshotManifest.model_validate(manifest_data) if review is not None else None
    )
    existing = {row.period for row in rows}
    envelope = {
        "status": "reviewed" if manifest else "awaiting_review",
        "manifest": manifest_data,
        "region": recipe.region.model_dump(mode="json"),
        "variable": variable.model_dump(mode="json"),
        "recipe": recipe.model_dump(mode="json"),
        "source_path": "sources/" + recipe.snapshot_id + ".csv",
        "missing_periods": [
            p for p in monthly_periods(first, last) if p not in existing
        ],
    }
    return snapshot, envelope, manifest


def write_import(
    root: Path,
    recipe: ImportRecipe,
    raw_source: bytes,
    rows: tuple[NormalizedMonthlyRecord, ...],
    review: ProvenanceReview | None = None,
) -> tuple[str, str | None]:
    """Write a new bundle; refuse overwrites and symlink output directories."""
    snapshot, envelope, manifest = build_artifacts(recipe, raw_source, rows, review)
    stem = recipe.snapshot_id
    snapshot_path, manifest_path = f"snapshots/{stem}.csv", f"manifests/{stem}.json"
    manifest_bytes = canonical_json(envelope)
    files = {
        snapshot_path: snapshot,
        manifest_path: manifest_bytes,
        envelope["source_path"]: raw_source,
    }
    descriptor_path = None
    if manifest is not None:
        descriptor = SnapshotDescriptor(
            variable=envelope["variable"],
            region=recipe.region,
            manifest=manifest,
            snapshot_path=snapshot_path,
            manifest_path=manifest_path,
            manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        )
        descriptor_path = f"manifests/{stem}.descriptor.json"
        files[descriptor_path] = canonical_json(descriptor.model_dump(mode="json"))
    # Staging directories should be a trusted, dedicated local preparation location.
    for parent in (root, *root.parents):
        if parent.is_symlink():
            raise ValueError("symlink output root")
    for relative in files:
        target = root / relative
        if target.exists() or target.is_symlink() or target.parent.is_symlink():
            raise FileExistsError("import never overwrites artifacts")
    created = []
    try:
        for relative, content in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                created.append(target)
                stream.write(content)
    except Exception:
        for target in created:
            target.unlink(missing_ok=True)
        raise
    return manifest_path, descriptor_path
