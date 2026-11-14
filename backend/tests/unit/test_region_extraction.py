"""Synthetic decoded grids, unrelated to actual Sri Lankan or NASA measurements."""

import math

import pytest
from pydantic import ValidationError

from app.data.region_extractor import area_average
from app.schemas.source import RegionDescriptor


def region(bbox):
    return RegionDescriptor(
        id="synthetic", name="Synthetic", bbox=bbox, geometry_source="synthetic"
    )


def test_spherical_latitude_area_weighting():
    result = area_average(region([0, 0, 1, 60]), (0, 1), (0, 30, 60), ((10,), (20,)))
    first = math.sin(math.radians(30))
    second = math.sin(math.radians(60)) - first
    assert result.value == pytest.approx((10 * first + 20 * second) / (first + second))
    assert result.value != pytest.approx(15)
    assert result.valid_fraction == pytest.approx(1)


def test_partial_boundary_cells_and_missing_area_fraction():
    result = area_average(region([0.5, 0, 2, 1]), (0, 1, 2), (0, 1), ((2, None),))
    assert result.value == 2
    assert result.valid_fraction == pytest.approx(1 / 3)


def test_fill_cells_and_all_missing():
    result = area_average(
        region([0, 0, 2, 1]), (0, 1, 2), (0, 1), ((-9999, None),), (-9999,)
    )
    assert result.value is None and result.valid_fraction == 0


@pytest.mark.parametrize("bbox", [[2, 0, 1, 1], [0, 0, 181, 1], [0, 0, None, 1]])
def test_invalid_region_bounds(bbox):
    with pytest.raises(ValidationError):
        region(bbox)


@pytest.mark.parametrize(
    "lons,lats,values",
    [
        ((0, 0), (0, 1), ((1,),)),
        ((0, 1), (1, 0), ((1,),)),
        ((0, float("nan")), (0, 1), ((1,),)),
        ((0, 1), (0, 1), ((1, 2),)),
        ((0, 1), (0, 1), ((-1,),)),
        ((0, 1), (0, 1), ((float("inf"),),)),
        ((0, 0.5), (0, 1), ((1,),)),
    ],
)
def test_invalid_or_incomplete_grid(lons, lats, values):
    with pytest.raises(ValueError):
        area_average(region([0, 0, 1, 1]), lons, lats, values)
