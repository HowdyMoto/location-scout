"""Catalog-driven, timestamped GTFS Realtime vehicle positions worldwide."""
import time
import gzip
import io
import urllib.request
from google.transit import gtfs_realtime_pb2
import feeds as f


def parse(raw, source):
    message = gtfs_realtime_pb2.FeedMessage()
    message.ParseFromString(raw)
    if not message.HasField('header') or not message.IsInitialized():
        raise ValueError('Invalid GTFS Realtime feed')
    if message.header.incrementality == gtfs_realtime_pb2.FeedHeader.DIFFERENTIAL:
        raise ValueError('Differential feed needs a stateful adapter')
    now = time.time()
    items = {}
    omitted = 0
    for entity in message.entity:
        if entity.is_deleted or not entity.HasField('vehicle'):
            continue
        v = entity.vehicle
        if not v.HasField('timestamp') or not -60 <= now-v.timestamp <= 300 or not v.HasField('position'):
            omitted += 1
            continue
        identifier = v.vehicle.id or entity.id
        route = v.trip.route_id or 'not supplied'
        item = f.point(identifier, v.position.latitude, v.position.longitude,
            f"{source['source']} · {v.vehicle.label or identifier}",
            f'Route ID {route}. Actual vehicle GPS report; route IDs are provider identifiers, not public route numbers.',
            int(v.timestamp)*1000, bounds=source['bounds'],
            summary=f"{source['source']} · Route ID {route}",
            heading=v.position.bearing if v.position.HasField('bearing') else None)
        if item and (identifier not in items or item['time'] > items[identifier]['time']):
            items[identifier] = item
    return f.result(list(items.values()),
        f"{source['source']}. Actual reported positions; {omitted} old or untimestamped records omitted. "
        'Coverage varies by service and time of day. No position extrapolation.')


def load(source):
    request = urllib.request.Request(source['endpoint'], headers={
        'User-Agent': f.USER_AGENT, 'ET-Client-Name': 'howdymoto-scout',
        'Accept-Encoding': 'gzip'})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(10_000_001)
        compressed = response.headers.get('Content-Encoding', '').lower() == 'gzip'
    if len(raw) > 10_000_000:
        raise ValueError('Vehicle feed exceeds size limit')
    if compressed:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            raw = stream.read(10_000_001)
        if len(raw) > 10_000_000:
            raise ValueError('Decoded vehicle feed exceeds size limit')
    return parse(raw, source)
