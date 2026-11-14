"""Artifact integrity and normalized-data checks, without ingestion or preprocessing."""

import hashlib
from pathlib import Path, PurePosixPath, PureWindowsPath

from app.schemas.repository import (
    NormalizedMonthlyRecord,
    SnapshotDescriptor,
    ValidatedMonthlySeries,
)


def checked_artifact(root: Path, relative: str) -> Path:
    """Fail closed on absolute/traversal paths, non-files and symlinks."""
    path = PurePosixPath(relative)
    if (
        path.is_absolute()
        or PureWindowsPath(relative).drive
        or "\\" in relative
        or "\x00" in relative
        or ".." in path.parts
        or not path.parts
    ):
        raise ValueError("unsafe artifact reference")
    base = root.resolve(strict=True)
    candidate = base
    for part in path.parts:
        candidate /= part
        if candidate.is_symlink():
            raise ValueError("symlink artifact reference")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(base) or not resolved.is_file():
        raise ValueError("artifact is not a regular file inside the repository")
    return resolved


def verify_artifact(root: Path, relative: str, expected_hash: str) -> None:
    path = checked_artifact(root, relative)
    with path.open("rb") as stream:
        actual_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual_hash != expected_hash.lower():
        raise ValueError("artifact integrity mismatch")


def monthly_periods(start: str, end: str) -> tuple[str, ...]:
    first_year, first_month = map(int, start.split("-"))
    last_year, last_month = map(int, end.split("-"))
    first, last = first_year * 12 + first_month - 1, last_year * 12 + last_month - 1
    return tuple(
        f"{index // 12:04d}-{index % 12 + 1:02d}" for index in range(first, last + 1)
    )


def validate_series(
    descriptor: SnapshotDescriptor,
    observations: tuple[NormalizedMonthlyRecord, ...],
    root: Path,
) -> ValidatedMonthlySeries:
    manifest = descriptor.manifest
    if descriptor.snapshot_path == descriptor.manifest_path:
        raise ValueError("manifest and snapshot must be separate artifacts")
    verify_artifact(root, descriptor.snapshot_path, manifest.output_sha256)
    verify_artifact(root, descriptor.manifest_path, descriptor.manifest_sha256)
    if not observations:
        raise ValueError("no normalized observations")
    periods = [row.period for row in observations]
    if periods != sorted(set(periods)):
        raise ValueError("duplicate or unordered periods")
    if periods[0] != manifest.time_start or periods[-1] != manifest.time_end:
        raise ValueError("observation coverage differs from manifest")
    for row in observations:
        if row.region_id != descriptor.region.id:
            raise ValueError("observation region differs from manifest")
    existing = set(periods)
    missing = tuple(
        period
        for period in monthly_periods(manifest.time_start, manifest.time_end)
        if period not in existing
    )
    return ValidatedMonthlySeries(
        descriptor=descriptor,
        observations=observations,
        missing_periods=missing,
    )
