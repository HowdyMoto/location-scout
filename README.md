# Location Scout — Explore the live world

Explore public geographic data by **panning and zooming anywhere**. **All layers are enabled by default, with SF parking-enforcement and citation calls hidden.** The map automatically selects feeds whose coverage intersects the view, with detailed city sources in Seattle / Puget Sound and the SF Bay Area, international transit feeds, plus nine viewport-driven source types. Place shortcuts move the camera; they do not lock data to a region.

The map opens in **World view**. Green destination markers reveal connected cities and sky views; nearby destinations share a clickable menu. Select one to jump into its feeds, or pan and zoom anywhere. The World view button returns to the overview. These destinations indicate available integrations, not guaranteed current activity.

## Automatic geographic coverage

- Moving or searching to SF immediately selects its city feeds; moving to Seattle selects its transit and dispatch feeds. A wide view can include both regions simultaneously.
- **Worldwide:** aircraft reception where available, USGS earthquakes, NASA EONET natural-event reports, NDBC buoy/coastal reports where stations exist, RainViewer radar mosaics where contributing networks provide coverage, and nine weather / air-quality model samples across each view. These are not claims of complete global receiver, sensor or city-data coverage.
- **Contiguous US:** USGS water gauges and NIFC wildfire reports. Detailed gauge / fire queries ask for a closer zoom on very wide views. Aircraft queries are bounded to the provider's 250-nautical-mile maximum radius.
- **Local coverage:** transit, dispatch, cameras, parking, outages/access candidates and other city feeds retain their actual provider coverage. New cities do not automatically gain local transit or dispatch integrations.
- Viewport requests use validated bounding boxes, padded query areas, cancellation of obsolete browser requests, per-provider caches (24 areas each), shared global-feed caching and provider-wide rate-limit backoff. Late responses cannot overwrite a newer viewport. Longitude wrapping and date-line crossings are handled explicitly.
- Layer preferences persist while exploring. SF parking-enforcement/citation calls have a separate toggle and are hidden by default. **Everything** explicitly includes them; **Reset** restores all layers with those calls hidden. Saved views retain this preference. Other presets remain optional. Search, geolocation and saved views use the same automatic coverage behavior.

During October 25 verification, moving the map to SF activated its sources without touching a region selector. Live London weather, Tokyo air-quality model samples and date-line earthquake queries succeeded. The worldwide aircraft layer now uses adsb.fi, verified around London, Singapore and Cape Town. Its public API is personal/noncommercial; public commercial deployment requires suitable access. No replacement positions are invented.

Connected international transit includes Helsinki, participating Norwegian operators, Adelaide, Canberra light rail, Rio de Janeiro, Bordeaux, the Netherlands and Renfe commuter trains across Spain, plus Boston, Los Angeles and the Seattle agencies. The world explorer includes city and airport shortcuts, local times and a Surprise me button. Feed freshness and service hours determine whether vehicles are present. The explorer shows fresh vehicle and bike-station reports within 50 km of each destination, plus vehicles moving in observation playback. Counts update while the dialog is open. Surprise me favors observed motion, then fresh vehicles or station availability, and avoids immediately repeating the previous destination. Unchecked, unavailable and quiet destinations remain selectable.

International bike availability is connected in Tokyo, Toronto and Buenos Aires. Zoom in for station bike counts; availability changes pulse on newer reports. These are changing inventories, not moving rider positions.

## Live motion experience

The default **Everything** view includes moving vehicles and all other available layers. **Live now** narrows the view to motion and live safety feeds. The map uses an **adaptive per-source playback buffer (10–180 seconds)**, interpolating between received positions. This is deliberately delayed observation playback, not a prediction or a zero-latency claim. A fresh server/browser needs observations to accumulate before motion starts. The server retains up to ten minutes of bounded history in memory, allowing subsequent clients to start with recent tracks.

- Directional aircraft, transit and vessel markers persist across updates. No extrapolation: missing reports hold their last position; long gaps and implausible jumps are not animated. Expired reports disappear.
- **Follow a flight / Follow transit / Follow ship**, or select a vehicle and follow it. Dragging the map stops following. Scene shortcuts focus on downtown, airport approaches and the water.
- **Pause** freezes displayed vehicle positions while data continues arriving. Resume returns to buffered playback. Reduced-motion preferences start playback paused.
- Fading trails connect observed points, not road or rail geometry. Tracks are individually visible at zoom 10+, with clusters when zoomed further out.
- **Radar loop** cycles up to 13 recent RainViewer mosaics worldwide. Times identify mosaic generation, not the age of every contributing radar. Native resolution is capped at zoom 7; blank areas can indicate missing coverage. New tiles load before replacing the previous frame; failed or timed-out frames retain the last successful frame and playback retries after five seconds. Public provider access is intended for personal/educational use.
- The activity sidebar rotates across enabled sources, so aircraft do not hide dispatches and transit. Newly received safety reports pulse briefly and retain their original report timestamps. Initial history does not trigger arrival pulses.
- Metro and Sound Transit route names come from `routes.txt` in the official GTFS download, cached for a day. If metadata is unavailable, the app explicitly shows the provider's internal route ID.

### Streamed Los Angeles vehicles

LA Metro bus and rail positions use the agency’s public WebSocket service. Each agency has one server-side connection shared across viewers. The browser refreshes its snapshot every five seconds; actual GPS observation timestamps determine freshness and motion. Connections stop after two minutes without snapshot requests and reconnect with backoff after interruption. Playback delay adapts to observed cadence and delivery age.

### Follow the International Space Station

**Follow ISS** finds the station anywhere on the globe and follows its ground track at a continental zoom. The gold marker and source panel explicitly identify an **orbital model estimate**, not live on-board GPS. Where the ISS at? supplies timestamped positions, altitude and orbital speed. A shared ten-second fetch feeds adaptive buffered playback, with a satellite-specific speed limit and continuous date-line trails. No future position is extrapolated when reports stop.

### Public Finnish vessel stream

The Gulf of Finland shortcut connects the public Fintraffic / Digitraffic AIS stream without an access key. Ship markers, trails and **Follow ship** use received position reports. Coverage follows the Finnish receiver network, with fresh vessels also visible along other Finnish coastal areas. One MQTT-over-TLS connection is shared across viewers and closes after two minutes without requests. Fintraffic attribution and the CC BY 4.0 license link appear on the map.

### Optional vessel feeds

Neither vessel credential was configured during implementation; both adapters are implemented and fixture-tested, but their authenticated network paths remain unverified.

Set `WSDOT_API_KEY` for Washington State Ferries and `AISSTREAM_API_KEY` for [AISStream](https://aisstream.io/). Set these in the server process environment and restart; `.env` files are not loaded automatically. Keys never go to the browser or public repository. AIS uses one compressed server-side WebSocket for both regions, bounded in-memory storage and exponential reconnect backoff. AIS timestamps identify reception time, which may differ from the vessel's sensor observation time.


## Expanded live motion

The catalog now has 60 active integrated layers, including 27 motion-capable layers (some require credentials). Vehicles remain visible as Canvas dots at regional/world zooms, changing to detailed icons at street zooms. Interpolation uses a binary search over up to 600 samples per track. Playback delay adapts between 10 and 180 seconds; it never extrapolates observed vehicles beyond the last received position.

- **New public observations:** Finnish train GPS, SondeHub weather balloons, Denver RTD vehicles, and Lisbon metropolitan buses. Train/balloon streams are shared, compressed MQTT-over-WebSocket connections and stop after two idle minutes.
- **Modeled orbital motion:** CelesTrak science satellites and stations, propagated with SGP4. Clearly labeled estimates, not spacecraft telemetry; the existing ISS layer stays separate. Follow buttons support both satellites and balloons.
- **Environmental animation:** a 6×6 Open-Meteo wind grid with bilinear interpolation, NOAA global infrared cloud loops, and NOAA/Vaisala 15-minute lightning-density loops. Wind particles illustrate modeled flow at exaggerated visual speed. Lightning is aggregate density, not individual flashes or a raw GOES GLM feed. Weather imagery plays at accelerated speed and retains original frame timestamps.
- **Route-aware transit:** static GTFS shapes load in the background for MBTA, King County Metro, and Sound Transit. Matching requires the same trip/shape, GPS within 80 m of the shape, plausible speed, and forward progress. Otherwise playback retains the straight segment between observations. Route availability depends on matching provider identifiers; a shape is never guessed from a route name.
- **Discovery:** opening the world view/explorer starts shared checks for up to 24 configured destinations, with two concurrent workers. Badges distinguish coordinate changes between checks from movement in browser playback. Checks stop after demand expires.
- **Credential-dependent integrations:** regional 511 Bay transit, viewport-driven AISStream vessels, Washington State Ferries, and sampled TomTom road flow are wired but need keys. AIS subscriptions follow viewed coastal regions, including the date line. TomTom samples up to nine nearby road segments; its particles represent aggregate speed, not individual cars or complete road coverage.

Set optional keys in the same shell before starting (see `.env.example` for names). The app does **not** automatically read `.env` files. Do not commit key values.

```powershell
$env:SF511_API_KEY = 'your-key'
$env:AISSTREAM_API_KEY = 'your-key'
$env:WSDOT_API_KEY = 'your-key'
$env:TOMTOM_API_KEY = 'your-key'
.\start.ps1
```

In Bash, use `export SF511_API_KEY='your-key'` (and equivalent variables), then `bash start.sh`. The default 511 quota is respected with a shared 65-second polling interval; credentials stay server-side.

For repeatable feed research, `python scout/discover_feeds.py provider-domain --output candidates.json` searches Transitland Atlas for GTFS VehiclePosition candidates. It does not auto-enable unverified feeds. Review provider terms and measure timestamp age, changing coordinates, gaps, coverage, and cadence before adding a candidate.

The expansion's timestamped API evidence is in [motion-expansion-verification.json](docs/motion-expansion-verification.json). Authenticated paths were not live-tested without keys. Browser automation was unavailable during this expansion; rendering logic was regression-tested and NOAA image responses were verified directly.

## Run

Quick start: the launchers create `.venv` if needed, install missing Python dependencies, and start the server. They try up to 20 nearby ports if the requested port is occupied, print the actual URL, and open it in your browser. No npm installation or environment activation is needed.

Windows PowerShell:

```powershell
.\start.ps1
# Optional custom port:
.\start.ps1 -Port 5282
```

If Windows blocks script execution, use `powershell -ExecutionPolicy Bypass -File .\start.ps1` for this invocation only.

macOS / Linux (Bash):

```bash
bash start.sh
# Optional custom port:
bash start.sh --port 5282
```

Use the **http://127.0.0.1:PORT** URL printed in the terminal, which may differ from 5281 if another server is already running. Avoid an old bookmark or `python -m http.server`: a static server can display the map but cannot provide live data. Keep the terminal open; **Ctrl+C** stops the server. Both scripts resolve paths relative to their own location, so they can also be called from another directory. Python 3.10+ must be installed; the first run needs internet access to download dependencies. Live feeds also require internet access.

### Manual setup

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

- **Moving vehicles:** King County Metro, Sound Transit, Community Transit, Everett Transit and Kitsap Transit GPS feeds, plus aircraft. Refresh every 30 seconds; transit reports expire after five minutes, aircraft after two. At regional and street zoom levels, vehicles move through buffered observations; short trails show the past three minutes (transit trails appear at zoom 12+). Lines do not represent roads or predicted travel.
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
- `scout/world.py`: fixed-provider viewport queries with validated bounding boxes, bounded caches and shared backoff.
- `scout/dist/explore.js`: pure geographic coverage, longitude wrapping and query-area helpers.
- `scout/ships.py`: optional server-side AIS receiver, never a browser WebSocket.
- `scout/dist/motion.js`: pure observation interpolation and activity balancing, tested with Node.
- `scout/dist/live.js`: persistent markers, following, pause controls and radar playback.
- `scout/dist/sources.json`: source registry and access inventory, shared by backend and UI.
- `scout/dist/`: buildless Leaflet UI, zoom-dependent clusters, presets, regional shortcuts, source details, saved views and city/coordinate search.
- `scout/tests/test_feeds.py`: deterministic adapter/cache tests; no network needed.

Python dependencies are `tzdata` for Pacific timestamps and `gtfs-realtime-bindings` / protobuf for transit feeds, and `websockets` for optional AIS ingestion. Backend fetches avoid browser CORS restrictions. The public layers need no personal API keys; the optional ferry adapter requires WSDOT_API_KEY. BART explicitly publishes the shared legacy API key used here. No credentials are stored in source. Saved map views use browser localStorage.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s scout/tests -v
node --test scout/tests/motion.test.cjs scout/tests/explore.test.cjs
node --check scout/dist/app.js
node --check scout/dist/live.js
```

All 18 Bay Area sources and 19 public Seattle sources returned successful responses on 2026-10-24. The live-motion update passes 29 Python regression tests and 15 JavaScript motion / coverage tests; browser checks covered region switching, source filtering and saved-view restoration. This is a point-in-time smoke test, not an uptime guarantee. Aircraft initially timed out and recovered on retry. Test counts and provider record counts will change.

## Data terms and limits

Map © OpenStreetMap contributors. Aircraft data © adsb.lol contributors, ODbL. CAMS / Open-Meteo model data requires CC BY 4.0 attribution; the free Open-Meteo API is for noncommercial use. Lyft Bike data and BART data have their own provider terms. Each source's documentation is linked in the catalog; data accessibility is not a blanket redistribution license. This prototype is intended for local exploration and needs an appropriate hosting/rate-limit/licensing plan before a public production deployment.

Dispatch records are reported calls, not verified crimes or confirmation of an ongoing emergency. Model estimates, planned closures, preliminary gauges, and agency wildfire reports must not be treated as emergency instructions.


### Worldwide natural-event reports

NASA EONET adds recent open wildfire, storm, sea-ice and other reported natural events. Scout uses the latest dated point for each event and a shared 15-minute refresh, then filters it to the map view. These are curated reports with approximate dates and positions, not live tracking or emergency alerts. Records older than a day are marked stale. Unsupported geometry and reports older than 30 days are omitted with a partial-coverage notice. Event details link directly to the NASA source record.
