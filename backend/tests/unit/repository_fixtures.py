"""SYNTHETIC ONLY: never a NASA dataset, source citation, ROI or review attestation."""

import hashlib
from pathlib import Path

from app.schemas.repository import (
    NormalizedMonthlyRecord,
    SnapshotDescriptor,
    SnapshotManifest,
)
from app.schemas.source import RegionDescriptor, VariableDescriptor


class SyntheticRepository:
    """Isolated test adapter; never registered by production dependency wiring."""

    def __init__(self, root: Path):
        self.descriptors = []
        self.rows = {}
        self.region_overrides = None
        for region_id, bbox in [
            ("jaffna_area", [0, 0, 1, 1]),
            ("colombo_area", [2, 2, 3, 3]),
        ]:
            rows = (
                NormalizedMonthlyRecord(
                    region_id=region_id,
                    period="2011-01",
                    precipitation_total_mm=7.25,
                    valid_fraction=0.8,
                    quality_flag="synthetic-valid",
                ),
                NormalizedMonthlyRecord(
                    region_id=region_id,
                    period="2011-03",
                    precipitation_total_mm=None,
                    valid_fraction=None,
                    quality_flag="synthetic-missing",
                ),
            )
            # This is only an artificial artifact to check file hashing; no CSV loader.
            snapshot = (
                "SYNTHETIC PYTEST ONLY\n" + "\n".join(r.model_dump_json() for r in rows)
            ).encode()
            manifest = SnapshotManifest(
                snapshot_id="synthetic-" + region_id,
                collection_id="GPM_3IMERGM_07",
                version_label="V07T",
                run_type="Final",
                source_url="https://example.invalid/synthetic-only",
                granule_ids_or_export_reference=("SYNTHETIC-NOT-A-REAL-GRANULE",),
                retrieved_at_utc="2012-01-01T00:00:00Z",
                time_start="2011-01",
                time_end="2011-03",
                original_variable_name="synthetic-variable",
                original_units="mm/hr",
                normalization_units="mm/month",
                spatial_aggregation="synthetic-pytest-only",
                rate_to_total_conversion="synthetic-adapter-already-normalized",
                missing_data_policy="preserve-missing-exclude-incomplete-years",
                input_sha256=hashlib.sha256(b"SYNTHETIC SOURCE ONLY").hexdigest(),
                output_sha256=hashlib.sha256(snapshot).hexdigest(),
                processing_script_or_steps="SYNTHETIC TEST ONLY",
                license_or_usage_notes="NOT A NASA OBSERVATION",
                review={
                    "status": "reviewed",
                    "reviewed_by": "synthetic-test-reviewer",
                    "reviewed_at": "2012-01-02T00:00:00Z",
                    "evidence_reference": "https://example.invalid/synthetic-review",
                },
            )
            raw_manifest = manifest.model_dump_json().encode()
            snapshot_path = f"snapshots/{region_id}.synthetic"
            manifest_path = f"manifests/{region_id}.synthetic.json"
            for relative, data in [
                (snapshot_path, snapshot),
                (manifest_path, raw_manifest),
            ]:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            variable = VariableDescriptor(
                id="precipitation",
                display_name="Synthetic precipitation fixture",
                description="SYNTHETIC TEST ONLY",
                source_dataset_id=manifest.collection_id,
                source_version=manifest.version_label,
                source_run=manifest.run_type,
                aggregation_units="mm",
                time_resolution="monthly",
                first_available_period=manifest.time_start,
                last_available_period=manifest.time_end,
                supported=True,
            )
            region = RegionDescriptor(
                id=region_id,
                name="SYNTHETIC TEST ONLY " + region_id,
                bbox=bbox,
                geometry_source="synthetic-pytest-only",
            )
            self.descriptors.append(
                SnapshotDescriptor(
                    variable=variable,
                    region=region,
                    manifest=manifest,
                    snapshot_path=snapshot_path,
                    manifest_path=manifest_path,
                    manifest_sha256=hashlib.sha256(raw_manifest).hexdigest(),
                )
            )
            self.rows[region_id] = rows

    def list_verified_datasets(self):
        return tuple(self.descriptors)

    def list_verified_regions(self, variable_id):
        assert variable_id == "precipitation"
        return (
            self.region_overrides
            if self.region_overrides is not None
            else tuple(d.region for d in self.descriptors)
        )

    def get_verified_monthly_series(self, variable_id, region_id):
        assert variable_id == "precipitation"
        return self.rows[region_id]


class UnvalidatedDescriptor:
    """Broken-adapter DTO used to ensure the service reparses every field."""

    def __init__(self, raw):
        self.raw = raw

    def model_dump(self, **kwargs):
        return self.raw
