"""Public Bay Area source adapters. No arbitrary URLs or browser-supplied credentials."""
import concurrent.futures
import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc
BBOX = (-123.6, 36.8, -121.2, 38.9)  # regional envelope, not a county boundary
USER_AGENT = 'LocationScout/0.3 (https://github.com/HowdyMoto/location-scout)'
BART_PUBLIC_KEY = 'MW9S-E7SL-26DU-VV8V'  # BART explicitly publishes this shared public key.
NIFC = 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0'

def fetch(url, params=None):
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = response.read(20_000_001)
        if len(raw) > 20_000_000:
            raise ValueError('Response exceeds size limit')
        data = json.loads(raw.decode('utf-8-sig'))
    if isinstance(data, dict) and data.get('error'):
        raise ValueError('Provider returned an error')
    return data

def stamp(value, local=False):
    if value is None or value == '':
        return None
    if isinstance(value, (int, float)):
        return int(value if value > 1e11 else value * 1000)
    try:
        d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if d.tzinfo is None:
            d = d.replace(tzinfo=ZoneInfo('America/Los_Angeles') if local else UTC)
        return int(d.timestamp() * 1000)
    except (ValueError, TypeError):
        return None

def point(identifier, lat, lon, title, description='', observed=None, *, bounds=BBOX, **extra):
    try:
        lat, lon = float(lat), float(lon)
        if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        if not (bounds[0] <= lon <= bounds[2] and bounds[1] <= lat <= bounds[3]):
            return None
    except (ValueError, TypeError):
        return None
    return dict(id=str(identifier), lat=lat, lon=lon, title=str(title), description=str(description), time=observed, **extra)

def result(items, note='', **extra):
    return dict(items=[i for i in items if i is not None], note=note, **extra)

def local_since(days):
    return (datetime.now(ZoneInfo('America/Los_Angeles')) - timedelta(days=days)).replace(tzinfo=None).isoformat(timespec='seconds')

def socrata(dataset, order, days, limit=5000):
    rows = fetch(f'https://data.sfgov.org/resource/{dataset}.json', {'$limit': limit, '$order': f'{order} DESC', '$where': f"{order} > '{local_since(days)}'"})
    if not isinstance(rows, list):
        raise ValueError('Unexpected DataSF response')
    return rows, len(rows) == limit

def police():
    rows, capped = socrata('gnap-fj3t', 'received_datetime', 2)
    items, hidden = [], 0
    for r in rows:
        g = r.get('intersection_point', {}).get('coordinates')
        if not g:
            hidden += 1
            continue
        items.append(point(r['cad_number'], g[1], g[0], r.get('call_type_final_desc') or r.get('call_type_original_desc', 'Dispatch'),
            f"{r.get('intersection_name', 'Location generalized')} · {r.get('agency', 'Law enforcement')} · {'Closed' if r.get('close_datetime') else 'Open in source'}. Reported call, not a verified crime. Location is generalized; no officer tracking.",
            stamp(r.get('received_datetime'), True), summary=r.get('analysis_neighborhood', 'San Francisco'), sourceUpdated=stamp(r.get('data_as_of'), True)))
    return result(items, f'Rolling 48h; 10-minute publication cycle plus 10-minute delay. {hidden} location-redacted records omitted.' + (' Result capped at 5,000 rows.' if capped else ''))

def fire():
    rows, capped = socrata('nuek-vuh3', 'received_dttm', 3)
    calls = {}
    for r in rows:
        calls.setdefault(r['call_number'], []).append(r)
    items = []
    for call, units in calls.items():
        r = next((r for r in units if r.get('case_location', {}).get('coordinates')), units[0])
        g = r.get('case_location', {}).get('coordinates')
        if not g:
            continue
        items.append(point(call, g[1], g[0], r.get('call_type', 'Fire / EMS call'),
            f"{r.get('address', 'San Francisco')} · {len(set(x.get('unit_id') for x in units))} responding units in retrieved records. {r.get('call_final_disposition', 'Disposition not supplied')}. Daily published history, not active dispatch status.", stamp(r.get('received_dttm'), True), summary=r.get('neighborhoods_analysis_boundaries', 'SF fire / EMS'), sourceUpdated=stamp(r.get('data_as_of'), True)))
    return result(items, 'Daily publication; last 72h of calls, deduplicated by call number.' + (' Input capped at 5,000 unit responses; older calls may be incomplete.' if capped else ''))

def civic():
    rows, capped = socrata('vw6y-z8j6', 'requested_datetime', 3)
    return result([point(r['service_request_id'], r.get('lat'), r.get('long'), r.get('service_name', '311 report'), f"{r.get('address', '')} · {r.get('service_subtype', '')} · {r.get('status_description', 'Unknown status')}. Public request, not a verified finding.", stamp(r.get('requested_datetime'), True), summary=r.get('analysis_neighborhood', 'SF 311')) for r in rows], 'Last 72h; daily dataset, not live dispatch.' + (' Capped at 5,000 reports.' if capped else ''))

def aircraft(bounds=BBOX, center='37.8/-122.3/65'):
    d = fetch('https://api.adsb.lol/v2/point/'+center)
    if 'ac' not in d:
        raise ValueError('Aircraft list missing')
    items = []
    for a in d['ac']:
        if a.get('seen_pos', 9999) > 120:
            continue
        title = (a.get('flight') or a.get('r') or a.get('hex', 'Aircraft')).strip()
        items.append(point(a.get('hex'), a.get('lat'), a.get('lon'), title,
            f"{a.get('t', 'Broadcast target')} · {'on ground' if a.get('alt_baro') == 'ground' else str(a.get('alt_baro', 'unknown')) + ' ft'} · {a.get('gs', 'unknown')} knots. Broadcast ADS-B/MLAT position; incomplete reception coverage.",
            int(d.get('now', time.time()*1000) - a.get('seen_pos', 0)*1000), bounds=bounds,summary='Aircraft · adsb.lol', heading=a.get('track')))
    return result(items, 'Regional ADS-B receiver query. Positions older than 2 minutes omitted. © adsb.lol contributors · ODbL.')

def bikes():
    base = 'https://gbfs.lyft.com/gbfs/2.3/bay/en/'
    info, status = parallel([lambda: fetch(base+'station_information.json'), lambda: fetch(base+'station_status.json')])
    status_by = {s['station_id']: s for s in status['data']['stations']}
    items = []
    for r in info['data']['stations']:
        s = status_by.get(r['station_id'])
        if not s:
            continue
        items.append(point(r['station_id'], r['lat'], r['lon'], r['name'],
            f"{s.get('num_bikes_available', '?')} bikes · {s.get('num_ebikes_available', '?')} e-bikes · {s.get('num_docks_available', '?')} docks available. Rentals {'enabled' if s.get('is_renting') else 'disabled'}; returns {'enabled' if s.get('is_returning') else 'disabled'}.", stamp(s.get('last_reported')), summary=f"{s.get('num_bikes_available', '?')} bikes / {s.get('num_docks_available', '?')} docks"))
    return result(items, 'Lyft Bike / Bay Wheels station availability. Station reports can lag the feed timestamp.')

def parallel(tasks):
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(tasks))) as pool:
        return list(pool.map(lambda task: task(), tasks))

def partial(tasks):
    def safe(task):
        try:
            return task(), None
        except Exception:
            return None, 'station unavailable'
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(tasks))) as pool:
        values = list(pool.map(safe, tasks))
    failed = sum(error is not None for _, error in values)
    if failed == len(tasks):
        raise ValueError('All stations unavailable')
    return [value for value, _ in values if value is not None], failed

def bart():
    p = {'key': BART_PUBLIC_KEY, 'json': 'y'}
    stations, departures = parallel([lambda: fetch('https://api.bart.gov/api/stn.aspx', {**p, 'cmd':'stns'}), lambda: fetch('https://api.bart.gov/api/etd.aspx', {**p, 'cmd':'etd', 'orig':'ALL'})])
    root = departures['root']
    # BART supplies a Pacific timestamp with explicit PDT/PST suffix.
    text = root.get('time', '')
    observed = None
    if text:
        d = datetime.strptime(root['date']+' '+text.rsplit(' ',1)[0], '%m/%d/%Y %I:%M:%S %p')
        observed = int(d.replace(tzinfo=timezone(timedelta(hours=-7 if text.endswith('PDT') else -8))).timestamp()*1000)
    by = {s['abbr']: s for s in root.get('station', [])}
    items=[]
    for s in stations['root']['stations']['station']:
        r=by.get(s['abbr'])
        if not r:
            continue
        estimates=[]
        for dest in r.get('etd', []):
            for e in dest.get('estimate', [])[:2]:
                estimates.append(f"{dest['destination']}: {e['minutes']}{' min' if e['minutes'].isdigit() else ''} (platform {e.get('platform','?')})")
        items.append(point(s['abbr'], s['gtfs_latitude'], s['gtfs_longitude'], s['name'], '; '.join(estimates) or 'No departure estimates supplied.', observed, summary='BART departure estimates · station, not train GPS'))
    return result(items, 'BART station departure predictions via the documented shared public key. Markers are stations, not moving trains.')

def caltrans(kind):
    d=fetch(f'https://cwwp2.dot.ca.gov/data/d4/{kind}/{kind}StatusD04.json')
    if 'data' not in d:
        raise ValueError('Caltrans data missing')
    items=[]
    for wrapper in d['data']:
        r=wrapper[kind]
        loc=r['location']
        if kind=='lcs':
            c=r['closure']; t=c['closureTimestamp']; loc=loc['begin']
            end=stamp(float(t['closureEndEpoch'])) if t.get('closureEndEpoch') else None
            cancelled=c.get('code1022',{}).get('isCode1022')=='true'
            finished=c.get('code1098',{}).get('isCode1098')=='true'
            if cancelled or finished or (end and end < time.time()*1000):
                continue
            start=stamp(float(t['closureStartEpoch'])) if t.get('closureStartEpoch') else None
            title=f"{loc.get('beginRoute')} · {c.get('typeOfWork', 'Closure')}"
            desc=f"{loc.get('beginLocationName')} to {r['location']['end'].get('endLocationName')}. {c.get('lanesClosed','?')} of {c.get('totalExistingLanes','?')} lanes. {'Planned' if start and start>time.time()*1000 else 'Within scheduled window'}; schedule is not confirmation of crews on site. Start {t.get('closureStartDate')} {t.get('closureStartTime')}; end {t.get('closureEndDate')} {t.get('closureEndTime')} Pacific."
            items.append(point(r['index'],loc.get('beginLatitude'),loc.get('beginLongitude'),title,desc,stamp(float(r['recordTimestamp']['recordEpoch'])),summary='Caltrans scheduled / active closure'))
        elif kind=='cctv':
            image=r.get('imageData',{}).get('static',{}).get('currentImageURL')
            items.append(point(r['index'],loc.get('latitude'),loc.get('longitude'),loc.get('locationName','Highway camera'), f"{loc.get('nearbyPlace')} · {loc.get('route')} · {'In service' if r.get('inService')=='true' else 'Out of service'}. Camera registry; image capture time is not supplied by this feed. Open the snapshot to inspect its embedded timestamp.",None,summary='Camera location · snapshot on demand',image=image if image and image.startswith('https://cwwp2.dot.ca.gov/') else None))
        else:
            m=r.get('message',{}); lines=[]
            for phase in ['phase1','phase2']:
                lines.extend(m.get(phase,{}).get(phase+'Line'+str(n),'') for n in range(1,4))
            text=' / '.join(line for line in lines if line)
            if not text:
                continue
            ts=m.get('messageTimestamp',{})
            items.append(point(r['index'],loc.get('latitude'),loc.get('longitude'),loc.get('locationName','Road sign'),text,stamp(ts.get('messageDate','')+'T'+ts.get('messageTime',''),True),summary='Caltrans message sign'))
    return result(items, 'Caltrans District 4. '+('Registry timestamps are not image timestamps.' if kind=='cctv' else 'Provider timestamps shown; schedules and messages may change.'))

def quakes(bounds=BBOX):
    d=fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson')
    return result([point(f['id'],f['geometry']['coordinates'][1],f['geometry']['coordinates'][0],f"M {f['properties']['mag']} · {f['properties']['place']}",f"Depth {f['geometry']['coordinates'][2]} km. Preliminary USGS observation; may be revised.",f['properties']['time'],bounds=bounds,summary='USGS earthquake · last 7 days') for f in d['features']], 'Last 7 days, filtered to the selected regional envelope.')

def alerts():
    d=fetch('https://api.weather.gov/alerts/active?area=CA')
    items=[]; missing=0
    for f in d['features']:
        p=f['properties']; g=f.get('geometry')
        # Resolve official forecast zones when the alert has no direct polygon.
        if not g:
            relevant=[u for u in p.get('affectedZones',[]) if u.rsplit('/',1)[-1] in BAY_ZONES]
            if not relevant:
                continue
            for u in relevant[:20]:
                try:
                    zone=fetch(u) if u.startswith('https://api.weather.gov/zones/') else None
                    if zone and zone.get('geometry'):
                        items.extend(geometry_items(p['id']+u,zone['geometry'],p['event'],p.get('headline',''),stamp(p.get('sent')),summary=p.get('areaDesc','')))
                except Exception:
                    missing+=1
        else:
            items.extend(geometry_items(p['id'],g,p['event'],p.get('headline',''),stamp(p.get('sent')),summary=p.get('areaDesc','')))
    return result(items,f'Active NWS alerts. {missing} zone geometries unavailable; unmapped alerts may exist.', partial=missing>0)

BAY_ZONES={'CAZ006','CAZ502','CAZ503','CAZ504','CAZ505','CAZ506','CAZ508','CAZ509','CAZ510','CAZ512','CAZ513','CAZ514','CAZ515','CAZ516','CAZ517','CAZ518','CAZ528','CAZ529','CAZ530'}

def coordinates(g):
    def walk(c):
        if c and isinstance(c[0],(int,float)):
            yield c
        else:
            for part in c:
                yield from walk(part)
    return list(walk(g.get('coordinates',[])))

def geometry_items(identifier,g,title,description,observed,*,bounds=BBOX,**extra):
    cs=coordinates(g)
    if not cs:
        return []
    west,south,east,north=min(c[0] for c in cs),min(c[1] for c in cs),max(c[0] for c in cs),max(c[1] for c in cs)
    if east<bounds[0] or west>bounds[2] or north<bounds[1] or south>bounds[3]:
        return []
    lon=(max(west,bounds[0])+min(east,bounds[2]))/2
    lat=(max(south,bounds[1])+min(north,bounds[3]))/2
    return [point(identifier,lat,lon,title,description,observed,bounds=bounds,geometry=g,**extra)]

def weather(bounds=BBOX, ids=None):
    ids=ids or ['KSFO','KOAK','KSJC','KSTS','KAPC','KCCR','KLVK','KHAF','KPAO','KSQL']
    data,failed=partial([lambda s=s:fetch(f'https://api.weather.gov/stations/{s}/observations/latest') for s in ids])
    items=[]
    for d in data:
        p=d['properties']; g=d.get('geometry')
        if not g: continue
        temp=p.get('temperature',{}).get('value'); wind=p.get('windSpeed',{}).get('value')
        items.append(point(p['stationId'],g['coordinates'][1],g['coordinates'][0],p['stationName'],f"{p.get('textDescription','')} · temperature {round(temp*9/5+32,1) if temp is not None else 'unavailable'} °F · wind {wind if wind is not None else 'unavailable'} km/h. Station observation, not a forecast.",stamp(p.get('timestamp')),bounds=bounds,summary='NWS weather observation'))
    return result(items,f'{len(data)}/{len(ids)} stations returned; {failed} unavailable.',partial=failed>0)

def tides(bounds=BBOX, ids=None):
    ids=ids or ['9414290','9414750','9414863','9415144','9414523','9415102','9415020']
    data,failed=partial([lambda s=s:fetch('https://api.tidesandcurrents.noaa.gov/api/prod/datagetter',dict(product='water_level',station=s,date='latest',datum='MLLW',time_zone='gmt',units='metric',format='json',application='LocationScout')) for s in ids])
    items=[]
    for d in data:
        if not d.get('data'):continue
        s=d['metadata']; r=d['data'][-1]
        items.append(point(s['id'],s['lat'],s['lon'],s['name'],f"Water level {r['v']} m relative to Mean Lower Low Water (MLLW). Quality: {r.get('q','unknown')}; preliminary readings are not flood-depth estimates.",stamp(r['t']),bounds=bounds,summary='NOAA tide gauge'))
    return result(items,f'{len(items)}/{len(ids)} gauges; {failed} unavailable. Latest preliminary observations, not tide predictions.',partial=failed>0)

def rivers(bounds=BBOX):
    since=(datetime.now(UTC)-timedelta(days=1)).isoformat()
    d=fetch('https://api.waterdata.usgs.gov/ogcapi/v1/collections/latest-continuous/items',dict(f='json',bbox=','.join(map(str,bounds)),parameter_code='00065',datetime=since+'/..',limit=1000))
    by={}
    for f in d['features']:
        p=f['properties'];g=f.get('geometry')
        if not g:continue
        key=p['monitoring_location_id']; t=stamp(p.get('time'))
        if key in by and (by[key]['time'] or 0)>=(t or 0):continue
        item=point(key,g['coordinates'][1],g['coordinates'][0],key,f"Gage height {p.get('value')} {p.get('unit_of_measure')}. {p.get('approval_status','')} measurement relative to this gauge's local datum; not water depth or a flood warning.",t,bounds=bounds,summary='USGS stream / water-level gauge')
        if item:by[key]=item
    capped=any(l['rel']=='next' for l in d.get('links',[]))
    return result(list(by.values()),'Gage height observations within 24h; one latest reading per site.'+(' Results truncated at 1,000 series.' if capped else ''))

def airquality(bounds=BBOX, cities=None):
    cities=cities or [('San Francisco',37.77,-122.42),('Oakland',37.8,-122.27),('San Jose',37.34,-121.89),('Santa Rosa',38.44,-122.71),('Napa',38.3,-122.29),('Concord',37.98,-122.03),('San Rafael',37.97,-122.53),('Fairfield',38.25,-122.04),('Redwood City',37.49,-122.24),('Livermore',37.68,-121.77)]
    d=fetch('https://air-quality-api.open-meteo.com/v1/air-quality',dict(latitude=','.join(str(c[1]) for c in cities),longitude=','.join(str(c[2]) for c in cities),current='us_aqi,pm2_5',timezone='UTC'))
    if not isinstance(d,list) or len(d)!=len(cities):raise ValueError('Unexpected model response')
    return result([point(name,lat,lon,f'{name} · modeled AQI {r["current"].get("us_aqi","unavailable")}',f"CAMS / Open-Meteo model estimate. PM2.5 {r['current'].get('pm2_5','unavailable')} μg/m³. This is a model grid sampled near the city, NOT a local air sensor.",stamp(r['current']['time']),bounds=bounds,summary='Modeled air quality · not measured') for (name,lat,lon),r in zip(cities,d)],'Model estimates, not sensor measurements. © CAMS / Open-Meteo · CC BY 4.0; free API for noncommercial use.')

def wildfire(bounds=BBOX):
    d=fetch(NIFC+'/query',dict(where='1=1',geometry=','.join(map(str,bounds)),geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects',outFields='*',outSR=4326,f='geojson',resultRecordCount=1000))
    items=[]
    for f in d['features']:
        p=f['properties'];g=f.get('geometry')
        if not g or p.get('FireOutDateTime'):continue
        items.append(point(p.get('IrwinID'),g['coordinates'][1],g['coordinates'][0],p.get('IncidentName','Wildfire'),f"{p.get('IncidentTypeCategory','')} · {p.get('IncidentSize','unknown')} acres · {p.get('PercentContained','unknown')}% contained. {p.get('POOCounty','')} county. Agency reports can lag; this is not an evacuation map.",stamp(p.get('ModifiedOnDateTime_dt')),bounds=bounds,summary='NIFC / WFIGS incident report'))
    return result(items,'Current WFIGS incident feed; no fixed reporting interval. Extinguished incidents omitted.'+(' Provider result limit reached.' if d.get('exceededTransferLimit') else ''))

ADAPTERS={'police':police,'fire':fire,'civic':civic,'air':aircraft,'bikes':bikes,'bart':bart,'cameras':lambda:caltrans('cctv'),'signs':lambda:caltrans('cms'),'closures':lambda:caltrans('lcs'),'quake':quakes,'alerts':alerts,'weather':weather,'tides':tides,'rivers':rivers,'airquality':airquality,'wildfire':wildfire}

def fetch_text(url):
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT})
    with urllib.request.urlopen(req,timeout=20) as r:
        data=r.read(10_000_001)
        if len(data)>10_000_000:raise ValueError('Response too large')
        return data.decode('utf-8')

def parse_buoys(text, bounds=BBOX):
    items=[]
    for line in text.splitlines():
        if line.startswith('#'):continue
        c=line.split()
        if len(c)<22:continue
        def value(n):return 'unavailable' if c[n]=='MM' else c[n]
        try:observed=int(datetime(*map(int,c[3:8]),tzinfo=UTC).timestamp()*1000)
        except ValueError:continue
        items.append(point(c[0],c[1],c[2],f'NDBC {c[0]}',f'Wind {value(9)} m/s · gust {value(10)} m/s · significant wave height {value(11)} m · dominant period {value(12)} s · water temperature {value(18)} °C. Missing values are not zero.',observed,bounds=bounds,summary='NOAA buoy / coastal observation'))
    return result(items,'NOAA NDBC latest available buoy/coastal reports. Some stations do not measure waves; observation ages vary.')

def buoys(bounds=BBOX):
    return parse_buoys(fetch_text('https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt'), bounds=bounds)

def radar():
    import xml.etree.ElementTree as ET
    url='https://opengeo.ncep.noaa.gov/geoserver/conus/conus_bref_qcd/ows'
    root=ET.fromstring(fetch_text(url+'?service=WMS&request=GetCapabilities'))
    ns={'w':'http://www.opengis.net/wms'}
    for layer in root.findall('.//w:Layer',ns):
        name=layer.find('w:Name',ns)
        if name is not None and name.text=='conus_bref_qcd':
            dim=layer.find("w:Dimension[@name='time']",ns)
            if dim is not None:
                frame=dim.attrib.get('default')
                if not stamp(frame):raise ValueError('Radar frame time missing')
                return result([],f'NOAA base reflectivity mosaic frame: {frame}. Radar echoes are not a forecast. Blank imagery can indicate no echo or unavailable radar.',raster={'url':url,'layer':'conus_bref_qcd','time':frame})
    raise ValueError('Radar time dimension unavailable')

ADAPTERS.update(buoys=buoys,radar=radar)
