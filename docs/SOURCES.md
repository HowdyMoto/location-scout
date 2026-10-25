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
