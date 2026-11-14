"""Fail-closed two-region catalog over a trusted, injected read-only repository."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request

from app.core.errors import APIError
from app.schemas.repository import NormalizedMonthlyRecord, SnapshotDescriptor
from app.schemas.source import RegionDescriptor, RegionsResponse, VariablesResponse
from app.services.snapshot_repository import SnapshotRepository, get_snapshot_repository
from app.services.snapshot_validation import validate_series

REQUIRED_REGIONS = ("jaffna_area", "colombo_area")


def dataset_unavailable() -> APIError:
    return APIError(
        503,
        "DATASET_UNAVAILABLE",
        "Verified two-region snapshots are unavailable or have not passed validation.",
    )


class CatalogService:
    def __init__(self, repository: SnapshotRepository, root: Path) -> None:
        self.repository = repository
        self.root = root

    def _validated_catalog(self) -> tuple[SnapshotDescriptor, ...]:
        try:
            # Reparse model dumps so mutated or model_construct-created nested DTOs
            # cannot bypass validation at this integration boundary.
            descriptors = tuple(
                SnapshotDescriptor.model_validate(record.model_dump(warnings="error"))
                for record in self.repository.list_verified_datasets()
            )
            if len(descriptors) != 2 or {d.region.id for d in descriptors} != set(
                REQUIRED_REGIONS
            ):
                raise ValueError("both required region artifacts must be present")
            first = descriptors[0]
            regions = tuple(
                RegionDescriptor.model_validate(region.model_dump(warnings="error"))
                for region in self.repository.list_verified_regions(first.variable.id)
            )
            if len(regions) != 2 or {r.id for r in regions} != set(REQUIRED_REGIONS):
                raise ValueError("region catalog is incomplete")
            region_map = {region.id: region for region in regions}
            for descriptor in descriptors:
                if descriptor.variable != first.variable:
                    raise ValueError("dataset variants or coverage cannot be mixed")
                if descriptor.region != region_map[descriptor.region.id]:
                    raise ValueError("region metadata differs between repository views")
                for field in (
                    "original_variable_name",
                    "original_units",
                    "normalization_units",
                    "spatial_aggregation",
                    "rate_to_total_conversion",
                    "missing_data_policy",
                ):
                    if getattr(descriptor.manifest, field) != getattr(
                        first.manifest, field
                    ):
                        raise ValueError("incompatible processing metadata")
                observations = tuple(
                    NormalizedMonthlyRecord.model_validate(
                        row.model_dump(warnings="error")
                    )
                    for row in self.repository.get_verified_monthly_series(
                        descriptor.variable.id,
                        descriptor.region.id,
                    )
                )
                validate_series(descriptor, observations, self.root)
            return tuple(
                sorted(descriptors, key=lambda d: REQUIRED_REGIONS.index(d.region.id))
            )
        except Exception:
            # Adapter failures, missing files and malformed DTOs are all unavailable.
            # No exception messages/private paths/raw records reach responses or logs.
            raise dataset_unavailable() from None

    def variables(self) -> VariablesResponse:
        descriptors = self._validated_catalog()
        return VariablesResponse(variables=[descriptors[0].variable])

    def regions(self) -> RegionsResponse:
        return RegionsResponse(regions=[d.region for d in self._validated_catalog()])


def get_catalog_service(
    request: Request,
    repository: Annotated[SnapshotRepository, Depends(get_snapshot_repository)],
) -> CatalogService:
    return CatalogService(repository, request.app.state.settings.snapshot_root)
