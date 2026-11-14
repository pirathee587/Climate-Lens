"""Synthetic bundles test the real loader; no live NASA output."""

import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.data.manifest_builder import canonical_json
from app.data.repository_adapter import ArtifactApproval, HarithSnapshotRepository
from app.main import create_app
from app.services.catalog import CatalogService
from app.services.snapshot_repository import get_snapshot_repository
from tests.unit.data_fixtures import synthetic_bundle


@pytest.fixture
def approved(tmp_path):
    return tmp_path, tuple(
        synthetic_bundle(tmp_path, region) for region in ("jaffna_area", "colombo_area")
    )


def test_real_adapter_satisfies_protocol_and_injected_catalogs(approved):
    root, approvals = approved
    repository = HarithSnapshotRepository(root, approvals)
    descriptors = repository.list_verified_datasets()
    assert len(descriptors) == 2
    rows = repository.get_verified_monthly_series("precipitation", "jaffna_area")
    assert [r.precipitation_total_mm for r in rows] == [672, 696]
    assert rows[1].valid_fraction is None
    assert len(repository.list_verified_regions("precipitation")) == 2
    assert repository.get_verified_monthly_series("precipitation", "unknown") == ()
    assert repository.list_verified_regions("other") == ()
    app = create_app(Settings(app_env="test", snapshot_root=root))
    app.dependency_overrides[get_snapshot_repository] = lambda: repository
    with TestClient(app) as client:
        assert client.get("/api/v1/variables").status_code == 200
        assert client.get("/api/v1/regions/presets").status_code == 200
    # Returned objects can be mutated without changing the next load from disk.
    descriptors[0].region.name = "mutated-test-object"
    assert repository.list_verified_datasets()[0].region.name == "SYNTHETIC TEST AREA"


def test_unapproved_files_are_never_discovered(approved):
    root, approvals = approved
    assert HarithSnapshotRepository(root, ()).list_verified_datasets() == ()
    partial = HarithSnapshotRepository(root, approvals[:1])
    with pytest.raises(Exception) as error:
        CatalogService(partial, root).variables()
    assert error.value.status_code == 503


@pytest.mark.parametrize(
    "relative", ["../private", "/etc/passwd", "C:/private", "missing.json"]
)
def test_unsafe_approval_paths_rejected(tmp_path, relative):
    repo = HarithSnapshotRepository(
        tmp_path,
        (ArtifactApproval(descriptor_path=relative, descriptor_sha256="a" * 64),),
    )
    with pytest.raises((ValueError, OSError)):
        repo.list_verified_datasets()


@pytest.mark.parametrize("artifact", ["descriptor", "manifest", "snapshot", "source"])
def test_artifact_corruption_and_hashes_rejected(approved, artifact):
    root, approvals = approved
    descriptor = json.loads((root / approvals[0].descriptor_path).read_bytes())
    path = {
        "descriptor": approvals[0].descriptor_path,
        "manifest": descriptor["manifest_path"],
        "snapshot": descriptor["snapshot_path"],
        "source": "sources/synthetic-jaffna_area.csv",
    }[artifact]
    (root / path).write_bytes(b"corrupted synthetic artifact")
    with pytest.raises((ValueError, OSError)):
        HarithSnapshotRepository(root, approvals).list_verified_datasets()


def test_descriptor_symlink_escape_rejected(approved, tmp_path):
    root, approvals = approved
    path = root / approvals[0].descriptor_path
    data = path.read_bytes()
    path.unlink()
    outside = tmp_path.parent / (tmp_path.name + "-outside.json")
    outside.write_bytes(data)
    path.symlink_to(outside)
    with pytest.raises(ValueError):
        HarithSnapshotRepository(root, approvals).list_verified_datasets()


def test_unreviewed_bundle_cannot_be_approved(tmp_path):
    synthetic_bundle(tmp_path, review=False)
    path = "manifests/synthetic-jaffna_area.json"
    approval = ArtifactApproval(
        descriptor_path=path,
        descriptor_sha256=hashlib.sha256((tmp_path / path).read_bytes()).hexdigest(),
    )
    with pytest.raises(ValueError):
        HarithSnapshotRepository(tmp_path, (approval,)).list_verified_datasets()


def test_product_variants_cannot_be_mixed(tmp_path):
    left = synthetic_bundle(tmp_path, "jaffna_area")
    right = synthetic_bundle(tmp_path, "colombo_area", version_label="V07U")
    with pytest.raises(ValueError):
        HarithSnapshotRepository(tmp_path, (left, right)).list_verified_datasets()


def test_reviewed_envelope_and_descriptor_must_agree(approved):
    root, approvals = approved
    raw = json.loads((root / approvals[0].descriptor_path).read_bytes())
    raw["region"]["bbox"] = [0, 0, 2, 2]
    content = canonical_json(raw)
    (root / approvals[0].descriptor_path).write_bytes(content)
    changed = ArtifactApproval(
        descriptor_path=approvals[0].descriptor_path,
        descriptor_sha256=hashlib.sha256(content).hexdigest(),
    )
    with pytest.raises(ValueError):
        HarithSnapshotRepository(root, (changed, approvals[1])).list_verified_datasets()


def test_rehashed_wrong_output_still_fails_source_reproduction(approved):
    root, approvals = approved
    descriptor_path = root / approvals[0].descriptor_path
    descriptor = json.loads(descriptor_path.read_bytes())
    snapshot = root / descriptor["snapshot_path"]
    snapshot.write_bytes(snapshot.read_bytes().replace(b"672.0", b"999.0"))
    envelope_path = root / descriptor["manifest_path"]
    envelope = json.loads(envelope_path.read_bytes())
    new_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    envelope["manifest"]["output_sha256"] = new_hash
    descriptor["manifest"]["output_sha256"] = new_hash
    envelope_path.write_bytes(canonical_json(envelope))
    descriptor["manifest_sha256"] = hashlib.sha256(
        envelope_path.read_bytes()
    ).hexdigest()
    descriptor_path.write_bytes(canonical_json(descriptor))
    changed = ArtifactApproval(
        descriptor_path=approvals[0].descriptor_path,
        descriptor_sha256=hashlib.sha256(descriptor_path.read_bytes()).hexdigest(),
    )
    with pytest.raises(ValueError):
        HarithSnapshotRepository(root, (changed, approvals[1])).list_verified_datasets()
