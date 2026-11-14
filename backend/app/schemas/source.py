"""Verified-manifest response shapes; constructing models does not verify sources."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, HttpUrl, model_validator

from app.schemas.common import APIModel, NonEmpty, Period

Coordinate = Annotated[float, Field(allow_inf_nan=False)]
BBox = tuple[Coordinate, Coordinate, Coordinate, Coordinate]


class RegionDescriptor(APIModel):
    id: NonEmpty
    name: NonEmpty
    bbox: BBox
    label_type: Literal["bbox_area_near_city"] = "bbox_area_near_city"
    geometry_source: NonEmpty

    @model_validator(mode="after")
    def valid_bounds(self) -> "RegionDescriptor":
        west, south, east, north = self.bbox
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("bbox must be ordered WGS84 west,south,east,north")
        return self


class SourceDescriptor(APIModel):
    collection_id: NonEmpty
    version: NonEmpty
    run_type: Literal["Final"]
    original_variable: NonEmpty
    original_unit: NonEmpty
    snapshot_id: NonEmpty
    snapshot_sha256: Annotated[str, Field(pattern=r"^[a-fA-F0-9]{64}$")]
    retrieved_at: AwareDatetime
    source_uri: HttpUrl
    aggregation_method: NonEmpty


class VariableDescriptor(APIModel):
    id: Literal["precipitation"]
    display_name: NonEmpty
    description: NonEmpty
    source_dataset_id: NonEmpty
    source_version: NonEmpty
    source_run: Literal["Final"]
    aggregation_units: Literal["mm"]
    time_resolution: Literal["monthly"]
    first_available_period: Period
    last_available_period: Period
    supported: Literal[True]

    @model_validator(mode="after")
    def ordered_coverage(self) -> "VariableDescriptor":
        if self.first_available_period > self.last_available_period:
            raise ValueError("catalog coverage must be ordered")
        return self


class VariablesResponse(APIModel):
    variables: list[VariableDescriptor]


class RegionsResponse(APIModel):
    regions: list[RegionDescriptor]
