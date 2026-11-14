# Harith NASA data module — TT-02 / TT-03

## 1. Implementation status

**CONTRACT-READY BUT BLOCKED** — 14 November 2026.
Offline external-export import, precipitation normalization, decoded-grid area
weighting, review-gated manifests and a concrete read-only repository adapter are
implemented. No real observations or genuine provenance review are available.
No NASA observations, reviewer records or scientific findings were fabricated.

Owner: Harith. The clean feature branch was created from the specified verified
remote Phase 02 branch at bb3dfb4, without reset/stash/merge. Pirathee's orchestration,
provider wiring, schemas, Gaja's algorithms, frontend, original specifications,
workflows, dependency pins and existing data/demo placeholders are unchanged.

Created files:

```text
backend/app/data/__init__.py
backend/app/data/nasa_client.py
backend/app/data/imerg_processor.py
backend/app/data/region_extractor.py
backend/app/data/manifest_builder.py
backend/app/data/snapshot_loader.py
backend/app/data/repository_adapter.py
backend/tests/unit/data_fixtures.py
backend/tests/unit/test_nasa_client.py
backend/tests/unit/test_imerg_processing.py
backend/tests/unit/test_region_extraction.py
backend/tests/unit/test_manifest_builder.py
backend/tests/unit/test_import_imerg_cli.py
backend/tests/integration/test_nasa_repository_adapter.py
scripts/import_imerg.py
backend/DATA_MODULE_REPORT.md
```

## 2. NASA acquisition method and actual access results

The implemented public CMR discovery command succeeded:

```bash
backend/.venv/bin/python scripts/import_imerg.py --discover
```

Actual [CMR collection query](https://cmr.earthdata.nasa.gov/search/collections.json?short_name=GPM_3IMERGM&version=07&page_size=10)
uses short name GPM_3IMERGM and version 07. A separate query for short name
GPM_3IMERGM_07 returned no collections; the latter is the backend product identifier.

A [January 2001 granule query](https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C2723754851-GES_DISC&temporal=2001-01-01T00%3A00%3A00Z,2001-01-31T23%3A59%3A59Z&page_size=1)
returned the actual published data URL below. Its HEAD request returned **403**:

https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGM.07/2001/3B-MO.MS.MRG.3IMERG.20010101-S000000-E235959.01.V07B.HDF5

No observation file was downloaded. No local .netrc or configured Earthdata
credential environment variables were present. This proves access failure for this
request, not its cause or that every NASA access method is unavailable. No restriction
was bypassed, and no unnecessary global dataset was downloaded.

Implemented fallback: authentic externally obtained, already area-averaged monthly
CSV exports, such as documented Giovanni exports, with explicit source metadata.
The module does not scrape Giovanni sessions, perform authenticated downloads, or
decode HDF5/NetCDF. The grid helper accepts a small decoded rectilinear grid; it is
not a satellite-file decoder. The CSV path never averages an export a second time.

References: [NASA IMERG](https://gpm.nasa.gov/data/imerg),
[NASA migration guidance](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md).

## 3. Exact dataset identifiers observed

- CMR collection: C2723754851-GES_DISC; short name GPM_3IMERGM; version 07.
- Title: GPM IMERG Final Precipitation L3 1 month 0.1 degree x 0.1 degree V07.
- January 2001 granule: G2819417581-GES_DISC.
- Published filename: 3B-MO.MS.MRG.3IMERG.20010101-S000000-E235959.01.V07B.HDF5.

V07B is visible in the filename. Internal field attributes, original units, scaling,
fill values and quality fields have not been inspected. Filename/collection discovery
is not file-level scientific verification.

## 4. Actual observation coverage

**No real processed observation coverage exists.** CMR metadata reports collection
coverage 1998-01-01 through 2025-09-30 and the discovered granule covers January 2001.
The preferred 2001–2024 window is a target, not locally verified snapshot coverage.

## 5. Geographic bounding boxes and evidence

[GeoNames Sri Lanka city listing](https://www.geonames.org/advanced-search.html?country=LK&q=)
reports Jaffna at latitude 9.668445975969965, longitude 80.00741958618164, and Colombo
at latitude 6.93548, longitude 79.84868. A reproducible candidate design is each city
point plus/minus 0.2 degrees in both axes, rounded to six decimals:

| Candidate area | WGS84 [west, south, east, north] |
|---|---|
| Jaffna area | [79.807420, 9.468446, 80.207420, 9.868446] |
| Colombo area | [79.648680, 6.735480, 80.048680, 7.135480] |

These are engineering study-window proposals derived from referenced points, not
verified NASA extraction extents or official district boundaries. They appear here
only and are not active presets. Coastal windows may include ocean/lagoon cells;
no land-only interpretation is justified. Human review must approve the footprint
and confirm it matches actual export metadata before activation. The importer requires
explicit bounds and geographic attribution, rather than shipping invented presets.

## 6. Original and normalized units

Actual source-file units remain unverified. The importer accepts explicitly documented
mm/hr, mm or mm/month. Output is mm/month; public aggregation units remain mm. No
source unit, version or date coverage is inferred from documentation examples.

## 7. Source-to-output transformation

CSV import uses explicit column/date mapping, UTF-8 decoding and bounded metadata-header
skipping. Values must already be decoded and spatially averaged; source scaling and
aggregation must be checked from export metadata and recorded in review evidence.

mm/hr is multiplied by 24 and actual Gregorian days in the month, including leap years.
Already accumulated mm/mm/month is unchanged. Declared fill values and missing tokens
remain null. Negative non-fill values, NaN/Infinity, invalid dates, malformed rows and
duplicate months are rejected. Rows are sorted; interior missing periods are listed,
not filled. Source quality flags and fractions are preserved where supplied; absent
fractions remain null. Generated valid/missing flags describe numeric usability only.

Canonical CSV columns are:
region_id,period,precipitation_total_mm,valid_fraction,quality_flag.
Blank numeric cells reload as null, never zero.

Decoded-grid weighting uses exact spherical latitude/longitude area proportional to
longitude width times sin(north)-sin(south), clipping partial boundary cells. Fill
cells are excluded; valid area/whole ROI area is reported. Uncovered ROIs are rejected.
This helper is separate from the already-area-averaged CSV import.

Limits: sources 10 MB; metadata/descriptor reads 1 MB; rows and span 2400 months;
decoded grids 100000 cells; CMR single-page metadata 2 MB and 20-second socket timeout.
No unbounded concurrency/pagination, database or public API downloader exists.
Imports refuse overwrites/symlink directories. Adapter reads reuse root-confinement
and traversal/absolute/Windows/symlink guards. Bundle directories must be trusted and
immutable during serving; this is not a sandbox for hostile concurrent filesystem writers.

## 8. Snapshot file list and preparation commands

**No real snapshots/manifests published.** data/demo remains untouched; test bundles
exist only in pytest temporary directories.

Generate the exact input contract without fake source metadata:

```bash
backend/.venv/bin/python scripts/import_imerg.py --recipe-schema > /tmp/imerg-recipe.schema.json
```

Populate a recipe from the authentic export and source metadata, including dataset,
version/run, source/granule references, source retrieval timestamp, actual units,
variable, region bounds/reference, spatial method, usage notes and CSV column names.
The recipe requires spatial_method=externally_area_averaged; optional fill tokens,
quality/fraction columns, date format and header skipping must match the export.

```bash
backend/.venv/bin/python scripts/import_imerg.py \
  --source /path/to/authentic-export.csv \
  --recipe /path/to/actual-recipe.json \
  --output-root data/raw/imerg-preparation
```

Default staging is gitignored. An unreviewed bundle contains:

```text
sources/<snapshot_id>.csv       # original bytes preserved
snapshots/<snapshot_id>.csv     # normalized records
manifests/<snapshot_id>.json    # envelope: awaiting_review, review null
```

A genuine supplied review JSON must satisfy the existing ProvenanceReview contract:
reviewed status, actual reviewer, timezone-aware review time and evidence URL. The
reviewer must check source authenticity, units/scaling, exact footprint, quality,
coverage, conversion and hashes. No command generates that attestation for them.

After review, rerun into a new staging root with --review /path/to/actual-review.json.
This additionally writes manifests/<snapshot_id>.descriptor.json and prints its
computed fingerprint. Never overwrite an existing bundle. Only then explicitly
promote approved bundles to the configured snapshot root. Original source bytes must
remain available inside that root for replay verification; do not commit large raw
files. Different archival storage requires a reviewed storage/adapter contract change.
No promotion/publishing occurred during this task.

## 9. Provenance review status

**Outstanding.** No real reviewed descriptor was generated. Unreviewed bundles cannot
pass the adapter's review gate. Test review objects are explicitly synthetic and
isolated in tests. Hashes are calculated from bytes and establish relative integrity,
not independent NASA authenticity or human scientific approval.

## 10. Repository adapter details

HarithSnapshotRepository implements list_verified_datasets, list_verified_regions and
get_verified_monthly_series. It accepts the configured root and explicit ArtifactApproval
objects containing descriptor paths and independently reviewed SHA-256 fingerprints.
No runtime glob/discovery/autoapproval or network access occurs; an empty allowlist
returns no data. Missing/malformed/unapproved artifacts are rejected.

Each load checks descriptor/envelope/snapshot hashes, existing DTOs, source provenance
and original source bytes. It replays the same importer and compares rebuilt metadata,
all normalized records and normalized bytes. Rehashing incorrect output alone cannot
hide a wrong source transformation. Mixed versions/coverage, incompatible processing,
missing review, mismatched geometry and duplicate approved regions are rejected.
Returned objects are freshly loaded, so caller mutation cannot affect later reads.
Pirathee's service still enforces complete two-region readiness and safe 503 errors.

## 11. Tests, security and Docker

Actual backend-directory commands:

```text
.venv/bin/python -m ruff check .                          PASS
.venv/bin/python -m ruff format --check .                 49 files formatted
.venv/bin/python -m ruff check ../scripts/import_imerg.py --config pyproject.toml
                                                         PASS
.venv/bin/python -m ruff format --check ../scripts/import_imerg.py --config pyproject.toml
                                                         1 file formatted
.venv/bin/python -m pytest -q                             219 passed, 1 warning
.venv/bin/python -m pip check                            No broken requirements found
.venv/bin/python -m pip_audit -r requirements-dev.lock --no-deps --disable-pip
                                                         No known vulnerabilities found
```

All 139 Phase 01/02 tests still pass. Added tests cover calendar conversions, no double
conversion, fill/null/quality behavior, missing months, duplicates/dates/finite values,
size/count limits, spherical weighting/partial cells, review gates, deterministic
hashes, actual CLI execution, corruption, path/symlink guards, source replay, mixed
versions and success through dependency-injected catalog APIs. No live network is
required by tests. One existing upstream Starlette/httpx deprecation warning remains;
pip-audit also recommends hashed wheel locks. Dependencies/pins were unchanged.

Repository-root verification:

```text
docker build -f backend/Dockerfile -t terratrend-api:tt03 backend
PASS; image sha256:863295b0468ff3a19831b4e825a5c3770dab4cc7a0887a2a5a3af94c24fa5f19
python3 /tmp/terratrend_tt03_smoke.py
PASS: data modules import without extra dependencies; UID 10001; network disabled;
Docker HEALTHCHECK healthy; health 200; catalogs 503; production docs 404;
analysis/comparison POST 404. Temporary container removed after verification.
docker run --rm -v "$PWD:/repo:ro" zricethezav/gitleaks:v8.24.2 dir /repo --redact --no-banner
PASS: no leaks found (scanned ~755111 bytes).
git diff --check                                         PASS
```

An initial root-directory lint invocation with an explicit backend config changed
import classification. The required backend-working-directory checks pass; no baseline
imports were rewritten to accommodate that invocation.

## 12. Git branch and commit

Repository: pirathee587/Climate-Lens.
Branch: feat/tt-03-harith-nasa-snapshots.
Base: origin/feat/tt-05-pirathee-phase02-nasa-integration at bb3dfb4.
Truthful message: feat(data): implement IMERG ingestion pipeline and repository adapter.
Commit SHA will be recorded after implementation commit/push.

## 13. GitHub push status

Pending initial implementation commit at report creation. Only the sixteen enumerated
Harith-owned module/test/script/report files may be staged. No git add . or git add -A,
force push, PR, merge or deployment is performed.

## 14. CI run URL and result

Existing backend CI supports main pushes, relevant PRs and manual dispatch; feature
pushes do not trigger it. Backend-only manual dispatch will be attempted after push.
Local verification above is distinct from hosted CI; its actual result will be recorded.

## 15. Remaining blockers

Genuine regional observations/exports, source attributes and actual extraction metadata
are absent. The tested CMR data URL returned 403 and no Earthdata credentials are
configured. Original units/scaling/quality and actual bounds need source inspection.
Independent provenance review and explicit approval remain outstanding. Authenticated
bulk retrieval/raw HDF5 decoding is not implemented; the supported fallback requires
an authentic externally area-averaged CSV. No numerical findings or full demo readiness
are claimed, and production catalogs remain unavailable.

## 16. Pirathee integration instructions

Do not activate now. Once both real source-reviewed bundles are available:

1. Keep original sources, normalized CSVs, envelopes and descriptors under immutable
   SNAPSHOT_ROOT; independently verify source evidence and descriptor fingerprints.
2. Create a tuple of ArtifactApproval(descriptor_path=..., descriptor_sha256=...) using
   reviewed fingerprints, not a runtime scan of arbitrary files.
3. Construct HarithSnapshotRepository(settings.snapshot_root, approvals).
4. In a separately authorized Pirathee integration change, connect that adapter through
   get_snapshot_repository and the existing dependency injection boundary. Provider
   wiring was not changed here; do not add a runtime importer or NASA downloader.
5. Verify both catalogs return actual validated metadata; missing either region must
   remain 503. Hand validated monthly totals, coverage/quality and missing-period
   information to the later science integration. Gaja/Pirathee Phase 03 stays separate.

Final conclusion: **CONTRACT-READY BUT BLOCKED**. Working ingestion and adapter code are
ready for authentic source acquisition and review; the production dataset is not ready.
