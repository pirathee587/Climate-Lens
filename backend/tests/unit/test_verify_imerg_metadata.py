"""Tests for metadata-only IMERG verification using synthetic HDF5 structure."""

from pathlib import Path

import h5py
import pytest

from scripts.verify_imerg_metadata import inspect_granule


def create_hdf5_fixture(path: Path, *, units: str = "mm/hr") -> None:
    with h5py.File(path, "w") as handle:
        handle.attrs["FileHeader"] = (
            "DOI=10.5067/GPM/IMERG/3B-MONTH/07;\n"
            "AlgorithmID=3IMERGM;\n"
            "ProductVersion=V07B;\n"
            "TimeInterval=MONTH;\n"
            "StartGranuleDateTime=2024-02-01T00:00:00.000Z;\n"
            "StopGranuleDateTime=2024-02-29T23:59:59.999Z;\n"
        )
        grid = handle.create_group("Grid")
        precipitation = grid.create_dataset(
            "precipitation", shape=(1, 3600, 1800), dtype="f4"
        )
        precipitation.attrs["DimensionNames"] = "time,lon,lat"
        precipitation.attrs["units"] = units
        precipitation.attrs["_FillValue"] = -9999.9
        precipitation.attrs["CodeMissingValue"] = "-9999.9"
        grid.create_dataset("lat", data=[-89.95, -89.85])
        grid["lat"].attrs["units"] = "degrees_north"
        grid.create_dataset("lon", data=[-179.95, -179.85])
        grid["lon"].attrs["units"] = "degrees_east"
        grid.create_dataset("time", data=[1390780800], dtype="i4")
        grid["time"].attrs["units"] = "seconds since 1980-01-06 00:00:00 UTC"
        grid["time"].attrs["calendar"] = "julian"
        grid.create_dataset("time_bnds", data=[[1390780800, 1393286400]], dtype="i4")


def test_inspection_requires_real_precipitation_units(tmp_path):
    path = tmp_path / "synthetic.h5"
    create_hdf5_fixture(path)

    report = inspect_granule(path, {"test_area": (-179.95, -89.95, -179.85, -89.85)})

    assert report.precipitation_path == "Grid/precipitation"
    assert report.precipitation_shape == (1, 3600, 1800)
    assert report.precipitation_units == "mm/hr"
    assert report.fill_value == pytest.approx(-9999.9)
    assert report.has_scale_factor is False
    assert report.decoded_time_start == "2024-02-01T00:00:00+00:00"
    assert report.regions["test_area"].grid_cells == 4


def test_inspection_rejects_non_rate_units(tmp_path):
    path = tmp_path / "synthetic.h5"
    create_hdf5_fixture(path, units="mm")

    with pytest.raises(ValueError, match="units must be mm/hr"):
        inspect_granule(path)
