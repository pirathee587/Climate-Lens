"""HTTP static/Vite checks only; this does not assert browser UI behavior."""

import argparse
import re
from urllib.parse import urljoin
from urllib.request import urlopen


def check_frontend(base_url: str, environment: str) -> None:
    with urlopen(base_url, timeout=5) as response:
        html = response.read().decode("utf-8")
        if response.status != 200 or 'id="root"' not in html:
            raise RuntimeError("frontend application root missing")
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)
    if not scripts:
        raise RuntimeError("frontend script assets missing")
    for source in scripts:
        with urlopen(urljoin(base_url, source), timeout=5) as response:
            if response.status != 200 or not response.read():
                raise RuntimeError("frontend asset unavailable")
    if environment == "production":
        with urlopen(urljoin(base_url, "/investigate"), timeout=5) as response:
            if 'id="root"' not in response.read().decode():
                raise RuntimeError("SPA fallback unavailable")
    print("PASS frontend HTTP assets and applicable SPA fallback; not browser E2E")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--environment", choices=("production", "development"), required=True
    )
    args = parser.parse_args()
    check_frontend(args.base_url, args.environment)
