"""Observed radar mosaics from the public RainViewer Weather Maps API."""
import re
import time
from datetime import datetime,timezone
import feeds as f

def parse(data):
    # Only the documented tile host and radar paths may reach browser rendering.
    if data.get('host') != 'https://tilecache.rainviewer.com':
        raise ValueError('Unexpected radar tile host')
    frames={}
    now=time.time()
    for frame in data.get('radar',{}).get('past',[]):
        t=frame.get('time');path=frame.get('path','')
        if not isinstance(t,(int,float)) or not now-10800<=t<=now+60:
            continue
        if not re.fullmatch(r'/v2/radar/[A-Za-z0-9_-]+',path):
            continue
        frames[t]='https://tilecache.rainviewer.com'+path+'/256/{z}/{x}/{y}/2/1_1.png'
    ordered=sorted(frames)[-13:]
    if not ordered or now-ordered[-1]>1800:
        raise ValueError('Radar observations unavailable or stale')
    times=[datetime.fromtimestamp(t,timezone.utc).isoformat() for t in ordered]
    return f.result([], 'RainViewer radar mosaics from the past two hours. Frame times are mosaic generation times; individual radars can be older. Blank areas can mean no rain OR no coverage. Personal/educational use; see provider terms.',
        raster={'type':'xyz','frames':times,'time':times[-1], 'frameUrls':[frames[t] for t in ordered],'maxNativeZoom':7})

def load():
    return parse(f.fetch('https://api.rainviewer.com/public/weather-maps.json'))
