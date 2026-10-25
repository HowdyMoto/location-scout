"""Shared, demand-driven LA Metro vehicle streams; fixed public endpoints only."""
import json
import math
import random
import threading
import time
import feeds as f

AGENCIES={'LACMTA':'LA Metro buses','LACMTA_Rail':'LA Metro rail'}
BOUNDS=(-119.2,33.3,-117,34.9)
STATES={a:{'lock':threading.Lock(),'thread':None,'items':{},'connected':False,'demand':0} for a in AGENCIES}


def parse(data,agency,now=None):
    if agency not in AGENCIES or not isinstance(data,dict):return None
    now=time.time() if now is None else now
    vehicle=data.get('vehicle',{});position=vehicle.get('position',{})
    raw=vehicle.get('timestamp')
    try:
        if isinstance(raw,bool):return None
        observed=float(raw)
        if not math.isfinite(observed) or not -60<=now-observed<=300:return None
    except (TypeError,ValueError):return None
    identifier=vehicle.get('vehicle',{}).get('id') or data.get('id')
    if not identifier:return None
    route=str(data.get('route_code') or '')
    heading=position.get('bearing')
    if not isinstance(heading,(int,float)) or not math.isfinite(heading) or not 0<=heading<360:heading=None
    return f.point(identifier,position.get('latitude'),position.get('longitude'),
        f"{AGENCIES[agency]} · {('Route '+route+' · ') if route else ''}{identifier}",
        'Timestamped vehicle position from the official LA Metro stream. Coverage and reporting frequency vary.',
        int(observed*1000),bounds=BOUNDS,heading=heading,routeLabel=route,
        summary=AGENCIES[agency]+(' · Route '+route if route else ''))


def receive(agency,item):
    state=STATES[agency]
    with state['lock']:
        previous=state['items'].get(item['id'])
        if not previous or item['time']>previous['time']:state['items'][item['id']]=item
        cutoff=time.time()*1000-300000
        state['items']={key:value for key,value in state['items'].items() if value['time']>=cutoff}
        if len(state['items'])>5000:
            state['items']=dict(sorted(state['items'].items(),key=lambda pair:pair[1]['time'],reverse=True)[:5000])


def wanted(state):
    with state['lock']:return time.monotonic()-state['demand']<120


def consume(agency):
    from websockets.sync.client import connect
    state=STATES[agency];delay=2
    try:
        while wanted(state):
            started=time.monotonic()
            try:
                with connect(f'wss://api.metro.net/ws/{agency}/vehicle_positions',open_timeout=15,
                             ping_interval=20,ping_timeout=20,max_size=2_000_000) as socket:
                    with state['lock']:state['connected']=True
                    while wanted(state):
                        try:raw=socket.recv(timeout=5)
                        except TimeoutError:continue
                        data=json.loads(raw)
                        item=parse(data,agency)
                        if item:receive(agency,item)
                        if time.monotonic()-started>30:delay=2
            except Exception:
                with state['lock']:state['connected']=False
                # Bounded reconnect backoff; stop when nobody requests this source.
                deadline=time.monotonic()+delay+random.random()
                while wanted(state) and time.monotonic()<deadline:time.sleep(.5)
                delay=min(60,delay*2)
    finally:
        with state['lock']:state['connected']=False


def snapshot(agency):
    if agency not in STATES:raise ValueError('Unknown Metro agency')
    state=STATES[agency]
    with state['lock']:
        state['demand']=time.monotonic()
        if state['thread'] is None or not state['thread'].is_alive():
            state['thread']=threading.Thread(target=consume,args=(agency,),name='metro-'+agency,daemon=True)
            state['thread'].start()
        items=[dict(i) for i in state['items'].values() if time.time()*1000-i['time']<=300000]
        connected=state['connected']
    return f.result(items,'LA Metro public vehicle stream. '+('Connected; ' if connected else 'Connecting or interrupted; ')+
        'individual observation timestamps retained. Old or untimestamped positions are omitted. No position extrapolation.',partial=not connected)
