"""Normalized adapter contracts, not Harith's raw manifest format or a CSV parser."""

from datetime import date
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from app.schemas.analysis import MonthlyItem
from app.schemas.common import APIModel, NonEmpty, Period
from app.schemas.source import RegionDescriptor, VariableDescriptor

SHA256 = Annotated[str, Field(pattern=r"^[a-fA-F0-9]{64}$")]


class BoundaryModel(APIModel):
    model_config = ConfigDict(frozen=True, revalidate_instances="always")

    @field_validator("*", mode="after")
    @classmethod
    def meaningful_text(cls, value):
        if isinstance(value, str):
            if not value.strip() or value.lower().startswith(("verify-", "replace_")):
                raise ValueError("reviewed metadata cannot contain placeholders")
        return value


class ProvenanceReview(BoundaryModel):
    """Trusted human review attestation, separate from artifact integrity."""

    status: Literal["reviewed"]
    reviewed_by: NonEmpty
    reviewed_at: AwareDatetime
    evidence_reference: HttpUrl


class SnapshotManifest(BoundaryModel):
    snapshot_id: NonEmpty
    collection_id: Literal["GPM_3IMERGM_07"]
    version_label: Annotated[str, Field(pattern=r"^V07[A-Z]?$", strict=True)]
    run_type: Literal["Final"]
    source_url: HttpUrl
    granule_ids_or_export_reference: Annotated[
        tuple[NonEmpty, ...], Field(min_length=1)
    ]
    retrieved_at_utc: AwareDatetime
    time_start: Period
    time_end: Period
    original_variable_name: NonEmpty
    original_units: Literal["mm/hr", "mm", "mm/month"]
    normalization_units: Literal["mm/month"]
    spatial_aggregation: NonEmpty
    rate_to_total_conversion: NonEmpty
    missing_data_policy: Literal["preserve-missing-exclude-incomplete-years"]
    input_sha256: SHA256
    output_sha256: SHA256
    processing_script_or_steps: NonEmpty
    license_or_usage_notes: NonEmpty
    review: ProvenanceReview

    @model_validator(mode="after")
    def consistent_dates(self) -> "SnapshotManifest":
        if self.time_start > self.time_end:
            raise ValueError("coverage must be ordered")
        # date.fromisoformat also rejects year 0000 and non-ASCII digits.
        date.fromisoformat(self.time_start + "-01")
        last = date.fromisoformat(self.time_end + "-01")
        if self.retrieved_at_utc.date() < last:
            raise ValueError("retrieval predates covered observations")
        if self.review.reviewed_at < self.retrieved_at_utc:
            raise ValueError("review predates retrieval")
        return self

    @field_validator("source_url")
    @classmethod
    def public_source_reference(cls, url: HttpUrl) -> HttpUrl:
        if (
            url.scheme != "https"
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ValueError(
                "source references must be public HTTPS URLs without credentials"
            )
        return url


class SnapshotDescriptor(BoundaryModel):
    variable: VariableDescriptor
    region: RegionDescriptor
    manifest: SnapshotManifest
    # Adapter-owned artifact references, never API parameters or response fields.
    snapshot_path: NonEmpty
    manifest_path: NonEmpty
    manifest_sha256: SHA256

    @model_validator(mode="after")
    def consistent_metadata(self) -> "SnapshotDescriptor":
        variable, manifest = self.variable, self.manifest
        pairs = [
            (variable.source_dataset_id, manifest.collection_id),
            (variable.source_version, manifest.version_label),
            (variable.source_run, manifest.run_type),
            (variable.first_available_period, manifest.time_start),
            (variable.last_available_period, manifest.time_end),
        ]
        if any(left != right for left, right in pairs):
            raise ValueError("catalog metadata differs from manifest")
        geometry = self.region.geometry_source
        # Geometry attribution is public metadata, never a private file path.
        if "/" in geometry or "\\" in geometry:
            url = HttpUrl(geometry)
            if url.scheme != "https" or url.username or url.password or url.query:
                raise ValueError("geometry source must be a public reference")
        return self


class NormalizedMonthlyRecord(MonthlyItem):
    """Already-normalized totals from Harith; no scientific conversion here."""

    region_id: NonEmpty
    quality_flag: NonEmpty

    @field_validator("period")
    @classmethod
    def valid_calendar_month(cls, period: str) -> str:
        date.fromisoformat(period + "-01")
        return period


class ValidatedMonthlySeries(BoundaryModel):
    descriptor: SnapshotDescriptor
    observations: tuple[NormalizedMonthlyRecord, ...]
    missing_periods: tuple[Period, ...]
