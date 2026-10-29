"""Timestamped NOAA nowCOAST imagery. Lightning is aggregate density, not raw strikes."""
import time
import urllib.request
import xml.etree.ElementTree as ET
import feeds as f

LAYERS={
    'clouds':('satellite','global_longwave_imagery_mosaic','NOAA global infrared cloud imagery · hourly frames'),
    'lightning':('lightning_detection','ldn_lightning_strike_density','NOAA / Vaisala lightning density · 15-minute aggregates, not individual flashes'),
}


def load(kind):
    service,name,note=LAYERS[kind]
    url=f'https://nowcoast.noaa.gov/geoserver/observations/{service}/ows'
    req=urllib.request.Request(url+'?service=WMS&version=1.3.0&request=GetCapabilities',headers={'User-Agent':f.USER_AGENT})
    with urllib.request.urlopen(req,timeout=20) as response:raw=response.read(5_000_001)
    if len(raw)>5_000_000:raise ValueError('Capabilities too large')
    root=ET.fromstring(raw);ns={'w':'http://www.opengis.net/wms'}
    for layer in root.findall('.//w:Layer',ns):
        if layer.findtext('w:Name',namespaces=ns)!=name:continue
        for d in layer.findall('w:Dimension',ns):
            if d.get('name')!='time':continue
            frames=sorted({t for value in (d.text or '').split(',') if (t:=f.stamp(value)) and time.time()*1000-21600000<t<=time.time()*1000+60000})[-12:]
            if not frames:raise ValueError('No recent NOAA imagery')
            return f.result([],note+'. Coverage varies; playback is accelerated.',weatherRaster={'url':url,'layer':name,'frames':frames,'time':frames[-1]})
    raise ValueError('NOAA layer not found')
