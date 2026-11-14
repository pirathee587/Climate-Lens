"""SYNTHETIC ONLY — no actual NASA observation, coordinate or human review."""

import hashlib
from pathlib import Path

from app.data.manifest_builder import ImportRecipe, write_import
from app.data.repository_adapter import ArtifactApproval
from app.data.snapshot_loader import load_source
from app.schemas.repository import ProvenanceReview

SYNTHETIC_SOURCE = (
    b"period,rate,fraction,quality\n"
    b"2023-02,1,0.5,synthetic-valid\n2024-02,1,,synthetic-valid\n"
)


def synthetic_recipe(region_id="jaffna_area", **overrides):
    data = dict(
        snapshot_id="synthetic-" + region_id,
        collection_id="GPM_3IMERGM_07",
        version_label="V07T",
        run_type="Final",
        source_url="https://example.invalid/synthetic",
        granule_ids_or_export_reference=("SYNTHETIC-NOT-A-GRANULE",),
        retrieved_at_utc="2025-01-01T00:00:00Z",
        original_variable_name="synthetic-variable",
        original_units="mm/hr",
        region={
            "id": region_id,
            "name": "SYNTHETIC TEST AREA",
            "bbox": [0, 0, 1, 1],
            "geometry_source": "synthetic-test-only",
        },
        display_name="SYNTHETIC precipitation",
        description="SYNTHETIC TEST ONLY",
        spatial_aggregation="synthetic-already-area-averaged",
        spatial_method="externally_area_averaged",
        source_metadata_reference="https://example.invalid/synthetic-metadata",
        license_or_usage_notes="SYNTHETIC TEST ONLY; NOT NASA",
        period_column="period",
        value_column="rate",
        valid_fraction_column="fraction",
        quality_flag_column="quality",
    )
    data.update(overrides)
    return ImportRecipe.model_validate(data)


def synthetic_review():
    return ProvenanceReview(
        status="reviewed",
        reviewed_by="synthetic-test-reviewer",
        reviewed_at="2025-01-02T00:00:00Z",
        evidence_reference="https://example.invalid/synthetic-review",
    )


def synthetic_bundle(root: Path, region_id="jaffna_area", review=True, **overrides):
    recipe = synthetic_recipe(region_id, **overrides)
    rows = load_source(SYNTHETIC_SOURCE, recipe)
    _, descriptor = write_import(
        root, recipe, SYNTHETIC_SOURCE, rows, synthetic_review() if review else None
    )
    if descriptor is None:
        return None
    return ArtifactApproval(
        descriptor_path=descriptor,
        descriptor_sha256=hashlib.sha256((root / descriptor).read_bytes()).hexdigest(),
    )
