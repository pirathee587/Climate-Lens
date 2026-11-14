"""Verify metadata and region coverage for a local IMERG monthly granule.

This script inspects metadata only. It does not convert values, generate
observations, download data, or write production snapshots.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import h5py

EXPECTED_COLLECTION = "GPM_3IMERGM"
EXPECTED_ALGORITHM_ID = "3IMERGM"
EXPECTED_VERSION = "V07B"
EXPECTED_PRECIPITATION_PATH = "Grid/precipitation"
EXPECTED_SHAPE = (1, 3600, 1800)
EXPECTED_RESOLUTION = 0.1
COORDINATE_BOUNDARY_TOLERANCE = 1e-5
TIME_EPOCH = datetime(1980, 1, 6, tzinfo=UTC)

REGION_BBOXES: dict[str, tuple[float, float, float, float]] = {
    "jaffna_area": (79.95, 9.60, 80.05, 9.70),
    "colombo_area": (79.80, 6.90, 79.90, 7.00),
}


@dataclass(frozen=True)
class RegionCoverage:
    bbox_wgs84: tuple[float, float, float, float]
    longitude_cells: int
    latitude_cells: int
    grid_cells: int
    review_required: bool


@dataclass(frozen=True)
class VerificationReport:
    file_name: str
    collection: str
    product_version: str
    run_type: str
    temporal_resolution: str
    granule_start: str
    granule_end: str
    precipitation_path: str
    precipitation_shape: tuple[int, ...]
    precipitation_dtype: str
    precipitation_units: str
    fill_value: float | None
    code_missing_value: str | None
    has_missing_value_attribute: bool
    has_scale_factor: bool
    has_add_offset: bool
    has_valid_range: bool
    latitude_units: str
    longitude_units: str
    latitude_order: str
    longitude_order: str
    latitude_resolution: float
    longitude_resolution: float
    time_units: str
    time_calendar: str
    decoded_time_start: str
    decoded_time_end: str
    regions: dict[str, RegionCoverage]
    warnings: tuple[str, ...]


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="strict")
    return str(value)


def _attribute(attrs: h5py.AttributeManager, name: str) -> Any:
    if name not in attrs:
        return None
    value = attrs[name]
    if hasattr(value, "item"):
        return value.item()
    return value


def _require_text(attrs: h5py.AttributeManager, name: str) -> str:
    value = _attribute(attrs, name)
    if value is None:
        raise ValueError(f"required HDF5 attribute is missing: {name}")
    return _text(value)


def _header_value(header: str, name: str) -> str:
    prefix = f"{name}="
    for field in header.replace("\r", "").replace("\n", "").split(";"):
        if field.startswith(prefix):
            value = field.removeprefix(prefix)
            if value:
                return value
    raise ValueError(f"required FileHeader field is missing: {name}")


def _require_close(actual: float, expected: float, name: str) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=0.001):
        raise ValueError(f"{name} must be approximately {expected}, got {actual}")


def _coordinate_resolution(values: list[float], name: str) -> float:
    if len(values) < 2:
        raise ValueError(f"{name} coordinate array must contain at least two values")
    differences = [
        right - left for left, right in zip(values, values[1:], strict=False)
    ]
    if not all(difference > 0 for difference in differences):
        raise ValueError(f"{name} coordinates must be strictly ascending")
    resolution = sum(differences) / len(differences)
    _require_close(resolution, EXPECTED_RESOLUTION, f"{name} resolution")
    return resolution


def _decode_time(value: int) -> str:
    return (TIME_EPOCH + timedelta(seconds=value)).isoformat()


def _region_coverage(
    bbox: tuple[float, float, float, float],
    longitudes: list[float],
    latitudes: list[float],
) -> RegionCoverage:
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError(f"invalid WGS84 bbox: {bbox}")
    longitude_cells = sum(
        west - COORDINATE_BOUNDARY_TOLERANCE
        <= value
        <= east + COORDINATE_BOUNDARY_TOLERANCE
        for value in longitudes
    )
    latitude_cells = sum(
        south - COORDINATE_BOUNDARY_TOLERANCE
        <= value
        <= north + COORDINATE_BOUNDARY_TOLERANCE
        for value in latitudes
    )
    grid_cells = longitude_cells * latitude_cells
    return RegionCoverage(
        bbox_wgs84=bbox,
        longitude_cells=longitude_cells,
        latitude_cells=latitude_cells,
        grid_cells=grid_cells,
        review_required=grid_cells < 4,
    )


def inspect_granule(
    path: Path,
    region_bboxes: dict[str, tuple[float, float, float, float]] = REGION_BBOXES,
) -> VerificationReport:
    """Inspect one IMERG HDF5 granule and return metadata-only verification."""
    with h5py.File(path, "r") as handle:
        file_header = _require_text(handle.attrs, "FileHeader")
        precipitation = handle[EXPECTED_PRECIPITATION_PATH]
        latitude = handle["Grid/lat"]
        longitude = handle["Grid/lon"]
        time = handle["Grid/time"]
        time_bounds = handle["Grid/time_bnds"]

        if f"AlgorithmID={EXPECTED_ALGORITHM_ID}" not in file_header:
            raise ValueError("FileHeader does not identify the expected IMERG product")
        product_version = _header_value(file_header, "ProductVersion")
        if product_version != EXPECTED_VERSION:
            raise ValueError(
                f"expected ProductVersion {EXPECTED_VERSION}, got {product_version}"
            )
        if _header_value(file_header, "TimeInterval") != "MONTH":
            raise ValueError("granule is not a monthly product")
        if precipitation.shape != EXPECTED_SHAPE:
            raise ValueError(
                f"unexpected precipitation shape: {precipitation.shape}; "
                f"expected {EXPECTED_SHAPE}"
            )
        if _require_text(precipitation.attrs, "units") != "mm/hr":
            raise ValueError("Grid/precipitation units must be mm/hr")
        if _require_text(precipitation.attrs, "DimensionNames") != "time,lon,lat":
            raise ValueError("unexpected precipitation dimension order")
        if "_FillValue" not in precipitation.attrs:
            raise ValueError("Grid/precipitation must define _FillValue")

        latitudes = [float(value) for value in latitude[...]]
        longitudes = [float(value) for value in longitude[...]]
        latitude_resolution = _coordinate_resolution(latitudes, "latitude")
        longitude_resolution = _coordinate_resolution(longitudes, "longitude")
        if _require_text(latitude.attrs, "units") != "degrees_north":
            raise ValueError("latitude units must be degrees_north")
        if _require_text(longitude.attrs, "units") != "degrees_east":
            raise ValueError("longitude units must be degrees_east")
        time_units = _require_text(time.attrs, "units")
        if time_units != "seconds since 1980-01-06 00:00:00 UTC":
            raise ValueError(f"unexpected time units: {time_units}")
        time_calendar = _require_text(time.attrs, "calendar")
        if time_calendar != "julian":
            raise ValueError(f"unexpected time calendar: {time_calendar}")
        if time.shape != (1,) or time_bounds.shape != (1, 2):
            raise ValueError("monthly time coordinates have unexpected dimensions")

        warnings = tuple(
            f"{region} intersects only {coverage.grid_cells} source grid cell(s); "
            "team review is required before finalizing the regional ROI."
            for region, coverage in (
                (name, _region_coverage(bbox, longitudes, latitudes))
                for name, bbox in region_bboxes.items()
            )
            if coverage.review_required
        )
        regions = {
            name: _region_coverage(bbox, longitudes, latitudes)
            for name, bbox in region_bboxes.items()
        }
        return VerificationReport(
            file_name=path.name,
            collection=EXPECTED_COLLECTION,
            product_version=product_version,
            run_type="Final",
            temporal_resolution=_header_value(file_header, "TimeInterval"),
            granule_start=_header_value(file_header, "StartGranuleDateTime"),
            granule_end=_header_value(file_header, "StopGranuleDateTime"),
            precipitation_path=EXPECTED_PRECIPITATION_PATH,
            precipitation_shape=tuple(precipitation.shape),
            precipitation_dtype=str(precipitation.dtype),
            precipitation_units=_require_text(precipitation.attrs, "units"),
            fill_value=float(precipitation.attrs["_FillValue"]),
            code_missing_value=_text(
                _attribute(precipitation.attrs, "CodeMissingValue")
            )
            if "CodeMissingValue" in precipitation.attrs
            else None,
            has_missing_value_attribute="missing_value" in precipitation.attrs,
            has_scale_factor="scale_factor" in precipitation.attrs,
            has_add_offset="add_offset" in precipitation.attrs,
            has_valid_range="valid_range" in precipitation.attrs,
            latitude_units=_require_text(latitude.attrs, "units"),
            longitude_units=_require_text(longitude.attrs, "units"),
            latitude_order="ascending",
            longitude_order="ascending",
            latitude_resolution=latitude_resolution,
            longitude_resolution=longitude_resolution,
            time_units=time_units,
            time_calendar=time_calendar,
            decoded_time_start=_decode_time(int(time[0])),
            decoded_time_end=_decode_time(int(time_bounds[0, 1])),
            regions=regions,
            warnings=warnings,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="local IMERG monthly HDF5 granule")
    args = parser.parse_args()
    report = inspect_granule(args.file)
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
