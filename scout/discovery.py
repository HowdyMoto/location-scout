"""Bounded activity checks for destinations not yet visited; shared between viewers."""
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor

LOCK=threading.Lock()
RESULTS={}
PREVIOUS={}
THREAD=None
LEASE=0


def distance(a,b):
    x,y=math.radians(b[0]-a[0]),math.radians(b[1]-a[1])
    return 6371000*2*math.asin(min(1,math.sqrt(math.sin(x/2)**2+math.cos(math.radians(a[0]))*math.cos(math.radians(b[0]))*math.sin(y/2)**2)))


def check(source,loader):
    key=source['id'];center=source.get('destination',{}).get('center') or ([47.61,-122.33] if key=='sea-metro' else [37.78,-122.42])
    try:
        d=loader(key);now=time.time()*1000
        if d.get('configurationRequired') or d['status'] not in ('ok','partial'):
            result={'vehicles':0,'moving':0,'stations':0,'checked':False,'unavailable':not d.get('configurationRequired',False)}
        else:
            items=[i for i in d['items'] if i.get('time') and -60000<=now-i['time']<=300000 and distance(center,[i['lat'],i['lon']])<=50000]
            previous=PREVIOUS.get(key,{});moving=0
            for i in items:
                a=previous.get(i['id'])
                if not a:continue
                dt=(i['time']-a['time'])/1000;meters=distance([a['lat'],a['lon']],[i['lat'],i['lon']])
                if 0<dt<=120 and 2<meters<=source.get('maxSpeed',65)*dt:moving+=1
            PREVIOUS[key]={i['id']:i for i in items}
            result={'vehicles':len(items),'moving':moving,'stations':0,'checked':True,'unavailable':False}
        with LOCK:RESULTS[key]={**result,'checkedAt':int(time.time()*1000)}
    except Exception:
        with LOCK:RESULTS[key]={'vehicles':0,'moving':0,'stations':0,'checked':False,'unavailable':True,'checkedAt':int(time.time()*1000)}


def snapshot(sources,loader):
    global THREAD,LEASE
    with LOCK:
        LEASE=time.monotonic()+90
        if THREAD is None or not THREAD.is_alive():
            selected=[s for s in sources.values() if s.get('motion') and (s.get('destination') or s['id'] in ('sea-metro','bay-transit'))][:24]
            def run():
                with ThreadPoolExecutor(max_workers=2) as pool:
                    while time.monotonic()<LEASE:
                        list(pool.map(lambda s:check(s,loader),selected))
                        for _ in range(60):
                            if time.monotonic()>=LEASE:return
                            time.sleep(1)
            THREAD=threading.Thread(target=run,daemon=True,name='destination-discovery');THREAD.start()
        return {'items':[],'destinations':{k:dict(v) for k,v in RESULTS.items() if time.time()*1000-v['checkedAt']<180000},'note':'Fresh reports within 50 km. Movement means changed coordinates between checks, not a prediction.'}
