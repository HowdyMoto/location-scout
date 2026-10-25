"""Current ISS orbital estimates, not on-board GPS telemetry."""
import math
import time
import feeds as f


def parse(data):
    timestamp = data.get('timestamp')
    if data.get('id') != 25544 or data.get('units') != 'kilometers':
        raise ValueError('Unexpected satellite or units')
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp) or not -60 <= time.time()-timestamp <= 120:
        raise ValueError('Missing or stale orbital estimate')
    item = f.point('25544', data.get('latitude'), data.get('longitude'),
        'ISS · orbital estimate',
        'International Space Station ground position calculated from orbital elements. This is a model estimate, not live on-board GPS telemetry. Altitude and speed refer to the spacecraft; the marker shows its ground projection.',
        int(timestamp*1000), bounds=(-180,-85,180,85), summary='Current orbital model · Where the ISS at?', heading=None)
    if item is None:
        raise ValueError('Invalid orbital coordinates')
    for field, label, unit in [('altitude','Altitude','km'),('velocity','Orbital speed','km/h')]:
        value=data.get(field)
        if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>=0:
            item['description'] += f' {label}: {value:,.1f} {unit}.'
    return f.result([item], 'Where the ISS at? / Bill Shupp. Orbital model estimates, timestamped by the provider. Playback interpolates received estimates with a 90-second delay; it does not predict future positions.')


def load():
    return parse(f.fetch('https://api.wheretheiss.at/v1/satellites/25544'))
