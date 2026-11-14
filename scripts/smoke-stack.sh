#!/usr/bin/env bash
# Uses a separate project, empty approvals, and removes only its own containers.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
mode=${1:-production}
scope=${2:-backend}
[[ "$mode" == production || "$mode" == development ]] || { echo 'Mode: production|development' >&2; exit 2; }
[[ "$scope" == backend || "$scope" == full ]] || { echo 'Scope: backend|full' >&2; exit 2; }
if [[ "$scope" == full ]]; then
  for required in frontend/package.json frontend/package-lock.json frontend/index.html; do
    [[ -f "$required" ]] || { echo "BLOCKED: missing $required; frontend scaffold must be reviewed/merged by its owner." >&2; exit 2; }
  done
fi
export SNAPSHOT_APPROVALS='[]' SNAPSHOT_QUALITY_POLICIES='[]'
export BACKEND_HOST_PORT=${SMOKE_BACKEND_HOST_PORT:-0}
export FRONTEND_HOST_PORT=${SMOKE_FRONTEND_HOST_PORT:-0}
export ALLOWED_ORIGINS=http://localhost:5173
if [[ "$scope" == full ]]; then
  export BACKEND_HOST_PORT=${SMOKE_BACKEND_HOST_PORT:-18000}
  export FRONTEND_HOST_PORT=${SMOKE_FRONTEND_HOST_PORT:-15173}
  export ALLOWED_ORIGINS="http://localhost:$FRONTEND_HOST_PORT"
  export VITE_API_BASE_URL="http://localhost:$BACKEND_HOST_PORT/api/v1"
fi
compose=(docker compose --project-name "${SMOKE_PROJECT_NAME:-terratrend-smoke-$$}" -f compose.yaml)
[[ "$mode" != development ]] || compose+=(-f compose.dev.yaml)
cleanup() {
  result=$?
  if (( result != 0 )); then "${compose[@]}" logs --tail=80 backend >&2 || true; fi
  "${compose[@]}" down --remove-orphans --timeout 15 >/dev/null || true
  exit "$result"
}
trap cleanup EXIT
"${compose[@]}" config --quiet
services=(backend)
[[ "$scope" != full ]] || services+=(frontend)
"${compose[@]}" up --detach --build --wait --wait-timeout 90 "${services[@]}"
[[ $("${compose[@]}" exec -T backend id -u) == 10001 ]]
test -s scripts/smoke_backend.py
smoke_code=$(cat scripts/smoke_backend.py)
container_output=$("${compose[@]}" exec -T backend python -c "$smoke_code" --environment "$mode" --origin "$ALLOWED_ORIGINS")
printf '%s\n' "$container_output"
[[ "$container_output" == *'PASS CORS and unconfigured-data checks'* ]]
"${compose[@]}" exec -T backend python -c 'import app.data.repository_adapter, app.statistics; print("PASS Harith/Gaja imports")'
"${compose[@]}" exec -T backend python -c 'import errno; from pathlib import Path
try: Path("/data/demo/.phase05-write-probe").write_text("probe")
except OSError as e: assert e.errno == errno.EROFS; print("PASS snapshot mount is read-only")
else: raise SystemExit("FAIL snapshot directory is writable")'
# Check browser-visible host connectivity separately from container-local liveness.
backend_address=$("${compose[@]}" port backend 8000)
python3 scripts/smoke_backend.py --base-url "http://$backend_address" --environment "$mode" --origin "$ALLOWED_ORIGINS"
if [[ "$scope" == full ]]; then
  frontend_address=$("${compose[@]}" port frontend "$([[ "$mode" == production ]] && echo 8080 || echo 5173)")
  python3 scripts/smoke_frontend.py --base-url "http://$frontend_address" --environment "$mode"
  echo 'PASS HTTP stack connectivity; browser rendering/E2E remains a separate release check.'
else
  echo 'PASS backend-only Compose smoke; frontend/full-system integration NOT TESTED.'
fi
