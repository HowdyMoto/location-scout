import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import feeds
import server

class FeedTests(unittest.TestCase):
    def test_pacific_dst_and_explicit_timezone(self):
        self.assertEqual(feeds.stamp('2026-07-01T12:00:00',True),feeds.stamp('2026-07-01T19:00:00Z'))
        self.assertEqual(feeds.stamp('2026-01-01T12:00:00',True),feeds.stamp('2026-01-01T20:00:00Z'))
        self.assertEqual(feeds.stamp('2026-07-01T12:00:00-07:00',True),feeds.stamp('2026-07-01T19:00:00Z'))
        self.assertIsNone(feeds.stamp('not a timestamp'))

    def test_missing_coordinates_are_not_mapped_to_zero(self):
        for lat,lon in [(None,None),('',''),(float('nan'),-122.4),(37.7,float('inf')),(47.6,-122.3)]:
            self.assertIsNone(feeds.point('x',lat,lon,'test'))
        self.assertIsNotNone(feeds.point('x','37.7','-122.4','test'))

    def test_fire_unit_deduplication(self):
        row={'call_number':'123','unit_id':'E1','case_location':{'coordinates':[-122.4,37.7]},'received_dttm':'2026-10-24T01:00:00'}
        with patch.object(feeds,'socrata',return_value=([row,{**row,'unit_id':'M1'}],False)):
            data=feeds.fire()
        self.assertEqual(len(data['items']),1)
        self.assertIn('2 responding units',data['items'][0]['description'])

    def test_redacted_police_location_omitted(self):
        with patch.object(feeds,'socrata',return_value=([{'cad_number':'secret'}],False)):
            data=feeds.police()
        self.assertEqual(data['items'],[])
        self.assertIn('1 location-redacted',data['note'])

    def test_old_aircraft_positions_dropped(self):
        d={'now':1790000000000,'ac':[{'hex':'old','lat':37.7,'lon':-122.4,'seen_pos':121},{'hex':'fresh','lat':37.8,'lon':-122.3,'seen_pos':2}]}
        with patch.object(feeds,'fetch',return_value=d), patch.object(feeds.time,'time',return_value=1790000000):data=feeds.aircraft()
        self.assertEqual([i['id'] for i in data['items']],['fresh'])
        self.assertEqual(data['items'][0]['time'],1790000000000-2000)

    def test_intersecting_warning_polygon(self):
        g={'type':'Polygon','coordinates':[[[-124,37],[-122,37],[-122,38],[-124,38],[-124,37]]]}
        self.assertEqual(len(feeds.geometry_items('x',g,'Warning','',None)),1)
        g={'type':'Point','coordinates':[-70,40]}
        self.assertEqual(feeds.geometry_items('x',g,'Warning','',None),[])

    def test_cache_does_not_refetch_and_preserves_age_on_failure(self):
        key='quake';server.CACHE.clear()
        item=feeds.point('x',37.7,-122.4,'Quake',observed=123)
        with patch.dict(server.ADAPTERS,{key:lambda:feeds.result([item],raster={'time':'2026-10-24T19:00:00Z'})}):
            a=server.load_source(key)
            with patch.dict(server.ADAPTERS,{key:lambda:(_ for _ in ()).throw(Exception('not called'))}):
                self.assertIs(server.load_source(key),a)
                server.CACHE[key]['retryAt']=0
                b=server.load_source(key)
        self.assertEqual(b['status'],'stale')
        self.assertEqual(b['fetchedAt'],a['fetchedAt'])
        self.assertEqual(b['raster'],a['raster'])
        self.assertEqual(b['items'][0]['time'],123)
        self.assertNotIn('not called',b['error'])
        server.CACHE.clear()

    def test_initial_failure_not_empty_success(self):
        server.CACHE.clear()
        with patch.dict(server.ADAPTERS,{'quake':lambda:(_ for _ in ()).throw(Exception('failed'))}):d=server.load_source('quake')
        self.assertEqual(d['status'],'unavailable')
        self.assertIsNone(d['fetchedAt'])
        server.CACHE.clear()

    def test_catalog_matches_adapters(self):
        self.assertEqual(set(server.SOURCES),set(feeds.ADAPTERS))

if __name__=='__main__':unittest.main()
