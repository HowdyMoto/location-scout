"""Run: python scout/server.py. Serves only dist and named, cached data adapters."""
import argparse
import json
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from feeds import ADAPTERS

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT/'dist/sources.json').read_text(encoding='utf-8'))
SOURCES = {s['id']:s for s in CATALOG if s['access']=='integrated'}
CACHE = {}
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
            response={**value,'id':key,'status':'partial' if value.get('partial') else 'ok','fetchedAt':int(time.time()*1000),'error':None}
            retry=time.time()+source['refresh']
        except Exception:
            # Never return exception URLs: optional future providers may put keys in them.
            previous=old['response'] if old else {}
            response={**previous,'id':key,'status':'stale' if previous.get('fetchedAt') else 'unavailable','items':previous.get('items',[]),'fetchedAt':previous.get('fetchedAt'),'note':previous.get('note',''),'error':'Provider unavailable or returned an unsupported response. Retrying after 60 seconds.'}
            retry=time.time()+60
        CACHE[key]={'response':response,'retryAt':retry}
        return response

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT/'dist'),**kwargs)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path.startswith('/api/'):
            key=path[len('/api/'):]
            if key not in SOURCES:
                return self.send_error(404,'Unknown source')
            data=json.dumps(load_source(key),allow_nan=False).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
            return
        if path not in {'/','/index.html','/app.js','/style.css','/sources.json'}:
            return self.send_error(404)
        super().do_GET()
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        super().end_headers()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=5281)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Scout Bay Area: http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
