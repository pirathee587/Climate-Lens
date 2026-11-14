# Gaja TT-04 — statistical trend analysis engine

## Status and scope

**COMPLETE — independently reference-tested statistical engine.** 14 November 2026.
This does not mean real NASA data, an analysis API or the full application is ready.
No observations or real-world scientific findings are claimed.

The clean branch was created from the user-specified remote Phase 02 base bb3dfb4,
not Harith's feature branch. It includes 139 existing Phase 01/02 tests and 64 new
statistical cases (203 total). Harith's separate TT-03 tests/code are not part of
this requested base, so this total is not comparable to that branch's 219 tests.
No existing API/service/schema, data-loader, frontend or workflow file was changed.

## Public interfaces and integration types

```python
from app.statistics import (
    AnnualObservation, MonthlyObservation, QualityPolicy,
    aggregate_annual_precipitation, analyze_annual_trend,
    InvalidDataError, InsufficientDataError, NumericalAnalysisError,
)
```

- AnnualObservation(year, total_mm) validates strict integer calendar years and finite,
  nonnegative totals. Inputs are copied/sorted; duplicate years are rejected.
- MonthlyObservation(region_id, period, total_mm, quality_flag, validity='valid',
  valid_fraction=None) carries normalized totals, source quality and explicit
  valid/missing/invalid state. No rate or geographic processing occurs.
- QualityPolicy specifies accepted source flags and an optional documented coverage
  minimum. Default accepts exactly 'valid'; unknown flags do not become valid by default.
- aggregate_annual_precipitation(rows, policy=..., year_range=None) returns immutable
  AggregationResult: complete AnnualObservations, every year's total/count summary,
  excluded years, absent periods and warnings. Incomplete year totals are null.
- analyze_annual_trend(annual, alpha=0.05, excluded_years=(), diagnostic_alpha=0.05)
  returns immutable TrendResult, actual years, counts, exclusions, OLS/Sen/MK estimates,
  diagnostics, direction, inference status, warnings and algorithm/library versions.
- result.statistics_payload() maps to the unchanged v1 Statistics schema as finite
  JSON-compatible values; undefined R² or diagnostics are null. Full dataclass results
  can be serialized with dataclasses.asdict and json.dumps(..., allow_nan=False).

InvalidDataError reports malformed inputs; InsufficientDataError includes available
and minimum counts (10 for the public engine); NumericalAnalysisError reports failed
or nonfinite calculations. No fake estimates or fallback methods replace failures.
The functions have no FastAPI request, database, filesystem or network dependency.

## Algorithms and scientific assumptions

### Complete-year aggregation

YYYY-MM dates are strictly checked, duplicates/mixed regions rejected, and dates
sorted by calendar lookup. Only 12 valid monthly accumulated mm values form an annual
total. Missing/invalid/unknown-quality months are excluded, never replaced with zero.
Zero coverage is unusable. If a coverage minimum is configured, an unknown fraction
cannot satisfy it. Existing source flags/fractions are not silently reinterpreted.
Nonfinite or negative precipitation is an invalid input, even if flagged invalid.
Explicit 'missing' state requires a null value. Positive finite but invalid-quality
values are excluded and counted. math.fsum minimizes summation error; overflow raises.

Without year_range, the first-to-last observed year defines the aggregation span.
A supplied inclusive range also reports wholly absent years, including boundaries.
The range never manufactures observations. Empty inputs, outside-range records and
excessive resource sizes fail explicitly. The engine performs no mm/hr conversion.

### OLS and Theil–Sen

SciPy linregress uses actual calendar years and annual totals, returning mm/year slope,
intercept and R². Scaling totals before computation improves numerical stability;
physical units are restored afterward. Constant totals have zero slope and undefined
R² (null), rather than an invented perfect explanatory fit.

SciPy theilslopes uses actual year spacing and alpha=0.95 for the fixed **Sen slope
95% confidence interval**, regardless of the MK significance alpha. It is not a
prediction interval. No OLS substitution is used. Bounds, estimate ordering and finite
outputs are checked. Unrepresentable estimates raise a numerical exception.
Constant series produce the mathematically degenerate zero slope/zero interval.

### Original Mann–Kendall

The original two-sided test computes signed pair score S in temporal order. Its
variance is [n(n−1)(2n+5) − sum(t(t−1)(2t+5))]/18 for exact-value tie-group sizes t.
Z uses continuity correction (S−1 for positive S, S+1 for negative S), divided by the
standard deviation. S=0 gives Z=0; constant-series variance=0 gives p=1 and no rejection.
Two-sided p is 2*norm.sf(abs(Z)), preserving small tails without CDF cancellation.
It is a normal approximation, not an exact permutation test. No generic correlation
coefficient is substituted for MK. The primitive reject_null flag is indicative only;
the public engine applies the assumption gate before final classification.

Method: two-sided-original-on-annual-totals.
Method version: terratrend-mk-ties-continuity-normal-v1.
Algorithm version: terratrend-annual-trend-v1.
SciPy/NumPy versions are recorded in every TrendResult.

### Dependence diagnostics and classification

The declared exploratory diagnostic is lag-one Ljung–Box screening of OLS-detrended
annual residuals. Residuals are scaled for numerical stability. r1 is the lag-one
residual cross-product divided by total residual squared sum; Q=n(n+2)r1²/(n−1).
Its approximate p-value uses chi-square df=1. diagnostic_alpha defaults to 0.05 and is
recorded separately from the analysis alpha. This is a declared screening policy,
not a universal numerical autocorrelation threshold.

This linear-detrending/chi-square screen is approximate: finite samples and estimated
trend affect calibration, nonlinear trends can cause flags, and non-rejection cannot
prove independence or rule out higher-lag dependence. There is no ARMA fit, validated
serial-correlation correction, prewhitening or modified MK implementation. Source
quality, outliers, processing-version breaks and causal mechanisms need separate
assessment; the engine cannot establish those from annual totals alone.

- Material positive OR negative residual dependence flagged by this screen yields
  indeterminate, even when raw MK p is below alpha.
- Gapped calendar years yield indeterminate: the regular lag-one test is not applied
  to compressed list indices. Available consecutive-pair count is reported.
- Constant/numerically exact linear series yield indeterminate because residual
  dependence is unassessable. Slopes and indicative MK remain available.
- Otherwise, status is significant when MK p<alpha, not_significant when p>=alpha;
  assumptions_status explicitly says not_rejected_by_lag1_screen, not 'proven independent'.
- Fewer than 10 complete years raises InsufficientDataError. Ten is a project rule,
  not a universal statistical law. Records below 20 years receive a short-series warning.

Undefined residual variance uses a documented numerical tolerance of 16 float eps
on scaled residuals, not an autocorrelation cutoff. The nominal Sen interval is not
corrected for serial dependence; warnings state that limitation. Sen slope sign gives
increasing/decreasing/no_clear_direction independently of significance. Neither a
p-value nor a nonzero slope establishes causation or environmental importance.

Input/coverage size is bounded at 200 years (2400 months) to constrain the quadratic
Sen estimator. This is a resource cap, not a scientific threshold. All computation
uses floating-point arithmetic with explicit finite-result checks.

## Synthetic reference-test results

All tests are labeled synthetic algorithm checks, not NASA observations.

| Required case | Evidence/result |
|---|---|
| ST-01 normalized monthly boundary | February total 696 is not converted again |
| ST-02 complete year | 12 valid monthly totals sum exactly as expected |
| ST-03 missing April | Year excluded, valid_months=11, total=null |
| ST-04 increasing annual totals | OLS/Sen +10 mm/year within float tolerance |
| ST-05 decreasing annual totals | OLS/Sen −5 mm/year within float tolerance |
| ST-06 constant series | Zero slope, R²=null, MK p=1, indeterminate |
| ST-07 unsorted years | Same result after deterministic calendar sorting |
| ST-08 gapped years | Calendar-year slopes preserved; inference guarded |
| ST-09 four years | Explicit minimum=10, available=4 exception |
| ST-10 missing data handoff | Exclusions/counts preserved from monthly aggregation |
| ST-11 tied observations | Tie-corrected score/variance/Z/p match PyMannKendall |
| ST-12 nonfinite values | NaN/Infinity/invalid negatives rejected |
| ST-13 alpha | Invalid values rejected; valid override preserves fixed Sen CI95 |
| ST-14 autocorrelation caveat | Positive/negative dependence overrides raw MK rejection |
| ST-15 confidence interval | Ordered limits match trusted SciPy reference |
| ST-16 independent references | Hand slope/pairwise median, tie math, normal tail, reference package |
| ST-17 reproducibility | Identical immutable/reversed inputs produce identical result |

Hand reference for values [1,2,2,3]: S=5, tie-adjusted variance=23/3,
Z=4/sqrt(23/3); the tail is independently checked using math.erfc.
Original MK is compared with pinned PyMannKendall on rising, falling, constant,
tied and noisy sequences. Sen slope is independently checked against the median of
all actual-calendar pairwise slopes. CI bounds use trusted SciPy theilslopes; OLS
uses hand-known lines and direct SciPy references. The residual Q statistic is checked
against an independent scalar calculation and the chi-square survival probability.

References:
[SciPy linregress](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html),
[SciPy theilslopes](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html),
[PyMannKendall implementation](https://github.com/mmhs013/pyMannKendall),
[NIST Box–Ljung definition](https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc4481.htm).
These references support the stated methods, not any regional climate finding.

## Dependency changes

Runtime: numpy==2.5.4, scipy==1.18.1. Test reference only: pymannkendall==1.4.3.
Direct requirement pins and both complete lock files were updated together. Existing
versions were preserved. A metadata-edge check confirmed every active Python 3.12
runtime dependency is present/pinned in requirements-runtime.lock; pip check passed.
No new package manager or system package was installed. Test-reference PyMannKendall
is not used by the runtime engine or included in the production Docker requirements.

## Exact created/modified files

```text
backend/app/statistics/__init__.py
backend/app/statistics/models.py
backend/app/statistics/annual_aggregation.py
backend/app/statistics/regression.py
backend/app/statistics/sen_slope.py
backend/app/statistics/mann_kendall.py
backend/app/statistics/diagnostics.py
backend/app/statistics/trend_engine.py
backend/tests/unit/test_annual_aggregation.py
backend/tests/unit/test_regression.py
backend/tests/unit/test_sen_slope.py
backend/tests/unit/test_mann_kendall.py
backend/tests/unit/test_trend_engine.py
backend/requirements.txt
backend/requirements-dev.txt
backend/requirements-runtime.lock
backend/requirements-dev.lock
backend/README.md
backend/STATISTICS_MODULE_REPORT.md
```

## Actual local verification

Backend directory:

```text
.venv/bin/python -m pip install -r requirements-dev.txt     PASS
.venv/bin/python -m ruff check .                           All checks passed!
.venv/bin/python -m ruff format --check .                  48 files formatted
.venv/bin/python -m pytest -q                              203 passed, 1 warning in 1.72s
.venv/bin/python -m pip check                             No broken requirements found
.venv/bin/python -m pip_audit -r requirements-dev.lock --no-deps --disable-pip
                                                          No known vulnerabilities found
Runtime dependency-edge completeness check                PASS
```

One existing upstream Starlette/httpx TestClient deprecation warning remains. Audit
also recommends hashed dependency artifacts; the existing locks are version pins.
An initial test-file write used the wrong working directory and was corrected before
scientific verification. No failed attempt was represented as successful testing.

Repository root:

```text
docker build -f backend/Dockerfile -t terratrend-api:tt04 backend
PASS; final image sha256:b23b31ae098b2f02ade2d937b3d2fb32a76547953d56700cb7a7b03aa1a493a5
python3 /tmp/terratrend_tt04_smoke.py
PASS; runtime scientific imports succeed, UID 10001, network disabled,
Docker HEALTHCHECK healthy. /health=200; both catalogs=503; production docs=404;
analysis/comparison POST=404. Temporary container removed after checking.
docker run --rm -v "$PWD:/repo:ro" zricethezav/gitleaks:v8.24.2 dir /repo --redact --no-banner
PASS; no leaks found (~887951 bytes scanned).
git diff --check                                         PASS
```

## Pirathee Phase 03 handoff

The engine is available for integration; no analysis route was implemented. Pirathee
must first validate real source provenance/units, region IDs and requested coverage.
Map normalized repository records to MonthlyObservation without another rate conversion.
Set explicit validity/accepted source flag semantics with Harith, and choose/document
coverage policy rather than automatically treating every arbitrary source flag as valid.

A science-service call, not a new HTTP endpoint:

```python
aggregation = aggregate_annual_precipitation(
    monthly_inputs, policy=approved_quality_policy,
    year_range=(requested_start_year, requested_end_year),
)
trend = analyze_annual_trend(
    aggregation.observations, alpha=request_alpha,
    excluded_years=aggregation.excluded_years,
)
statistics_json = trend.statistics_payload()
warnings = [*aggregation.warnings, *trend.warnings]
```

Preserve aggregation year counts, excluded/missing periods, actual analyzed years,
chosen quality policy, all warnings and algorithm/library metadata. Shared Statistics
validation is exercised in tests. Catch the explicit science exceptions at the future
service boundary and map insufficient/invalid inputs to the existing API errors.
Do not return a significant badge for an indeterminate result or infer a significant
between-region slope difference from independent tests. Real-data activation still
requires Harith's artifacts/review; that does not block completion of this pure engine.

## GitHub delivery and CI

Repository: pirathee587/Climate-Lens.
Branch: feat/tt-04-gaja-statistics-engine.
Base: origin/feat/tt-05-pirathee-phase02-nasa-integration (bb3dfb4).
Required message: feat(statistics): implement annual rainfall trend analysis engine.
Commit/push verification and actual hosted CI result will be added after delivery.
Only the listed Gaja code/tests, necessary dependency files and documentation are staged.
No git add . / git add -A, force push, PR, merge, deployment or Phase 03 work is performed.

The existing Backend CI supports main pushes, relevant PRs and manual dispatch.
Feature pushes do not trigger it; an authorized backend-only dispatch will be run.
Local results above are not GitHub-hosted CI evidence.

Final status: **COMPLETE for TT-04**, with the explicit scientific limitations above.
