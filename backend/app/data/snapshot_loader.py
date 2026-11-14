"""Bounded CSV loading, shared by offline import and the approved adapter."""

import csv
import io
import math
from datetime import datetime
from pathlib import Path

from app.data.imerg_processor import normalize_precipitation, parse_period
from app.data.manifest_builder import (
    CSV_COLUMNS,
    MAX_MONTHS,
    MAX_SOURCE_BYTES,
    ImportRecipe,
)
from app.schemas.repository import NormalizedMonthlyRecord
from app.services.snapshot_validation import checked_artifact


def read_bounded(root: Path, relative: str, limit: int = MAX_SOURCE_BYTES) -> bytes:
    path = checked_artifact(root, relative)
    with path.open("rb") as stream:
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise ValueError("artifact exceeds size limit")
    return content


def _csv_rows(raw: bytes, skip: int = 0) -> csv.DictReader:
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds size limit")
    stream = io.StringIO(raw.decode("utf-8-sig"), newline="")
    for _ in range(skip):
        if not stream.readline():
            raise ValueError("source header skip exceeds file")
    reader = csv.DictReader(stream)
    names = reader.fieldnames
    if not names or len(names) != len(set(names)):
        raise ValueError("source header is missing or duplicated")
    return reader


def _optional_number(value: str, missing_tokens: tuple[str, ...]) -> float | None:
    if value in missing_tokens:
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite source observation")
    return result


def load_source(
    raw: bytes, recipe: ImportRecipe
) -> tuple[NormalizedMonthlyRecord, ...]:
    reader = _csv_rows(raw, recipe.skip_header_lines)
    required = [recipe.period_column, recipe.value_column]
    required += [
        c for c in (recipe.valid_fraction_column, recipe.quality_flag_column) if c
    ]
    if not set(required).issubset(reader.fieldnames):
        raise ValueError("source columns do not match explicit import mapping")
    rows, periods = [], set()
    for index, entry in enumerate(reader):
        if (
            index >= MAX_MONTHS
            or None in entry
            or any(v is None for v in entry.values())
        ):
            raise ValueError("source row limit or shape violation")
        raw_period = entry[recipe.period_column]
        parsed = datetime.strptime(raw_period, recipe.period_format)
        if parsed.strftime(recipe.period_format) != raw_period:
            raise ValueError("source date must exactly match declared format")
        period = parsed.strftime("%Y-%m")
        parse_period(period)
        if period in periods:
            raise ValueError("duplicate region-month record")
        periods.add(period)
        value = _optional_number(entry[recipe.value_column], recipe.missing_tokens)
        total = normalize_precipitation(
            value, period, recipe.original_units, recipe.fill_values
        )
        fraction = (
            _optional_number(entry[recipe.valid_fraction_column], recipe.missing_tokens)
            if recipe.valid_fraction_column
            else None
        )
        quality = (
            entry[recipe.quality_flag_column]
            if recipe.quality_flag_column
            else ("missing" if total is None else "valid_numeric_no_source_quality")
        )
        rows.append(
            NormalizedMonthlyRecord(
                region_id=recipe.region.id,
                period=period,
                precipitation_total_mm=total,
                valid_fraction=fraction,
                quality_flag=quality,
            )
        )
    if not rows:
        raise ValueError("no source observations")
    return tuple(sorted(rows, key=lambda row: row.period))


def load_normalized(raw: bytes) -> tuple[NormalizedMonthlyRecord, ...]:
    reader = _csv_rows(raw)
    if tuple(reader.fieldnames) != CSV_COLUMNS:
        raise ValueError("normalized CSV columns do not match canonical contract")
    rows = []
    for index, entry in enumerate(reader):
        if (
            index >= MAX_MONTHS
            or None in entry
            or any(v is None for v in entry.values())
        ):
            raise ValueError("normalized CSV row limit or shape violation")
        parse_period(entry["period"])
        for column in ("precipitation_total_mm", "valid_fraction"):
            entry[column] = _optional_number(entry[column], ("",))
        rows.append(NormalizedMonthlyRecord.model_validate(entry))
    return tuple(rows)
