"""Shared v1 contracts. Undefined scientific values are explicit nulls."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue

Year = Annotated[int, Field(strict=True, ge=1, le=9999)]
Alpha = Annotated[float, Field(gt=0, lt=1, allow_inf_nan=False)]
NonEmpty = Annotated[str, Field(min_length=1)]
Period = Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


class APIModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        validate_assignment=True,
        validate_default=True,
    )


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
    service: Literal["terratrend-api"] = "terratrend-api"
    api_version: Literal["v1"] = "v1"


class ErrorDetail(APIModel):
    code: NonEmpty
    message: NonEmpty
    details: dict[str, JsonValue] = Field(default_factory=dict)
    request_id: UUID


class ErrorResponse(APIModel):
    error: ErrorDetail
