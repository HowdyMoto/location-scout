import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import feeds
class BuoyTests(unittest.TestCase):
 def test_missing_wave_value_and_utc_timestamp(self):
  d=feeds.parse_buoys('46026 37.750 -122.838 2026 10 24 19 00 240 2.0 2.0 MM MM MM MM 1017.5 +0.0 MM 17.4 MM MM MM')
  self.assertEqual(len(d['items']),1)
  self.assertIn('wave height unavailable',d['items'][0]['description'])
  self.assertIn('temperature 17.4',d['items'][0]['description'])
  self.assertEqual(d['items'][0]['time'],feeds.stamp('2026-10-24T19:00:00Z'))
if __name__=='__main__':unittest.main()
