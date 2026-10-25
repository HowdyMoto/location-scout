# Bay Area source audit

Checked 2026-10-24. The scope is live/recent geographic activity across the nine Bay Area counties, with SF-only sources explicitly labeled. This inventory distinguishes verified working adapters from discovery candidates; it does not claim universal coverage.

## Connected adapters

All 18 below were exercised against live endpoints. The browser subsequently showed 18/18 responding. Credentials are not required beyond BART's explicitly published shared public key. Feed availability can change.

| Source | Coverage | Data meaning / limits | Fetch interval |
| --- | --- | --- | --- |
| [SF law-enforcement calls](https://data.sf.gov/d/gnap-fj3t) | San Francisco; rolling 48h | Delayed: 10-minute refresh plus 10-minute delay. Some locations are redacted. | 600 seconds |
| [SF fire & EMS history](https://data.sf.gov/d/nuek-vuh3) | San Francisco; last 72h | Daily: Daily publication. Responding units combined into incidents. | 3600 seconds |
| [SF 311 reports](https://data.sf.gov/d/vw6y-z8j6) | San Francisco; last 72h | Daily: Public service requests, not confirmed findings. | 3600 seconds |
| [Aircraft](https://api.adsb.lol/docs) | 65 nautical miles around 37.8, -122.3 | Live: ADS-B/MLAT reception is incomplete. ODbL attribution applies. | 30 seconds |
| [Bikes & available docks](https://lyftbikes.com/system-data) | Participating Bay Area stations | Live: Live GBFS station reports; includes rental/return status. | 60 seconds |
| [BART departures](https://www.bart.gov/schedules/developers/api) | BART stations | Estimates: Predicted departures at stations, not train GPS. Uses BART’s published public key. | 60 seconds |
| [Highway cameras](https://cwwp2.dot.ca.gov/documentation/cctv/cctv.htm) | Caltrans District 4 | Registry: Camera locations and on-demand snapshots. Capture time is not supplied in metadata. | 1800 seconds |
| [Highway message signs](https://cwwp2.dot.ca.gov/documentation/cms/cms.htm) | Caltrans District 4 | Live: Only signs with a nonblank message are shown. | 300 seconds |
| [Highway lane closures](https://cwwp2.dot.ca.gov/documentation/lcs/lcs.htm) | Caltrans District 4 | Schedule: Active schedule windows and planned closures; not a congestion measurement. | 300 seconds |
| [Earthquakes](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php) | Regional envelope; last 7 days | Observed: Recent seismic events, not earthquake prediction. | 300 seconds |
| [Weather warnings](https://www.weather.gov/documentation/services-web-api) | Bay Area intersecting polygons / forecast zones | Alerts: Active warnings and advisories. Zone geometry may be broader than the event. | 300 seconds |
| [Weather stations](https://www.weather.gov/documentation/services-web-api) | 10 Bay Area airport stations | Observed: Measured station conditions; observation age shown. | 600 seconds |
| [Tide gauges](https://api.tidesandcurrents.noaa.gov/api/prod/) | Seven Bay / nearby coastal gauges | Observed: Preliminary water levels relative to MLLW; not water depth. | 360 seconds |
| [River & water gauges](https://api.waterdata.usgs.gov/docs/ogcapi/) | Regional envelope; observations within 24h | Observed: Local gauge datum, not flood-depth estimates. Anonymous API rate limits apply. | 900 seconds |
| [Air quality model](https://open-meteo.com/en/docs/air-quality-api) | 10 city samples across nine counties | Modeled: Model estimates, not local sensors. CC BY 4.0; free endpoint noncommercial. | 3600 seconds |
| [Wildfire incidents](https://data-nifc.opendata.arcgis.com/) | Regional envelope | Reports: Agency incident reports, not evacuation boundaries or guaranteed current perimeters. | 900 seconds |
| [Weather radar](https://www.weather.gov/gis/cloudgiswebservices) | NOAA CONUS mosaic viewed over the Bay Area | Radar: Timestamped base reflectivity raster overlay. Echoes are not a forecast; blank tiles do not establish good weather. | 300 seconds |
| [Buoys & coastal conditions](https://www.ndbc.noaa.gov/) | Regional envelope: offshore and coastal stations | Observed: Latest NDBC wind, wave and water-temperature reports. Missing observations remain missing. | 600 seconds |

## Additional sources and gaps

These are catalog entries, **not implemented adapters**. A key or agreement alone does not make them connected; the stream/API adapter and end-to-end verification are still required. For entries marked audit needed, even a suitable live endpoint has not been established. No credentials have been requested, generated, or purchased.

| Source | Access / implementation state | Notes |
| --- | --- | --- |
| [Regional transit vehicles](https://511.org/open-data/transit) | API key required | Muni, AC Transit, VTA, SamTrans, Caltrain, ferries and other participating agencies. GTFS-RT/SIRI; availability varies by operator. Default token budget 60 calls/hour. |
| [Traffic incidents & tolls](https://511.org/open-data/traffic) | API key required | Regional traffic events, WZDx closures and bridge/express-lane tolls. Distinct from Caltrans lane schedules. |
| [Vessel positions](https://aisstream.io/) | API key required | WebSocket AIS observations; requires an account/key and persistent stream adapter. Coverage is receiver-dependent. |
| [Measured air quality](https://docs.airnowapi.org/) | API key required | Regulatory monitor / reporting-area AQI. Separate from the integrated CAMS model. |
| [Neighborhood air sensors](https://api.purpleair.com/) | API key / credits required | Community sensors; corrections, placement and usage charges matter. |
| [Satellite heat detections](https://firms.modaps.eosdis.nasa.gov/api/area/) | API key required | Satellite-overpass detections; free MAP_KEY. Heat is not necessarily a wildfire. |
| [Power outages](https://pgealerts.alerts.pge.com/outage-tools/outage-map/) | Provider access needed | Public outage viewer. No supported reusable public API verified. Also investigate Silicon Valley Power and Palo Alto Utilities; PG&E does not cover every customer. |
| [Aggregated power outages](https://poweroutage.us/use-our-data) | Commercial access | Licensed API; provider geography/granularity varies. |
| [EV charging availability](https://evroaming.org/ocpi/) | Partner access needed | Live stall status generally requires operator/roaming access. Charger-location catalogs alone are not live availability. |
| [EV charger locations](https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/) | API key required | Station directory; not a promise of live stall occupancy. |
| [Parking availability](https://www.sfmta.com/garages-lots) | Feed not verified | Historical/open parking datasets are not proof of a working live occupancy feed. |
| [Evacuation zones](https://protect.genasys.com/) | Provider access needed | Use official county alerts. A stable, licensed regional ingestion API has not been verified. |
| [CAL FIRE reports](https://www.fire.ca.gov/incidents) | Public viewer | Official incident reports; not updated on a guaranteed schedule. NIFC incident feed is integrated separately. |
| [Oakland civic datasets](https://data.oaklandca.gov/) | Dataset audit needed | Local 311 and civic data. Not yet verified as a near-live dispatch source. |
| [San Jose civic datasets](https://data.sanjoseca.gov/) | Dataset audit needed | Municipal open data; cadence and public API availability must be verified dataset by dataset. |
| [Other county dispatch / alerts](https://www.bayareametro.gov/about-bay-area) | Coverage varies | Alameda, Contra Costa, Marin, Napa, San Mateo, Santa Clara, Solano and Sonoma require separate feed agreements/audits. SF dispatch is not regional dispatch coverage. |

## Findings that affect the product

- **Police vs fire:** SF's near-live law-enforcement feed is delayed. SF fire/EMS is a separate daily dataset. They cannot be advertised as equally live. Multiple fire unit responses are collapsed by call number.
- **Geography:** SF data is not a substitute for Oakland, San Jose or county dispatch. Regional sources have varying station/receiver coverage. The rectangular envelope includes adjacent areas.
- **BART:** Legacy departure estimates are served at stations. No train positions are inferred from those estimates. BART also recommends GTFS/GTFS-RT for future development.
- **511:** The documented default token allowance is 60 requests/hour; a future multi-operator integration needs shared scheduling or a raised allowance rather than polling every operator every minute.
- **Aircraft:** Receiver coverage is incomplete. Fetching a fresh response does not make every aircraft position fresh; observation age is checked separately.
- **Cameras:** Caltrans registry record timestamps can be old even when the snapshot is updated. They are never presented as image capture times.
- **Air quality:** Open-Meteo/CAMS is explicitly modeled. AirNow/PurpleAir would be separate measurement layers and are not substituted with invented sensor points.
- **Incidents:** Caltrans closures are schedule records. Some are future planned work. NIFC reports have variable reporting latency and are not an evacuation service.
- **Water:** NOAA MLLW and USGS local gauge datum are different reference frames; neither is simply flood depth at a nearby street.
- **Limits:** DataSF queries explicitly report reaching their 5,000-row cap. Redacted or missing coordinates are omitted and never geocoded into a guessed incident location. A source outage preserves cached timestamps and shows a stale state.
- **Access:** PG&E's public viewer is not treated as a documented reusable API. AIS requires a server-side WebSocket and credentials. Static EV/parking directories do not establish current availability.

## Follow-up priority

1. MTC 511 credential and budget: regional transit vehicles, traffic incidents, WZDx and tolls.
2. AISStream credential and persistent stream worker: vessel positions.
3. AirNow/PurpleAir credentials and terms: measured AQI.
4. NASA FIRMS MAP_KEY: satellite heat detections, separate from incident reports.
5. Utility/provider agreements for outages; county-specific dispatch and evacuation API audits.
6. Charging/parking partner feeds and additional municipal source audits.


## Seattle / Puget Sound audit — 2026-10-24

Official [Sound Transit OTD downloads](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads) links the transit endpoints. [Metro developer resources and terms](https://kingcounty.gov/en/dept/metro/rider-tools/mobile-and-web-apps) provides the enhanced JSON feed and attribution requirement. The app preserves vehicle observation timestamps rather than substituting the GTFS header time. Old/missing observations are omitted.

The former Traffic_Cameras_CDL service now returned a token requirement; the public SDOT_Traffic_Cameras replacement exposes locations but no image URLs. We link its markers to the official viewer and label them Directory. No protected camera endpoint or third-party credentials are used.

All 19 public adapters returned valid responses during the live smoke test. An empty active-warning response is valid. WSDOT ferry parsing is implemented but cannot be verified end-to-end without a user-owned access code. Pierce Transit returned HTTP 401 and remains unconnected. Police and parking publication delay was measured from maximum source timestamps, not inferred from the page title.

| Source | Status | Meaning / limitation |
| --- | --- | --- |
| [Aircraft](https://api.adsb.lol/docs) | integrated | ADS-B/MLAT reception is incomplete. ODbL attribution applies. |
| [Earthquakes](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php) | integrated | Recent seismic events, not earthquake prediction. |
| [Weather stations](https://www.weather.gov/documentation/services-web-api) | integrated | Measured station conditions; observation age shown. |
| [Tide gauges](https://api.tidesandcurrents.noaa.gov/api/prod/) | integrated | Preliminary water levels relative to MLLW; not water depth. |
| [River & water gauges](https://api.waterdata.usgs.gov/docs/ogcapi/) | integrated | Local gauge datum, not flood-depth estimates. Anonymous API rate limits apply. |
| [Wildfire incidents](https://data-nifc.opendata.arcgis.com/) | integrated | Agency incident reports, not evacuation boundaries or guaranteed current perimeters. |
| [Buoys & coastal conditions](https://www.ndbc.noaa.gov/) | integrated | Latest NDBC wind, wave and water-temperature reports. Missing observations remain missing. |
| [Weather radar](https://www.weather.gov/gis/cloudgiswebservices) | integrated | Timestamped base reflectivity raster overlay. Echoes are not a forecast; blank tiles do not establish good weather. |
| [Air quality model](https://open-meteo.com/en/docs/air-quality-api) | integrated | Model estimates, not local sensors. CC BY 4.0; free endpoint noncommercial. |
| [Seattle fire & EMS calls](https://data.seattle.gov/d/kzjm-xkqj) | integrated | Past six hours of dispatches, not active-incident confirmation. |
| [Seattle police call history](https://data.seattle.gov/d/33kz-ixgy) | integrated | Published call history can lag days. Last seven days, no officer tracking. |
| [Paid parking snapshots](https://data.seattle.gov/d/hiyf-7edq) | integrated | Latest published payment-derived estimate. Not live space availability; publication may lag a day. |
| [SDOT traffic cameras](https://www.arcgis.com/home/item.html?id=45a7e9f4d9584dbd9fdce1b951a7c4f6) | integrated | Active camera locations; imagery opens on the official SDOT traveler map. Registry is not live imagery. |
| [Weather warnings](https://www.weather.gov/documentation/services-web-api) | integrated | Active NWS warnings and zone polygons intersecting Puget Sound. |
| [King County Metro vehicles](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads) | integrated | Observed GPS positions, refreshed every 30 seconds. Positions older than five minutes or without observation time are omitted. Route IDs are not necessarily public route numbers. |
| [Sound Transit vehicles](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads) | integrated | Observed GPS positions, refreshed every 30 seconds. Positions older than five minutes or without observation time are omitted. Route IDs are not necessarily public route numbers. |
| [Community Transit vehicles](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads) | integrated | Observed GPS positions, refreshed every 30 seconds. Positions older than five minutes or without observation time are omitted. Route IDs are not necessarily public route numbers. |
| [Everett Transit vehicles](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads) | integrated | Observed GPS positions, refreshed every 30 seconds. Positions older than five minutes or without observation time are omitted. Route IDs are not necessarily public route numbers. |
| [Kitsap Transit vehicles](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads) | integrated | Observed GPS positions, refreshed every 30 seconds. Positions older than five minutes or without observation time are omitted. Route IDs are not necessarily public route numbers. |
| [Washington State Ferries](https://www.wsdot.wa.gov/ferries/api/vessels/documentation/) | Configured adapter; needs WSDOT key | Adapter ready. Set WSDOT_API_KEY on the server; registration required. No simulated vessels. |
| [Pierce Transit vehicles](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads) | access / research needed | Official linked Swiftly endpoint returned HTTP 401; provider authorization needed. |
| [WSDOT incidents, speeds & highway cameras](https://wsdot.wa.gov/traffic/api/) | access / research needed | WSDOT Traveler API registration/access code needed. Separate feeds for incidents, cameras, mountain passes and travel times. |
| [Seattle City Light outages](https://www.seattle.gov/city-light/outages) | access / research needed | Official outage viewer available; no supported anonymous API verified. PSE, Tacoma Power and Snohomish PUD require separate integrations. |
| [Commercial vessels & AIS](https://aisstream.io/) | access / research needed | AISStream key and server-side WebSocket ingestion required; AIS coverage is incomplete. |
| [Shared bikes & scooters](https://www.seattle.gov/transportation/projects-and-programs/programs/bike-program/bike-share) | access / research needed | Operator GBFS endpoints and access terms need verification; private rider trips are not mapped. |
| [Measured air quality & smoke](https://docs.airnowapi.org/) | access / research needed | AirNow API key required. The connected CAMS layer is modeled air quality, not measured sensors. |
| [Mountain snow & avalanche conditions](https://nwac.us/) | access / research needed | NWAC observations and forecasts are promising; stable API and reuse terms still need verification. |
| [Whale sightings](https://www.orcanetwork.org/) | access / research needed | Sightings are delayed community reports, not real-time animal tracking. No supported open API verified. |


## Live-motion update

The map now distinguishes received reports from their buffered visualization. A 90-second playhead interpolates only between observations separated by at most two minutes, rejecting implausible speeds. This is not proof that a vehicle followed the straight segment between reports. Source reports and fetch times remain visible separately from map playback time. New safety-report highlighting means newly received by this browser, not necessarily a newly occurring event.

[NOAA WMS](https://opengeo.ncep.noaa.gov/geoserver/conus/conus_bref_qcd/ows?service=WMS&request=GetCapabilities) advertises actual observation timestamps; the latest 12 are used for radar playback. The renderer loads the next frame before swapping and holds the previous frame on tile errors.

[AISStream](https://aisstream.io/documentation) is now an implemented optional adapter for both regions, not merely a candidate. It requires AISSTREAM_API_KEY, uses a compressed backend connection, subscribes to supported position-report variants and reconnects with jittered exponential backoff. The bounded viewport covers the two known regions. Unconfigured credentials produce an explicit access-needed state. Reception timestamps are labeled as such, and five-minute-old vessel reports are omitted. No authenticated ferry or AIS endpoint was tested because no keys were configured.

Metro rider-facing route names are joined from the officially linked [GTFS schedule](https://metro.kingcounty.gov/GTFS/google_transit.zip), capped at 30 MB compressed / 2 MB route-table size and cached for 24 hours. Failure falls back to explicitly labeled internal route IDs rather than guessed route numbers.

Sound Transit rail route labels are joined independently from its [official static feed](https://www.soundtransit.org/GTFS-rail/40_gtfs.zip), avoiding collisions between agency route identifiers.


## Viewport-driven exploration — 2026-10-25

All connected layers are enabled initially. Provider coverage is selected from map bounds, not a manually chosen region. Regional feeds use their documented envelope and global duplicates are replaced in the UI by shared viewport layers. Existing fixed regional API routes remain available for compatibility.

New `/api/world-{kind}?bbox=west,south,east,north` routes accept only eight fixed provider kinds and validated numeric bounds. Antimeridian views use west > east. Models sample nine points, not every location. Worldwide earthquake and buoy downloads are shared across viewport requests. NOAA radar tiles are restricted to the contiguous-US footprint; river and wildfire queries are also restricted to that region. Aircraft queries require a radius no greater than 250 nautical miles, matching [adsb.lol's API documentation](https://api.adsb.lol/docs). Open-Meteo current weather is [modeled data](https://open-meteo.com/en/docs), not a station measurement.

Live checks: SF city feeds automatically loaded after coordinate search; London weather and Tokyo air-quality models returned nine samples each; a date-line earthquake view returned 18 events. Aircraft calls returned HTTP 429, so worldwide aircraft rendering could not be live-verified in this run. The existing decoder is reused with explicit global bounds; outage handling is tested and honors Retry-After across views. An independent Airplanes.live probe returned HTTP 403 and was not integrated.

Regional-only sources retain their existing access restrictions, including WSDOT and AISStream credentials. Exploring a new city does not imply local transit / dispatch coverage there.

## International vehicle motion (2026-10-25)

Sources with `adapter: "gtfs-rt"` in `scout/dist/sources.json` use the shared `scout/transit.py` adapter. Their `bounds` and optional `coverageBounds` select feeds from the map viewport; `destination` adds an exploration shortcut. The server caches each source across viewers and retains timestamped motion history. Each vehicle must have its own recent observation timestamp; feed-header timestamps are not substituted. Differential feeds are rejected until a stateful adapter is implemented.

| Source | Official documentation | Refresh | Coverage limits |
| --- | --- | --- | --- |
| HSL | https://hsldevcom.github.io/gtfs_rt/ | 15 seconds | Helsinki region; only reported vehicles |
| MBTA | https://www.mbta.com/developers/gtfs-realtime | 20 seconds | Boston region; only reported vehicles |
| Adelaide Metro – Department for Infrastructure and Transport, South Australia | https://www.adelaidemetro.com.au/developer-info | 30 seconds | Adelaide; fewer vehicles outside service hours |
| Entur | https://developer.entur.no/open-data/realtime | 20 seconds | Participating Norwegian operators, not every operator or service |

All four returned fresh GPS records through the Scout API during integration. Geographic footprints are approximate selection areas, not guarantees of reception. Norway uses multiple rectangles to avoid activating its nationwide feed over Helsinki. Route IDs are labeled as provider IDs until static route metadata is connected.

Malaysia official GTFS endpoints were also investigated (https://developer.data.gov.my/realtime-api/gtfs-realtime.en). At the time of probing, KL, Penang and KTMB feeds were empty, MRT feeder data was stale, and Kuantan returned 404. These are not advertised as working integrations. Recheck during service hours before connecting them.

Remaining global expansion: additional continents and public transit providers; reliable worldwide aircraft coverage; ships with licensed access; worldwide animated weather; discovery destinations showing current source health; shared ingestion suitable for a deployed multi-user service. Current loopback server caches across local viewers but is not yet that deployment architecture.

### South America and France expansion

- Rio de Janeiro SMTR: official beta GTFS Realtime vehicle positions at `https://dados.mobilidade.rio/gtfs/realtime/onibus/vehicle-positions`; documentation: https://www.data.rio/documents/997bc16cc4344a5cb0e48ab06cbdfd1f/about. Approximately 1,700 fresh unique buses returned during verification. Snapshot counts fluctuate.
- TBM / Bordeaux Métropole: https://transport.data.gouv.fr/resources/83026 links the public vehicle feed. Its `opendata-bordeaux-metropole-flux-gtfs-rt` API parameter is the publicly published open-data access value, not a personal credential. Approximately 200 fresh vehicles returned during verification.
- Both use 20-second shared server caching, approximate regional footprints, per-vehicle timestamps, five-minute expiry and the existing bounded motion history. Neither converts schedules into invented positions.
- World explorer: available from the map in every region, with eight connected destinations, local time zones, source descriptions and a manual Surprise me action. It does not claim every destination has active vehicles at all hours. The map stays freely pannable outside these shortcuts.
- Further Malaysian BAS.MY Johor and Melaka probes returned no fresh positions; these remain unconnected pending usable observations.

### Worldwide aircraft restored with adsb.fi

The viewport aircraft layer now uses the documented public regional endpoint from adsb.fi: `https://opendata.adsb.fi/api/v3/lat/{lat}/lon/{lon}/dist/{nautical_miles}`. Documentation and terms: https://github.com/adsbfi/opendata/blob/main/README.md. Attribution: https://adsb.fi.

The public service is for personal, noncommercial use only. This local prototype uses that service; a commercial deployment needs suitable provider permission/access. The server serializes aircraft requests across viewports and spaces upstream calls by at least 1.1 seconds, caches each view for 30 seconds, and honors shared backoff. There is no attempt to rotate identities or evade limits. Regional radius remains capped at 250 NM. The old regional compatibility endpoints still use adsb.lol; the visible worldwide layer uses adsb.fi.

Aircraft feed clocks must be recent, and each aircraft needs a finite nonnegative position age no greater than 120 seconds. No feed time is fabricated when missing. The existing observation playback uses received positions and holds on gaps. Source attribution and noncommercial limits appear in source notes and record summaries.

Live API checks returned aircraft around London, Singapore and Cape Town (135, 7 and 5 respectively during verification). Counts vary and do not establish complete coverage. Added sky destinations for those areas to the world explorer. Remaining work includes wider local source coverage, worldwide weather animation, and production-grade access for a public commercial deployment.

### Worldwide animated radar

The visible `world-radar` layer now uses RainViewer's past radar mosaics worldwide, replacing its previous contiguous-US-only selection. The legacy NOAA regional adapters remain available for compatibility. Official documentation: https://www.rainviewer.com/api/weather-maps-api.html and https://www.rainviewer.com/api.html.

The backend shares one five-minute cached manifest across all views. It accepts only the documented HTTPS tile host and radar paths, sorts and bounds the last 13 past frames, excludes nowcast data, and rejects stale manifests. The browser loads actual XYZ radar tiles, caps native zoom at 7 (enlarging tiles at closer zooms), credits RainViewer visibly, and swaps frames only after loading. Pause/play remains available.

Frame times are mosaic generation timestamps, not synchronized timestamps for every contributing radar. Blank regions can mean no coverage rather than no precipitation. The playback label says coverage varies; source notes explain the distinction. The public service is intended for personal/educational use; commercial deployment needs suitable provider terms. During verification, the live manifest supplied 13 frames and a European PNG tile returned successfully; browser playback advanced outside the US without console errors.

Radar recovery regression checks cover failed frames, delayed Leaflet cleanup, stalled tile timeouts, late completion and disabling playback during a load. A failed frame advances to the next candidate after a five-second backoff; the last successful frame remains visible.

### Spain commuter trains

Renfe Cercanías is connected through the official public `https://gtfsrt.renfe.com/vehicle_positions.pb` feed. Source and CC BY 4.0 attribution: https://data.renfe.com/dataset/ubicacion-vehiculos. The publisher specifies 20-second updates; Scout uses that refresh interval and the shared GTFS Realtime adapter. Madrid is an explorer shortcut, while panning anywhere within the Spanish selection envelope activates the feed. The envelope is only a discovery area: individual services and observations determine actual coverage.

Live verification returned approximately 300 fresh trains, and 56 matching train identifiers changed coordinates between two snapshots. Missing per-vehicle timestamps and reports older than five minutes are excluded. A comparison probe of Renfe's separate high-speed/long-distance feed returned 243 entities without individual timestamps and a feed header roughly an hour old, so that feed is not connected. Finland's documented GTFS location endpoint returned HTTP 406, including with its documented protobuf media type, and remains unconnected.

### International bike availability

A reusable `gbfs` catalog adapter joins reviewed station-information and station-status endpoints, supporting GBFS 1/2 numeric timestamps and GBFS 3 ISO timestamps/localized names. Station coordinates are cached for one hour; availability refreshes every 60 seconds. Discovery URLs were obtained from MobilityData's public systems registry (https://github.com/MobilityData/gbfs/blob/master/systems.csv); runtime requests use only the fixed reviewed endpoint fields in the catalog. Specification: https://gbfs.org/documentation/reference/.

Connected systems:
- Tokyo: Docomo Bike Share / ODPT, https://api-public.odpt.org/api/v4/gbfs/docomo-cycle-tokyo/gbfs.json. The system-information feed declares CC BY 4.0. Approximately 1,930 timestamped stations verified; 9 changed availability between comparison snapshots.
- Buenos Aires: Ecobici, https://buenosaires.publicbikesystem.net/customer/gbfs/v3.0/gbfs.json. Public operator GBFS feed; approximately 392 timestamped stations verified, 2 with changed availability between snapshots.
- Toronto: Bike Share Toronto, https://toronto.publicbikesystem.net/customer/gbfs/v3.0/gbfs.json. Public operator GBFS feed; approximately 1,067 timestamped stations verified, 40 with changed availability between snapshots.

Counts vary. Individual station reports older than five minutes are visibly stale; reports older than fifteen minutes, future reports and missing timestamps are omitted. Unknown counts are not represented as zero. Both rental and return availability are shown. Initial station loads do not pulse; changed availability on a newer report pulses and is labeled `AVAILABILITY CHANGED`. These are inventory changes, potentially including maintenance/rebalancing, not inferred trips or tracked riders. Street-level markers display available bikes; wider views cluster stations.

Paris Vélib's public feed was investigated but all 1,519 reports were outside the freshness window during integration. It is not included as a connected live source. Its official open-data documentation is https://www.velib-metropole.fr/donnees-open-data-gbfs-du-service-velib-metropole.

### World-map discovery

The default camera now opens on the world. At zoom levels 7 and below, the map draws catalog-driven destination markers alongside enabled data layers. Nearby destinations are grouped by screen proximity to reduce label overlap; clicking a group opens its destination menu. City and sky markers are shortcuts, not new observations or claims of active vehicles. They disappear when zooming into local data. The World view button restores the overview; local feeds remain selected from map bounds.

Browser checks verified a grouped Madrid selection, the Renfe feed loading there, and direct selection of Tokyo with its bike layer. No manual region selector was required. Regression tests cover preserving every destination and grouping nearby labels across arbitrary grid boundaries.

### Shared LA Metro vehicle streams

Official API: https://api.metro.net/. WebSocket documentation: https://lacmta.github.io/metro-api-v2/docs/websockets/. Fixed endpoints are `wss://api.metro.net/ws/LACMTA/vehicle_positions` (buses) and `wss://api.metro.net/ws/LACMTA_Rail/vehicle_positions` (rail). The public documentation describes stream updates every three seconds, but Scout does not equate message delivery with new GPS observations.

`scout/metro.py` maintains one demand-driven connection per agency, shared across local viewers. Snapshot requests renew a two-minute lease; idle connections close. Reconnects use bounded exponential backoff with jitter. Messages have a 2 MB cap, each agency retains at most 5,000 vehicles, and observations older than five minutes are omitted. Only valid per-vehicle observation timestamps and coordinates in the configured LA envelope are accepted; out-of-order reports cannot replace newer positions. No timestamp is fabricated from receipt time. The browser refreshes shared snapshots every five seconds and uses the existing bounded observation history for playback. Route codes come from the agency's `route_code` field.

Live checks received approximately 1,135 fresh bus positions and 119 fresh rail positions, with both streams connected. Counts vary by service. Unit checks cover timestamp validation, geographic limits, out-of-order messages, shared connections and idle demand expiry. Strætó Iceland's official documentation was also reviewed, but real-time access requires an application, so it was not connected.

A 20-second comparison through Scout's API found 859 buses and 64 rail vehicles with newer timestamps and changed coordinates. After the playback buffer filled, the browser displayed 606 moving vehicles in the LA view; following a Metro Route 460 bus confirmed its detail state was moving between timestamped observations.

### Public Finnish coastal AIS

Official marine API documentation: https://www.digitraffic.fi/en/marine-traffic/. The implemented public transport is MQTT over TLS WebSockets at `wss://meri.digitraffic.fi:443/mqtt`, using the documented `vessels-v2/+/location` and metadata topics. The separate REST endpoint returned HTTP 406 during the probe; the documented MQTT service accepted the connection and delivered fresh position messages.

`scout/finnish_ships.py` uses Paho MQTT 2.x, one shared connection, a two-minute idle lease, automatic reconnect delay from 2 to 60 seconds, and bounded caches (5,000 position records / 10,000 vessel names). Position `time` is epoch seconds as documented; metadata timestamps are not substituted. Invalid coordinates, future/missing timestamps, old reports and AIS unavailable heading/speed sentinels are handled explicitly. Out-of-order messages cannot replace newer locations. Stationary ships remain stationary; interpolation uses only actual received reports. The browser refreshes snapshots every five seconds.

Source: Fintraffic / Digitraffic. License and attribution requirements: https://www.digitraffic.fi/en/terms-of-service/ and https://creativecommons.org/licenses/by/4.0/. The map credits the provider and license and labels the data as filtered/interpolated. Reception coverage is incomplete and is not worldwide AIS. Initial direct-stream verification received 304 fresh vessels within a short sample. `Follow ship` is available alongside flight and transit following.

The integrated API comparison showed 350 fresh vessels and 245 matching vessels changing coordinates over 25 seconds. The browser rendered ship markers and verified Follow ship on a vessel reporting 6.3 knots with a moving playback state. Later snapshots exceeded 400 fresh reports as the stream accumulated coverage.

### Global playback verification

Date-line crossings now interpolate longitude along the short arc instead of traveling through Greenwich. Trails unwrap each adjacent point into the same displayed world, and vehicle following uses the closest longitude copy. Deterministic tests cover eastbound and westbound crossings, impossible-speed rejection and trail continuity around 0, ±180 and 540 degrees. These are fixture tests; they do not claim a live aircraft crossing was observed.

Live API checks returned nine timestamped weather-model samples in views across Africa, Asia, Europe, North America, South America and Oceania. A browser search near Fiji at longitude 179.9 automatically loaded global layers without a region selection and showed model points on both sides of the date line without console errors. The sampled aircraft viewport was empty; no vehicle positions were fabricated.


### Netherlands transit — OVapi / Stichting OpenGeo

Provider directory: https://gtfs.ovapi.nl/nl/ . Feed: https://gtfs.ovapi.nl/nl/vehiclePositions.pb . Usage and license: https://gtfs.ovapi.nl/README . This is the provider's best-effort conversion of open Dutch transit data, not an agency affiliation or service-level guarantee. Coverage includes reporting vehicles across the Netherlands; do not infer every train has GPS coverage.

The layer activates automatically from its Netherlands footprint and adds Amsterdam to world discovery. It requests one shared snapshot per minute with an identifying project User-Agent and Accept-Encoding: gzip, following the provider's usage policy. Both compressed and decoded payloads are bounded to 10 MB. The adapter also accepts uncompressed protobuf. Only timestamped positions within five minutes and the configured coverage bounds are shown; the existing 90-second observation playback applies.

Initial direct verification found 1,718 fresh reports, and the integrated endpoint returned 1,660 fresh vehicles. All eight catalog-driven GTFS providers returned fresh positions after the shared gzip transport change. Deterministic tests cover both HTTP encodings and reject excessive decompressed payloads. A coordinate search into Amsterdam activated the feed without selecting a region.

Malaysia's documented official feeds were rechecked during local overnight hours: KTMB, Rapid KL and Penang were empty, while MRT feeder, Johor and Kuching samples were stale. They remain candidates rather than verified live integrations. Official endpoint documentation: https://developer.data.gov.my/realtime-api/gtfs-realtime .

A consecutive integrated snapshot contained 1,654 fresh reports; 1,423 matching vehicles changed coordinates with newer timestamps. Browser playback showed 322 moving objects in the Amsterdam view and successfully followed a Dutch transit vehicle with a moving state. No console errors were reported in this check.


### Discovery based on observed activity

World-explorer cards use already-fetched source snapshots to count reports within 50 km of each destination. Only healthy snapshots fetched in the last five minutes qualify; individual reports must satisfy the stricter of five minutes or their source age limit. Stale/unavailable, access-required, coverage-unavailable and zoom-limited responses never count as fresh activity. Aircraft counts also require the destination to lie within the actual requested view. Station availability is identified separately from moving vehicles.

Movement counts use the same 90-second interpolation and gap/speed rejection as map playback. Surprise me prefers destinations with observed movement, then fresh vehicles, then fresh station reports, and falls back to other destinations when no checked activity is available. This does not claim a quiet/unchecked area has no activity. Badges update in place while the dialog is open, without extra network requests or reordering focused controls.

Browser verification showed badges updating in place for transit, ships and bikes, an unavailable Bordeaux feed, and unchecked sky views. Surprise me opened the Netherlands, where moving playback was visible. No browser console errors were reported. Five new deterministic cases cover geographic filtering, stale/future timestamps, stationary and impossible tracks, date-line distance, unavailable/unchecked sources and activity-based selection.


### Canberra light rail — public legacy feed

Official catalog: https://www.data.act.gov.au/Transport/Canberra-Metro-Light-Rail-Transit-Feed-Vehicle-Upd/4f7h-bvpk . Source feed: https://files.transport.act.gov.au/feeds/lightrail.pb . Catalog metadata identifies Canberra Metro / ACT Government, a 15-second update frequency and CC BY-SA 4.0. The map links that attribution/license and identifies filtering and interpolation. This is light rail only, not bus coverage.

The developer page (https://www.transport.act.gov.au/contact-us/information-for-developers) marks the legacy feed deprecated, although it returned two fresh light-rail positions during the early-morning verification. It remains explicitly described as a legacy feed, with standard stale/unavailable handling. The replacement MyWay+ endpoint returned HTTP 401 and requires separately requested developer credentials; the published access guide is https://www.transport.act.gov.au/__data/assets/pdf_file/0005/2865398/MyWayPlus-GTFS-developer-access-guide-v1.2.pdf . No account was created and no credentials were fabricated. The catalog's specific share-alike license is retained even though the general developer page links a BY license.

Canberra is now an exploration destination and its feed activates from map bounds. The existing GTFS adapter discards old, future and out-of-bounds reports and uses received position history for playback.

### Queensland follow-up candidate

Official source documentation: https://translink.com.au/about-translink/open-data . The public SEQ feed https://gtfsrt.api.translink.com.au/api/realtime/SEQ/VehiclePositions returned 151 fresh positions. It is not activated in Scout yet: https://translink.com.au/about-translink/open-data/terms-and-conditions requires current developer contact details, and the source documentation says realtime feeds must be used with GTFS schedules. Follow-up should complete the developer-contact requirement and route metadata integration before activation. No contact details were submitted or messages sent.

Canberra verification: both fresh vehicles (LRV15 and LRV17) changed coordinates between integrated snapshots. The browser activated the layer from a coordinate search, showed two moving vehicles after the playback buffer filled, and followed LRV15. Provider/license attribution was visible; no console errors were reported.


### International Space Station orbital model

Provider and documentation: https://wheretheiss.at/w/developer . Fixed current-position endpoint: https://api.wheretheiss.at/v1/satellites/25544 . The provider permits unauthenticated access with roughly one request per second; Scout shares a ten-second cache across viewers. Attribution links to Where the ISS at? / Bill Shupp. This is a calculated orbital position, not onboard GPS reception or a claim of live spacecraft telemetry.

Only ISS ID 25544, kilometer units, finite coordinates, and provider timestamps within the past 120 seconds (up to 60 seconds future tolerance) are accepted. Missing altitude or speed is omitted rather than invented. The model layer is enabled worldwide; its gold satellite marker remains individually visible at world zoom. Follow ISS uses continental zoom, unlike street-level transit following. Playback still uses only received timestamps with a 90-second delay. Its 9,000 m/s ground-track sanity limit is isolated from aircraft (400 m/s) and ground/water (65 m/s) limits. Date-line wrapping and long-gap rejection remain in force.

Tests cover stale/future/missing timestamps, wrong satellite/units, invalid coordinates, optional metadata, satellite-speed interpolation, unchanged aircraft/ground rejection and holding after the last received sample.

Live verification returned an ISS estimate less than a second from the request time. Integrated samples changed from approximately 49.86° S, 60.70° W to 50.93° S, 54.14° W over 70 provider seconds, with six history samples accumulated. Browser Follow ISS centered the South Atlantic at continental zoom, rendered the model-labeled marker, and showed moving playback after the buffer filled, with no console errors. The radar independently reported an unavailable frame and retained its previous frame during this view.


### NASA EONET worldwide natural events

API documentation: https://eonet.gsfc.nasa.gov/docs/v3 . Fixed request: https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=30 . EONET curates dated event locations from contributing sources; its scope and limitations are described at https://eonet.gsfc.nasa.gov/what-is-eonet . Open status is the provider's classification, not confirmation of present danger, and metadata may only identify a reporting day.

Scout shares one global response per 15 minutes across map views. It selects the newest dated geometry, supports Point reports, rejects closed events, future/old dates and invalid coordinates, and preserves provider dates. It does not fall back to an older point when the latest geometry is unsupported. The map includes an explicit partial-response note for omissions. Date-line-aware viewport filtering uses the same world adapter as earthquakes and buoys. Source record URLs are generated from validated EONET identifiers.

Live verification returned 47 recent open events (34 wildfires, three severe storms and ten sea/lake-ice events). The integrated endpoint retained 46 latest valid points and reported one omitted event. A Pacific date-line view returned zero matching reports without borrowing records from other areas. Fixture tests cover newest-geometry selection, timestamp preservation, old/future/invalid/closed reports, polygon handling and shared fetches across views.

Browser verification activated the layer from a coordinate search near a dated storm report, showed its original report time separately from fetch time, and exposed the correct NASA event-record link. The detail remained open while zooming out; no console errors were reported.
