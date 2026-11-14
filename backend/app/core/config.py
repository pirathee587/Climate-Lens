"""Explicit environment configuration; no implicit .env or credential loading."""

import json
import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.data.repository_adapter import ArtifactApproval
from app.schemas.quality import ReviewedQualityPolicy

DEFAULT_SNAPSHOT_ROOT = Path(__file__).resolve().parents[3] / "data" / "demo"


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, validate_default=True, extra="forbid")
    app_env: Literal["development", "test", "production"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    allowed_origins: tuple[str, ...] = ("http://localhost:5173",)
    snapshot_root: Path = DEFAULT_SNAPSHOT_ROOT
    snapshot_approvals: tuple[ArtifactApproval, ...] = Field(default=(), max_length=2)
    snapshot_quality_policies: tuple[ReviewedQualityPolicy, ...] = Field(
        default=(), max_length=2
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("snapshot_approvals", "snapshot_quality_policies")
    @classmethod
    def unique_review_records(cls, records):
        keys = [
            record.descriptor_path
            if isinstance(record, ArtifactApproval)
            else record.snapshot_sha256.lower()
            for record in records
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate snapshot review configuration")
        return records

    @field_validator("allowed_origins")
    @classmethod
    def explicit_origins(cls, origins: tuple[str, ...]) -> tuple[str, ...]:
        for origin in origins:
            parsed = urlsplit(origin)
            try:
                _ = parsed.port
            except ValueError:
                raise ValueError("invalid origin port") from None
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or "*" in origin
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
                or any(c.isspace() for c in origin)
            ):
                raise ValueError("ALLOWED_ORIGINS requires explicit HTTP(S) origins")
        return tuple(dict.fromkeys(origins))

    @classmethod
    def from_env(cls) -> "Settings":
        values = {}
        for name in cls.model_fields:
            raw = os.environ.get(name.upper())
            if raw is not None:
                if name in {"snapshot_approvals", "snapshot_quality_policies"}:
                    values[name] = json.loads(raw)
                    continue
                values[name] = (
                    tuple(s.strip() for s in raw.split(",") if s.strip())
                    if name == "allowed_origins"
                    else raw
                )
        return cls.model_validate(values)
