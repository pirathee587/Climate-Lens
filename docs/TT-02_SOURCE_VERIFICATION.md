# TT-02 — NASA source verification

**Owner:** Harith  
**Status:** Source metadata verified from an authenticated NASA Earthdata granule; regional ROI definitions remain subject to team approval.  
**Scope:** Metadata and acquisition preparation only. No historical observations or production snapshots are created by TT-02.

## Verified source

| Property | Verified value |
|---|---|
| Mission/product | NASA GPM IMERG Final monthly precipitation |
| CMR short name | `GPM_3IMERGM` |
| CMR collection ID | `C2723754851-GES_DISC` |
| Product version | `V07B` |
| Run | Final |
| Granule inspected | `3B-MO.MS.MRG.3IMERG.20240201-S000000-E235959.02.V07B.HDF5` |
| Granule period | 2024-02-01 through 2024-02-29 |
| File DOI | `10.5067/GPM/IMERG/3B-MONTH/07` |
| Processing algorithm | `3IMERGM_7.0` |
| Processing system | PPS |
| Temporal resolution | Monthly |
| Source coverage | 1998-01 through 2025-09 for V07 Final, according to NASA CMR |

Authoritative references:

- [NASA Earthdata collection](https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergm-07)
- [NASA CMR collection](https://cmr.earthdata.nasa.gov/search/concepts/C2723754851-GES_DISC)
- [NASA IMERG documentation](https://gpm.nasa.gov/data/imerg)
- [NASA V07/V08 transition notice](https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule)
- [NASA GES DISC migration guidance](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md)

## HDF5 metadata verification

The inspection was performed with `h5py` against the authenticated local granule. The
script is [verify_imerg_metadata.py](../backend/scripts/verify_imerg_metadata.py).

| Metadata | Verified value |
|---|---|
| Dataset | `Grid/precipitation` |
| Shape | `(1, 3600, 1800)` |
| Data type | `float32` |
| Dimension order | `time,lon,lat` |
| Units | `mm/hr` |
| Missing indicator | `_FillValue = -9999.900390625`; `CodeMissingValue = "-9999.9"` |
| `missing_value` attribute | Absent; do not infer one |
| `scale_factor` | Absent |
| `add_offset` | Absent |
| `valid_range` | Absent |
| Latitude | `Grid/lat`, `float32`, degrees north, ascending |
| Longitude | `Grid/lon`, `float32`, degrees east, ascending |
| Grid spacing | Approximately `0.1° × 0.1°` |
| Grid registration | Cell centers; southwest origin |
| Time | Seconds since `1980-01-06 00:00:00 UTC` |
| Calendar | `julian`; no leap seconds added |
| Decoded granule time | 2024-02-01 00:00 UTC; end bound 2024-03-01 00:00 UTC |

The precipitation values are raw HDF5 values with no scale or offset transformation
indicated by the inspected dataset attributes. Missing values must be recognized by
the fill indicator and must not be treated as zero.

The time bound endpoint is the next-month boundary represented by the file, not a
claim that the February observation ends on March 1. The file-level granule metadata remains the
authoritative period boundary: 2024-02-01 through 2024-02-29.

## Proposed study regions

These are project-defined study boxes, not official administrative boundaries:

| Region | Proposed WGS84 bbox `[west, south, east, north]` | Intersected source centers | Review |
|---|---|---:|---|
| `jaffna_area` | `[79.95, 9.60, 80.05, 9.70]` | 2 | Required: narrow spatial support |
| `colombo_area` | `[79.80, 6.90, 79.90, 7.00]` | 1 | Required: single-cell support |

The boxes are valid WGS84 rectangles and intersect the actual source grid. Coordinate
comparisons use a small tolerance for float32 cell-center rounding at exact box edges.
However, the Colombo box intersects only one source cell and the Jaffna box only two cells.
They should not be treated as robust regional averages without review. The boxes
must not be silently enlarged or finalized; Harith, Gaja and Kavishanth must approve
the final study-area definitions before TT-03.

City reference points used only to describe the approximate area:

- [Jaffna GeoNames reference](https://www.geonames.org/1242833/jaffna.html)
- [Colombo GeoNames reference](https://www.geonames.org/1248991/colombo.html)

## Processing requirements for TT-03

1. Select the same V07B Final collection and processing method for both regions.
2. Read `Grid/precipitation` as a rate in `mm/hr`.
3. Apply `monthly_mm = rate_mm_per_hour × 24 × actual_days_in_month` exactly once.
4. Preserve fill values as missing; never replace them with zero.
5. Record valid-cell coverage and quality indicators for every month.
6. Use complete 12-month calendar years only for annual totals.
7. Preserve the granule identifier, source URL, retrieval time, file checksum,
   variable metadata, ROI, processing version, and NASA attribution.
8. Use the verified V07 Final coverage only; do not concatenate V08 or another run.

The proposed 2001-01 through 2024-12 analysis interval lies within the verified
V07 Final collection coverage, but complete monthly availability for both selected
ROIs must be checked during TT-03 acquisition.

## Acquisition and security

The authenticated acquisition path is NASA Earthdata Cloud through `earthaccess`.
Credentials remain local to the ingestion environment. The raw HDF5 file under
`backend/nasa-test-data/` is local verification input and is excluded from Git by
the repository's `*.hdf5` ignore rule. It must not be committed, copied into
`data/demo/`, or exposed through the backend.

TT-02 does not activate the production repository adapter and does not create
normalized CSV observations.
