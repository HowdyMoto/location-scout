import sys, time, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import events, world

class EventTests(unittest.TestCase):
 def event(self, identifier='EONET_test'):
  return {'id':identifier,'title':'Storm test','closed':None,'categories':[{'title':'Severe Storms'}], 'geometry':[{'date':time.time()-10,'type':'Point','coordinates':[179,10]}]}
 def test_latest_report_wins_without_fabricating_time(self):
  e=self.event();e['geometry'].append({'date':time.time()-100,'type':'Point','coordinates':[0,0]})
  item=events.parse({'events':[e]})['items'][0]
  self.assertEqual(item['lon'],179);self.assertEqual(item['time'],int(e['geometry'][0]['date']*1000))
  self.assertIn('not live tracking',item['description']);self.assertTrue(item['eventUrl'].endswith('/EONET_test'))
 def test_old_future_closed_invalid_and_polygon_are_not_misrepresented(self):
  for update in [{'date':time.time()-31*86400},{'date':time.time()+120},{'date':None},{'coordinates':[181,0]},{'type':'Polygon','coordinates':[[[1,2],[3,4]]]}]:
   e=self.event();e['geometry'][0].update(update)
   with self.subTest(update=update):
    result=events.parse({'events':[e]});self.assertEqual(result['items'],[]);self.assertTrue(result['partial'])
  e=self.event();e['closed']='2026-01-01';self.assertEqual(events.parse({'events':[e]})['items'],[])
 def test_new_polygon_does_not_reuse_an_old_point(self):
  e=self.event();e['geometry'].append({'date':time.time(),'type':'Polygon','coordinates':[]})
  self.assertEqual(events.parse({'events':[e]})['items'],[])
 def test_shared_fetch_and_dateline_view_filter(self):
  world.SHARED.pop('events',None)
  rows=events.parse({'events':[self.event()]})
  with patch.object(events,'load',return_value=rows) as load:
   self.assertEqual(len(world.fetch_view('events',(170,0,-170,20))['items']),1)
   self.assertEqual(world.fetch_view('events',(-10,0,10,20))['items'],[])
   self.assertEqual(load.call_count,1)
  world.SHARED.pop('events',None)
