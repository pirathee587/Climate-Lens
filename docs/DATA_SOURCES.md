# NASA data sources, acquisition and reproducibility

**Owner:** Harith | **Scientific review:** Gaja | **Source mode:** prevalidated local snapshot for 48-hour P0.

## 1. Official primary source

**TT-02 verification status:** The selected source and one authenticated V07B Final
monthly granule have now been inspected with `h5py`. Detailed evidence is recorded
in [TT-02_SOURCE_VERIFICATION.md](TT-02_SOURCE_VERIFICATION.md). The regional
bounding boxes remain proposed study areas pending team approval; they are not
administrative boundaries.

| Property | Verified selection |
|---|---|
| Mission/algorithm | NASA / JAXA GPM, IMERG multisatellite precipitation estimate |
| Collection | **GPM_3IMERGM_07** (Monthly Final, Version 07 product collection) |
| Data version label | **V07B**, verified in the inspected granule |
| Data variable | `Grid/precipitation`, verified in the inspected HDF5 file |
| Original units | `mm/hr`, verified from the dataset `units` attribute |
| Typical grid | **0.1° × 0.1°** latitude/longitude cell centers, verified in the file |
| Source historical coverage | **1998-01 through 2025-09**, verified through NASA CMR |
| P0 analysis period | **2001–2024** lies within source coverage; monthly completeness remains to be checked |
| P0 regions | Proposed boxes documented in the TT-02 verification report; team approval pending |
| Preferred runtime mode | **Verified offline snapshot**, no live NASA dependency |

**Official references:** [NASA IMERG](https://gpm.nasa.gov/data/imerg), [NASA Earthdata collection](https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergm-07), [NASA CMR collection](https://cmr.earthdata.nasa.gov/search/concepts/C2723754851-GES_DISC), [GPM Data Directory](https://gpm.nasa.gov/data/directory), [NASA Giovanni](https://giovanni.gsfc.nasa.gov/), [NASA Earthdata Search](https://search.earthdata.nasa.gov/).

## 2. 2026 data-access cautions

- NASA's 28 April 2026 announcement says **IMERG V07 Final stops with September 2025**, partly to avoid discontinuities in its upstream algorithm inputs. The 6 August update revised expected V08 transition timing. **Do not assert 2026 Final V07 data exist** or mix the Final V07 and V08 time records. [NASA April advisory](https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule) and [August update](https://gpm.nasa.gov/data/news/update-imerg-v08-transition-schedule-aug-2026).
- NASA GES DISC migrated away from legacy on-premises download servers around September 2026. Use **Earthdata Cloud, CMR, Earthaccess and current official NASA guidance** rather than assuming old hard-coded server URLs continue working. [NASA migration guidance](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md).
- NASA products may require a free **Earthdata Login**; keep credentials secure on the **server or offline ingestion machine**, never in the frontend.
- Depending on download format, precipitation can be an average **rate in mm/hr** or an accumulated **total in mm**; file attribute and product documentation decide conversion. [NASA IMERG data page](https://gpm.nasa.gov/data/imerg).

## 3. Two legitimate acquisition paths (choose one)

### A. Giovanni regional time series (fastest manual proof of concept)

1. Open NASA [Giovanni](https://giovanni.gsfc.nasa.gov/).
2. Choose the correct **IMERG Final monthly collection and exact field**; confirm version/run.
3. Define the date window and first bbox; generate **area-averaged time series**.
4. Export the actual data and plot metadata; repeat with the second bbox, same source/period/aggregation.
5. Document axis units, any fill/missing handling, notes on spatial operation and exported CSV checksums.
6. Preserve links or metadata sufficient to reproduce. Avoid assuming every Giovanni service/data product remains available without checking.

### B. NASA Earthdata Cloud with Earthaccess/Xarray (more programmable)

1. Identify matching collection/granules via [Earthdata Search](https://search.earthdata.nasa.gov/) or NASA [CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html).
2. Use [Earthaccess](https://earthaccess.readthedocs.io/) with proper account authorization; save exact collection/granule IDs and retrieval timestamp.
3. Inspect original NetCDF/HDF5 metadata with Xarray/NetCDF libraries; follow official fill values and scaling rules.
4. Select documented region grid cells; compute spatially appropriate weighted averages; convert monthly rate to monthly accumulation only if needed.
5. Save normalized regional CSV/JSON manifests, hashes and extraction script.

**Selection rule:** Use Path A if it yields reliable, auditable real data fastest. Don't build a full global downloader for the hackathon. If neither path works, disclose source-access failure; no invented "NASA" figures.

## 4. Required output artifacts once implementation begins

```text
data/demo/
  snapshots/
    imerg_v07b_jaffna_area_2001_2024_monthly.csv
    imerg_v07b_colombo_area_2001_2024_monthly.csv
  manifests/
    imerg_v07b_jaffna_area_2001_2024.json
    imerg_v07b_colombo_area_2001_2024.json
  README.md
scripts/
  import_imerg.py   # exact extraction, optional if Giovanni source is reproducibly documented
```

**Caution:** These filenames are **planned**, not existing verified NASA downloads in the documentation bundle. The CSV should have one row per month for each region and precise `YYYY-MM` timestamps.

### Canonical normalized CSV columns

```csv
region_id,period,precipitation_total_mm,valid_fraction,quality_flag
```

**No example observation rows** are included to avoid creating apparent NASA measurements. `precipitation_total_mm` is numeric or explicit missing; `valid_fraction` is in `[0,1]` if source supports it; `quality_flag` documents valid/missing/low_coverage as applicable.

### Manifest minimum keys

```json
{
  "snapshot_id": "team-assigned-unique-id",
  "collection_id": "GPM_3IMERGM_07",
  "version_label": "verify-V07B-in-file",
  "run_type": "Final",
  "source_url": "official-product-or-granule-link",
  "granule_ids_or_export_reference": [],
  "retrieved_at_utc": null,
  "bbox_wgs84": null,
  "region_label_type": "bbox_area_near_city",
  "time_start": "2001-01",
  "time_end": "2024-12",
  "original_variable_name": "verify",
  "original_units": "verify",
  "normalization_units": "mm/month",
  "spatial_aggregation": "document-exact-method",
  "rate_to_total_conversion": "document-applied-or-not",
  "missing_data_policy": "preserve-missing-exclude-incomplete-years",
  "input_sha256": "compute",
  "output_sha256": "compute",
  "processing_script_or_steps": "reproducible-steps",
  "license_or_usage_notes": "verify-source-specific-terms"
}
```

Replace all schema placeholders with genuine metadata, otherwise the snapshot is *unverified*.

## 5. Data quality checklist

- [ ] Same collection, algorithm version and Final run for both regions.
- [ ] Accurate, actual ROI bounds and geometry labels; map exactly matches manifest.
- [ ] Same calendar interval and spatial aggregation procedure.
- [ ] Variable, file scale and measurement units validated.
- [ ] Missing values recognized (`NaN`, fill codes etc.), not treated as zero.
- [ ] Area aggregation reviewed; report missing-grid/coverage fraction.
- [ ] Calendar-month hours handled correctly; no conversion twice.
- [ ] Annual totals only when all 12 months valid.
- [ ] Original data/source exported or reproducibly retrievable.
- [ ] Input/output hashes recorded; version and processing script reference retained.
- [ ] Credits, scientific caveats and NASA attribution included.

## 6. Optional next datasets (not MVP promises)

| Future variable | NASA source | Possible value |
|---|---|---|
| Temperature / evaporation | [MERRA-2](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/) | Long-term atmospheric and surface processes |
| Soil moisture / runoff | [GLDAS](https://ldas.gsfc.nasa.gov/gldas) | Hydrological and drought context |
| Vegetation indices | [MODIS](https://modis.gsfc.nasa.gov/) | Ecosystem/vegetation changes |
| River/lake water surface elevation | [SWOT](https://swot.jpl.nasa.gov/) | Surface-water observations (record length may limit trend tests) |

These datasets differ in units, validity, archive access and time coverage and should not be made active until independently integrated and tested.
