"""NASA EONET recent open-event reports; never live vehicle tracking."""
import math
import re
import time
import feeds as f


def parse(data):
    if not isinstance(data.get('events'), list):
        raise ValueError('Missing EONET events')
    items = {}
    omitted = 0
    now = time.time()*1000
    for event in data['events']:
        if event.get('closed'):
            continue
        identifier = event.get('id', '')
        if not re.fullmatch(r'EONET_[A-Za-z0-9_-]+', identifier):
            omitted += 1
            continue
        geometries = [(f.stamp(g.get('date')), g) for g in event.get('geometry', [])]
        geometries = [(t,g) for t,g in geometries if t is not None]
        if not geometries:
            omitted += 1
            continue
        timestamp, geometry = max(geometries, key=lambda x:x[0])
        coordinates = geometry.get('coordinates', [])
        if geometry.get('type') != 'Point' or len(coordinates)!=2 or not -60000 <= now-timestamp <= 30*86400000:
            omitted += 1
            continue
        category = ', '.join(c.get('title','') for c in event.get('categories', [])) or 'Natural event'
        description = f'{category}. Latest reported location for an event NASA EONET lists as open. Event locations and dates are approximate; this is a dated report, not live tracking or an emergency alert.'
        value = geometry.get('magnitudeValue')
        if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value):
            description += f" Reported magnitude: {value:g} {geometry.get('magnitudeUnit','')}."
        item = f.point(identifier, coordinates[1], coordinates[0], event.get('title',identifier), description, timestamp,
            bounds=(-180,-90,180,90), summary=f'NASA EONET · {category}', eventUrl=f'https://eonet.gsfc.nasa.gov/api/v3/events/{identifier}')
        if item:
            if identifier not in items or item['time']>items[identifier]['time']:
                items[identifier]=item
        else:
            omitted += 1
    return f.result(list(items.values()), f'NASA EONET recent open events. One latest point per event; dates and extents are approximate. Not a real-time emergency feed. {omitted} unsupported, old or invalid events omitted.', partial=bool(omitted))


def load():
    return parse(f.fetch('https://eonet.gsfc.nasa.gov/api/v3/events', {'status':'open','days':30}))
