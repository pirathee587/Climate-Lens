"""Bounded public CMR discovery for controlled offline preparation."""

import json
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_METADATA_BYTES = 2_000_000


class _CMRRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname != "cmr.earthdata.nasa.gov":
            raise ValueError("CMR redirect left approved host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _metadata(path: str, parameters: dict[str, str]) -> dict:
    url = "https://cmr.earthdata.nasa.gov/search/" + path + "?" + urlencode(parameters)
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "TerraTrend-offline-import/1",
        },
    )
    with build_opener(_CMRRedirects()).open(request, timeout=20) as response:
        raw = response.read(MAX_METADATA_BYTES + 1)
    if len(raw) > MAX_METADATA_BYTES:
        raise ValueError("CMR response exceeds metadata limit")
    return json.loads(raw)


def discover_monthly_imerg() -> dict:
    # CMR short name differs from the documented product identifier GPM_3IMERGM_07.
    return _metadata(
        "collections.json",
        {"short_name": "GPM_3IMERGM", "version": "07", "page_size": "10"},
    )


def discover_granules(collection_concept_id: str, temporal: str) -> dict:
    if not collection_concept_id.startswith("C") or not temporal or len(temporal) > 100:
        raise ValueError("invalid discovery constraints")
    # Bounded single-page discovery; no bulk download or unbounded pagination.
    return _metadata(
        "granules.json",
        {
            "collection_concept_id": collection_concept_id,
            "temporal": temporal,
            "page_size": "10",
        },
    )
