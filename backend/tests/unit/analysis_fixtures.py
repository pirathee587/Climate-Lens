"""Synthetic integration bundles only; never installed as production NASA data."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.data.manifest_builder import write_import
from app.data.repository_adapter import ArtifactApproval, HarithSnapshotRepository
from app.data.snapshot_loader import load_source
from app.schemas.quality import ReviewedQualityPolicy
from tests.unit.data_fixtures import synthetic_recipe, synthetic_review


@dataclass(frozen=True)
class SyntheticAnalysisCase:
    settings: Settings
    repository: HarithSnapshotRepository
    request: dict


def make_case(
    root: Path,
    *,
    start=2001,
    end=2012,
    slope=10,
    missing=(),
    rejected=(),
    nulls=(),
    original_units="mm",
    fractions=True,
    region_options=None,
) -> SyntheticAnalysisCase:
    approvals, policies = [], []
    for region in ("jaffna_area", "colombo_area"):
        options = (region_options or {}).get(region, {})
        region_missing = options.get("missing", missing)
        region_slope = options.get("slope", slope)
        recipe = synthetic_recipe(region, original_units=original_units)
        raw = ["period,rate,fraction,quality"]
        for year in range(start, end + 1):
            for month in range(1, 13):
                period = f"{year}-{month:02d}"
                if period in region_missing:
                    continue
                value = (
                    1
                    if original_units == "mm/hr"
                    else (500 + region_slope * (year - start)) / 12
                )
                raw_value = "" if period in nulls else str(value)
                quality = (
                    "synthetic-rejected" if period in rejected else "synthetic-valid"
                )
                fraction = "1" if fractions else ""
                raw.append(f"{period},{raw_value},{fraction},{quality}")
        source = ("\n".join(raw) + "\n").encode()
        rows = load_source(source, recipe)
        _, descriptor_path = write_import(
            root, recipe, source, rows, synthetic_review()
        )
        content = (root / descriptor_path).read_bytes()
        descriptor = json.loads(content)
        approvals.append(
            ArtifactApproval(
                descriptor_path=descriptor_path,
                descriptor_sha256=hashlib.sha256(content).hexdigest(),
            )
        )
        policies.append(
            ReviewedQualityPolicy(
                snapshot_sha256=descriptor["manifest"]["output_sha256"],
                accepted_quality_flags=("synthetic-valid",),
                minimum_valid_fraction=None,
                review=synthetic_review(),
            )
        )
    settings = Settings(
        app_env="test",
        snapshot_root=root,
        snapshot_approvals=tuple(approvals),
        snapshot_quality_policies=tuple(policies),
    )
    request = dict(
        variable_id="precipitation",
        region_id="jaffna_area",
        start_year=start,
        end_year=end,
        alpha=0.05,
        source_mode="verified_snapshot",
    )
    return SyntheticAnalysisCase(
        settings, HarithSnapshotRepository(root, tuple(approvals)), request
    )
