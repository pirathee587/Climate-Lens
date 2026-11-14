# Pirathee Phase 03 — TT-05 analysis API

## 1. Status

**CONTRACT-READY BUT BLOCKED.** Synthetic, explicitly configured test artifacts
exercise Harith's real importer/repository and Gaja's real statistical engine.
No independently approved NASA observations or source-quality policies are present.
Production therefore returns 503 DATASET_UNAVAILABLE; tests are not NASA results.

## 2. Branch strategy

Repository: pirathee587/Climate-Lens.
Branch: feat/tt-05-pirathee-phase03-analysis-api.
Isolated worktree: /tmp/terratrend-phase03. Original checkout stays on main and its
pre-existing uncommitted docs/API_SPEC.md comparison edit is preserved, excluded.
Remote heads were fetched and matched the supplied reviewed SHAs. Phase 02 base:
bb3dfb4bbb88f4addc8adb1d9c2d5df9b86d2f83.
Gaja completed branch d765f2ced4559c4ede98049585a2a404a025ad3f is the base.
No main merge, force push, PR, deployment or Phase 04 implementation.

## 3. Harith integration

Chronological cherry-picks, without conflicts:

- a28e4040fbc89fbb8e88ce82e9794eb9174fea26 → e93fc2cd84b4d8cd648dc209f2f829a0cce22f88
- 91a59693f3e265dc171bbd152bb8b071622db282 → 47693793041a18d8d9f808865ea8fabd49a45d85

HarithSnapshotRepository and ArtifactApproval are used directly. No second
repository protocol, discovery scanner or preprocessing implementation was added.
Diff against Harith head for backend/app/data is empty.

## 4. Gaja integration

Base includes scientific implementation e3b40dae7e82dd0a2de5bb00ad674696708f513e,
format correction c047c1ea81c3de7817765176e91448ad19bc3d6d and delivery report d765f2c.
Existing dependency pins/locks are preserved. Diff against Gaja head for
backend/app/statistics is empty. NumPy 2.5.4 and SciPy 1.18.1 import in the image.

## 5. Created and modified files

Created:

- backend/app/api/v1/analyses.py
- backend/app/schemas/quality.py
- backend/app/services/analysis_service.py
- backend/app/services/statistics_adapter.py
- backend/tests/unit/analysis_fixtures.py
- backend/tests/unit/test_analysis_service.py
- backend/tests/integration/test_analysis_api.py
- backend/PHASE03_REPORT.md

Modified:

- backend/app/api/v1/router.py
- backend/app/core/config.py
- backend/app/services/catalog.py
- backend/app/services/snapshot_repository.py
- backend/tests/integration/test_catalog_ready.py
- backend/tests/integration/test_catalog_unavailable.py
- backend/tests/integration/test_health.py
- backend/README.md
- docs/API_SPEC.md

No frontend, workflow, Dockerfile, dependency, data-module or statistics-module
implementation edits were needed. Integrated Harith commits retain their own files.

## 6. HTTP behavior

POST /api/v1/analyses uses the existing AnalysisRequest and AnalysisResponse.
With complete trusted sources and eligible years: 200, fresh UUID, echoed request,
manifest-derived source, region, selected normalized monthly values, annual
summaries, Statistics, warnings and algorithm version. UUIDs are not stored.
Invalid schema/business/scientific inputs: 422 INVALID_ARGUMENT.
Fewer than ten complete years: 422 INSUFFICIENT_DATA.
Missing/corrupt/unreviewed data or policy: 503 DATASET_UNAVAILABLE.
Engine import/load unavailable: 503 STATISTICS_ENGINE_UNAVAILABLE (documented in
API_SPEC). Numerical/nonfinite response failures: sanitized 500 ANALYSIS_ERROR.
Existing request IDs, CORS and safe logging remain active. No exception/path leaks.
Health remains independent. Comparison, result retrieval and CSV export remain404.
Production documentation/OpenAPI remain disabled.

## 7. Statistical interfaces

FastAPI Depends injects CatalogService and the real GajaStatisticsAdapter.
CatalogService.validated_snapshots returns the exact validated descriptor/records;
analysis reuses this rather than duplicating artifact validation.
NormalizedMonthlyRecord maps to MonthlyObservation, preserving values/flags/fractions:
null is missing; unacceptable quality flag is invalid; accepted flags are eligible.
No second rate conversion or rainfall imputation occurs.
aggregate_annual_precipitation receives reviewed QualityPolicy and inclusive years.
Ten complete observations are required, then analyze_annual_trend receives actual
annual observations, alpha and excluded years. Statistics validates
trend.statistics_payload(). Annual summaries preserve incomplete null totals/counts.
All aggregation/trend warnings, actual analyzed years, missing periods and method/
library/algorithm versions are retained. Direction and significance stay separate;
indeterminate results remain indeterminate. No scientific algorithm was reimplemented.

## 8. Source provenance

Explicit reviewed descriptor fingerprints activate Harith's read-only repository.
Its source replay, descriptor/manifest/snapshot hashes and provenance are preserved.
Existing catalog validation checks both required regions and source consistency,
coverage, root confinement and symlinks. Request coverage is checked against actual
metadata. Source version, original units, retrieval timestamp, hashes, processing
and boundaries are taken from validated manifests, never fabricated.
Checksums and supplied attestations do not independently prove NASA authenticity.
Artifacts must remain immutable during serving; no network fetch occurs per request.

## 9. Quality policy

SNAPSHOT_APPROVALS and SNAPSHOT_QUALITY_POLICIES are JSON arrays, empty by default,
maximum two records each. Duplicate descriptors/policy hashes fail configuration.
ReviewedQualityPolicy binds output snapshot SHA256, nonempty unique accepted flags,
nullable fraction threshold and ProvenanceReview. Review cannot predate source
retrieval; evidence must be public HTTPS without query/fragment/credentials.
Actual scientific/data owners must approve flag semantics and thresholds. No
completeness threshold, real-source flag approval or production fixture is invented.
Missing coverage metadata produces warnings; rejected monthly values remain visible
but cannot contribute to annual analysis. Test artifacts exist only in pytest temp.

## 10. Automated tests

Actual local run: python -m pytest -q → **320 passed, 1 warning**, 4.04 seconds.
The warning is Starlette TestClient's upstream httpx deprecation.
Includes existing Phase 01/02, Harith and Gaja tests plus new orchestration/API tests:
valid ten years, positive/negative/constant trends, OLS/Sen CI/MK mapping, provenance,
year bounds, missing/null/quality-rejected months, whole-year gaps, <10 complete
years, warning preservation, UUID/CORS/request IDs, rejected artifacts, default
production failure, explicit environment configuration, stale quality review,
engine exceptions/unavailability, nonfinite output and sanitized failure logging.
Existing boundary tests cover invalid provenance, incompatible metadata and
nonfinite observations. No combined test count was assumed before execution.

## 11. Lint, dependencies and security

Executed using the existing Python 3.12 venv with the isolated backend working directory:

- python -m ruff check .: passed.
- python -m ruff format --check .: passed (71 Python files).
- python -m pip check: no broken requirements.
- python -m pip_audit -r requirements-dev.lock --no-deps --disable-pip:
  no known vulnerabilities. Audit advises hash locking; current locks pin versions.
- Harith scripts/import_imerg.py: Ruff lint and format check passed using backend config.
- Gitleaks v8.24.2 directory scan: no leaks, 544.68 KB scanned before report creation.
- git diff --check: passed.

Initial lint found an overlong test comment and datetime alias style; corrected.
No dependency updates were needed. Final post-report checks are recorded below.

## 12. Docker

Image terratrend-api:phase03 built successfully with existing backend/Dockerfile.
Direct path build failed because Snap Docker cannot access this /tmp worktree.
Equivalent build succeeded by streaming the backend tar context into docker build
-f Dockerfile -t terratrend-api:phase03 -. No application change was required.
Image ID: sha256:0727c27cd7ceea71a699fd6eec9489450e8b44b6ddf2a0842cf119460355229f.
Offline smoke used --network none: UID10001; Harith/Gaja/NumPy/SciPy imports passed;
health200; catalogs503; valid analysis request503 DATASET_UNAVAILABLE; docs/OpenAPI404;
comparison/export404. No NASA access, database or credentials required. Container removed.

## 13. GitHub delivery

Implementation commit/push verification will be recorded after local checks.
Suggested message: feat(backend): integrate NASA repository and statistical analysis API.
The report and commit explicitly retain the real-data blocker.

## 14. Hosted backend CI

Pending the authorized branch push and backend-ci.yml workflow_dispatch.
No earlier Harith/Gaja CI run is claimed as Phase 03 evidence.
A later documentation-only commit will record the actual implementation SHA/run.

## 15. Remaining blockers

Harith must provide real NASA source artifacts and independently reviewed descriptor
fingerprints, provenance, actual region geometries and supported coverage. Scientific/
data owners must approve snapshot-bound quality flags and any fraction threshold.
Neither a catalog nor a real production analysis is asserted until that happens.
Frontend OLS fitted points remain a separate coordinated additive contract change;
Phase 03 preserves existing schemas and does not modify the frontend mirror.

## 16. Phase 04 readiness

Repository validation, reusable real-engine adapter, annual summaries, UUID responses
and provenance can support later comparison/cache/export. GET
/api/v1/analyses/{analysis_id}/export.csv remains the agreed future export contract.
Comparison, cache, retrieval and export are not implemented. Do not start Phase04.
