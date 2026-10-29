"""One server-side AISStream connection for both supported regions. No browser secrets."""
import json
import os
import random
import threading
import time
from datetime import datetime, timezone
import feeds

BOUNDS={'bay':feeds.BBOX,'seattle':(-123.6,46.8,-121.2,48.8)}
LOCK=threading.Lock()
STOP=threading.Event()
TRACKS={}
THREAD=None
CONNECTED=False
DEMANDS={}

def parse_message(data,received=None,global_view=False):
    received=received or time.time()*1000
    kind=data.get('MessageType')
    if kind not in {'PositionReport','StandardClassBPositionReport','ExtendedClassBPositionReport'}:return None
    p=data.get('Message',{}).get(kind,{})
    if p.get('Valid') is False:return None
    meta=data.get('MetaData',{});mmsi=meta.get('MMSI') or p.get('UserID')
    lat=p.get('Latitude',meta.get('latitude',meta.get('Latitude')))
    lon=p.get('Longitude',meta.get('longitude',meta.get('Longitude')))
    if not mmsi:return None
    # Reception time is explicitly labeled; AIS UTC-second alone cannot establish report age.
    timestamp=meta.get('time_utc')
    observed=feeds.stamp(timestamp) if timestamp else None
    timestamp_kind='provider reception' if observed else 'local reception'
    t=observed or received
    heading=p.get('TrueHeading');course=p.get('Cog');speed=p.get('Sog')
    heading=heading if isinstance(heading,(int,float)) and 0<=heading<360 else course if isinstance(course,(int,float)) and 0<=course<360 else None
    speed=speed if isinstance(speed,(int,float)) and 0<=speed<102.3 else None
    for region,bounds in ({'global':(-180,-90,180,90)} if global_view else BOUNDS).items():
        item=feeds.point(mmsi,lat,lon,(meta.get('ShipName') or f'Vessel {mmsi}').strip(),f"AIS MMSI {mmsi} · {str(speed)+' knots' if speed is not None else 'speed unavailable'}. Timestamp is {timestamp_kind}, not a verified sensor observation time. Reception and vessel coverage are incomplete.",t,bounds=bounds,heading=heading,summary='AIS vessel · reception timestamp',timestampKind=timestamp_kind)
        if item:return region,item
    return None

def consume():
    global CONNECTED
    from websockets.sync.client import connect
    delay=2
    while not STOP.is_set():
        with LOCK:
            if not any(expiry>time.monotonic() for _,expiry in DEMANDS.values()):break
        try:
            with connect('wss://stream.aisstream.io/v0/stream',compression='deflate',open_timeout=15,ping_interval=20,ping_timeout=20,max_size=1_000_000) as socket:
                previous=None
                while not STOP.is_set():
                    with LOCK:
                        for key in list(DEMANDS):
                            if DEMANDS[key][1]<=time.monotonic():del DEMANDS[key]
                        bounds=[v[0] for v in DEMANDS.values()]
                    if not bounds:break
                    boxes=[[[b[1],b[0]],[b[3],b[2]]] for b in bounds]
                    signature=json.dumps(boxes)
                    if signature!=previous:
                        socket.send(json.dumps({'APIKey':os.environ['AISSTREAM_API_KEY'],'BoundingBoxes':boxes,'FilterMessageTypes':['PositionReport','StandardClassBPositionReport','ExtendedClassBPositionReport']}));previous=signature
                    try:message=json.loads(socket.recv(timeout=5))
                    except TimeoutError:continue
                    if message.get('error') or message.get('MessageType')=='Error':raise ValueError('Stream rejected subscription')
                    if message.get('MessageType')=='SubscriptionConfirmation':
                        with LOCK:CONNECTED=True
                        delay=2
                    value=parse_message(message,global_view=True)
                    if value:
                        region,item=value
                        with LOCK:
                            old=TRACKS.get((region,item['id']))
                            if old and old['time']>=item['time']:continue
                            if item['time']>time.time()*1000+60000:continue
                            TRACKS[(region,item['id'])]=item
                            CONNECTED=True;delay=2
                            now=time.time()*1000
                            for k in list(TRACKS):
                                if TRACKS[k]['time']<now-300000:del TRACKS[k]
                            if len(TRACKS)>5000:
                                oldest=min(TRACKS,key=lambda k:TRACKS[k]['time']);del TRACKS[oldest]
        except Exception:
            # Never log exceptions: subscription details contain a private API key.
            with LOCK:CONNECTED=False
            STOP.wait(delay+random.random());delay=min(delay*2,60)
    with LOCK:CONNECTED=False

def snapshot(region):
    return snapshot_view(BOUNDS[region])


def snapshot_view(bounds):
    global THREAD
    if not os.environ.get('AISSTREAM_API_KEY'):
        return feeds.result([],'Set AISSTREAM_API_KEY on the server to enable streamed ship positions. No vessel data is simulated.',configurationRequired=True)
    with LOCK:
        w,s,e,n=bounds
        parts=[bounds] if w<e else [(w,s,180,n),(-180,s,e,n)]
        if (e-w if e>w else 360+e-w)>30 or n-s>30:
            return feeds.result([],'Zoom to a coastal region for AIS receiver coverage.',zoomRequired=True)
        for part in parts:DEMANDS[tuple(part)]=(part,time.monotonic()+120)
        while len(DEMANDS)>24:del DEMANDS[min(DEMANDS,key=lambda k:DEMANDS[k][1])]
        if THREAD is None or not THREAD.is_alive():
            STOP.clear();THREAD=threading.Thread(target=consume,name='aisstream',daemon=True);THREAD.start()
        now=time.time()*1000
        items=[dict(v) for v in TRACKS.values() if v['time']>now-300000 and any(a<=v['lon']<=c and b<=v['lat']<=d for a,b,c,d in parts)]
        connected=CONNECTED
    return feeds.result(items,'AIS reception stream connected. Timestamps describe reception, not guaranteed sensor observation time.' if connected else 'AIS stream connecting or interrupted; retrying with backoff. Last received positions retain their timestamps.',partial=not connected)
