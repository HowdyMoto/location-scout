"""Viewport wind-model grids and optional sampled traffic flow. Neither tracks individuals."""
import math
import os
import time
import feeds as f


def wind(bounds):
    w,s,e,n=bounds; span=e-w if e>w else 360+e-w;size=6
    coordinates=[(s+(n-s)*y/(size-1),(w+span*x/(size-1)+180)%360-180) for y in range(size) for x in range(size)]
    rows=f.fetch('https://api.open-meteo.com/v1/forecast',dict(
        latitude=','.join(str(round(p[0],3)) for p in coordinates),longitude=','.join(str(round(p[1],3)) for p in coordinates),
        current='wind_speed_10m,wind_direction_10m',wind_speed_unit='ms',timezone='UTC',forecast_days=1))
    if not isinstance(rows,list) or len(rows)!=len(coordinates):raise ValueError('Incomplete wind grid')
    vectors=[];times=[]
    for row in rows:
        c=row['current'];speed=c.get('wind_speed_10m');direction=c.get('wind_direction_10m');stamp=f.stamp(c.get('time'))
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (speed,direction)) or not stamp or not -60000<=time.time()*1000-stamp<=7200000:
            raise ValueError('Invalid or stale wind grid')
        if not 0<=speed<=150 or not 0<=direction<=360:raise ValueError('Invalid wind vector')
        # Meteorological direction describes where wind comes FROM.
        angle=math.radians(direction);vectors.append([-speed*math.sin(angle),-speed*math.cos(angle)]);times.append(stamp)
    return f.result([],'Open-Meteo wind model / CC BY 4.0. Animated particles illustrate flow; they are not tracked air parcels. Visual speed is exaggerated.',
        field={'bounds':bounds,'size':size,'vectors':vectors,'time':min(times)},attribution='Open-Meteo / CC BY 4.0')


def traffic(bounds):
    key=os.environ.get('TOMTOM_API_KEY')
    if not key:return f.result([],'Set TOMTOM_API_KEY on the server for sampled road speeds.',configurationRequired=True)
    w,s,e,n=bounds
    if e<w or e-w>1 or n-s>1:return f.result([],'Zoom to a city for sampled road speeds.',zoomRequired=True)
    items=[];seen=set();failed=0
    for y in (.2,.5,.8):
        for x in (.2,.5,.8):
            lat=s+(n-s)*y;lon=w+(e-w)*x
            try:
                row=f.fetch('https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/12/json',{'key':key,'point':f'{lat},{lon}','unit':'KMPH'})['flowSegmentData']
                coordinates=[[p['longitude'],p['latitude']] for p in row['coordinates']['coordinate']]
                speed=row['currentSpeed'];free=row['freeFlowSpeed'];confidence=row.get('confidence',0)
                if len(coordinates)<2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for p in coordinates for v in p):continue
                if not all(-180<=p[0]<=180 and -90<=p[1]<=90 for p in coordinates):continue
                if not isinstance(speed,(int,float)) or not 0<=speed<=250:continue
                identifier=str(coordinates)
                if identifier in seen:continue
                seen.add(identifier);t=int(time.time()*1000)
                item=f.point(identifier,coordinates[0][1],coordinates[0][0],'Road flow · '+str(speed)+' km/h',
                    f'Aggregate road speed; free flow {free} km/h, confidence {confidence}. Sampled roads only, not individual vehicles. Time is fetch time.',t,
                    bounds=(-180,-90,180,90),summary='TomTom · aggregate flow',timestampKind='fetch time',
                    flow={'coordinates':coordinates,'speed':speed,'free':free},geometry={'type':'LineString','coordinates':coordinates})
                if item:items.append(item)
            except Exception:failed+=1
    if failed==9:raise ValueError('Traffic provider unavailable')
    return f.result(items,'TomTom traffic: up to nine sampled road segments, not full road coverage. Moving particles represent aggregate flow, not tracked cars.',partial=bool(failed))
