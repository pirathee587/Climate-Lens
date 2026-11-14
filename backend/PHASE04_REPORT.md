# Pirathee Phase 04 — TT-05 comparison, result cache and exports

## 1. Final status

**CONTRACT-READY BUT BLOCKED.** Working comparison, result retrieval, monthly/annual
CSV and reproducibility metadata routes pass synthetic integration tests. Real
independently reviewed NASA observations and approved source-quality policies are
still absent. Production analysis/comparison/catalogs therefore remain 503. Synthetic
results are artificial algorithm/integration fixtures, not NASA measurements.

## 2. Implementation summary and ownership

Base branch: feat/tt-05-pirathee-phase03-analysis-api.
Actual fetched base SHA: d04715427f7237f3e50ee55f7ce15d2d22841010.
New branch: feat/tt-05-pirathee-phase04-comparison-export.
Separate clean worktree: /tmp/terratrend-phase04. The original checkout's uncommitted
shared_analyzed_years documentation edit remains untouched. No reset/rebase/force
push, main merge, PR, deployment or Phase 05 work.
Existing latest Phase 03 base was tested before editing: 320 passed, 1 warning,
3.48 seconds. Prior 9c1eb57 CI was not reused as Phase 04 evidence.
Harith's backend/app/data, Gaja's backend/app/statistics and all frontend files
remain byte-identical to the base (verified with git diff). No dependencies,
Dockerfile or workflows changed. FR-017/018/019 and NFR-011/014 are addressed;
SRS was inspected and its requirements/traceability were not rewritten.

## 3. Comparison API

POST /api/v1/comparisons reuses existing ComparisonRequest/ComparisonResponse.
FastAPI Depends injects ComparisonService, existing AnalysisService and an
application-local cache. A single catalog validation pass returns exact checked
snapshots used by both regional analyses. Harith's repository may internally replay
artifacts multiple times; no unmeasured performance improvement is claimed.
Same region, invalid variable/alpha/source mode/period/unknown region →422
INVALID_ARGUMENT; <10 shared complete years →422 INSUFFICIENT_DATA.
Missing/corrupt/unreviewed source or policy →503 DATASET_UNAVAILABLE.
Existing safe science errors, CORS and X-Request-ID remain intact.
Both output analyses are independently computed by the unchanged real engine.
No analysis is copied for the other region. Distinct server UUIDs are preserved.
ComparisonResponse validates exact ordered shared years, minimum 10, distinct regions/
IDs and matching requested period. Each side retains monthly/annual/source/statistics/
warning fields. Cache publication occurs only after complete comparison success.

## 4. Compatibility validation

The existing strict two-region CatalogService checks source variable, collection,
version, Final run, original units/normalization, spatial method, time coverage,
conversion/missing policy and reviewed provenance. Both source-bound quality
policies are checked by the existing analysis service. No readiness bypass added.
Missing/mutated or inconsistent repository metadata cannot establish trustworthy
compatibility and remain 503. The final trusted-result compatibility defense compares
product/version/Final run and original variable/unit/processing; a proven mismatch
there raises 409 INCOMPATIBLE_DATA. Under the strict current catalog, normal source
mismatches fail earlier 503. Unit tests simulate trusted results at the defensive
check; they are not evidence that unreviewed repository mismatches return 409.
Compatibility flags on successful responses are truthful and all true.

## 5. Shared complete-year methodology

Each region's annual totals/counts and statistics come from Gaja through the existing
AnalysisService. A year is complete only when 12 eligible monthly values produced a
nonnull annual total. shared_analyzed_years is the sorted intersection. At least 10
shared years are mandatory; requested endpoints are never changed or extended.
Independent estimates retain each region's own complete-year sample. This preserves
the Phase 03 scientific pipeline without changing Gaja algorithms. If sets differ,
explicit warnings state these are not matched-sample comparisons and list left,
right and shared years. Annual nulls, valid-month counts, excluded-year and quality
warnings stay visible. No cross-region difference significance or cause is inferred.
Kavishanth's current frontend mirror lacks shared_analyzed_years and derives display
years locally; its owner should consume the backend field. Backend fields are
preserved; frontend files were inspected and left unchanged. Fitted OLS points
remain a separate coordinated additive contract, not implemented here.

## 6. Result cache design

ResultCache belongs to app.state, one instance per create_app call. Standard library
OrderedDict, RLock, time.monotonic and immutable UTF-8 JSON payload bytes are used.
Every batch is deeply revalidated/serialized before any mutation; reads deserialize
fresh nested objects. Caller mutations cannot corrupt stored results. Successful
single analyses preserve their original UUID. Successful comparison pairs publish
atomically under one lock; unsuccessful analyses/comparisons publish nothing.
No source credentials or raw NASA files are cached. No database or external service.

## 7. TTL, capacity and memory limits

- RESULT_CACHE_TTL_SECONDS: default 1200 (20 minutes), integer range 1..86400.
- RESULT_CACHE_MAX_ENTRIES: default 100, integer range 2..1000. Minimum two allows pairs.
- Fixed serialized JSON limit 2 MiB per entry and 32 MiB total retained payloads.
- Expired entries are purged on cache operations; expired IDs cannot be returned.
- Oldest insertion is deterministically evicted at count or byte capacity.
- Reads refresh neither deadlines nor eviction order.
- Invalid/oversized batches fail before eviction/publication; no partial pair remains.

Limits bound retained payloads, not a claim about total Python process RSS. There is
no background expiry thread; expired entries consume bounded capacity until the
next operation. Restart clears results. Independent apps/workers/replicas cannot
retrieve each other's IDs. Use a single worker for the P0 demonstration.
Tests inject a clock and cover exact expiry boundaries, FIFO, mutation and threads.

## 8. Retrieval

GET /api/v1/analyses/{analysis_id}: original validated AnalysisResponse, same content,
ID, provenance and warnings. Unknown/expired/evicted/restarted IDs return 404
NOT_FOUND; malformed UUIDs return 422 INVALID_ARGUMENT. No source reload, NASA
network request or statistical recomputation occurs. Request tracing is preserved.

## 9. CSV contracts

GET /api/v1/analyses/{id}/export.csv monthly columns:
region_id,period,precipitation_total_mm,valid_fraction,snapshot_id.
GET /api/v1/analyses/{id}/annual.csv annual columns:
region_id,year,precipitation_total_mm,valid_months,snapshot_id.
UTF-8 text/csv; charset=utf-8; deterministic headers and chronological rows.
Null numeric values are blank, annual nulls/counts match cached output exactly.
Standard csv quoting handles commas, quotes, CR/LF and Unicode. Dangerous text
beginning with =,+,-,@ after whitespace/BOM, or tab/CR/LF, is apostrophe-prefixed
for spreadsheets. JSON retains original identifiers; unsafe CSV identifiers use
that safe representation. Download filenames contain only UUID plus fixed suffix.
Allowed-origin CORS exposes Content-Disposition. Exports read only bounded cached
results, no arbitrary paths, files, network or aggregation. Unknown/expired IDs 404.
The sessionless POST export alternative is not implemented.

## 10. Metadata and provenance

Full analysis retrieval is canonical reproducibility JSON. The additive download
GET /api/v1/analyses/{id}/metadata.json provides analysis_id, request, region, source,
normalized_units, statistics, algorithm_version, warnings and scientific_limitations.
Source includes actual validated collection/version/Final run, variable/original
units, snapshot ID/hash, source URI, retrieval timestamp and processing method.
Normalized monthly/annual units are mm; slope mm/year. Method and assumptions are
retained in statistics/warnings; measurement, completeness and inference caveats are
explicit. No local source paths or review credentials are returned. Safe JSON
attachment filename uses UUID. The additive contract is documented in API_SPEC.

## 11. Exact changed files

- backend/PHASE04_REPORT.md
- backend/README.md
- backend/app/api/v1/analyses.py
- backend/app/api/v1/comparisons.py
- backend/app/api/v1/router.py
- backend/app/core/config.py
- backend/app/main.py
- backend/app/schemas/analysis.py
- backend/app/services/analysis_service.py
- backend/app/services/comparison_service.py
- backend/app/services/export_service.py
- backend/app/services/result_cache.py
- backend/tests/integration/test_analysis_api.py
- backend/tests/integration/test_catalog_ready.py
- backend/tests/integration/test_catalog_unavailable.py
- backend/tests/integration/test_comparison_api.py
- backend/tests/integration/test_export_api.py
- backend/tests/integration/test_health.py
- backend/tests/unit/analysis_fixtures.py
- backend/tests/unit/test_comparison_service.py
- backend/tests/unit/test_export_service.py
- backend/tests/unit/test_result_cache.py
- docs/API_SPEC.md

## 12. Actual local tests and checks

Final full run: python -m pytest -q → **385 passed, 1 warning in 5.86 seconds**.
One upstream Starlette TestClient/httpx deprecation warning remains; no failed tests.
Coverage includes the 320 existing Phase01–03/Harith/Gaja cases and 65 new cases:
independent rising/falling analyses; single validation pass; exactly 10 common years;
different samples; <10 intersection even with 10 per side; source version/run/
processing/provenance failure; unknown/same region; missing policy/artifacts;
no partial cache after second-side scientific failure or insufficient common years;
configuration/TTL/entry and byte limits/FIFO/mutation/thread access; app isolation/
restart; CSV fields/rows/nulls/fractions/annual counts; Unicode/quoting/formula
protection/safe filenames; canonical and dedicated metadata; expired IDs; offline
retrieval; production safe503 and disabled docs.
Initial expanded run had 384 passes and one fixture failure: removal of the first
month changed declared source coverage and correctly caused 503. Test gap moved to
April to test insufficient common years without invalidating coverage. No validation
rule was weakened. Initial Ruff style findings were corrected before final checks.

Executed with the existing Python 3.12 venv and isolated backend working directory:

- python -m ruff check .: passed.
- python -m ruff format --check .: passed, 81 files before this report.
- python -m pip check: no broken requirements.
- python -m pip_audit -r requirements-dev.lock --no-deps --disable-pip:
  no known vulnerabilities. Existing version locks are not wheel hash locks.
- scripts/import_imerg.py Ruff lint/format using backend config: passed.
- Gitleaks v8.24.2 directory scan: no leaks; 638.03 KB before report creation.
- git diff --check: passed.

## 13. Docker verification

Existing backend Dockerfile built terratrend-api:phase04 successfully. Snap Docker
cannot access host /tmp directly, so backend context was tar-streamed into
docker build -f Dockerfile -t terratrend-api:phase04 -. No Dockerfile workaround
or source changes were needed. Image e6b8b00371485f56cb18e226e6e070cd08a00bdf25623d6b3d9e76f0a666dee2.
A later app module docstring cleanup does not change runtime behavior; hosted CI
will build the exact committed tree.
Real smoke with --network none passed: UID 10001; Harith/Gaja/NumPy/SciPy imports;
health 200; variables/regions/valid analysis/valid comparison 503 DATASET_UNAVAILABLE;
unknown result, monthly CSV, annual CSV and metadata 404 NOT_FOUND; malformed UUID 422;
production docs/OpenAPI 404. Temporary container removed. No database/NASA credentials
or runtime external network dependency. Synthetic API 200 tests are not a real-data
Docker demonstration and do not imply NASA readiness.

## 14. GitHub delivery

Repository: pirathee587/Climate-Lens. Required commit message:
feat(backend): implement regional comparison and CSV export.
Implementation SHA: 1a225c146f2e502a9134ba9890411256638c56db.
Push succeeded with upstream tracking set to the new Phase 04 branch. git ls-remote
confirmed this exact remote implementation SHA. A subsequent documentation-only
commit records hosted evidence; it does not change tested application code.
Latest report commit SHA is available from branch HEAD and final delivery response.
No git add . or git add -A.
Only the listed backend/test/documentation files are staged individually.

## 15. Hosted backend CI

**SUCCESS** — backend-ci.yml workflow_dispatch, run 43585154230.
https://github.com/pirathee587/Climate-Lens/actions/runs/43585154230
Actual tested SHA: 1a225c146f2e502a9134ba9890411256638c56db.
All hosted steps succeeded: pinned installation, Ruff lint/formatting, 385 tests,
pip check, vulnerability audit, exact committed Docker image build and non-root
container health smoke. Actual jobs, step conclusions and logs inspected.
Completed 2026-11-14T10:25:53Z. No unrelated workflow dispatched.
The subsequent report commit is documentation only; this run tests the implementation
SHA above. Final local post-report format check passed (82 files), diff check passed,
and repeated Gitleaks scan found no leaks (651.65 KB).

## 16. Remaining real-data blockers

Need authentic Harith source artifacts, independent source/provenance review,
reviewed descriptor fingerprints, actual region geometry/coverage and scientific
approval of snapshot-bound flag semantics and any fraction threshold. No fake
approval hashes, data, production fixture, threshold or NASA findings were added.
Until then, the end-to-end production real-data path remains blocked.

## 17. Phase 05 readiness

Backend routes, cache lifecycle, single-worker constraint, CORS/download behavior,
source activation configuration and export contracts are ready for later Compose,
frontend integration and deployment preparation. Frontend owner must coordinate
shared_analyzed_years and run integration tests once its scaffold is available.
Full-system Compose, CI/CD expansion and deployment belong to Phase 05. No PR,
main merge, deployment or Phase 05 implementation performed. Stop after delivery.
