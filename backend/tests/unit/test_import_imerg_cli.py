"""The actual CLI is exercised only with synthetic files in pytest tmp_path."""

import json
import subprocess
import sys
from pathlib import Path

from tests.unit.data_fixtures import SYNTHETIC_SOURCE, synthetic_recipe

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "import_imerg.py"


def test_cli_draft_and_recipe_schema(tmp_path):
    source, recipe = tmp_path / "source.csv", tmp_path / "recipe.json"
    source.write_bytes(SYNTHETIC_SOURCE)
    recipe.write_text(synthetic_recipe().model_dump_json())
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source",
            str(source),
            "--recipe",
            str(recipe),
            "--output-root",
            str(tmp_path / "bundle"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["status"] == "awaiting_review"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--recipe-schema"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "original_units" in json.loads(result.stdout)["properties"]


def test_cli_error_does_not_leak_source_paths(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source",
            str(tmp_path / "private"),
            "--recipe",
            str(tmp_path / "missing"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert str(tmp_path) not in result.stderr
    assert "Traceback" not in result.stderr
