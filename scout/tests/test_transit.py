import sys, unittest, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from google.transit import gtfs_realtime_pb2 as pb
import transit
import gzip, io
from unittest.mock import patch
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


 def test_load_accepts_gzip_and_plain_protobuf(self):
  m=pb.FeedMessage();m.header.gtfs_realtime_version='2.0'
  raw=m.SerializeToString()
  source={'source':'test','bounds':[-180,-90,180,90],'endpoint':'https://example.test/vehicles'}
  for compressed in [False,True]:
   response=io.BytesIO(gzip.compress(raw) if compressed else raw)
   response.headers={'Content-Encoding':'gzip'} if compressed else {}
   with patch('transit.urllib.request.urlopen',return_value=response) as fetch:
    self.assertEqual(transit.load(source)['items'],[])
    self.assertEqual(fetch.call_args.args[0].get_header('Accept-encoding'),'gzip')
 def test_gzip_expansion_is_bounded(self):
  response=io.BytesIO(gzip.compress(b'x'*10_000_001));response.headers={'Content-Encoding':'gzip'}
  with patch('transit.urllib.request.urlopen',return_value=response):
   with self.assertRaisesRegex(ValueError,'Decoded vehicle feed exceeds'):
    transit.load({'endpoint':'https://example.test/vehicles'})
