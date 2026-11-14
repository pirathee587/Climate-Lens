"""Phase 02 boundary: only Harith's verified metadata may enable catalogs."""

from app.core.errors import APIError


def require_verified_catalog() -> None:
    # Deliberately unavailable until the verified repository adapter is integrated.
    # File presence alone must never make an unvalidated dataset selectable.
    raise APIError(
        503,
        "DATASET_UNAVAILABLE",
        "Verified snapshots are not integrated. Dataset catalogs are unavailable.",
    )
