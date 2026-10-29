"""Shared, demand-driven MQTT/WebSocket collectors; no browser connections or secrets."""
import json
import math
import threading
import time
import uuid
import urllib.request
from urllib.parse import urlsplit
from websockets.sync.client import connect
import feeds as f


def fresh(value):
    t = f.stamp(value)
    return t if t and -60000 <= time.time()*1000-t <= 300000 else None


def train(row):
    t = fresh(row.get('timestamp'))
    xy = row.get('location', {}).get('coordinates', [])
    if not t or len(xy) < 2 or row.get('trainNumber') is None:
        return None
    return f.point(f"{row.get('departureDate', '')}:{row['trainNumber']}", xy[1], xy[0],
        f"Finnish train {row['trainNumber']}", 'Fintraffic GPS observation. Not all trains report positions.',
        t, bounds=(19,59,32,71), summary='Fintraffic · train GPS', routeLabel=str(row['trainNumber']))


def balloon(row):
    t = fresh(row.get('datetime'))
    if not t or not row.get('serial'):
        return None
    altitude = row.get('alt')
    if not isinstance(altitude, (int, float)) or not math.isfinite(altitude) or not -500 <= altitude <= 60000:
        return None
    return f.point(row['serial'], row.get('lat'), row.get('lon'), f"Balloon {row['serial']}",
        f"Radiosonde GPS · altitude {altitude:,.0f} m. Volunteer receiver coverage; no predicted landing position.",
        t, bounds=(-180,-90,180,90), summary=f'SondeHub · {altitude:,.0f} m', heading=row.get('heading'), altitude=altitude)


def packet(kind, payload=b''):
    size=len(payload); prefix=bytearray([kind])
    while True:
        digit=size%128; size//=128; prefix.append(digit|(128 if size else 0))
        if not size:break
    return bytes(prefix)+payload


def string(value):
    raw=value.encode();return len(raw).to_bytes(2,'big')+raw


def packets(buffer):
    out=[]; offset=0
    while offset+2<=len(buffer):
        size=0; multiplier=1; index=offset+1
        while True:
            if index>=len(buffer):return out,buffer[offset:]
            digit=buffer[index];index+=1;size+=(digit&127)*multiplier
            if size>2_000_000 or multiplier>128**3:raise ValueError('Oversized MQTT packet')
            if not digit&128:break
            multiplier*=128
        if index+size>len(buffer):break
        out.append((buffer[offset],buffer[index:index+size]));offset=index+size
    return out,buffer[offset:]


def sonde_url():
    req=urllib.request.Request('https://api.v2.sondehub.org/sondes/websocket',headers={'User-Agent':f.USER_AGENT})
    with urllib.request.urlopen(req,timeout=20) as r: url=r.read(16000).decode().strip().strip('"')
    host=urlsplit(url).hostname or ''
    if not url.startswith('wss://') or not (host.endswith('.amazonaws.com') or host.endswith('.sondehub.org')):
        raise ValueError('Unexpected SondeHub connection host')
    return url


class Stream:
    def __init__(self, name, url, topic, parser):
        self.name=name;self.url=url;self.topic=topic;self.parser=parser
        self.lock=threading.Lock();self.items={};self.history={};self.thread=None
        self.lease=0;self.connected=False;self.stop=threading.Event()

    def accept(self, rows):
        with self.lock:
            for row in rows if isinstance(rows,list) else [rows]:
                if not isinstance(row,dict):continue
                try:item=self.parser(row)
                except (ValueError,TypeError,KeyError,OverflowError):continue
                if not item:continue
                old=self.items.get(item['id'])
                if old and old['time']>=item['time']:continue
                self.items[item['id']]=item
                track=self.history.setdefault(item['id'],[])
                track.append({k:item[k] for k in ('lat','lon','time','heading') if k in item})
                self.history[item['id']]=[p for p in track if p['time']>time.time()*1000-600000][-600:]
            cutoff=time.time()*1000-300000
            for key in list(self.items):
                if self.items[key]['time']<cutoff:self.items.pop(key);self.history.pop(key,None)
            while len(self.items)>3000:
                key=min(self.items,key=lambda k:self.items[k]['time']);self.items.pop(key);self.history.pop(key,None)

    def consume(self):
        delay=2
        while not self.stop.is_set() and time.monotonic()<self.lease:
            try:
                url=self.url() if callable(self.url) else self.url
                with connect(url,subprotocols=['mqtt'],compression='deflate',open_timeout=20,max_size=2_000_000) as ws:
                    ws.send(packet(0x10,string('MQTT')+bytes([4,2,0,30])+string('scout-'+uuid.uuid4().hex[:16])))
                    pending=b'';ping=time.monotonic()
                    while not self.stop.is_set() and time.monotonic()<self.lease:
                        if time.monotonic()-ping>15:ws.send(packet(0xc0));ping=time.monotonic()
                        try:raw=ws.recv(timeout=5)
                        except TimeoutError:continue
                        if not isinstance(raw,bytes):continue
                        pending+=raw
                        frames,pending=packets(pending)
                        for code,body in frames:
                            if code>>4==2:
                                if len(body)!=2 or body[1]!=0:raise ValueError('MQTT rejected connection')
                                ws.send(packet(0x82,b'\x00\x01'+string(self.topic)+b'\x00'))
                            elif code>>4==9:
                                if len(body)<3 or body[2]>=128:raise ValueError('Subscription rejected')
                                self.connected=True;delay=2
                            elif code>>4==3:
                                size=int.from_bytes(body[:2],'big');start=2+size;qos=(code>>1)&3
                                if qos:
                                    identifier=body[start:start+2];start+=2
                                    if qos==1:ws.send(packet(0x40,identifier))
                                self.accept(json.loads(body[start:]))
            except Exception:
                # Signed connection URLs must never appear in logs or API errors.
                self.connected=False
                self.stop.wait(delay);delay=min(60,delay*2)
            finally:self.connected=False

    def snapshot(self):
        with self.lock:
            self.lease=time.monotonic()+120
            if not self.thread or not self.thread.is_alive():
                self.stop.clear();self.thread=threading.Thread(target=self.consume,daemon=True,name=self.name);self.thread.start()
            items=[dict(i) for i in self.items.values() if i['time']>time.time()*1000-300000]
            history={i['id']:list(self.history.get(i['id'],[])) for i in items}
            return f.result(items,f'{self.name}: '+('stream connected.' if self.connected else 'connecting or interrupted; retrying.')+' Original observation times retained.',history=history,partial=not self.connected)


TRAINS=Stream('Fintraffic rail','wss://rata.digitraffic.fi/mqtt','train-locations/#',train)
BALLOONS=Stream('SondeHub balloons',sonde_url,'batch',balloon)
