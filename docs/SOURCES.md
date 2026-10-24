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
