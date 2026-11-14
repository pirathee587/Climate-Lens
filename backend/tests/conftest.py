import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def app():
    return create_app(Settings(app_env="test"))


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client
