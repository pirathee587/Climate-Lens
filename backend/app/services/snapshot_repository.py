"""Read-only integration port. No discovery, imports, network calls or CSV parsing."""

from collections.abc import Sequence
from typing import Protocol

from app.schemas.repository import NormalizedMonthlyRecord, SnapshotDescriptor
from app.schemas.source import RegionDescriptor


class SnapshotRepository(Protocol):
    """Harith's future trusted adapter must map verified artifacts to these DTOs."""

    def list_verified_datasets(self) -> Sequence[SnapshotDescriptor]: ...

    def list_verified_regions(self, variable_id: str) -> Sequence[RegionDescriptor]: ...

    def get_verified_monthly_series(
        self, variable_id: str, region_id: str
    ) -> Sequence[NormalizedMonthlyRecord]: ...


class UnavailableSnapshotRepository:
    """Safe default until Harith's public repository and review evidence exist."""

    def list_verified_datasets(self) -> tuple[SnapshotDescriptor, ...]:
        return ()

    def list_verified_regions(self, variable_id: str) -> tuple[RegionDescriptor, ...]:
        return ()

    def get_verified_monthly_series(
        self, variable_id: str, region_id: str
    ) -> tuple[NormalizedMonthlyRecord, ...]:
        return ()


def get_snapshot_repository() -> SnapshotRepository:
    # Wire a reviewed Harith adapter here in a later explicitly authorized change.
    # Merely dropping CSV/JSON files into SNAPSHOT_ROOT never activates catalogs.
    return UnavailableSnapshotRepository()
