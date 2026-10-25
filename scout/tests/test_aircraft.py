import sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import feeds,world
class AircraftTests(unittest.TestCase):
 def test_adsb_fi_url_attribution_and_observation_time(self):
  now=time.time()*1000
  data={'now':now,'ac':[{'hex':'test','lat':1.3,'lon':103.8,'seen_pos':2,'track':90}]}
  with patch.object(feeds,'fetch',return_value=data) as fetch:
   r=feeds.aircraft(world.GLOBE,'1.3/103.8/80',provider='adsb.fi')
  self.assertEqual(fetch.call_args.args[0],'https://opendata.adsb.fi/api/v3/lat/1.3/lon/103.8/dist/80')
  self.assertEqual(r['items'][0]['time'],int(now-2000))
  self.assertIn('adsb.fi',r['items'][0]['summary']);self.assertIn('noncommercial',r['note'])
 def test_stale_feed_or_missing_clock_rejected(self):
  for now in [None,float('nan'),time.time()*1000-181000]:
   with patch.object(feeds,'fetch',return_value={'now':now,'ac':[]}):
    with self.assertRaises(ValueError):feeds.aircraft(provider='adsb.fi')
 def test_missing_negative_or_nonfinite_position_age_omitted(self):
  data={'now':time.time()*1000,'ac':[{'hex':str(i),'lat':1.3,'lon':103.8,'seen_pos':age} for i,age in enumerate([None,-1,float('nan'),121])]}
  with patch.object(feeds,'fetch',return_value=data):self.assertEqual(feeds.aircraft(world.GLOBE,provider='adsb.fi')['items'],[])
 def test_air_queries_are_paced_across_viewports(self):
  with patch.object(world,'LAST_AIR_REQUEST',100),patch.object(world.time,'monotonic',return_value=100.4),patch.object(world.time,'sleep') as sleep,patch.object(world.f,'aircraft',return_value={'items':[]}):
   world.fetch_view('air',(-.2,51.4,0,51.6))
   self.assertAlmostEqual(sleep.call_args.args[0],.7)
