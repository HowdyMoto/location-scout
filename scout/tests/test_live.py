import sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server,ships

class LiveTests(unittest.TestCase):
 def tearDown(self):server.HISTORY.clear()
 def test_history_preserves_observation_time_and_deduplicates(self):
  now=time.time()*1000
  a={'id':'plane','lat':47.6,'lon':-122.3,'time':now-60000}
  server.remember_positions('test',[a]);server.remember_positions('test',[a])
  d=server.remember_positions('test',[{**a,'lat':47.61,'time':now-30000}])
  self.assertEqual(len(d['plane']),2);self.assertEqual(d['plane'][0]['time'],a['time'])
 def test_history_expires_and_rejects_future_data(self):
  now=time.time()*1000
  a={'id':'old','lat':47.6,'lon':-122.3,'time':now-400000}
  self.assertEqual(server.remember_positions('test',[a,{**a,'id':'future','time':now+120000}]),{})
 def test_ais_coordinates_and_sentinel_heading(self):
  data={'MessageType':'PositionReport','MetaData':{'MMSI':123456789,'ShipName':' TEST '},'Message':{'PositionReport':{'Latitude':47.6,'Longitude':-122.3,'TrueHeading':511,'Cog':92,'Sog':102.3}}}
  region,item=ships.parse_message(data,received=1000000)
  self.assertEqual(region,'seattle');self.assertEqual(item['heading'],92);self.assertEqual(item['time'],1000000)
  self.assertEqual(item['timestampKind'],'local reception');self.assertIn('speed unavailable',item['description'])
  data['Message']['PositionReport']['Latitude']=91
  self.assertIsNone(ships.parse_message(data))
 def test_ais_configuration_does_not_start_network(self):
  with patch.dict('os.environ',{},clear=True):
   self.assertTrue(ships.snapshot('seattle')['configurationRequired'])
   self.assertIsNone(ships.THREAD)

if __name__=='__main__':unittest.main()
