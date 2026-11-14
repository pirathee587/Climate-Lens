"""All generated bundles are synthetic and live only in pytest tmp_path."""

import json

import pytest
from pydantic import ValidationError

from app.data.manifest_builder import build_artifacts, write_import
from app.data.snapshot_loader import load_source
from tests.unit.data_fixtures import (
    SYNTHETIC_SOURCE,
    synthetic_recipe,
    synthetic_review,
)


def test_review_is_never_automatically_fabricated(tmp_path):
    recipe = synthetic_recipe()
    rows = load_source(SYNTHETIC_SOURCE, recipe)
    path, descriptor = write_import(tmp_path, recipe, SYNTHETIC_SOURCE, rows)
    envelope = json.loads((tmp_path / path).read_bytes())
    assert envelope["status"] == "awaiting_review"
    assert envelope["manifest"]["review"] is None
    assert descriptor is None
    assert not list(tmp_path.rglob("*.descriptor.json"))
    assert "2023-03" in envelope["missing_periods"]
    assert (tmp_path / envelope["source_path"]).read_bytes() == SYNTHETIC_SOURCE


def test_deterministic_import_and_calculated_hashes():
    import hashlib

    recipe = synthetic_recipe()
    rows = load_source(SYNTHETIC_SOURCE, recipe)
    a = build_artifacts(recipe, SYNTHETIC_SOURCE, rows, synthetic_review())
    b = build_artifacts(recipe, SYNTHETIC_SOURCE, rows, synthetic_review())
    assert a == b
    assert a[2].input_sha256 == hashlib.sha256(SYNTHETIC_SOURCE).hexdigest()
    assert a[2].output_sha256 == hashlib.sha256(a[0]).hexdigest()


def test_import_refuses_overwrite(tmp_path):
    recipe = synthetic_recipe()
    rows = load_source(SYNTHETIC_SOURCE, recipe)
    write_import(tmp_path, recipe, SYNTHETIC_SOURCE, rows)
    with pytest.raises(FileExistsError):
        write_import(tmp_path, recipe, SYNTHETIC_SOURCE, rows)


def test_import_rejects_symlink_directory(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "snapshots").symlink_to(outside, target_is_directory=True)
    recipe = synthetic_recipe()
    with pytest.raises(FileExistsError):
        write_import(
            root, recipe, SYNTHETIC_SOURCE, load_source(SYNTHETIC_SOURCE, recipe)
        )
    assert not list(outside.iterdir())


@pytest.mark.parametrize(
    "overrides",
    [
        {"original_units": "kelvin"},
        {"collection_id": "GPM_3IMERGM_08"},
        {"version_label": "V08B"},
        {"run_type": "Early"},
        {"source_url": "http://example.invalid"},
        {"source_url": "https://user:secret@example.invalid"},
        {"snapshot_id": "../escape"},
        {"fill_values": [float("nan")]},
    ],
)
def test_invalid_source_metadata(overrides):
    with pytest.raises(ValidationError):
        synthetic_recipe(**overrides)


def test_review_must_follow_actual_retrieval():
    recipe = synthetic_recipe()
    review = synthetic_review().model_copy(
        update={"reviewed_at": recipe.retrieved_at_utc.replace(year=2020)}
    )
    with pytest.raises(ValidationError):
        build_artifacts(
            recipe, SYNTHETIC_SOURCE, load_source(SYNTHETIC_SOURCE, recipe), review
        )
