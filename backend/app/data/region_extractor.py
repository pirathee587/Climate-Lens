"""Spherical area average for a small decoded rectilinear grid, not a file decoder."""

import math
from dataclasses import dataclass

from app.data.imerg_processor import checked_value
from app.schemas.source import RegionDescriptor

MAX_CELLS = 100_000


@dataclass(frozen=True)
class AreaAverage:
    value: float | None
    valid_fraction: float


def _area(west: float, south: float, east: float, north: float) -> float:
    # R^2 cancels in the weighted mean; exact spherical lat/lon cell areas.
    return math.radians(east - west) * (
        math.sin(math.radians(north)) - math.sin(math.radians(south))
    )


def area_average(
    region: RegionDescriptor,
    longitude_edges: tuple[float, ...],
    latitude_edges: tuple[float, ...],
    values: tuple[tuple[float | None, ...], ...],
    fill_values: tuple[float, ...] = (),
) -> AreaAverage:
    region = RegionDescriptor.model_validate(region.model_dump())
    nx, ny = len(longitude_edges) - 1, len(latitude_edges) - 1
    if nx < 1 or ny < 1 or nx * ny > MAX_CELLS:
        raise ValueError("grid size outside supported limits")
    for edges, low, high in [(longitude_edges, -180, 180), (latitude_edges, -90, 90)]:
        if any(not math.isfinite(x) for x in edges):
            raise ValueError("nonfinite coordinates")
        if (
            edges[0] < low
            or edges[-1] > high
            or any(a >= b for a, b in zip(edges, edges[1:], strict=False))
        ):
            raise ValueError("grid edges must be increasing WGS84 coordinates")
    if len(values) != ny or any(len(row) != nx for row in values):
        raise ValueError("grid shape mismatch")
    west, south, east, north = region.bbox
    if not (
        longitude_edges[0] <= west < east <= longitude_edges[-1]
        and latitude_edges[0] <= south < north <= latitude_edges[-1]
    ):
        raise ValueError("requested region is not fully covered by grid")
    weighted_values, valid_area = [], 0.0
    for j in range(ny):
        for i in range(nx):
            w, e = max(west, longitude_edges[i]), min(east, longitude_edges[i + 1])
            s, n = max(south, latitude_edges[j]), min(north, latitude_edges[j + 1])
            if w >= e or s >= n:
                continue
            value = checked_value(values[j][i], fill_values)
            if value is not None:
                weight = _area(w, s, e, n)
                valid_area += weight
                weighted_values.append((value, weight))
    fraction = min(1.0, max(0.0, valid_area / _area(west, south, east, north)))
    mean = (
        math.fsum(value * (weight / valid_area) for value, weight in weighted_values)
        if valid_area
        else None
    )
    if mean is not None and not math.isfinite(mean):
        raise ValueError("spatial aggregation overflow")
    return AreaAverage(mean, fraction)
