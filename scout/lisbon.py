"""Carris Metropolitana v2 live bus observations."""
import time
import feeds as f


def parse(rows):
    items=[];omitted=0
    for r in rows:
        t=f.stamp(r.get('timestamp'))
        if not t or not -60000<=time.time()*1000-t<=300000:omitted+=1;continue
        item=f.point(r.get('id'),r.get('lat'),r.get('lon'),f"Carris Metropolitana {r.get('line_id','')} · {r.get('id','')}",
            'Reported bus GPS in metropolitan Lisbon. Operator coverage varies; not every city service is included.',t,
            bounds=(-9.6,38.3,-8.5,39.3),summary='Carris Metropolitana · line '+str(r.get('line_id','')),
            heading=r.get('bearing'),routeLabel=r.get('line_id'),tripId=r.get('trip_id'))
        if item:items.append(item)
    return f.result(items,f'Carris Metropolitana GPS; {omitted} old or untimestamped reports omitted.')


def load():return parse(f.fetch('https://api.carrismetropolitana.pt/v2/vehicles'))
