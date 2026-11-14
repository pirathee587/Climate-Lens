"""CSV safety and fidelity over artificial cached analyses."""

import csv
import io

import pytest

from app.schemas.analysis import AnalysisRequest
from app.services.export_service import csv_download, metadata, spreadsheet_text
from tests.unit.analysis_fixtures import make_case
from tests.unit.test_analysis_service import service


@pytest.mark.parametrize(
    "text",
    [
        "=1+1",
        "+SUM(A1)",
        "-2+3",
        "@SUM(A1)",
        "  =1",
        "\t=1",
        "\r=1",
        "\n@X",
        "\ufeff=1",
    ],
)
def test_formula_text_is_neutralized(text):
    assert spreadsheet_text(text) == "'" + text


@pytest.mark.parametrize("text", ['SYNTHETIC, "quoted"\nதமிழ்', "snapshot-1", ""])
def test_safe_unicode_text_is_preserved(text):
    assert spreadsheet_text(text) == text


def test_csv_roundtrip_preserves_escaping_and_only_sanitizes_unsafe_text(tmp_path):
    case = make_case(tmp_path)
    result = service(case).analyze(AnalysisRequest(**case.request))
    for snapshot in ['SYNTHETIC, "quoted"\nதமிழ்', '=HYPERLINK("unsafe")']:
        result.source.snapshot_id = snapshot
        response = csv_download(result, "monthly")
        rows = list(csv.DictReader(io.StringIO(response.body.decode("utf-8"))))
        assert rows[0]["snapshot_id"] == spreadsheet_text(snapshot)
        assert len(rows) == len(result.monthly)
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert snapshot not in response.headers["content-disposition"]
        assert str(result.analysis_id) in response.headers["content-disposition"]
    data = metadata(result)
    assert data.source.snapshot_id == result.source.snapshot_id
    assert data.normalized_units == {
        "monthly": "mm",
        "annual": "mm",
        "slope": "mm/year",
    }
    assert data.statistics == result.statistics
    assert data.warnings == result.warnings
