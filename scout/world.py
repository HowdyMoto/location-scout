"""Validated viewport queries for fixed public providers; bounded, per-provider caches."""
import math
import threading
import time
import urllib.error
from email.utils import parsedate_to_datetime
from collections import OrderedDict
import feeds as f

GLOBE=(-180,-90,180,90)
US=(-125,24,-66,50)
KINDS={'air':30,'quake':300,'buoys':600,'weather':900,'airquality':3600,'radar':300,'rivers':900,'wildfire':900}
LOCKS={k:threading.Lock() for k in KINDS}
CACHE={k:OrderedDict() for k in KINDS}
SHARED={}
TRACKS={}
COOLDOWN={k:0 for k in KINDS}

def parse_bounds(text):
    try:b=tuple(float(v) for v in text.split(','))
    except (ValueError,AttributeError):raise ValueError('bbox must contain west,south,east,north')
    if len(b)!=4 or not all(math.isfinite(v) for v in b):raise ValueError('Invalid bounding box')
    w,s,e,n=b
    if not (-180<=w<=180 and -180<=e<=180 and -85.1<=s<n<=85.1) or w==e:raise ValueError('Bounding box out of range')
    return b

def segments(b):
    w,s,e,n=b
    return [b] if w<e else [(w,s,180,n),(-180,s,e,n)]

def contains(b,lat,lon):
    return any(w<=lon<=e and s<=lat<=n for w,s,e,n in segments(b))

def intersects(a,b):
    return any(x[0]<=y[2] and x[2]>=y[0] and x[1]<=y[3] and x[3]>=y[1] for x in segments(a) for y in segments(b))

def width(b):return b[2]-b[0] if b[2]>b[0] else 360+b[2]-b[0]
def center(b):return ((b[1]+b[3])/2,((b[0]+width(b)/2+180)%360)-180)

def query_radius(b):
    lat,_=center(b)
    return math.ceil(math.hypot((b[3]-b[1])*30,width(b)*30*max(.05,math.cos(math.radians(lat)))))

def samples(b):
    return [(f'{lat:.2f}, {lon:.2f}',lat,lon) for y in (.2,.5,.8) for x in (.2,.5,.8) for lat,lon in [(b[1]+(b[3]-b[1])*y,((b[0]+width(b)*x+180)%360)-180)]]

def shared(kind,fn):
    old=SHARED.get(kind)
    if old and time.time()<old[0]:return old[1]
    value=fn();SHARED[kind]=(time.time()+KINDS[kind],value);return value

def history(items):
    now=time.time()*1000
    for i in items:
        t=i.get('time')
        if not t or not now-600000<t<=now+60000:continue
        track=TRACKS.setdefault(i['id'],[])
        if not track or t>track[-1]['time']:track.append({k:i[k] for k in ('lat','lon','time','heading') if k in i})
        TRACKS[i['id']]=[p for p in track if p['time']>now-600000][-40:]
    for key in list(TRACKS):
        if not TRACKS[key] or TRACKS[key][-1]['time']<now-300000:del TRACKS[key]
    if len(TRACKS)>5000:
        for key in sorted(TRACKS,key=lambda k:TRACKS[k][-1]['time'])[:len(TRACKS)-5000]:del TRACKS[key]
    return {i['id']:list(TRACKS.get(i['id'],[])) for i in items}

def fetch_view(kind,b):
    if kind in {'quake','buoys'}:
        value=shared(kind,lambda:f.quakes(GLOBE) if kind=='quake' else f.buoys(GLOBE))
        return {**value,'items':[i for i in value['items'] if contains(b,i['lat'],i['lon'])]}
    if kind=='radar':
        if not intersects(b,US):return f.result([],'NOAA radar covers the contiguous United States.',coverageUnavailable=True)
        return shared(kind,f.radar)
    if kind=='air':
        lat,lon=center(b)
        radius=query_radius(b)
        if radius>250:return f.result([],'Zoom in to a regional view for aircraft (maximum query radius 250 nautical miles).',zoomRequired=True)
        value=f.aircraft(GLOBE,f'{lat:.3f}/{lon:.3f}/{max(10,radius)}')
        value['items']=[i for i in value['items'] if contains(b,i['lat'],i['lon'])]
        value['history']=history(value['items'])
        return value
    if kind in {'rivers','wildfire'}:
        if not intersects(b,US):return f.result([],'This source covers the contiguous United States.',coverageUnavailable=True)
        if width(b)>15 or b[3]-b[1]>15:return f.result([],'Zoom in to a regional view for detailed US observations.',zoomRequired=True)
        parts=[(max(w,US[0]),max(s,US[1]),min(e,US[2]),min(n,US[3])) for w,s,e,n in segments(b) if intersects((w,s,e,n),US)]
        items=[];notes=[]
        for bounds in parts:
            value=f.rivers(bounds) if kind=='rivers' else f.wildfire(bounds)
            items+=value['items'];notes.append(value['note'])
        return f.result(items,' '.join(notes))
    cities=samples(b)
    if kind=='airquality':return f.airquality(GLOBE,cities)
    if kind=='weather':
        d=f.fetch('https://api.open-meteo.com/v1/forecast',dict(latitude=','.join(str(c[1]) for c in cities),longitude=','.join(str(c[2]) for c in cities),current='temperature_2m,wind_speed_10m,wind_direction_10m,precipitation,cloud_cover',timezone='UTC',forecast_days=1))
        if not isinstance(d,list) or len(d)!=len(cities):raise ValueError('Unexpected weather response')
        return f.result([f.point(name,lat,lon,f"{r['current'].get('temperature_2m','?')} °C · {name}",f"Modeled conditions: wind {r['current'].get('wind_speed_10m','?')} km/h, precipitation {r['current'].get('precipitation','?')} mm, cloud cover {r['current'].get('cloud_cover','?')}%. Sampled model grid, not a station measurement.",f.stamp(r['current']['time']),bounds=GLOBE,summary='Open-Meteo · modeled conditions',heading=r['current'].get('wind_direction_10m')) for (name,lat,lon),r in zip(cities,d)],'Nine model samples across this view. Open-Meteo attribution / CC BY 4.0; free API is noncommercial.')
    raise ValueError('Unknown world source')

def load(kind,b):
    if kind not in KINDS:raise ValueError('Unknown world source')
    if kind=='air' and query_radius(b)>250:
        return {**f.result([],'Zoom in to a regional view for aircraft (maximum query radius 250 nautical miles).',zoomRequired=True),'status':'ok','fetchedAt':int(time.time()*1000),'error':None}
    with LOCKS[kind]:
        cache=CACHE[kind];old=cache.get(b)
        if old and time.time()<old[0]:cache.move_to_end(b);return old[1]
        if time.time()<COOLDOWN[kind]:
            previous=old[1] if old else {}
            return {**previous,'items':previous.get('items',[]),'status':'stale' if previous.get('fetchedAt') else 'unavailable','fetchedAt':previous.get('fetchedAt'),'error':'Provider temporarily unavailable or rate limited. Automatic retry scheduled.','retryAfter':math.ceil(COOLDOWN[kind]-time.time())}
        try:
            value=fetch_view(kind,b)
            response={**value,'status':'partial' if value.get('partial') else 'ok','fetchedAt':int(time.time()*1000),'error':None}
            retry=time.time()+KINDS[kind]
        except Exception as error:
            wait=60
            if isinstance(error,urllib.error.HTTPError) and error.code in {429,503}:
                value=error.headers.get('Retry-After','') if error.headers else ''
                try:wait=max(60,min(3600,float(value)))
                except ValueError:
                    try:wait=max(60,min(3600,parsedate_to_datetime(value).timestamp()-time.time()))
                    except (ValueError,TypeError,OverflowError):pass
                COOLDOWN[kind]=time.time()+wait
            previous=old[1] if old else {}
            response={**previous,'items':previous.get('items',[]),'fetchedAt':previous.get('fetchedAt'),'status':'stale' if previous.get('fetchedAt') else 'unavailable','error':'Provider unavailable or rate limited. Automatic retry scheduled.','retryAfter':wait}
            retry=time.time()+wait
        cache[b]=(retry,response);cache.move_to_end(b)
        while len(cache)>24:cache.popitem(last=False)
        return response
