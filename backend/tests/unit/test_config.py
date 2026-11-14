from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_SNAPSHOT_ROOT, Settings


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)


def test_defaults_are_explicit():
    settings = Settings.from_env()
    assert settings.app_env == "development"
    assert settings.app_port == 8000
    assert settings.allowed_origins == ("http://localhost:5173",)
    assert settings.snapshot_root == DEFAULT_SNAPSHOT_ROOT
    assert (
        settings.snapshot_root == Path(__file__).resolve().parents[3] / "data" / "demo"
    )
    assert settings.log_level == "INFO"


def test_environment_overrides(monkeypatch, tmp_path):
    for name, value in {
        "APP_ENV": "production",
        "APP_PORT": "8123",
        "ALLOWED_ORIGINS": "https://example.org, http://localhost:5173",
        "SNAPSHOT_ROOT": str(tmp_path),
        "LOG_LEVEL": "WARNING",
    }.items():
        monkeypatch.setenv(name, value)
    settings = Settings.from_env()
    assert settings.app_env == "production"
    assert settings.app_port == 8123
    assert settings.allowed_origins == ("https://example.org", "http://localhost:5173")
    assert settings.snapshot_root == tmp_path
    assert settings.log_level == "WARNING"


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*.example.org",
        "ftp://example.org",
        "https://example.org/path",
        "https://user:secret@example.org",
        "https://example.org:bad",
        "null",
        "https://example.org?token=secret",
        "https://example.org/#secret",
    ],
)
def test_unsafe_origins_rejected(origin):
    with pytest.raises(ValidationError):
        Settings(allowed_origins=(origin,))


@pytest.mark.parametrize(
    "name,value",
    [
        ("APP_ENV", "invalid"),
        ("APP_PORT", "0"),
        ("APP_PORT", "65536"),
        ("LOG_LEVEL", "VERBOSE"),
    ],
)
def test_invalid_environment_fails_at_startup(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings.from_env()


def test_empty_origin_list_disables_browser_access(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "")
    assert Settings.from_env().allowed_origins == ()
