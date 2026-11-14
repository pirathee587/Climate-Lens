"""Operator-supplied source-quality review, bound to a normalized snapshot hash."""

from typing import Annotated

from pydantic import Field, model_validator

from app.schemas.repository import (
    SHA256,
    BoundaryModel,
    ProvenanceReview,
    SnapshotManifest,
)


class ReviewedQualityPolicy(BoundaryModel):
    snapshot_sha256: SHA256
    accepted_quality_flags: Annotated[
        tuple[str, ...], Field(min_length=1, max_length=64)
    ]
    minimum_valid_fraction: Annotated[float, Field(ge=0, le=1)] | None = None
    review: ProvenanceReview

    @model_validator(mode="after")
    def reviewed_flags(self) -> "ReviewedQualityPolicy":
        if len(set(self.accepted_quality_flags)) != len(self.accepted_quality_flags):
            raise ValueError("accepted quality flags must be unique")
        if any(not flag.strip() for flag in self.accepted_quality_flags):
            raise ValueError("quality flags must be nonempty")
        SnapshotManifest.public_source_reference(self.review.evidence_reference)
        return self
