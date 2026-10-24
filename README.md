# Location Scout — Seattle + SF Bay Area

Explore public geographic data on one map, defaulting to **Seattle / Puget Sound**, with a region selector for the **SF Bay Area**. Seattle has **19 public adapters plus a configurable WSDOT ferry adapter**; the Bay Area retains its **18 adapters**. No simulated events.

This is a researched starting inventory, not every regional API. Seattle's envelope is longitude −123.6…−121.2, latitude 46.8…48.8; the Bay Area envelope is −123.6…−121.2, 36.8…38.9. These include adjacent areas, not exact municipal boundaries. City dispatch feeds cover only their city.

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

## Seattle / Puget Sound

- **Moving vehicles:** King County Metro, Sound Transit, Community Transit, Everett Transit and Kitsap Transit GPS feeds, plus aircraft. Refresh every 30 seconds; transit reports expire after five minutes, aircraft after two. At zoom level 12+, short trails connect up to six observations from the past three minutes. Lines do not represent roads or predicted travel.
- **Safety:** Seattle fire / EMS calls from the last six hours; active NWS weather warnings; NIFC wildfire reports; seven days of earthquakes.
- **Water and weather:** nine weather stations, five tide gauges, USGS river gauges, NDBC buoy/coastal conditions, NOAA radar and eight modeled air-quality samples.
- **City context:** 393 active SDOT camera locations during verification, linking to the official camera viewer; delayed police call history and paid-parking snapshots, off by default. Parking is derived from payments, not live available-space sensors.
- **Ferries:** parser implemented, awaiting a WSDOT access code. Register through [WSDOT](https://www.wsdot.wa.gov/ferries/api/vessels/documentation/), set `$env:WSDOT_API_KEY='your-code'` in the server shell and restart. The code stays on the server; do not commit it. Real provider responses have not been tested without credentials.

During the October 24, 2026 live smoke test, all 19 public Seattle adapters responded, including about 615 transit vehicles, 121 aircraft, 76 fire calls, 146 river gauges and 13 coastal observations. Counts change. Police's newest published call was October 20; parking's newest snapshot was October 23. These are labeled delayed history.

Transit scheduling, geographic, and real-time data provided by permission of King County.

## Bay Area integrated data

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
- `scout/seattle.py`: Seattle-specific feeds and explicit regional configuration for shared adapters.
- `scout/dist/sources.json`: source registry and access inventory, shared by backend and UI.
- `scout/dist/`: buildless Leaflet UI, zoom-dependent clusters, presets, regional shortcuts, source details, saved views and city/coordinate search.
- `scout/tests/test_feeds.py`: deterministic adapter/cache tests; no network needed.

Python dependencies are `tzdata` for Pacific timestamps and `gtfs-realtime-bindings` / protobuf for transit feeds. Backend fetches avoid browser CORS restrictions. The public layers need no personal API keys; the optional ferry adapter requires WSDOT_API_KEY. BART explicitly publishes the shared legacy API key used here. No credentials are stored in source. Saved map views use browser localStorage.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s scout/tests -v
node --check scout/dist/app.js
```

All 18 Bay Area sources and 19 public Seattle sources returned successful responses on 2026-10-24. All 15 regression tests passed; browser checks covered region switching, source filtering and saved-view restoration. This is a point-in-time smoke test, not an uptime guarantee. Aircraft initially timed out and recovered on retry. Test counts and provider record counts will change.

## Data terms and limits

Map © OpenStreetMap contributors. Aircraft data © adsb.lol contributors, ODbL. CAMS / Open-Meteo model data requires CC BY 4.0 attribution; the free Open-Meteo API is for noncommercial use. Lyft Bike data and BART data have their own provider terms. Each source's documentation is linked in the catalog; data accessibility is not a blanket redistribution license. This prototype is intended for local exploration and needs an appropriate hosting/rate-limit/licensing plan before a public production deployment.

Dispatch records are reported calls, not verified crimes or confirmation of an ongoing emergency. Model estimates, planned closures, preliminary gauges, and agency wildfire reports must not be treated as emergency instructions.
