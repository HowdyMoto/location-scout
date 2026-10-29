"""Run: python scout/server.py. Serves only dist and named, cached data adapters."""
import argparse
import json
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from startup import bind_server
from urllib.parse import urlsplit, parse_qs
from feeds import ADAPTERS
from seattle import ADAPTERS as SEATTLE_ADAPTERS
import ships
import world
import transit
import gbfs
import metro
import finnish_ships
import orbit
import streamfeeds
import satellites
import discovery
import lisbon
ADAPTERS.update(SEATTLE_ADAPTERS)
ADAPTERS['fi-ships']=finnish_ships.snapshot
ADAPTERS['iss-orbit']=orbit.load
ADAPTERS['fi-trains']=streamfeeds.TRAINS.snapshot
ADAPTERS['balloons']=streamfeeds.BALLOONS.snapshot
ADAPTERS['satellites']=satellites.load
ADAPTERS['lisbon-vehicles']=lisbon.load
ADAPTERS.update({'sea-ships':lambda:ships.snapshot('seattle'),'bay-ships':lambda:ships.snapshot('bay')})

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT/'dist/sources.json').read_text(encoding='utf-8'))
SOURCES = {s['id']:s for s in CATALOG if s['access']=='integrated' and s.get('region')!='world'}
ADAPTERS.update({key:lambda source=source:transit.load(source) for key,source in SOURCES.items() if source.get('adapter')=='gtfs-rt'})
ADAPTERS.update({key:lambda source=source:gbfs.load(source) for key,source in SOURCES.items() if source.get('adapter')=='gbfs'})
ADAPTERS.update({key:lambda source=source:metro.snapshot(source['agency']) for key,source in SOURCES.items() if source.get('adapter')=='metro-stream'})
CACHE = {}
HISTORY = {}
LOCKS = {key:threading.Lock() for key in SOURCES}


def load_source(key):
    source=SOURCES[key]
    with LOCKS[key]:
        old=CACHE.get(key)
        now=time.time()
        if old and now<old['retryAt']:
            return old['response']
        try:
            value=ADAPTERS[key]()
            if not isinstance(value.get('items'),list):raise ValueError('Invalid adapter output')
            if source.get('motion'):
                for identifier,points in value.get('history',{}).items():
                    remember_positions(key,[{**p,'id':identifier} for p in points])
                value['history']=remember_positions(key,value['items'])
            response={**value,'id':key,'status':'partial' if value.get('partial') else 'ok','fetchedAt':int(time.time()*1000),'error':None}
            retry=time.time()+source['refresh']
        except Exception:
            # Never return exception URLs: optional future providers may put keys in them.
            previous=old['response'] if old else {}
            response={**previous,'id':key,'status':'stale' if previous.get('fetchedAt') else 'unavailable','items':previous.get('items',[]),'fetchedAt':previous.get('fetchedAt'),'note':previous.get('note',''),'error':'Provider unavailable or returned an unsupported response. Retrying after 60 seconds.'}
            retry=time.time()+60
        CACHE[key]={'response':response,'retryAt':retry}
        return response

def remember_positions(key,items):
    """Per-source lock is held by load_source; bound memory and keep actual timestamps."""
    now=time.time()*1000
    tracks=HISTORY.setdefault(key,{})
    for item in items:
        t=item.get('time')
        if not isinstance(t,(int,float)) or not now-600000<t<=now+60000:continue
        track=tracks.setdefault(item['id'],[])
        if not track or t>track[-1]['time']:
            track.append({k:item[k] for k in ('lat','lon','time','heading','tripId','shapeId','routeDistance') if k in item})
        tracks[item['id']]=[p for p in track if p['time']>now-600000][-600:]
    for identifier in list(tracks):
        if not tracks[identifier] or tracks[identifier][-1]['time']<now-300000:del tracks[identifier]
    if len(tracks)>5000:
        for identifier in sorted(tracks,key=lambda k:tracks[k][-1]['time'])[:len(tracks)-5000]:del tracks[identifier]
    return {k:list(v) for k,v in tracks.items()}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT/'dist'),**kwargs)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path.startswith('/api/'):
            key=path[len('/api/'):]
            if key=='discovery':
                value=discovery.snapshot(SOURCES,load_source)
            elif key.startswith('world-'):
                if key[6:] not in world.KINDS:return self.send_error(404,'Unknown source')
                try:bounds=world.parse_bounds(parse_qs(urlsplit(self.path).query).get('bbox',[''])[0])
                except ValueError:return self.send_error(400,'Invalid bounding box')
                value=world.load(key[6:],bounds)
            else:
                if key not in SOURCES:return self.send_error(404,'Unknown source')
                value=load_source(key)
            data=json.dumps(value,allow_nan=False).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
            return
        if path not in {'/','/index.html','/app.js','/motion.js','/live.js','/environment.js','/explore.js','/style.css','/sources.json'}:
            return self.send_error(404)
        super().do_GET()
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        super().end_headers()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=5281)
    parser.add_argument('--auto-port',action='store_true',help='Try nearby ports if the requested port is unavailable')
    parser.add_argument('--open-browser',action='store_true',help='Open the actual server URL in your browser')
    args=parser.parse_args()
    try:server=bind_server(Handler,args.port,args.auto_port)
    except (OSError,ValueError) as exc:parser.exit(1,f'{exc}\n')
    url=f'http://127.0.0.1:{server.server_port}'
    print(f'Scout: {url} (Ctrl+C to stop)',flush=True)
    if args.open_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        ships.STOP.set()
        streamfeeds.TRAINS.stop.set()
        streamfeeds.BALLOONS.stop.set()
        server.server_close()
