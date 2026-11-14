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
| GET | `/api/v1/analyses/{id}` | Retrieve stored analysis | Optional if result cache implemented |
| POST | `/api/v1/regions/analyze-bbox` | Custom region processing | P1 |
| POST | `/api/v1/data/refresh` | Earthdata cloud live refresh | P1 |

A sessionless alternative to result IDs is `POST /api/v1/exports/csv` with the immutable analysis JSON and source checksum; choose **one** export contract early and update SRS/UX consistently. The primary specification assumes short-lived result ID storage is implemented.

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
  "dataset_compatibility": {"same_product": true, "same_version": true, "same_run": true},
  "left": {"analysis_id": "...", "region": {}, "monthly": [], "annual": [], "statistics": {}, "source": {}},
  "right": {"analysis_id": "...", "region": {}, "monthly": [], "annual": [], "statistics": {}, "source": {}},
  "warnings": ["Separate trend tests do not test whether the two slopes differ significantly."]
}
```

Server must align or explicitly list differences in complete calendar years. For a like-for-like graphical comparison prefer only shared complete years; include the exact shared analyzed years. If the common interval has fewer than 10 valid years, return `INSUFFICIENT_DATA` rather than silently changing the period.

## 7. Export: GET /api/v1/analyses/{id}/export.csv

- `200 OK` with `Content-Type: text/csv; charset=utf-8` and safe file name.
- Monthly columns: `region_id,period,precipitation_total_mm,valid_fraction,snapshot_id`.
- Annual output may be a separate `annual.csv` endpoint or a `level` column; choose consistently and document.
- Metadata JSON is accessible via analysis result; include source/version/run/hash and scientific method in export README or metadata download.
- `404 NOT_FOUND` if the server no longer retains the requested analysis result.
- CSV cell formula injection mitigation: only numeric/date/known predefined region IDs from validated sources, no uncontrolled CSV labels.

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
