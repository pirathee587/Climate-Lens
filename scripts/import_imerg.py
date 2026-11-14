#!/usr/bin/env python3
"""Offline import of authentic external regional exports, not an API downloader."""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

# Supports direct invocation from the repository root without installing a package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.data.manifest_builder import MAX_SOURCE_BYTES, ImportRecipe, write_import
from app.data.nasa_client import discover_monthly_imerg
from app.data.snapshot_loader import load_source
from app.schemas.repository import ProvenanceReview


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--discover", action="store_true", help="public bounded CMR metadata only"
    )
    parser.add_argument("--recipe-schema", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--recipe", type=Path)
    parser.add_argument(
        "--output-root", type=Path, default=Path("data/raw/imerg-preparation")
    )
    parser.add_argument(
        "--review",
        type=Path,
        help="genuine human review JSON; never generated automatically",
    )
    args = parser.parse_args()
    if args.recipe_schema:
        print(json.dumps(ImportRecipe.model_json_schema(), indent=2))
        return 0
    if args.discover:
        print(json.dumps(discover_monthly_imerg(), indent=2))
        return 0
    if not args.source or not args.recipe:
        parser.error("--source and --recipe are required for offline import")
    if args.recipe.stat().st_size > 1_000_000 or (
        args.review and args.review.stat().st_size > 1_000_000
    ):
        raise ValueError("metadata exceeds size limit")
    recipe = ImportRecipe.model_validate_json(args.recipe.read_bytes())
    review = (
        ProvenanceReview.model_validate_json(args.review.read_bytes())
        if args.review
        else None
    )
    with args.source.open("rb") as stream:
        source = stream.read(MAX_SOURCE_BYTES + 1)
    if len(source) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds size limit")
    rows = load_source(source, recipe)
    manifest, descriptor = write_import(args.output_root, recipe, source, rows, review)
    result = {
        "status": "reviewed_artifact_created" if descriptor else "awaiting_review",
        "manifest": manifest,
        "descriptor": descriptor,
        "record_count": len(rows),
    }
    if descriptor:
        result["descriptor_sha256"] = hashlib.sha256(
            (args.output_root / descriptor).read_bytes()
        ).hexdigest()
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, csv.Error) as error:
        print(
            "Import failed: "
            + type(error).__name__
            + ". Check source metadata and limits locally.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
