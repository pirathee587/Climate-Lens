"""CMR tests use synthetic mocked responses; no network in the test suite."""

import io
from urllib.request import Request

import pytest

from app.data import nasa_client


def test_discovery_uses_actual_cmr_short_name(monkeypatch):
    calls = []

    def metadata(path, parameters):
        calls.append((path, parameters))
        return {"synthetic": True}

    monkeypatch.setattr(nasa_client, "_metadata", metadata)
    assert nasa_client.discover_monthly_imerg() == {"synthetic": True}
    assert calls[0][1]["short_name"] == "GPM_3IMERGM"
    assert calls[0][1]["version"] == "07"
    nasa_client.discover_granules("C123-TEST", "2001-01-01,2001-02-01")
    assert calls[1][1]["page_size"] == "10"


def test_metadata_size_limit(monkeypatch):
    class FakeOpener:
        def open(self, request, timeout):
            assert timeout == 20
            assert request.host == "cmr.earthdata.nasa.gov"
            return io.BytesIO(b"x" * (nasa_client.MAX_METADATA_BYTES + 1))

    monkeypatch.setattr(nasa_client, "build_opener", lambda *args: FakeOpener())
    with pytest.raises(ValueError):
        nasa_client.discover_monthly_imerg()


def test_external_redirect_is_rejected():
    request = Request("https://cmr.earthdata.nasa.gov/search/collections.json")
    with pytest.raises(ValueError):
        nasa_client._CMRRedirects().redirect_request(
            request, None, 302, "", {}, "https://untrusted.example"
        )
