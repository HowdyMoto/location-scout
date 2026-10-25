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

def parse_message(data,received=None):
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
    for region,bounds in BOUNDS.items():
        item=feeds.point(mmsi,lat,lon,(meta.get('ShipName') or f'Vessel {mmsi}').strip(),f"AIS MMSI {mmsi} · {str(speed)+' knots' if speed is not None else 'speed unavailable'}. Timestamp is {timestamp_kind}, not a verified sensor observation time. Reception and vessel coverage are incomplete.",t,bounds=bounds,heading=heading,summary='AIS vessel · reception timestamp',timestampKind=timestamp_kind)
        if item:return region,item
    return None

def consume():
    global CONNECTED
    from websockets.sync.client import connect
    delay=2
    while not STOP.is_set():
        try:
            with connect('wss://stream.aisstream.io/v0/stream',compression='deflate',open_timeout=15,ping_interval=20,ping_timeout=20,max_size=1_000_000) as socket:
                boxes=[[[b[1],b[0]],[b[3],b[2]]] for b in BOUNDS.values()]
                socket.send(json.dumps({'APIKey':os.environ['AISSTREAM_API_KEY'],'BoundingBoxes':boxes,'FilterMessageTypes':['PositionReport','StandardClassBPositionReport','ExtendedClassBPositionReport']}))
                while not STOP.is_set():
                    try:message=json.loads(socket.recv(timeout=10))
                    except TimeoutError:continue
                    if message.get('error') or message.get('MessageType')=='Error':raise ValueError('Stream rejected subscription')
                    if message.get('MessageType')=='SubscriptionConfirmation':
                        with LOCK:CONNECTED=True
                        delay=2
                    value=parse_message(message)
                    if value:
                        region,item=value
                        with LOCK:
                            TRACKS[(region,item['id'])]=item
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
    global THREAD
    if not os.environ.get('AISSTREAM_API_KEY'):
        return feeds.result([],'Set AISSTREAM_API_KEY on the server to enable streamed ship positions. No vessel data is simulated.',configurationRequired=True)
    with LOCK:
        if THREAD is None or not THREAD.is_alive():
            STOP.clear();THREAD=threading.Thread(target=consume,name='aisstream',daemon=True);THREAD.start()
        now=time.time()*1000
        items=[dict(v) for (r,_),v in TRACKS.items() if r==region and v['time']>now-300000]
        connected=CONNECTED
    return feeds.result(items,'AIS reception stream connected. Timestamps describe reception, not guaranteed sensor observation time.' if connected else 'AIS stream connecting or interrupted; retrying with backoff. Last received positions retain their timestamps.',partial=not connected)
