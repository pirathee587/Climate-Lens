# REST API specification

**API version:** v1 | **Owner:** Pirathee | **Transport:** HTTPS JSON (local HTTP in development).  
**Implementation:** FastAPI + Pydantic, documented OpenAPI at `/docs` when enabled. The examples below are **contracts, not actual computed NASA values**.

## 1. Conventions

- Base path: `/api/v1` (health outside prefix: `/health`).
- Dates: monthly `YYYY-MM`, annual `YYYY`; inclusive `start_year` and `end_year`.
- Region selection: **verified** preset ID, no arbitrary bbox in P0 API.
- Geographic bbox: `[west, south, east, north]`, longitude/latitude WGS84.
- Units: monthly/annual precipitation total `mm`; annual trend slope `mm/year`.
- Stat significance: two-sided MK at `alpha=0.05` unless valid override; confidence interval labeled `sen_slope_ci95_mm_per_year`.
- Error response: `{ "error": { "code": "...", "message": "...", "details": {}, "request_id": "..." } }`.
- API response data arrays must be chronologically ordered and all numbers finite JSON values (no NaN/Infinity; missing is `null`).

## 2. Endpoints overview

| Method | Path | Summary | P0 |
|---|---|---|---|
| GET | `/health` | Health/liveness | Yes |
| GET | `/api/v1/variables` | Supported variables, units and available dates | Yes |
| GET | `/api/v1/regions/presets` | Region IDs and bbox metadata | Yes |
| POST | `/api/v1/analyses` | One region's time series and statistics | Yes |
| POST | `/api/v1/comparisons` | Two regions; independent analyses | Yes |
| GET | `/api/v1/analyses/{id}/export.csv` | CSV of completed series | Yes (if result storage enabled) |
| GET | `/api/v1/analyses/{id}` | Retrieve completed cached analysis | Yes |
| GET | `/api/v1/analyses/{id}/annual.csv` | Annual series CSV | Yes |
| GET | `/api/v1/analyses/{id}/metadata.json` | Reproducibility metadata download | Yes |
| POST | `/api/v1/regions/analyze-bbox` | Custom region processing | P1 |
| POST | `/api/v1/data/refresh` | Earthdata cloud live refresh | P1 |

Phase 04 selects the primary GET export contract with a bounded process-local result cache. `POST /api/v1/exports/csv` is not implemented.

## 3. Catalog: GET /api/v1/variables

```json
{
  "variables": [
    {
      "id": "precipitation",
      "display_name": "Precipitation",
      "description": "Estimated rainfall accumulated over a period",
      "source_dataset_id": "GPM_3IMERGM_07",
      "source_version": "V07B",
      "source_run": "Final",
      "aggregation_units": "mm",
      "time_resolution": "monthly",
      "first_available_period": "2001-01",
      "last_available_period": "2024-12",
      "supported": true
    }
  ]
}
```

`2001–2024` are **proposed target snapshot dates**; actual availability must come from verified imports, and the implementation must not emit them before verification.

## 4. Regions: GET /api/v1/regions/presets

```json
{
  "regions": [
    {
      "id": "jaffna_area",
      "name": "Jaffna area",
      "label_type": "bbox_area_near_city",
      "bbox": null,
      "geometry_source": "verified-in-import-manifest"
    },
    {
      "id": "colombo_area",
      "name": "Colombo area",
      "label_type": "bbox_area_near_city",
      "bbox": null,
      "geometry_source": "verified-in-import-manifest"
    }
  ]
}
```

`null` bbox values are placeholders in the **documentation example**. Production API **must** emit checked actual four-number bounds before declaring the region selectable.

## 5. Single analysis: POST /api/v1/analyses

### Request

```json
{
  "variable_id": "precipitation",
  "region_id": "jaffna_area",
  "start_year": 2001,
  "end_year": 2024,
  "alpha": 0.05,
  "source_mode": "verified_snapshot"
}
```

### Response (schematic types, not observational values)

```json
{
  "analysis_id": "uuid-generated-by-server",
  "request": {
    "variable_id": "precipitation",
    "region_id": "jaffna_area",
    "start_year": 2001,
    "end_year": 2024,
    "alpha": 0.05
  },
  "region": {
    "id": "jaffna_area",
    "name": "Jaffna area",
    "bbox": null,
    "label_type": "bbox_area_near_city"
  },
  "source": {
    "collection_id": "GPM_3IMERGM_07",
    "version": "V07B",
    "run_type": "Final",
    "original_variable": "verify-from-file",
    "original_unit": "verify-from-file",
    "snapshot_id": "verify-after-import",
    "snapshot_sha256": "verify-after-import",
    "retrieved_at": null,
    "source_uri": "https://gpm.nasa.gov/data/directory",
    "aggregation_method": "verify-after-import"
  },
  "monthly": [
    {"period": "2001-01", "precipitation_total_mm": null, "valid_fraction": null}
  ],
  "annual": [
    {"year": 2001, "precipitation_total_mm": null, "valid_months": 12}
  ],
  "statistics": {
    "sample_years": null,
    "ols_slope_mm_per_year": null,
    "ols_r_squared": null,
    "sen_slope_mm_per_year": null,
    "sen_slope_ci95_mm_per_year": [null, null],
    "mann_kendall_p_value": null,
    "mann_kendall_method": "two-sided-original-on-annual-totals",
    "alpha": 0.05,
    "direction": null,
    "significance_status": "indeterminate",
    "assumptions_status": "not_evaluated"
  },
  "warnings": ["Numbers shown as null are schematic placeholders, not NASA observations"],
  "algorithm_version": "proposed-v1"
}
```

**Implementation requirement:** return real finite numbers, validated actual region bbox and source manifest. The placeholder response above must **never** be shipped as the production result.

### Validation and business rules

- Only known `region_id` values with real snapshots are permitted.
- At least 10 complete years must be available, inclusive in requested range; do not automatically impute missing periods.
- `2001 ≤ start_year ≤ end_year ≤ verified_last_year`, with bounds derived from snapshot rather than hardcoded after import.
- `0 < alpha < 1` with default 0.05. For meaningful user UX optionally restrict to 0.01, 0.05 or 0.10 presets.
- `source_mode=verified_snapshot` only in P0.
- `significance_status`: `significant`, `not_significant`, `indeterminate`; if assumptions invalid/insufficient, `indeterminate` takes precedence.
- `direction`: `increasing`, `decreasing`, `no_clear_direction` based on slope and method; direction is not significance.

## 6. Compare: POST /api/v1/comparisons

### Request

```json
{
  "variable_id": "precipitation",
  "left_region_id": "jaffna_area",
  "right_region_id": "colombo_area",
  "start_year": 2001,
  "end_year": 2024,
  "alpha": 0.05,
  "source_mode": "verified_snapshot"
}
```

### Response shape

```json
{
  "shared_requested_period": {"start_year": 2001, "end_year": 2024},
  "shared_analyzed_years": [],
  "dataset_compatibility": {"same_product": true, "same_version": true, "same_run": true},
  "left": {"analysis_id": "...", "region": {}, "monthly": [], "annual": [], "statistics": {}, "source": {}},
  "right": {"analysis_id": "...", "region": {}, "monthly": [], "annual": [], "statistics": {}, "source": {}},
  "warnings": ["Separate trend tests do not test whether the two slopes differ significantly."]
}
```

`shared_analyzed_years` is a required array of unique integer calendar years in ascending order. It identifies the complete, valid years actually shared by the left and right analyses, derived from verified data after quality and completeness checks. It must not be populated by simply expanding the requested start/end range. The empty array above illustrates the response shape only; a successful comparison requires at least 10 shared complete years.

Phase 04 computes independent regional statistics using each region's complete years within the unchanged requested interval. It returns their exact intersection; it does not recompute estimates on only that intersection. If samples differ, warnings explicitly identify both year sets and state that estimates are not matched-sample comparisons. Each side retains all annual summaries, excluded-year warnings and its actual sample count. The tests do not establish a significant difference between slopes.

Strict two-region catalog validation remains the first gate. Missing/unreviewed/corrupt or inconsistent artifacts return 503 DATASET_UNAVAILABLE. A defensive check after trusted result construction returns 409 INCOMPATIBLE_DATA for proven source incompatibility; ordinary version/run/processing mismatches fail the earlier catalog gate with 503. This gate is not weakened to make 409 reachable.

Frontend coordination: Kavishanth's comparisonTypes.ts mirror lacks shared_analyzed_years and comparisonValidation.ts derives display years locally. The frontend owner should consume the backend field; existing fields are preserved and frontend files are unchanged.

Server must align or explicitly list differences in complete calendar years. For a like-for-like graphical comparison prefer only shared complete years; include the exact shared analyzed years. If the common interval has fewer than 10 valid years, return `INSUFFICIENT_DATA` rather than silently changing the period.

## 7. Export: GET /api/v1/analyses/{id}/export.csv

- `200 OK` with `Content-Type: text/csv; charset=utf-8` and safe file name.
- Monthly columns: `region_id,period,precipitation_total_mm,valid_fraction,snapshot_id`.
- Annual endpoint: `GET /api/v1/analyses/{id}/annual.csv`, columns `region_id,year,precipitation_total_mm,valid_months,snapshot_id`.
- `GET /api/v1/analyses/{id}` returns the original complete analysis JSON unchanged.
- Additive metadata endpoint: `GET /api/v1/analyses/{id}/metadata.json`, JSON attachment with analysis_id, request, region, source, normalized_units (monthly/annual mm; slope mm/year), statistics, algorithm_version, warnings and scientific_limitations. Source includes collection/version/Final run, original variable/unit, snapshot ID/hash, retrieval timestamp, public URI and processing method.
- `404 NOT_FOUND` if the server no longer retains the requested analysis result.
- CSV is UTF-8 with deterministic headers and chronological rows. Null numeric values are empty fields; annual valid-month counts and null totals match the analysis exactly.
- Potentially unsafe text cells beginning with =, +, -, @ (including whitespace/BOM prefixes), tab, CR or LF are prefixed with an apostrophe. Standard csv quoting handles commas, quotes, line breaks and Unicode. For such identifiers, JSON retains the original text; CSV contains the safe spreadsheet representation.
- Download filenames use only the server UUID and fixed suffixes. Content-Disposition is exposed through allowed-origin CORS. No source fetch or recalculation occurs during retrieval/export.

## 8. Health: GET /health

```json
{"status": "ok", "service": "terratrend-api", "api_version": "v1"}
```

Liveness does not automatically mean valid source data are loaded; a readiness indicator can be extended to `dataset_ready` after manifest validation.

## 9. Error model and HTTP codes

```json
{
  "error": {
    "code": "INSUFFICIENT_DATA",
    "message": "At least 10 complete calendar years are needed for this exploratory analysis.",
    "details": {"complete_years": 7, "minimum": 10},
    "request_id": "generated-request-id"
  }
}
```

| HTTP | Code | Trigger |
|---|---|---|
| 400 | `BAD_REQUEST` | Malformed payload not fitting basic JSON expectations |
| 404 | `NOT_FOUND` | Analysis ID absent after cache expiry |
| 409 | `INCOMPATIBLE_DATA` | Compared sources or time coverage not scientifically comparable |
| 422 | `INVALID_ARGUMENT` | Invalid region ID, alpha or invalid date period |
| 422 | `INSUFFICIENT_DATA` | Too few complete annual observations |
| 503 | `DATASET_UNAVAILABLE` | Verified snapshot not installed or corrupt |
| 503 | `UPSTREAM_UNAVAILABLE` | Optional P1 NASA request failed |
| 500 | `ANALYSIS_ERROR` | Unexpected internal analysis defect; no fake fallback |

FastAPI's default validation error schema may be transformed at a central exception handler to meet this contract. Add CORS and pagination/rate limiting only if needed for deployment.

## 10. API lifecycle / compatibility

- Keep a stable `/api/v1` prefix for the hackathon.
- Schema updates must be communicated before merging to frontend; no silent breaking changes.
- Include `source_mode`, `algorithm_version`, `snapshot_id` and provenance for reproducibility.
- Endpoint integration tests must compare generated responses to checked scientific references.
- Auth is not required for the non-personal P0 demo; protect any P1 import/admin routes.


## Phase 04 implementation and availability

`POST /api/v1/analyses` is implemented using the existing request/response schemas.
Default production catalogs remain 503 until both independently reviewed NASA
snapshots are configured. Analysis additionally requires snapshot-bound reviewed
quality policies.
Successful POST analyses are cached under their existing UUID. Successful comparisons
publish both side UUIDs atomically only after full validation. Retrieval, monthly/
annual CSV and metadata download use this cache without any source or science calls.
Monthly values are normalized source records; annual summaries and statistics come
from Gaja's unchanged engine.

The cache is per application/process: monotonic TTL defaults to 1200 seconds,
RESULT_CACHE_TTL_SECONDS range 1..86400; capacity defaults to 100,
RESULT_CACHE_MAX_ENTRIES range 2..1000 (minimum two for atomic comparison pairs).
Fixed additional limits: 2 MiB serialized JSON per entry and 32 MiB total retained
JSON. Entries expire on access/insertion and oldest insertion is evicted first
when count/byte capacity is reached. Reads do not refresh TTL or eviction order.
Nested results are validated, serialized and deserialized to prevent caller mutation;
access is synchronized. Oversized/invalid results fail safely rather than being
partially cached. Expired, evicted, unknown or previous-process IDs return 404.
There is no database, multi-worker synchronization or persistence. Use one worker
for P0; a restart or another replica cannot recover IDs.

Additional public error: HTTP 503 `STATISTICS_ENGINE_UNAVAILABLE` means the
scientific engine cannot be imported/loaded, distinct from `DATASET_UNAVAILABLE`.
Its structured error envelope and X-Request-ID follow the existing contract.
Numerical failures return sanitized HTTP 500 `ANALYSIS_ERROR`; insufficient
complete years return HTTP 422 `INSUFFICIENT_DATA`.

No fitted OLS line field is added in Phase 03; that additive frontend contract
requires a coordinated schema, client and traceability update.
