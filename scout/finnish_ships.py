"""Public Fintraffic AIS stream, shared across viewers with an idle lease."""
import json
import math
import re
import threading
import time
import uuid
import feeds as f

BOUNDS=(16,57,32,67)
LOCK=threading.Lock()
STATE={'thread':None,'connected':False,'demand':0,'items':{},'names':{}}


def parse(topic,data,now=None):
    match=re.fullmatch(r'vessels-v2/(\d{9})/locations?',topic)
    if not match or not isinstance(data,dict):return None
    now=time.time() if now is None else now
    observed=data.get('time')
    if isinstance(observed,bool) or not isinstance(observed,(int,float)) or not math.isfinite(observed) or not -60<=now-observed<=300:return None
    def angle(value):
        return value if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and 0<=value<360 else None
    heading=angle(data.get('heading'))
    if heading is None:heading=angle(data.get('cog'))
    speed=data.get('sog')
    speed=speed if isinstance(speed,(int,float)) and not isinstance(speed,bool) and math.isfinite(speed) and 0<=speed<102.3 else None
    mmsi=match[1]
    return f.point(mmsi,data.get('lat'),data.get('lon'),'Vessel '+mmsi,
        f'AIS MMSI {mmsi}. '+(f'{speed:g} knots. ' if speed is not None else 'Speed unavailable. ')+
        'Position report from the Finnish AIS receiver network; coverage is incomplete. Timestamp is supplied by the location feed.',
        int(observed*1000),bounds=BOUNDS,heading=heading,summary='Fintraffic AIS'+(f' · {speed:g} knots' if speed is not None else ''))


def accept(topic,data):
    metadata=re.fullmatch(r'vessels-v2/(\d{9})/metadata',topic)
    if metadata and isinstance(data,dict) and isinstance(data.get('name'),str):
        with LOCK:
            STATE['names'][metadata[1]]=data['name'].strip()[:100]
            while len(STATE['names'])>10000:STATE['names'].pop(next(iter(STATE['names'])))
        return
    item=parse(topic,data)
    if not item:return
    with LOCK:
        old=STATE['items'].get(item['id'])
        if not old or item['time']>old['time']:STATE['items'][item['id']]=item
        cutoff=time.time()*1000-300000
        STATE['items']={k:i for k,i in STATE['items'].items() if i['time']>=cutoff}
        if len(STATE['items'])>5000:STATE['items']=dict(sorted(STATE['items'].items(),key=lambda pair:pair[1]['time'],reverse=True)[:5000])


def wanted():
    with LOCK:return time.monotonic()-STATE['demand']<120


def consume():
    import paho.mqtt.client as mqtt
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='HowdyMoto/Scout; '+str(uuid.uuid4()),transport='websockets')
    def connected(c,u,flags,reason,properties):
        with LOCK:STATE['connected']=reason==0
        if reason==0:c.subscribe([('vessels-v2/+/location',0),('vessels-v2/+/metadata',0)])
    def disconnected(c,u,flags,reason,properties):
        with LOCK:STATE['connected']=False
    def message(c,u,msg):
        if len(msg.payload)>100000:return
        try:accept(msg.topic,json.loads(msg.payload))
        except (TypeError,ValueError,KeyError):return
    client.on_connect=connected;client.on_disconnect=disconnected;client.on_message=message
    client.tls_set();client.ws_set_options(path='/mqtt');client.connect_timeout=15
    client.reconnect_delay_set(min_delay=2,max_delay=60)
    try:
        client.connect_async('meri.digitraffic.fi',443,keepalive=30);client.loop_start()
        while wanted():time.sleep(1)
    finally:
        client.disconnect();client.loop_stop()
        with LOCK:STATE['connected']=False


def snapshot():
    with LOCK:
        STATE['demand']=time.monotonic()
        if STATE['thread'] is None or not STATE['thread'].is_alive():
            STATE['thread']=threading.Thread(target=consume,name='fintraffic-ais',daemon=True);STATE['thread'].start()
        now=time.time()*1000
        items=[{**i,'title':STATE['names'].get(i['id']) or i['title']} for i in STATE['items'].values() if now-i['time']<=300000]
        connected=STATE['connected']
    return f.result(items,'Fintraffic / Digitraffic AIS, CC BY 4.0. '+('Connected. ' if connected else 'Connecting or interrupted; retrying. ')+
        'Finnish receiver coverage only. Position-feed timestamps retained; old reports omitted. Ships hold when updates stop; no extrapolation.',partial=not connected)
