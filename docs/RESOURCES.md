# Reference resources and external links

**Verified reference list | Compiled 2026-11-14.** Always confirm dataset availability, server migration and software version details again before implementation. NASA does not endorse this student project.

## 1. NASA challenge and Earth science sources

| Resource | Link | Purpose |
|---|---|---|
| NASA Space Apps Challenge | https://www.spaceappschallenge.org/ | Event portal; find the exact challenge and official rules from event navigation |
| GPM IMERG overview | https://gpm.nasa.gov/data/imerg | Mission/product, unit and source interpretation |
| GPM product directory | https://gpm.nasa.gov/data/directory | Data versions, forms, collection identifiers and documentation |
| IMERG V07 → V08 transition (April 2026) | https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule | Statement about V07 Final ending September 2025 |
| IMERG V08 transition update (August 2026) | https://gpm.nasa.gov/data/news/update-imerg-v08-transition-schedule-aug-2026 | Revised anticipated V08 timetable; check present status separately |
| NASA GPM documents | https://gpm.nasa.gov/resources/documents | V07 scientific/algorithm documentation |
| NASA Giovanni | https://giovanni.gsfc.nasa.gov/ | Time-series/area-averaged data exploration and export |
| NASA Earthdata Search | https://search.earthdata.nasa.gov/ | Discover downloadable NASA collections and granules |
| NASA Common Metadata Repository | https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html | Collection/granule discovery interfaces |
| NASA Earthaccess Python | https://earthaccess.readthedocs.io/ | Programmatic Earthdata access |
| NASA GES DISC tutorials | https://github.com/nasa/gesdisc-tutorials | Working example notebooks and data workflows |
| NASA 2026 GES DISC migration guidance | https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md | Why old on-premises URLs should not be hardcoded |
| NASA Earthdata Login | https://urs.earthdata.nasa.gov/ | Account if authenticated source retrieval is necessary |
| NASA AppEEARS | https://appeears.earthdatacloud.nasa.gov/ | Potential P2 geospatial extraction service |
| NOAA Climate Data Online | https://www.ncei.noaa.gov/cdo-web/ | Independent weather/climate data reference if needed |
| KNMI Climate Explorer | https://climexp.knmi.nl/ | Alternative public science analysis context |

## 2. NASA partner and future dataset resources (NOT implemented in MVP)

| Future dataset / program | Link | Potential use |
|---|---|---|
| NASA MERRA-2 | https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/ | Reanalysis temperature and atmospheric variables |
| NASA GLDAS | https://ldas.gsfc.nasa.gov/gldas | Water/land surface model variables |
| NASA MODIS | https://modis.gsfc.nasa.gov/ | Vegetation/land-surface observations |
| SWOT mission | https://swot.jpl.nasa.gov/ | Lake/river/ocean surface water measurements |
| Canada RCM data | https://donnees-data.asc-csa.gc.ca/en/dataset/rcm | Radar-based ecosystem / maritime context |
| Canada Geo.ca | https://geo.ca/ | Canadian geospatial data discovery |
| Canadian SAR tutorial | https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial | Future SAR learning resource |

## 3. Scientific statistics documentation

- SciPy OLS regression: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html
- SciPy Theil–Sen slopes/CI: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html
- SciPy Kendall rank correlation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kendalltau.html
- PyMannKendall Python package (check methods/version before using): https://github.com/mmhs013/pyMannKendall
- NASA IMERG overview, with warning on rates vs accumulations: https://gpm.nasa.gov/data/imerg

## 4. Technology reference links

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- Python: https://docs.python.org/3/
- pandas: https://pandas.pydata.org/docs/
- NumPy: https://numpy.org/doc/
- SciPy: https://docs.scipy.org/doc/scipy/
- Xarray: https://docs.xarray.dev/
- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/docs/
- Vite: https://vite.dev/guide/
- Tailwind: https://tailwindcss.com/docs/
- Recharts: https://recharts.org/
- Leaflet: https://leafletjs.com/reference.html
- React Leaflet: https://react-leaflet.js.org/
- Pytest: https://docs.pytest.org/
- GitHub Actions: https://docs.github.com/en/actions
- GitHub issue templates: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests
- OpenAPI specification: https://spec.openapis.org/oas/latest.html
- Warp official project-scoped agent rules (`AGENTS.md`): https://docs.warp.dev/getting-started/quickstart/coding-in-warp/

## 5. Referencing and data integrity rules

1. Cite **specific NASA product/collection IDs, version, run, timestamps, bbox, variable, units and processing methods** in any data analysis or report.
2. Do not cite a generic NASA home page as proof of a specific numerical result. Data-based claims require actual identifiable source series/granules.
3. Distinguish independent calculations, reference-source facts, suggested engineering choices and UI example schemas.
4. Confirm the provider terms for datasets and any OSM/map tiles; preserve attribution.
5. NASA's data source is credited but the project's claims/design are the team's own. This project is not NASA-endorsed.

## 6. NASA dataset status notes as of document date

- The NASA GPM directory lists IMERG V07 with ~0.1° spatial resolution and historical coverage from January 1998. The available product format and run must be checked when downloading.
- NASA published the V07/V08 Final Run transition notices on **2026-04-28** and **2026-08-06**. The plan intentionally restricts the baseline to complete pre-2025 years; it does **not** assert the present-day state of V08 availability.
- NASA's 2026 GES DISC migration guidance recommends current Earthdata Cloud workflows instead of old on-premises hard-coded download URLs.

All of these are **source and integration considerations**, not claims about actual regional precipitation trends.
