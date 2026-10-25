import sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import feeds,seattle

class SeattleTests(unittest.TestCase):
 def test_explicit_bounds_do_not_leak_between_regions(self):
  self.assertIsNotNone(seattle.point('x',47.6,-122.3,'Seattle'))
  self.assertIsNone(feeds.point('x',47.6,-122.3,'Seattle'))
  self.assertIsNone(seattle.point('x',37.8,-122.3,'Bay'))
  self.assertIsNotNone(feeds.point('x',37.8,-122.3,'Bay'))
 def test_string_timestamp_and_vehicle_not_header_time(self):
  now=int(time.time())
  def row(id,t,lat=47.6):return {'id':id,'vehicle':{'timestamp':t,'vehicle':{'id':id},'position':{'latitude':lat,'longitude':-122.3}}}
  data={'header':{'timestamp':now},'entity':[row('fresh',str(now)),row('old',now-301),row('missing',None),row('future',now+120),row('other-region',now,37.8)]}
  result=seattle.parse_transit(data,'Test')
  self.assertEqual([i['id'] for i in result['items']],['fresh'])
  self.assertEqual(result['items'][0]['time'],now*1000)
 def test_transit_public_route_label_is_metadata_not_inferred(self):
  row={'id':'bus','vehicle':{'timestamp':int(time.time()),'vehicle':{'id':'7100'},'position':{'latitude':47.6,'longitude':-122.3},'trip':{'route_id':'100001'}}}
  item=seattle.parse_transit({'entity':[row]},'Metro',{'100001':'1'})['items'][0]
  self.assertEqual(item['routeLabel'],'1')
  self.assertIn('Route 1',item['summary'])
  item=seattle.parse_transit({'entity':[row]},'Metro')['items'][0]
  self.assertIsNone(item['routeLabel']);self.assertIn('Route ID 100001',item['summary'])
 def test_ferry_provider_timestamp_and_expiration(self):
  now=int(time.time()*1000)
  def row(id,t):return {'VesselID':id,'VesselName':'Test ferry','Latitude':47.6,'Longitude':-122.3,'TimeStamp':f'/Date({t}-0700)/','Speed':12,'AtDock':False}
  with patch.dict('os.environ',{'WSDOT_API_KEY':'fixture-only'}),patch.object(feeds,'fetch',return_value=[row(1,now-2000),row(2,now-301000),row(3,now+120000)]):
   data=seattle.ferries()
  self.assertEqual([i['id'] for i in data['items']],['1'])
  self.assertEqual(data['items'][0]['time'],now-2000)
  self.assertNotIn('fixture-only',str(data))
 def test_ferries_need_configuration_without_network(self):
  with patch.dict('os.environ',{},clear=True),patch.object(feeds,'fetch',side_effect=AssertionError('No network expected')):
   self.assertTrue(seattle.ferries()['configurationRequired'])
 def test_shared_aircraft_adapter_respects_region(self):
  data={'now':time.time()*1000,'ac':[{'hex':'sea','lat':47.6,'lon':-122.3,'seen_pos':2},{'hex':'bay','lat':37.8,'lon':-122.3,'seen_pos':2}]}
  with patch.object(feeds,'fetch',return_value=data):
   self.assertEqual([i['id'] for i in seattle.ADAPTERS['sea-air']()['items']],['sea'])
   self.assertEqual([i['id'] for i in feeds.aircraft()['items']],['bay'])
 def test_seattle_warning_bounds(self):
  g={'type':'Polygon','coordinates':[[[-123,47],[-122,47],[-122,48],[-123,48],[-123,47]]]}
  self.assertEqual(len(feeds.geometry_items('x',g,'Warning','',None,bounds=seattle.BOUNDS)),1)
  self.assertEqual(feeds.geometry_items('x',g,'Warning','',None),[])

if __name__=='__main__':unittest.main()
