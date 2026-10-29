"""Seattle / Puget Sound adapters, using explicit geographic bounds."""
import os
import re
import time
import urllib.request
import csv
import io
import zipfile
import routes
import threading
from google.transit import gtfs_realtime_pb2
import feeds as f

BOUNDS=(-123.6,46.8,-121.2,48.8)
TRANSIT={
 'metro':('King County Metro','https://s3.amazonaws.com/kcm-alerts-realtime-prod/vehiclepositions_enhanced.json'),
 'sound':('Sound Transit','https://feeds.sound-transit.continuousgtfs.io/vehicle_positions.pb'),
 'community':('Community Transit','https://s3.amazonaws.com/commtrans-realtime-prod/vehiclepositions.pb'),
 'everett':('Everett Transit','https://everett.mapstrat.com/current/gtfrealtime_VehiclePositions.bin'),
 'kitsap':('Kitsap Transit','https://kttracker.com/gtfsrt/vehicles'),
}

def point(*args,**kwargs):return f.point(*args,bounds=BOUNDS,**kwargs)

def fire():
 rows=f.fetch('https://data.seattle.gov/resource/kzjm-xkqj.json',{'$limit':2000,'$order':'datetime DESC','$where':f"datetime > '{f.local_since(.25)}'"})
 if not isinstance(rows,list):raise ValueError('Unexpected fire response')
 by={}
 for r in rows:
  item=point(r['incident_number'],r.get('latitude'),r.get('longitude'),r.get('type','Fire / EMS dispatch'),f"{r.get('address','Seattle')} · Public dispatch report; not confirmation that an incident is still active.",f.stamp(r.get('datetime'),True),summary='Seattle Fire · past 6 hours')
  if item:by[item['id']]=item
 return f.result(list(by.values()),'Seattle Fire public 911 calls, last six hours. Dispatch time is not incident-clearance time.'+(' Results capped at 2,000.' if len(rows)==2000 else ''))

ROUTE_LOCK=threading.Lock()
ROUTE_LABELS={}
ROUTE_RETRY={}
ROUTE_URLS={'metro':'https://metro.kingcounty.gov/GTFS/google_transit.zip','sound':'https://www.soundtransit.org/GTFS-rail/40_gtfs.zip'}

def transit_route_labels(key):
 """Small route table from the official static GTFS; never infer public route numbers."""
 global ROUTE_RETRY,ROUTE_LABELS
 with ROUTE_LOCK:
  if time.time()<ROUTE_RETRY.get(key,0):return ROUTE_LABELS.get(key,{})
  try:
   request=urllib.request.Request(ROUTE_URLS[key],headers={'User-Agent':f.USER_AGENT})
   with urllib.request.urlopen(request,timeout=20) as response:raw=response.read(30_000_001)
   if len(raw)>30_000_000:raise ValueError('Static GTFS exceeds size limit')
   with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    info=archive.getinfo('routes.txt')
    if info.file_size>2_000_000:raise ValueError('Route table too large')
    with archive.open(info) as route_file:
     rows=csv.DictReader(io.TextIOWrapper(route_file,encoding='utf-8-sig'))
     labels={row['route_id']:row.get('route_short_name') or row.get('route_long_name') for row in rows}
   ROUTE_LABELS[key]={k:v for k,v in labels.items() if v};ROUTE_RETRY[key]=time.time()+86400
  except Exception:ROUTE_RETRY[key]=time.time()+300
  return ROUTE_LABELS.get(key,{})

def parse_transit(data,agency,route_labels=None):
 items=[]; omitted=0
 for entity in data.get('entity',[]):
  v=entity.get('vehicle',{}); p=v.get('position',{}); t=f.stamp(int(v['timestamp'])) if v.get('timestamp') else None
  # A feed-header time is not the time a vehicle was observed.
  if not t or not -60_000 <= time.time()*1000-t <= 300_000:
   omitted+=1;continue
  vehicle=v.get('vehicle',{});trip=v.get('trip',{});route=trip.get('route_id',trip.get('routeId','unknown'))
  route_label=(route_labels or {}).get(route)
  route_text=f'Route {route_label}' if route_label else f'Route ID {route}'
  identifier=vehicle.get('id') or entity.get('id')
  items.append(point(identifier,p.get('latitude'),p.get('longitude'),f"{agency}{' · '+route_label if route_label else ''} · {vehicle.get('label') or identifier}",f"{route_text} · {v.get('current_status','Status not supplied')} · stop ID {v.get('stop_id','unknown')}. Route IDs are provider identifiers, not necessarily the number on the vehicle. GPS observation, not a scheduled position.",t,summary=f'{agency} · {route_text}',heading=p.get('bearing'),routeLabel=route_label,tripId=trip.get('trip_id',trip.get('tripId')),routeId=route))
 return f.result(items,f'Actual reported vehicle locations; {omitted} old or untimestamped records omitted. Coverage varies by route and vehicle. No position extrapolation.')

def transit(key):
 agency,url=TRANSIT[key]
 if key=='metro':data=f.fetch(url)
 else:
  from google.protobuf.json_format import MessageToDict
  req=urllib.request.Request(url,headers={'User-Agent':f.USER_AGENT})
  with urllib.request.urlopen(req,timeout=20) as r:raw=r.read(10_000_001)
  if len(raw)>10_000_000:raise ValueError('Transit feed too large')
  message=gtfs_realtime_pb2.FeedMessage();message.ParseFromString(raw)
  if not message.HasField('header'):raise ValueError('Missing GTFS header')
  data=MessageToDict(message,preserving_proto_field_name=True)
 value=parse_transit(data,agency,transit_route_labels(key) if key in ROUTE_URLS else None)
 return routes.enrich(value,ROUTE_URLS[key]) if key in ROUTE_URLS else value

def ferries():
 key=os.environ.get('WSDOT_API_KEY')
 if not key:return f.result([], 'Set WSDOT_API_KEY on the server to enable actual ferry GPS positions.',configurationRequired=True)
 rows=f.fetch('https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations',{'apiaccesscode':key})
 items=[]
 for r in rows:
  m=re.search(r'/Date\((\d+)',r.get('TimeStamp',''));t=int(m.group(1)) if m else f.stamp(r.get('TimeStamp'))
  if not t or not -60_000 <= time.time()*1000-t <= 300_000:continue
  items.append(point(r['VesselID'],r.get('Latitude'),r.get('Longitude'),r['VesselName'],f"{r.get('DepartingTerminalName','?')} → {r.get('ArrivingTerminalName','?')} · {r.get('Speed','?')} knots · {'At dock' if r.get('AtDock') else 'Underway'}. ETA is subject to change.",t,summary='Washington State Ferries',heading=r.get('Heading')))
 return f.result(items,'WSDOT vessel GPS reports; positions older than five minutes omitted.')

ADAPTERS={
 'sea-fire':fire,'sea-air':lambda:f.aircraft(BOUNDS,'47.6/-122.3/85'),
 'sea-quake':lambda:f.quakes(BOUNDS),'sea-weather':lambda:f.weather(BOUNDS,['KSEA','KBFI','KPAE','KTIW','KOLM','KBLI','KCLM','KAWO','KPWT']),
 'sea-tides':lambda:f.tides(BOUNDS,['9447130','9446484','9444900','9449880','9444090']),
 'sea-rivers':lambda:f.rivers(BOUNDS),'sea-wildfire':lambda:f.wildfire(BOUNDS),
 'sea-buoys':lambda:f.buoys(BOUNDS),'sea-radar':f.radar,
 'sea-airquality':lambda:f.airquality(BOUNDS,[('Seattle',47.61,-122.33),('Tacoma',47.25,-122.44),('Everett',47.98,-122.2),('Bellevue',47.61,-122.2),('Olympia',47.04,-122.9),('Bremerton',47.57,-122.63),('Bellingham',48.75,-122.48),('Port Angeles',48.12,-123.43)]),
 'sea-ferries':ferries,
 **{'sea-'+k:lambda k=k:transit(k) for k in TRANSIT},
}

def police():
 rows=f.fetch('https://data.seattle.gov/resource/33kz-ixgy.json',{'$limit':5000,'$order':'cad_event_original_time_queued DESC','$where':f"cad_event_original_time_queued > '{f.local_since(7)}'"})
 by={}
 for r in rows:
  identifier=r['cad_event_number']
  if identifier in by:continue
  i=point(identifier,r.get('dispatch_latitude'),r.get('dispatch_longitude'),r.get('initial_call_type','Police call'),f"{r.get('dispatch_address','Generalized location')} · {r.get('cad_event_clearance_description','Disposition unavailable')}. Historical call record; not an active incident or verified crime.",f.stamp(r.get('cad_event_original_time_queued'),True),summary=r.get('dispatch_neighborhood','Seattle police call history'))
  if i:by[identifier]=i
 return f.result(list(by.values()),'Last seven days of published call history, deduplicated by event. Publication can lag by days. No officer positions.'+(' Input capped at 5,000 unit rows.' if len(rows)==5000 else ''))

def parking():
 url='https://data.seattle.gov/resource/hiyf-7edq.json'
 newest=f.fetch(url,{'$select':'max(occupancydatetime) as latest'})
 if not newest or not newest[0].get('latest'):raise ValueError('No parking snapshot')
 latest=newest[0]['latest']
 rows=f.fetch(url,{'$where':f"occupancydatetime = '{latest}'",'$limit':5000})
 return f.result([point(r['sourceelementkey'],r['location']['coordinates'][1],r['location']['coordinates'][0],r.get('blockfacename','Paid parking'),f"{r.get('paidoccupancy','?')} paid sessions / {r.get('parkingspacecount','?')} spaces · {r.get('sideofstreet','')} side. Payment-derived estimate, NOT a sensor or proof of an available space.",f.stamp(r.get('occupancydatetime'),True),summary=r.get('paidparkingarea','SDOT paid parking')) for r in rows if r.get('location')],f'Latest published minute: {latest} Pacific. Publication may lag a day or more; payment-derived occupancy, not live availability.'+(' Capped at 5,000 blocks.' if len(rows)==5000 else ''))

def cameras():
 url='https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/SDOT_Traffic_Cameras/FeatureServer/0/query'
 d=f.fetch(url,dict(where="SERVSTAT='ACTV'",outFields='OBJECTID,LOCATION,SERVSTAT',outSR=4326,f='json',resultRecordCount=2000))
 return f.result([point(r['attributes']['OBJECTID'],r['geometry']['y'],r['geometry']['x'],r['attributes']['LOCATION'],'SDOT traffic camera location. Open the official traveler map to view camera imagery; this registry does not publish a verified image capture time.',summary='SDOT camera location',link='https://web.seattle.gov/Travelers/') for r in d['features'] if r.get('geometry')],'Camera locations from the city registry, refreshed daily. Imagery is viewed on the official SDOT map; these markers are not live traffic measurements.',partial=bool(d.get('exceededTransferLimit')))

def alerts():
 data=f.fetch('https://api.weather.gov/alerts/active?area=WA');items=[];missing=0;zones={}
 for row in data['features']:
  p=row['properties'];g=row.get('geometry')
  if g:geometries=[g]
  else:
   geometries=[]
   for u in p.get('affectedZones',[]):
    if not u.startswith('https://api.weather.gov/zones/'):continue
    if u not in zones:
     if len(zones)>=30:missing+=1;continue
     try:zones[u]=f.fetch(u).get('geometry')
     except Exception:zones[u]=None
    if zones[u]:geometries.append(zones[u])
    else:missing+=1
  for n,g in enumerate(geometries):items.extend(f.geometry_items(p['id']+str(n),g,p['event'],p.get('headline',''),f.stamp(p.get('sent')),bounds=BOUNDS,summary=p.get('areaDesc','')))
 return f.result(items,f'Active Washington alerts intersecting the regional envelope. {missing} zone geometries unresolved; other alerts may exist.',partial=missing>0)

ADAPTERS.update({'sea-police':police,'sea-parking':parking,'sea-cameras':cameras,'sea-alerts':alerts})
