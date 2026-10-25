import sys,unittest,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import world
class WorldTests(unittest.TestCase):
 def tearDown(self):
  for c in world.CACHE.values():c.clear()
  world.SHARED.clear();world.TRACKS.clear()
  for k in world.COOLDOWN:world.COOLDOWN[k]=0
 def test_validation(self):
  for b in ['', '1,2,3','nan,0,1,2','-181,0,1,2','0,5,2,4','0,0,0,2','0,-90,1,90']:
   with self.assertRaises(ValueError):world.parse_bounds(b)
  self.assertEqual(world.parse_bounds('170,-10,-170,10'),(170,-10,-170,10))
 def test_dateline(self):
  b=(170,-10,-170,10)
  self.assertTrue(world.contains(b,0,-179));self.assertTrue(world.contains(b,0,179));self.assertFalse(world.contains(b,0,0))
  self.assertEqual(world.center(b),(0,-180))
 def test_cache_is_scoped_to_view_and_bounded(self):
  with patch.object(world,'fetch_view',return_value={'items':[]} ) as fn:
   a=(0,0,1,1);b=(2,0,3,1)
   world.load('weather',a);world.load('weather',a);world.load('weather',b)
   self.assertEqual(fn.call_count,2)
   for n in range(30):world.load('weather',(n,0,n+1,1))
   self.assertEqual(len(world.CACHE['weather']),24)
 def test_failure_does_not_return_another_places_data(self):
  with patch.object(world,'fetch_view',return_value={'items':[{'id':'London'}]}):world.load('air',(0,50,1,51))
  with patch.object(world,'fetch_view',side_effect=ValueError('private URL')):d=world.load('air',(139,35,140,36))
  self.assertEqual(d['items'],[]);self.assertEqual(d['status'],'unavailable');self.assertNotIn('private',d['error'])
 def test_broad_air_view_requests_zoom_not_false_empty_success(self):
  with patch.object(world.f,'aircraft',side_effect=AssertionError('Do not fetch')):self.assertTrue(world.fetch_view('air',(-180,-85,180,85))['zoomRequired'])
 def test_shared_earthquakes_filtered_without_duplicate_upstream_fetches(self):
  rows={'items':[{'lat':51.5,'lon':0,'id':'London'},{'lat':35.7,'lon':139.7,'id':'Tokyo'}]}
  with patch.object(world.f,'quakes',return_value=rows) as fn:
   self.assertEqual(world.fetch_view('quake',(-1,50,1,52))['items'][0]['id'],'London')
   self.assertEqual(world.fetch_view('quake',(139,35,140,36))['items'][0]['id'],'Tokyo')
   self.assertEqual(fn.call_count,1)
 def test_rate_limit_backoff_is_shared_across_views(self):
  import urllib.error
  error=urllib.error.HTTPError('https://provider.invalid',429,'Limit',{'Retry-After':'120'},None)
  with patch.object(world,'fetch_view',side_effect=error) as fn:
   world.load('air',(0,50,1,51));second=world.load('air',(139,35,140,36))
   self.assertEqual(fn.call_count,1);self.assertGreater(second['retryAfter'],100)
 def test_model_samples_are_inside_wrapped_view(self):
  b=(175,-10,-175,10)
  points=world.samples(b);self.assertEqual(len(points),9)
  self.assertTrue(all(world.contains(b,lat,lon) for _,lat,lon in points))
if __name__=='__main__':unittest.main()
