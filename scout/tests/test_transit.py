import sys, unittest, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from google.transit import gtfs_realtime_pb2 as pb
import transit
class TransitTests(unittest.TestCase):
 def test_only_fresh_valid_observations_within_coverage(self):
  m=pb.FeedMessage();m.header.gtfs_realtime_version='2.0';m.header.timestamp=int(time.time())
  for id,age,lat,lon in [('fresh',2,60.17,24.94),('old',301,60.17,24.94),('future',-120,60.17,24.94),('elsewhere',2,42,-71),('invalid',2,float('nan'),24),('zero',2,0,0)]:
   e=m.entity.add();e.id=id;v=e.vehicle;v.timestamp=int(time.time())-age;v.position.latitude=lat;v.position.longitude=lon
  e=m.entity.add();e.id='missing-time';e.vehicle.position.latitude=60.17;e.vehicle.position.longitude=24.94
  result=transit.parse(m.SerializeToString(),{'source':'HSL','bounds':[23,59,26,62]})
  self.assertEqual([i['id'] for i in result['items']],['fresh'])
  self.assertIsNone(result['items'][0]['heading'])
 def test_differential_feed_is_not_misrepresented_as_complete(self):
  m=pb.FeedMessage();m.header.gtfs_realtime_version='2.0';m.header.incrementality=pb.FeedHeader.DIFFERENTIAL
  with self.assertRaises(ValueError):transit.parse(m.SerializeToString(),{'source':'test','bounds':[-180,-90,180,90]})
 def test_empty_overnight_feed_is_valid(self):
  m=pb.FeedMessage();m.header.gtfs_realtime_version='2.0'
  self.assertEqual(transit.parse(m.SerializeToString(),{'source':'test','bounds':[-180,-90,180,90]})['items'],[])

