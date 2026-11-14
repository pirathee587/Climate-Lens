"""Explicitly allowlisted, read-only implementation of Pirathee's repository port."""

import hashlib
import json
from pathlib import Path
from typing import Annotated

from pydantic import Field

from app.data.manifest_builder import ImportRecipe, build_artifacts, canonical_json
from app.data.snapshot_loader import load_normalized, load_source, read_bounded
from app.schemas.repository import (
    SHA256,
    BoundaryModel,
    NormalizedMonthlyRecord,
    SnapshotDescriptor,
)
from app.schemas.source import RegionDescriptor
from app.services.snapshot_validation import validate_series


class ArtifactApproval(BoundaryModel):
    descriptor_path: Annotated[str, Field(min_length=1)]
    descriptor_sha256: SHA256


class HarithSnapshotRepository:
    """Only operator-supplied reviewed descriptor fingerprints may be loaded."""

    def __init__(self, root: Path, approvals: tuple[ArtifactApproval, ...]) -> None:
        if len(approvals) > 2:
            raise ValueError("P0 repository supports at most two approved snapshots")
        self.root = root
        self.approvals = tuple(
            ArtifactApproval.model_validate(a.model_dump()) for a in approvals
        )

    def _load(
        self,
    ) -> tuple[tuple[SnapshotDescriptor, tuple[NormalizedMonthlyRecord, ...]], ...]:
        results = []
        for approval in self.approvals:
            raw = read_bounded(self.root, approval.descriptor_path, 1_000_000)
            if hashlib.sha256(raw).hexdigest() != approval.descriptor_sha256.lower():
                raise ValueError("unapproved descriptor fingerprint")
            descriptor = SnapshotDescriptor.model_validate_json(raw)
            envelope_raw = read_bounded(self.root, descriptor.manifest_path, 1_000_000)
            if (
                hashlib.sha256(envelope_raw).hexdigest()
                != descriptor.manifest_sha256.lower()
            ):
                raise ValueError("manifest hash mismatch")
            envelope = json.loads(envelope_raw)
            if envelope.get("status") != "reviewed":
                raise ValueError("provenance review is outstanding")
            if envelope["manifest"] != descriptor.manifest.model_dump(mode="json"):
                raise ValueError("manifest contents do not match approved descriptor")
            recipe = ImportRecipe.model_validate(envelope["recipe"])
            source = read_bounded(self.root, envelope["source_path"])
            rows = load_normalized(read_bounded(self.root, descriptor.snapshot_path))
            derived = load_source(source, recipe)
            # Bind every normalized observation and metadata field to original bytes.
            expected_snapshot, expected_envelope, _ = build_artifacts(
                recipe,
                source,
                derived,
                descriptor.manifest.review,
            )
            if canonical_json(expected_envelope) != canonical_json(envelope):
                raise ValueError("source provenance envelope is inconsistent")
            if (
                descriptor.region.model_dump(mode="json") != envelope["region"]
                or descriptor.variable.model_dump(mode="json") != envelope["variable"]
            ):
                raise ValueError("region or variable metadata changed")
            if (
                expected_snapshot != read_bounded(self.root, descriptor.snapshot_path)
                or rows != derived
            ):
                raise ValueError(
                    "normalized snapshot differs from source transformation"
                )
            validate_series(descriptor, rows, self.root)
            results.append((descriptor, rows))
        if len({item[0].region.id for item in results}) != len(results):
            raise ValueError("duplicate approved region")
        if results:
            first = results[0][0]
            for descriptor, _ in results:
                if descriptor.variable != first.variable:
                    raise ValueError("product variants or coverage must not be mixed")
                for field in (
                    "original_units",
                    "original_variable_name",
                    "spatial_aggregation",
                    "rate_to_total_conversion",
                ):
                    if getattr(descriptor.manifest, field) != getattr(
                        first.manifest, field
                    ):
                        raise ValueError("incompatible source processing")
        return tuple(results)

    def list_verified_datasets(self) -> tuple[SnapshotDescriptor, ...]:
        return tuple(item[0] for item in self._load())

    def list_verified_regions(self, variable_id: str) -> tuple[RegionDescriptor, ...]:
        if variable_id != "precipitation":
            return ()
        return tuple(item[0].region for item in self._load())

    def get_verified_monthly_series(
        self, variable_id: str, region_id: str
    ) -> tuple[NormalizedMonthlyRecord, ...]:
        if variable_id != "precipitation":
            return ()
        for descriptor, rows in self._load():
            if descriptor.region.id == region_id:
                return rows
        return ()
