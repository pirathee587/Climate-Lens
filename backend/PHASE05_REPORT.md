# Pirathee Phase 05 — TT-11 Docker, Compose and CI integration

## 1. Status

**INFRASTRUCTURE-READY BUT INTEGRATION BLOCKED.** Exact hardened backend production,
offline smoke and both Compose variants passed hosted CI on the implementation SHA.
Frontend/full-stack jobs were explicitly skipped because the real scaffold is absent.
This is not full-system or real NASA demonstration readiness. Local Snap Docker still
cannot execute no-new-privileges containers; diagnostic runs omitting that flag are
reported separately and are not hardened local successes.

## 2. Base and branch

Repository: pirathee587/Climate-Lens.
Verified latest origin/main and base: 24b04b37b578888db74775e7dd69df6a83e37448.
New branch: feat/tt-11-pirathee-phase05-docker-ci-integration.
Isolated clean worktree: /home/piratheepan/Desktop/ClimateLens-phase05.
Original main checkout is preserved. No reset, stash, rebase, main merge, force push,
PR, deployment or Phase 06 work. Frontend branch inspected without merging:
feat/tt-06-frontend-scaffold at e8270f0d2d9e7cca83436283764f88ef49cf5976.

## 3. Docker configuration

Backend preserves Python 3.12, unchanged pinned NumPy/SciPy/runtime dependencies,
UID 10001, safe request logs, healthcheck and disabled production docs. Production
command explicitly sets --workers 1 for process-local result IDs. Existing development
target retains reload. No application/data/statistics code or dependency files changed.
Frontend Dockerfile is preserved because the real scaffold is absent. Both build
contexts now exclude nested dependency outputs, private review/configuration files
and credential-like filenames in addition to existing env/key exclusions. No private
approvals, source credentials or raw NASA downloads are baked into images.

## 4. Production Compose

Two services only, backend 8000 and frontend 8080 on the shared default network;
loopback host ports are configurable. Backend root filesystem and existing snapshot
bind are read-only, /tmp is bounded tmpfs, all capabilities dropped,
no-new-privileges enabled. Snapshot mount uses create_host_path:false. Frontend uses
its existing unprivileged Nginx image; read-only root, bounded /tmp, dropped
capabilities, no-new-privileges and read-only Nginx configuration mount.
Frontend waits for backend service_healthy, which proves liveness only. Health probes
do not establish dataset readiness. Foreground application processes handle shutdown;
an unnecessary init wrapper was removed during local diagnostics.
Browser API strategy: two-port localhost/public API URL, not Docker service DNS.
Nginx config provides static/SPA fallback, missing-asset 404, rejects accidental /api/
HTML fallback and disables access logs. nginx -t passed against the actual unprivileged
Nginx base image (UID 101). This is configuration validation, not a frontend build.
Full production startup is blocked by missing real frontend source and locally also
by the Snap runtime's no-new-privileges incompatibility.

## 5. Development Compose

Development targets, APP_ENV=development, read-only backend source mount and reload,
read-only snapshots, Vite source/public mounts and frontend dev API environment.
Frontend development root remains writable for Vite dependency caches; production
remains read-only. !override replaces frontend ports/mounts; Compose >=2.24.4 required.
Both docker compose config --quiet variants passed. scripts/check_compose.py parsed
rendered default JSON and verified service list, targets, loopback ports, security,
mounts, healthy ordering and empty review defaults in both variants.

## 6. Backend container tests and local limitation

Environment: Linux x86_64; host Python 3.12.3; image Python 3.12.16;
Docker client/server 29.8.0 (Snap); Compose 5.5.1. Existing Python 3.12 venv reused.
Both production/development images built successfully using actual backend contexts.
Exact-profile local starts failed: exec /usr/local/bin/python: operation not permitted.
A minimal python --version probe isolated the flag: baseline, read-only, cap-drop ALL
and tmpfs separately succeed; no-new-privileges alone exits 255. The committed setting
was retained. The earlier optional init wrapper was not the underlying cause.

Diagnostic local runs used a temporary, deleted override omitting only that flag:
both modes became healthy as UID 10001, with read-only root/snapshots and dropped
capabilities. Container-local and loopback host HTTP smoke passed: health 200,
variables/regions/valid analysis/comparison 503 DATASET_UNAVAILABLE, unknown cached
result/monthly/annual/metadata 404 NOT_FOUND, malformed UUID 422 INVALID_ARGUMENT,
configured CORS/preflight and exposed download headers. Production docs/OpenAPI 404;
development docs/OpenAPI 200. Harith/Gaja imports, snapshot write rejection (EROFS),
shutdown/restart and development reload passed; reload replaced server child 8→77.
These diagnostic runs are NOT success of the hardened local profile.

An attempted docker cp into read-only containers failed; the final checker executes
its known source via python -c instead, requiring a completion marker. It does not
rely on copying into read-only roots or silent stdin execution. Subsequent diagnostic
runs confirmed that final script source executes and reaches the completion marker.
Temporary containers/networks/diagnostic override removed. No system Docker/AppArmor
settings were modified. Exact offline hardened verification is delegated to hosted
Backend CI; exact Compose variants to hosted Docker CI.

## 7. Frontend readiness

No frontend/package.json, package-lock.json or index.html exists on this branch.
No npm install/lint/typecheck/test/build or frontend Docker target can be verified.
Frontend test count: NOT TESTED (not zero passing tests). Host Node is also absent;
that is not worked around by inventing a scaffold. Full smoke exits 2 with an explicit
BLOCKED missing frontend/package.json message. No application code auto-merged.
Remote owner Dockerfile already fixes /app and node_modules ownership by installing
as USER node; that fix must be retained when the owner's actual scaffold is reviewed.
The current starter Dockerfile is not claimed runnable merely because it exists.

## 8. Connectivity and API compatibility

Backend-only container/host HTTP and CORS verified in the explicitly limited local
diagnostic runs. Full browser/frontend/backend connectivity, static application
assets, React unavailable state and SPA application navigation remain NOT TESTED.
Future full mode builds the actual applications and checks HTTP assets/SPA fallback;
it explicitly does not claim browser E2E. It configures matching fixed smoke ports,
frontend build/dev API URL and backend CORS. A service name is never a browser URL.
Current comparisonTypes.ts lacks shared_analyzed_years, side request/geometry_source
and has permissive bbox/retrieval nulls; comparisonValidation.ts derives shared years
locally. Exact owner handoff is documented in DEPLOYMENT.md. Remote scaffold types/api.ts
already includes shared_analyzed_years and compatible error/null/series metadata;
optional annual ols_fitted_mm remains pending backend work. Remote api/client.ts uses
the correct default browser URL, GET CSV and structured error handling. No backend
fields removed and no frontend application/API-client files edited.

## 9. CI workflow improvements

Existing workflows improved, no duplicates/new deployment workflow:

- backend-ci.yml: existing Python lint/format/pytest/audit preserved; lint/format
  now include scripts/importer; seven smoke checker tests; production build; offline
  no-new-privileges/read-only/cap-drop smoke, non-root imports and full error/CORS checks.
- docker-build.yml: both rendered Compose variants, infrastructure invariant checks,
  bash syntax, production/development backend Compose builds/runtime smoke. Actual
  frontend/full-stack matrix runs only when all real application manifests exist.
- frontend-ci.yml: explicit readiness job and visibly skipped frontend job if absent;
  when available require npm ci, lint, typecheck, npm test -- --run, build and audit.
- security.yml: full-history/tree Gitleaks preserved; checkout SHA pinned and no
  persisted credentials. All workflows default to contents:read, pinned actions and
  no image publishing/deployment. Frontend workflow readiness success is not test success.

Actionlint 1.7.7 release archive checksum verified; workflow validation passed. Shellcheck
is unavailable, so actionlint shellcheck integration was disabled explicitly; bash -n
passed. Standard checker tests 7 passed. Ruff passed across backend/scripts, 87 files
formatted before report creation. Backend pytest: 385 passed, 1 upstream Starlette/httpx
deprecation warning in 6.57 seconds. Dependency compatibility passed, no known audited
vulnerabilities. No dependency changes. git diff --check passed.

## 10. Hosted verification

All runs used implementation **73f16d94700e2e6362eeab7b1710520bf3588ed1**:

| Workflow | Run | Actual result |
|---|---|---|
| Backend CI | https://github.com/pirathee587/Climate-Lens/actions/runs/43587759307 | SUCCESS: 385 tests, 7 checker tests, lint/format/audit, production build, non-root offline hardened smoke |
| Docker build | https://github.com/pirathee587/Climate-Lens/actions/runs/43587762514 | SUCCESS: Compose invariants, production and development backend builds/runtime smoke; full-stack job SKIPPED |
| Frontend CI | https://github.com/pirathee587/Climate-Lens/actions/runs/43587765842 | Readiness SUCCESS; frontend job SKIPPED / NOT TESTED |
| Secret scanning | https://github.com/pirathee587/Climate-Lens/actions/runs/43587769070 | SUCCESS: full implementation history and working tree, no leaks |

Actual workflow tested SHAs, job/step conclusions and logs inspected. Backend logs:
385 passed, 1 warning in 9.99 seconds; 7 infrastructure tests in 3.553 seconds; no known
vulnerabilities. Offline container ran with network none, read-only root, dropped
capabilities and no-new-privileges. Docker matrix logs confirm both mode health 200,
read-only snapshot checks, container-local/host HTTP/CORS and cleanup passed with
all committed restrictions. This resolves exact-profile infrastructure validation
on a compatible runtime; it does not fix local Snap Docker. Frontend/full-stack jobs
are not passing application checks: they have no test/build execution.
All existing workflows were dispatchable by branch ref; no new default-branch
workflow registration or main merge was needed. No deployment/image publishing.
A subsequent documentation-only commit records this evidence; CI tests the
implementation SHA above, not that later report commit.

## 11. Security verification

Gitleaks v8.24.2: working-tree scan no leaks (~1.42 MB); original shared repository
history scan no leaks, 22 commits (~1.04 MB). Scan output redacted. Exact new commit
history/tree will also be scanned by hosted security workflow. No credential, fake
Earthdata token, real approval record, private source or synthetic production data.
Ports loopback-only; no-new-privileges retained; contexts exclude private env/key/review
files. Existing cache count/byte limits, CSV formula protection, tracing and error
redaction are unchanged and covered by existing 385 regression tests. Health200 is
never claimed as scientific source readiness. No database or runtime NASA downloader.

## 12. Deployment documentation

Created docs/DEPLOYMENT.md: prerequisites; Python/Node setup; Compose environments;
production/development commands; actual frontend blocker; browser URL/CORS/build-time
Vite behavior; read-only snapshot structure and review; health vs readiness; safe
logging; shutdown/restart; single-worker cache/expiry; security and Snap runtime
troubleshooting; exact frontend contract handoff and future hosting prerequisites.
Root/backend READMEs and backend/root environment examples updated accurately.
Docker primary documentation supports Compose merge/version and service_healthy
behavior; links included in deployment guide. No cloud/domain/paid hosting/deployment.

## 13. Exact changed files

- .env.example
- .github/workflows/backend-ci.yml
- .github/workflows/docker-build.yml
- .github/workflows/frontend-ci.yml
- .github/workflows/security.yml
- README.md
- backend/.dockerignore
- backend/.env.example
- backend/Dockerfile
- backend/PHASE05_REPORT.md
- backend/README.md
- compose.dev.yaml
- compose.yaml
- docs/DEPLOYMENT.md
- frontend/.dockerignore
- infra/nginx/default.conf
- scripts/check_compose.py
- scripts/smoke-stack.sh
- scripts/smoke_backend.py
- scripts/smoke_frontend.py
- scripts/tests/test_smoke_backend.py

## 14. Remaining blockers

Frontend owner must supply/review/merge the genuine scaffold and non-root Docker fix;
comparison owner must align its mirror/shared-year use. Until then frontend checks,
full Compose stack, actual browser behavior and production assets are blocked.
Local exact hardened startup requires a Docker runtime with working no-new-privileges;
no host security workaround is committed. Real NASA artifacts, independent provenance
review, verified geometry/coverage and approved snapshot-bound quality policies remain
absent. No real scientific offline demo or release readiness is claimed.

## 15. GitHub delivery

Commit message: ci(devops): configure TerraTrend Docker Compose and integration workflows.
Implementation SHA: 73f16d94700e2e6362eeab7b1710520bf3588ed1.
Automatic push succeeded with upstream tracking; git ls-remote matched the exact
implementation SHA. All 21 authorized paths staged individually; no git add . / -A.
A later documentation-only commit updates this report, README and deployment guide.
Its final verified remote SHA is available from branch HEAD/final delivery response;
application, scripts, Compose and workflow content remain the hosted-tested versions.
Original main checkout remains clean and unchanged. No PR/main merge/deployment.

## 16. Phase 06 prerequisites

Exact-profile infrastructure CI has passed. Remaining prerequisites: reviewed frontend scaffold and contract alignment, compatible local Docker runtime,
real reviewed immutable source bundles/policies, browser E2E, verified-data offline
scientific demo, performance/accessibility/QA and release review. None of those
remaining release gates is replaced by liveness, mock data or readiness skips.
Do not start Phase 06 or deploy as part of this task.
