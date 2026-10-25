import sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import radar,world
class RadarTests(unittest.TestCase):
 def data(self):
  now=int(time.time())
  return {'host':'https://tilecache.rainviewer.com','radar':{'past':[{'time':now-600,'path':'/v2/radar/first'},{'time':now,'path':'/v2/radar/last'}],'nowcast':[{'time':now+600,'path':'/v2/radar/future'}]}}
 def test_only_past_frames_with_aligned_times_and_urls(self):
  r=radar.parse(self.data())['raster']
  self.assertEqual(len(r['frames']),2);self.assertEqual(len(r['frameUrls']),2)
  self.assertIn('/first/',r['frameUrls'][0]);self.assertIn('/last/',r['frameUrls'][1])
  self.assertEqual(r['time'],r['frames'][-1]);self.assertEqual(r['maxNativeZoom'],7)
 def test_unexpected_hosts_and_stale_manifests_rejected(self):
  d=self.data();d['host']='https://untrusted.invalid'
  with self.assertRaises(ValueError):radar.parse(d)
  d=self.data();d['radar']['past']=[{'time':time.time()-3600,'path':'/v2/radar/old'}]
  with self.assertRaises(ValueError):radar.parse(d)
 def test_paths_cannot_change_host_or_escape_radar_directory(self):
  d=self.data();d['radar']['past']=[{'time':time.time(),'path':'//untrusted.invalid/radar'}]
  with self.assertRaises(ValueError):radar.parse(d)
 def test_world_views_share_one_manifest(self):
  world.SHARED.pop('radar',None)
  try:
   with patch.object(radar,'load',return_value={'items':[],'raster':{}}) as load:
    world.fetch_view('radar',(0,50,1,51));world.fetch_view('radar',(103,1,104,2))
    self.assertEqual(load.call_count,1)
  finally:world.SHARED.pop('radar',None)
