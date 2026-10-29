"""Optional static GTFS shapes, loaded off the live-request path and matched conservatively."""
import csv
import io
import math
import threading
import time
import urllib.request
import zipfile
import feeds as f

CACHE={}
RETRY={}
LOADING=set()
LOCK=threading.Lock()


def parse(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        def rows(name):
            info=archive.getinfo(name)
            if info.file_size>150_000_000:raise ValueError('GTFS table too large')
            with archive.open(info) as stream:
                yield from csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig'))
        trips={r['trip_id']:r.get('shape_id') for r in rows('trips.txt')}
        shapes={}
        for count,r in enumerate(rows('shapes.txt')):
            if count>2_000_000:raise ValueError('Too many shape points')
            lat,lon=float(r['shape_pt_lat']),float(r['shape_pt_lon'])
            if not math.isfinite(lat+lon) or not -90<=lat<=90 or not -180<=lon<=180:continue
            shapes.setdefault(r['shape_id'],[]).append((int(r['shape_pt_sequence']),lat,lon))
        for key,points in shapes.items():
            path=[];length=0
            for _,lat,lon in sorted(points):
                if path:
                    a=path[-1];length+=math.hypot((lat-a[0])*111195,(lon-a[1])*111195*math.cos(math.radians(lat)))
                path.append([lat,lon,length])
            shapes[key]=path if len(path)<=15000 else []
        return trips,shapes


def project(item,path):
    best=None;cos=math.cos(math.radians(item['lat']))
    for a,b in zip(path,path[1:]):
        ax=(a[1]-item['lon'])*111195*cos;ay=(a[0]-item['lat'])*111195
        dx=(b[1]-a[1])*111195*cos;dy=(b[0]-a[0])*111195;size=dx*dx+dy*dy
        if not size:continue
        t=max(0,min(1,-(ax*dx+ay*dy)/size));error=math.hypot(ax+t*dx,ay+t*dy)
        if best is None or error<best[0]:best=(error,a[2]+t*(b[2]-a[2]))
    return best[1] if best and best[0]<=80 else None


def enrich(value,url):
    with LOCK:
        cached=CACHE.get(url)
        if time.time()>=RETRY.get(url,0) and url not in LOADING:
            LOADING.add(url)
            def load():
                try:
                    request=urllib.request.Request(url,headers={'User-Agent':f.USER_AGENT})
                    with urllib.request.urlopen(request,timeout=30) as r:raw=r.read(60_000_001)
                    if len(raw)>60_000_000:raise ValueError('Static feed too large')
                    result=parse(raw)
                    with LOCK:CACHE[url]=result;RETRY[url]=time.time()+86400
                except Exception:
                    with LOCK:RETRY[url]=time.time()+600
                finally:
                    with LOCK:LOADING.discard(url)
            threading.Thread(target=load,daemon=True,name='gtfs-shapes').start()
    if not cached:return value
    trips,shapes=cached;used={}
    for i in value['items']:
        shape=trips.get(i.get('tripId'));path=shapes.get(shape,[])
        if not path:continue
        along=project(i,path)
        if along is not None:
            i['shapeId']=shape;i['routeDistance']=along;used[shape]=path
    return {**value,'shapes':used,'note':value['note']+' Matching trips use GTFS route geometry when GPS is within 80 m; other reports retain raw positions.'}
