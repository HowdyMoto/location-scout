# Location Scout — SF Bay Area

Explore public Bay Area data on one map. **18 integrated source adapters**, plus a searchable catalog of **16 additional providers / source families** that need credentials, agreements, or further verification. No simulated events.

This is a researched starting inventory, not an exhaustive list of every API in the region. San Francisco dispatch and 311 feeds cover SF only. Regional feeds use the envelope longitude −123.6…−121.2, latitude 36.8…38.9, which includes adjacent areas and is not an exact nine-county boundary.

## Run

Requires Python 3.10+ and an internet connection. Use the backend below; `python -m http.server` cannot serve the data adapters.

```sh
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r scout/requirements.txt
.\.venv\Scripts\python.exe scout/server.py
```

macOS / Linux:

```sh
.venv/bin/python -m pip install -r scout/requirements.txt
.venv/bin/python scout/server.py
```

Open **http://127.0.0.1:5281**. Choose another port with `--port 5282`. On Windows, `scout/start.cmd` launches the project virtual environment after installation.

## Integrated data

| Layer | Coverage / meaning | Fetch interval |
| --- | --- | --- |
| SF law-enforcement calls | Rolling 48h, generalized intersections; 10-minute publication cycle plus 10-minute delay | 10 min |
| SF fire / EMS | Daily history, last 72h; responding units deduplicated into calls | 1 hour |
| SF 311 | Daily reports, last 72h; capped at 5,000 with an explicit notice | 1 hour |
| Aircraft | adsb.lol positions within 65 nautical miles of the Bay query point; positions older than 2 min omitted | 30 sec |
| Bike stations | Lyft Bike / Bay Wheels availability, e-bikes, docks and rental status | 1 min |
| BART | Station departure estimates, **not train GPS** | 1 min |
| Highway cameras | Caltrans District 4 locations; snapshots opened on demand; capture time not inferred from registry metadata | 30 min |
| Highway message signs | Nonblank Caltrans District 4 messages | 5 min |
| Highway lane closures | Caltrans active/planned schedule windows, **not congestion** | 5 min |
| Earthquakes | USGS events, past 7 days within regional envelope | 5 min |
| Weather warnings | Active NWS polygons or resolved Bay Area forecast zones | 5 min |
| Weather stations | Observations at 10 regional airport stations | 10 min |
| Tide gauges | Seven NOAA gauges, water level relative to MLLW | 6 min |
| River / water gauges | Latest USGS gage heights within 24h, local station datum | 15 min |
| Air-quality model | Ten city samples from CAMS / Open-Meteo, **not measured sensors** | 1 hour |
| Weather radar | NOAA base reflectivity raster with explicit frame timestamp | 5 min |
| Buoys / coastal stations | NDBC wind, wave and water-temperature observations | 10 min |
| Wildfire incidents | Current NIFC/WFIGS incident reports; not evacuation guidance | 15 min |

A fetch interval is not a guarantee of upstream freshness. Each record distinguishes observation/report time from fetch time. Empty results, failed sources and partial station responses remain distinct. Failed fetches retain last-known records with their original timestamps and a stale label. Aircraft positions age out after two minutes.

See [the source audit](docs/SOURCES.md) for provider links, access requirements and the remaining integration gaps. The in-app **Data sources** dialog is searchable and shows current health.

## Implementation

- `scout/server.py`: loopback-only Python HTTP server, fixed adapter routes, per-source cache and locks; no generic proxy.
- `scout/feeds.py`: provider adapters and normalized records. Coordinates are validated and bounded; redacted locations are not reconstructed.
- `scout/dist/sources.json`: source registry and access inventory, shared by backend and UI.
- `scout/dist/`: buildless Leaflet UI, zoom-dependent clusters, presets, regional shortcuts, source details, saved views and city/coordinate search.
- `scout/tests/test_feeds.py`: deterministic adapter/cache tests; no network needed.

The only Python dependency is `tzdata` for reliable Pacific timestamps on Windows. Backend fetches avoid browser CORS restrictions. No personal API keys are required for the integrated layers: BART explicitly publishes the shared legacy API key used here. No credentials are stored in source. Saved map views use browser localStorage.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s scout/tests -v
node --check scout/dist/app.js
```

All 18 integrated sources returned successful responses in the browser on 2026-10-24. This is a point-in-time smoke test, not an uptime guarantee. Aircraft initially timed out and recovered on retry. Test counts and provider record counts will change.

## Data terms and limits

Map © OpenStreetMap contributors. Aircraft data © adsb.lol contributors, ODbL. CAMS / Open-Meteo model data requires CC BY 4.0 attribution; the free Open-Meteo API is for noncommercial use. Lyft Bike data and BART data have their own provider terms. Each source's documentation is linked in the catalog; data accessibility is not a blanket redistribution license. This prototype is intended for local exploration and needs an appropriate hosting/rate-limit/licensing plan before a public production deployment.

Dispatch records are reported calls, not verified crimes or confirmation of an ongoing emergency. Model estimates, planned closures, preliminary gauges, and agency wildfire reports must not be treated as emergency instructions.
