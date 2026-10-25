"""Fixed-catalog GBFS station availability (versions 1, 2 and 3)."""
import time
import feeds as f

INFORMATION = {}


def count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def name(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        texts = [x for x in value if isinstance(x, dict) and isinstance(x.get('text'), str)]
        return next((x['text'] for x in texts if x.get('language') == 'en'), texts[0]['text'] if texts else '')
    return ''


def parse(information, status, source):
    stations = information.get('data', {}).get('stations')
    reports = status.get('data', {}).get('stations')
    if not isinstance(stations, list) or not isinstance(reports, list):
        raise ValueError('Invalid GBFS station response')
    lookup = {str(s['station_id']): s for s in stations if isinstance(s, dict) and 'station_id' in s}
    items = {}; omitted = 0; now = time.time()*1000
    for row in reports:
        station = lookup.get(str(row.get('station_id')))
        observed = f.stamp(row.get('last_reported'))
        if not station or not observed or not -60000 <= now-observed <= 900000:
            omitted += 1
            continue
        bikes = count(row.get('num_vehicles_available', row.get('num_bikes_available')))
        docks = count(row.get('num_docks_available'))
        bike_text = str(bikes) if bikes is not None else 'unknown'
        dock_text = str(docks) if docks is not None else 'unknown'
        def enabled(key):
            value = row.get(key)
            return 'enabled' if value is True or value == 1 else 'disabled' if value is False or value == 0 else 'unknown'
        summary = f'{bike_text} bikes / {dock_text} docks'
        item = f.point(station['station_id'], station.get('lat'), station.get('lon'),
            name(station.get('name')) or str(station['station_id']),
            f'{summary} available. Rentals {enabled("is_renting")}; returns {enabled("is_returning")}. Station availability, not rider positions or trip counts.',
            observed, bounds=source['bounds'], summary=summary,
            availability={'bikes':bikes,'docks':docks,'renting':row.get('is_renting'),'returning':row.get('is_returning')})
        if item and (item['id'] not in items or item['time'] > items[item['id']]['time']):
            items[item['id']] = item
    return f.result(list(items.values()), f"{source['source']}. Station availability reports; {omitted} unmatched, old or untimestamped reports omitted. Reports older than five minutes are marked stale; older than fifteen minutes are omitted. Availability changes can include maintenance and rebalancing, not only trips.")


def load(source):
    # URLs come only from the reviewed server catalog, never a browser query or
    # a fetched discovery document. Cache coordinates separately from live counts.
    key = source['stationInformation']
    old = INFORMATION.get(key)
    if not old or time.time()-old[0] >= 3600:
        info = f.fetch(key)
        if not isinstance(info.get('data', {}).get('stations'), list):
            raise ValueError('Invalid GBFS station information')
        INFORMATION[key] = (time.time(), info)
    return parse(INFORMATION[key][1], f.fetch(source['stationStatus']), source)
