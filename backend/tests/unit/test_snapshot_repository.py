"""Integrity validation over exclusively synthetic adapter fixtures in tmp_path."""

import hashlib

import pytest
from pydantic import ValidationError

from app.core.errors import APIError
from app.schemas.repository import SnapshotDescriptor, SnapshotManifest
from app.services.catalog import CatalogService
from app.services.snapshot_repository import UnavailableSnapshotRepository
from app.services.snapshot_validation import checked_artifact, validate_series
from tests.unit.repository_fixtures import SyntheticRepository, UnvalidatedDescriptor


@pytest.fixture
def repo(tmp_path):
    return SyntheticRepository(tmp_path)


def replace_descriptor(repo, transform):
    data = repo.descriptors[0].model_dump()
    transform(data)
    # A broken upstream adapter must not bypass structural revalidation.
    repo.descriptors[0] = UnvalidatedDescriptor(data)


def assert_unavailable(repo, root):
    for operation in ("variables", "regions"):
        with pytest.raises(APIError) as error:
            getattr(CatalogService(repo, root), operation)()
        assert error.value.status_code == 503
        assert error.value.code == "DATASET_UNAVAILABLE"
        assert str(root) not in error.value.message


def test_default_repository_stays_unavailable_even_with_files(repo, tmp_path):
    assert_unavailable(UnavailableSnapshotRepository(), tmp_path)


def test_successful_catalog_preserves_adapter_values(repo, tmp_path):
    service = CatalogService(repo, tmp_path)
    assert service.variables().variables == [repo.descriptors[0].variable]
    assert service.regions().regions == [d.region for d in repo.descriptors]
    assert service.variables().variables[0].source_version == "V07T"
    assert service.variables().variables[0].first_available_period == "2011-01"


def test_gap_and_null_are_preserved_without_imputation(repo, tmp_path):
    d = repo.descriptors[0]
    validated = validate_series(d, repo.rows[d.region.id], tmp_path)
    assert validated.missing_periods == ("2011-02",)
    assert validated.observations[1].precipitation_total_mm is None
    assert validated.observations[1].valid_fraction is None
    assert validated.observations[1].quality_flag == "synthetic-missing"
    assert validated.observations[0].precipitation_total_mm == 7.25
    assert validated.descriptor.manifest.original_units == "mm/hr"
    assert validated.descriptor.manifest.normalization_units == "mm/month"


@pytest.mark.parametrize(
    "field",
    [
        "source_url",
        "review",
        "input_sha256",
        "output_sha256",
        "granule_ids_or_export_reference",
        "processing_script_or_steps",
        "original_units",
    ],
)
def test_missing_manifest_fields_rejected(repo, tmp_path, field):
    replace_descriptor(repo, lambda data: data["manifest"].pop(field))
    assert_unavailable(repo, tmp_path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("collection_id", "OTHER_DATASET"),
        ("version_label", "V08B"),
        ("run_type", "Early"),
        ("normalization_units", "mm/hr"),
        ("output_sha256", "not-a-checksum"),
        ("time_start", "0000-01"),
        ("time_end", "2010-01"),
        ("retrieved_at_utc", "2000-01-01T00:00:00Z"),
        ("source_url", "https://user:private@example.invalid/file"),
        ("source_url", "https://example.invalid/file?token=private"),
        ("granule_ids_or_export_reference", []),
    ],
)
def test_invalid_manifest_values_rejected(repo, tmp_path, field, value):
    replace_descriptor(repo, lambda data: data["manifest"].update({field: value}))
    assert_unavailable(repo, tmp_path)


@pytest.mark.parametrize("artifact", ["snapshot_path", "manifest_path"])
@pytest.mark.parametrize("operation", ["remove", "corrupt"])
def test_missing_or_corrupt_artifacts(repo, tmp_path, artifact, operation):
    path = tmp_path / getattr(repo.descriptors[0], artifact)
    if operation == "remove":
        path.unlink()
    else:
        path.write_bytes(b"CORRUPTED SYNTHETIC FIXTURE")
    assert_unavailable(repo, tmp_path)


@pytest.mark.parametrize(
    "bbox",
    [
        [0, 0, None, 1],
        [0, 0, 181, 1],
        [2, 0, 1, 1],
        [0, 0, float("nan"), 1],
        [0, -91, 1, 1],
    ],
)
def test_invalid_geometry_rejected(repo, tmp_path, bbox):
    replace_descriptor(repo, lambda data: data["region"].update(bbox=bbox))
    assert_unavailable(repo, tmp_path)


@pytest.mark.parametrize("region", [None, "unexpected_region"])
def test_two_region_requirement(repo, tmp_path, region):
    if region is None:
        repo.descriptors.pop()
    else:
        replace_descriptor(repo, lambda data: data["region"].update(id=region))
    assert_unavailable(repo, tmp_path)


def test_repository_region_views_must_agree(repo, tmp_path):
    repo.region_overrides = (repo.descriptors[0].region,)
    assert_unavailable(repo, tmp_path)


@pytest.mark.parametrize(
    "operation", ["duplicate", "reverse", "empty", "wrong_region", "outside_coverage"]
)
def test_invalid_series_rejected(repo, tmp_path, operation):
    key = repo.descriptors[0].region.id
    rows = repo.rows[key]
    repo.rows[key] = {
        "duplicate": rows + (rows[1],),
        "reverse": rows[::-1],
        "empty": (),
        "wrong_region": (rows[0].model_copy(update={"region_id": "other"}), rows[1]),
        "outside_coverage": (rows[0], rows[1].model_copy(update={"period": "2012-01"})),
    }[operation]
    assert_unavailable(repo, tmp_path)


@pytest.mark.parametrize("field", ["precipitation_total_mm", "valid_fraction"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_adapter_records_rejected(repo, tmp_path, field, value):
    key = repo.descriptors[0].region.id
    rows = repo.rows[key]
    repo.rows[key] = (rows[0].model_copy(update={field: value}), rows[1])
    assert_unavailable(repo, tmp_path)


@pytest.mark.parametrize(
    "relative",
    [
        "../private",
        "/etc/passwd",
        "snapshots/../../private",
        "C:/private",
        "C:\\private",
        "\\\\server\\private",
        "",
        ".",
        "snapshots",
    ],
)
def test_unsafe_or_nonfile_paths_rejected(repo, tmp_path, relative):
    with pytest.raises((ValueError, OSError)):
        checked_artifact(tmp_path, relative)


def test_symlink_escape_rejected(repo, tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-private")
    outside.write_bytes(b"synthetic private file")
    link = tmp_path / "escape"
    link.symlink_to(outside)
    with pytest.raises(ValueError):
        checked_artifact(tmp_path, "escape")
    (tmp_path / "escape-dir").symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(ValueError):
        checked_artifact(tmp_path, "escape-dir/" + outside.name)


def test_artifact_path_failures_map_to_safe_503(repo, tmp_path):
    replace_descriptor(repo, lambda data: data.update(snapshot_path="../private"))
    assert_unavailable(repo, tmp_path)


def test_unreviewed_hash_match_is_not_verification(repo, tmp_path):
    replace_descriptor(
        repo, lambda data: data["manifest"]["review"].update(status="unreviewed")
    )
    assert_unavailable(repo, tmp_path)


def test_dataset_variants_cannot_be_mixed(repo, tmp_path):
    # Both internally valid but incompatible source versions must fail together.
    raw = repo.descriptors[1].model_dump()
    raw["variable"]["source_version"] = "V07U"
    raw["manifest"]["version_label"] = "V07U"
    manifest_bytes = (
        SnapshotManifest.model_validate(raw["manifest"]).model_dump_json().encode()
    )
    (tmp_path / raw["manifest_path"]).write_bytes(manifest_bytes)
    raw["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    repo.descriptors[1] = SnapshotDescriptor.model_validate(raw)
    assert_unavailable(repo, tmp_path)


def test_manifest_catalog_mismatch_rejected(repo):
    data = repo.descriptors[0].model_dump()
    data["variable"]["source_version"] = "V07Z"
    with pytest.raises(ValidationError):
        SnapshotDescriptor.model_validate(data)


def test_artifacts_are_read_only(repo, tmp_path):
    files = list(tmp_path.rglob("*.synthetic*"))
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
    CatalogService(repo, tmp_path).variables()
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files} == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("original_units", "kelvin"),
        ("original_variable_name", "verify-from-file"),
        ("spatial_aggregation", "   "),
    ],
)
def test_undocumented_units_and_placeholder_metadata_rejected(
    repo, tmp_path, field, value
):
    replace_descriptor(repo, lambda data: data["manifest"].update({field: value}))
    assert_unavailable(repo, tmp_path)


def test_invalid_period_from_adapter_rejected(repo, tmp_path):
    key = repo.descriptors[0].region.id
    rows = repo.rows[key]
    repo.rows[key] = (rows[0].model_copy(update={"period": "2011-13"}), rows[1])
    assert_unavailable(repo, tmp_path)
