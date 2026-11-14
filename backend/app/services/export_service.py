"""Deterministic bounded exports of cached results; no filesystem/network/science."""

import csv
import io
from typing import Literal

from starlette.responses import Response

from app.schemas.analysis import AnalysisResponse, ReproducibilityMetadata

MONTHLY_COLUMNS = (
    "region_id",
    "period",
    "precipitation_total_mm",
    "valid_fraction",
    "snapshot_id",
)
ANNUAL_COLUMNS = (
    "region_id",
    "year",
    "precipitation_total_mm",
    "valid_months",
    "snapshot_id",
)


def spreadsheet_text(value: str) -> str:
    # CSV quoting alone does not prevent spreadsheet formula interpretation.
    significant = value.lstrip(" \t\r\n\ufeff")
    if significant.startswith(("=", "+", "-", "@")) or value.startswith(
        ("\t", "\r", "\n")
    ):
        return "'" + value
    return value


def csv_download(
    result: AnalysisResponse, frequency: Literal["monthly", "annual"]
) -> Response:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(MONTHLY_COLUMNS if frequency == "monthly" else ANNUAL_COLUMNS)
    region = spreadsheet_text(result.region.id)
    snapshot = spreadsheet_text(result.source.snapshot_id)
    if frequency == "monthly":
        for row in result.monthly:
            writer.writerow(
                (
                    region,
                    row.period,
                    row.precipitation_total_mm,
                    row.valid_fraction,
                    snapshot,
                )
            )
    else:
        for row in result.annual:
            writer.writerow(
                (
                    region,
                    row.year,
                    row.precipitation_total_mm,
                    row.valid_months,
                    snapshot,
                )
            )
    # UUID + server constant only: source IDs never enter filenames or headers.
    filename = f"terratrend-{result.analysis_id}-{frequency}.csv"
    return Response(
        buffer.getvalue().encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def metadata(result: AnalysisResponse) -> ReproducibilityMetadata:
    return ReproducibilityMetadata(
        analysis_id=result.analysis_id,
        request=result.request,
        region=result.region,
        source=result.source,
        normalized_units={"monthly": "mm", "annual": "mm", "slope": "mm/year"},
        statistics=result.statistics,
        algorithm_version=result.algorithm_version,
        warnings=result.warnings,
        scientific_limitations=[
            "Satellite-derived estimates have source and measurement uncertainty.",
            "Annual totals require 12 eligible months; missing values are not imputed.",
            "Trend evidence establishes neither causes nor between-region differences.",
            "Respect returned assumptions, warnings and indeterminate significance.",
        ],
    )
