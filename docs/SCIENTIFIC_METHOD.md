# Scientific analysis methodology and guardrails

**Owner:** Gaja (statistical engine), Harith (input processing)  
**Status:** Implementation design, not completed analysis. **No findings are claimed.**

## 1. Scientific question and scope

For each verified region, evaluate whether **complete calendar-year precipitation totals** show a long-term monotonic and/or linear trend. Use the **same underlying NASA product/version/run**, consistent spatial aggregation and overlapping study interval for both regions. A graph's direction, estimated slope, its uncertainty and the statistical significance test answer different questions and must remain distinct.

## 2. Source and measurement interpretation

Primary NASA product: **GPM IMERG Final L3 1-month, collection `GPM_3IMERGM_07`**, product metadata label V07B. NASA documentation describes gridded monthly mean precipitation rates in `mm/hr` for relevant HDF5/NetCDF fields, while other download formats can contain accumulated precipitation in `mm`. **Always inspect the actual field, units and scaling in the source file**; the mathematical method depends on it. See [NASA IMERG](https://gpm.nasa.gov/data/imerg) and [data directory](https://gpm.nasa.gov/data/directory).

**NASA version caveat:** NASA's April 28, 2026 transition advisory said V07 Final stops at September 2025; August 6 update discussed the planned V08 timetable. Do not silently concatenate Final V07 with a different run or V08. Use a single internally consistent historical snapshot for P0. [April](https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule) · [August](https://gpm.nasa.gov/data/news/update-imerg-v08-transition-schedule-aug-2026).

## 3. Preprocessing: a validated transformation chain

1. Confirm source collection, run, version, variable, coordinates, timestamps, `_FillValue`, `scale_factor`, `add_offset`, valid range and units.
2. Extract and document each bounding box. City-area boxes are not official administrative district polygons.
3. Compute an area-weighted mean over valid grid cells for each month when processing raw grid data. Latitude/longitude cells have different areas; a suitable approximate weight is proportional to `cos(latitude)` if scientifically appropriate for the selected grid. Alternatively use a Giovanni **already area-averaged** time series and record that choice.
4. Record fraction of usable source grid cells and any quality filters per month; choose and document a reasonable completeness threshold rather than silently accepting nearly empty ROI data.
5. **For rates only**, calculate monthly accumulated precipitation: `monthly_mm = mean_rate_mm_per_hour × 24 × days_in_month`. Do not convert a value that is **already** a monthly accumulation (`mm`).
6. Use the Gregorian calendar including leap years (Feb 2024 has 29 days).
7. Construct annual precipitation total only when all 12 monthly values are valid: `annual_total_mm = Σ monthly_total_mm`.
8. Exclude incomplete years and show which were excluded. Never silently substitute zero for missing rainfall.

### Unit examples (synthetic math checks, not NASA measurements)

- `1 mm/hr × 24 × 28 = 672 mm` for February 2023.
- `1 mm/hr × 24 × 29 = 696 mm` for February 2024.
- `1 mm/hr × 24 × 31 = 744 mm` for January 2024.

For same spatial method and verified product, apply identical transformations to both regions.

## 4. Annual trend estimation

Let `x_i = calendar year` and `y_i = annual precipitation total in mm` for only valid years.

### 4.1 OLS linear regression

Model `y_i = b_0 + b_1 x_i + e_i`.

- `b_1` is the estimated annual-total trend slope in **mm/year**.
- OLS explains a linear component; report `R²` as descriptive fit quality, not proof of causality.
- Use `scipy.stats.linregress(x, y)` for a basic estimate; report assumptions and do not confuse a regression p-value with the independently chosen MK p-value.

### 4.2 Theil–Sen slope

`Sen_slope = median((y_j − y_i)/(x_j − x_i))` for all `j > i`.

- Robust trend magnitude, again in **mm/year**.
- `scipy.stats.theilslopes(y, x, alpha=0.95)` can return slope plus lower/upper 95% confidence limits.
- Label the interval **Sen slope 95% confidence interval**, not a confidence interval for predicted monthly rainfall.
- [Official SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html).

### 4.3 Mann–Kendall significance test

- Two-sided null: **no monotonic temporal trend**; alternative: **monotonic increase or decrease**.
- Compute test statistic and p-value using a documented versioned method (`pymannkendall.original_test` after validation or a tested MK equivalent with tie handling); label chosen implementation.
- Default significance threshold `alpha=0.05`.
- Base the app's reported statistical inference on the **MK p-value**, not on whether a chart line visually slopes up/down.
- Annual observations can still have autocorrelation. Document diagnostic limitations; do not automatically treat annual aggregation as fixing dependence.

### 4.4 Classification

| Condition | `significance_status` | Display |
|---|---|---|
| Insufficient valid years or invalid source | `indeterminate` | Cannot evaluate reliably |
| Material serial dependence / invalid test assumptions without valid correction | `indeterminate` | Test assumptions are not satisfied; p-value indicative only |
| Assumptions adequate and `p < alpha` | `significant` | Evidence of monotonic trend at chosen threshold |
| Assumptions adequate and `p >= alpha` | `not_significant` | Data do not show strong enough evidence at this threshold |

`direction` is a *separate* field and can be increasing/decreasing/no clear direction even if the trend is not significant. Do not label a tiny but statistically significant slope as environmentally important without appropriate impact context. A confidence interval covering zero and a low p-value from a different method can disagree because methods/assumptions differ; disclose rather than conceal that disagreement.

## 5. Minimum data and diagnostics

- **Hard minimum:** 10 complete years; **preferred:** 15–20+ complete years. These are pragmatic P0 design thresholds, not a universal scientific standard.
- Flag missing-year gaps, short records, outliers, ties/constant series, high interannual variability, suspicious abrupt processing changes and serial dependence.
- Investigate sample lag-one dependence. A fixed numerical cut-off is **not** scientifically universal; if dependence is material, use a justified modified MK test or describe significance as *indeterminate*.
- Record `n_complete_years`, `excluded_years`, `assumptions_status`, `method_version`, `warnings`.
- Station observations, land use records or independent studies would be needed to infer physical causes; these are beyond MVP.

## 6. Two-region comparison

- Both regions must use same dataset ID/version/run and compatible extraction/normalization.
- Synchronized charts should use the same years; list missing years and the actual intersection.
- Calculate independent OLS/Sen/MK results for each region. **Do not infer statistical significance of the difference of slopes** from one significant and one non-significant test; a separate appropriate comparison procedure would be necessary.
- Different trend signs can be described as *observed estimated directions*, with statistical evidence independently reported.

## 7. Expected code interface

```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class AnnualObservation:
    year: int
    total_mm: float

@dataclass(frozen=True)
class TrendResult:
    ols_slope_mm_per_year: float
    sen_slope_mm_per_year: float
    sen_ci95_low_mm_per_year: float
    sen_ci95_high_mm_per_year: float
    mann_kendall_p_value: float | None
    significance_status: Literal["significant", "not_significant", "indeterminate"]
    assumptions_status: str
    n_complete_years: int
    warnings: tuple[str, ...]
```

This is interface guidance, **not a completed implementation**. Be careful with Python constant series and `NaN`: encode undefined p-values as `null` in JSON and choose `indeterminate` if the method is not valid.

## 8. Validation test matrix

| Test | Synthetic input | Expected result |
|---|---|---|
| ST-01 rate conversion | 1 mm/hr in Feb 2024 | 696 mm |
| ST-02 non-leap conversion | 1 mm/hr in Feb 2023 | 672 mm |
| ST-03 completeness | Missing April | Exclude year, warning |
| ST-04 perfect trend | Annual totals `500 + 10*(year−2000)` | OLS slope exactly +10 mm/year |
| ST-05 falling trend | Annual totals `1500 − 5*(year−2000)` | OLS and Sen slope −5 mm/year |
| ST-06 constant | Same total all years | Zero slope, no fabricated strong significance |
| ST-07 unsorted/missing years | Years in random order, non-contiguous | Sorted, use actual year spacing |
| ST-08 unsupported period | 4 valid annual observations | Insufficient-data error |
| ST-09 comparison | Same product but region-specific series | Separate statistics, common-year coverage |
| ST-10 metadata mismatch | V07 Final versus different version/run | Reject or explicitly identify incomparability |

## 9. Interpretation copy template

> In the **[named verified area]** during **[actual complete years]**, the estimated annual rainfall total trend was **[calculated Sen slope] mm/year**. The chosen Mann–Kendall test returned **p = [computed]**, with **[supported status]** at the selected threshold. These results describe statistical evidence in satellite-derived estimates, **not the cause** of the observed change. [Any specific quality/assumption warnings].

Never substitute illustrative values in the final result cards. Include the period and dataset/run/version for reproducibility.

## 10. Scientific references

- NASA IMERG: https://gpm.nasa.gov/data/imerg
- NASA data directory: https://gpm.nasa.gov/data/directory
- NASA April 2026 transition: https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule
- NASA August 2026 update: https://gpm.nasa.gov/data/news/update-imerg-v08-transition-schedule-aug-2026
- SciPy `linregress`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html
- SciPy `theilslopes`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html
- SciPy `kendalltau`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kendalltau.html
