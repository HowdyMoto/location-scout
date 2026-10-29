"""Current SGP4 orbital estimates from cached CelesTrak OMM elements, not telemetry."""
import math
import time
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from sgp4 import omm
import feeds as f

ELEMENTS=[]
EXPIRES=0


def position(sat, seconds):
    d=datetime.fromtimestamp(seconds,timezone.utc)
    jd,fr=jday(d.year,d.month,d.day,d.hour,d.minute,d.second+d.microsecond/1e6)
    error,r,_=sat.sgp4(jd,fr)
    if error:return None
    # TEME -> Earth-fixed longitude with Greenwich mean sidereal time.
    t=(jd+fr-2451545.0)/36525
    gmst=math.radians((280.46061837+360.98564736629*(jd+fr-2451545)+.000387933*t*t-t*t*t/38710000)%360)
    lon=(math.degrees(math.atan2(r[1],r[0])-gmst)+180)%360-180
    horizontal=math.hypot(r[0],r[1]);lat=math.atan2(r[2],horizontal)
    for _ in range(5):
        n=6378.137/math.sqrt(1-.00669437999014*math.sin(lat)**2)
        lat=math.atan2(r[2]+.00669437999014*n*math.sin(lat),horizontal)
    return math.degrees(lat),lon


def load():
    global ELEMENTS,EXPIRES
    now=time.time()
    if now>=EXPIRES:
        records=f.fetch('https://celestrak.org/NORAD/elements/gp.php',{'GROUP':'science','FORMAT':'json'})
        records+=f.fetch('https://celestrak.org/NORAD/elements/gp.php',{'GROUP':'stations','FORMAT':'json'})
        parsed={}
        for r in records:
            epoch=f.stamp(r.get('EPOCH'))
            if not epoch or not -86400000<=now*1000-epoch<=14*86400000:continue
            try:sat=Satrec();omm.initialize(sat,r)
            except (ValueError,KeyError,TypeError):continue
            if str(r['NORAD_CAT_ID'])=='25544':continue # dedicated ISS layer already exists
            parsed[str(r['NORAD_CAT_ID'])]=(sat,r['OBJECT_NAME'],epoch)
        if not parsed:raise ValueError('No current orbital elements')
        ELEMENTS=list(parsed.items())[:300];EXPIRES=now+21600
    items=[];history={}
    for identifier,(sat,name,epoch) in ELEMENTS:
        if now*1000-epoch>14*86400000:continue
        points=[]
        for offset in range(-60,1,10):
            xy=position(sat,now+offset)
            if xy:points.append({'lat':xy[0],'lon':xy[1],'time':int((now+offset)*1000)})
        if not points:continue
        p=points[-1]
        item=f.point(identifier,p['lat'],p['lon'],name+' · modeled',
            'SGP4 orbital estimate from CelesTrak elements. Not onboard GPS or live spacecraft telemetry. '+
            f"Element epoch: {datetime.fromtimestamp(epoch/1000,timezone.utc).isoformat()}.",p['time'],
            bounds=(-180,-90,180,90),summary='CelesTrak / SGP4 · modeled orbit',elementEpoch=epoch)
        if item:items.append(item);history[identifier]=points
    return f.result(items,'Science satellites and space stations. Modeled positions; orbital elements cached six hours, rejected after 14 days.',history=history)
