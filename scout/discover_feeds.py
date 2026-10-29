"""Find GTFS VehiclePosition candidates in Transitland Atlas. Does not auto-enable feeds.

Example: python scout/discover_feeds.py denver --output candidates.json
Review provider documentation, license and rate limits before adding a candidate.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import quote
import feeds


def discover(query,limit=10):
    tree=feeds.fetch('https://api.github.com/repos/transitland/transitland-atlas/git/trees/main',{'recursive':1})
    names=[x['path'] for x in tree.get('tree',[]) if x['path'].startswith('feeds/') and x['path'].endswith('.dmfr.json') and query.lower() in x['path'].lower()][:limit]
    results=[]
    for name in names:
        data=feeds.fetch('https://raw.githubusercontent.com/transitland/transitland-atlas/main/'+quote(name,safe='/'))
        for feed in data.get('feeds',[]):
            url=feed.get('urls',{}).get('realtime_vehicle_positions')
            if not url:continue
            results.append({'id':feed.get('id'),'vehiclePositions':url,'license':feed.get('license',{}),'authorization':feed.get('authorization',{}),
                'catalogFile':name,'operators':[o.get('name') for o in data.get('operators',[])],
                'status':'Candidate only: verify provider terms, freshness, changing coordinates, bounds and update cadence before integration.'})
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query',help='Match provider/domain in catalog filenames')
    parser.add_argument('--limit',type=int,default=10)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result={'catalog':'Transitland Atlas','candidates':discover(args.query,max(1,min(20,args.limit)))}
    text=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.write_text(text,encoding='utf-8')
    else:print(text)
