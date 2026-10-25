import sys,time,unittest,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import finnish_ships as ships
class FinnishShipsTests(unittest.TestCase):
 def message(self):return {'time':1000,'lat':59.8,'lon':24.9,'heading':511,'cog':247,'sog':4.3}
 def test_location_timestamp_and_course_fallback(self):
  i=ships.parse('vessels-v2/273343170/location',self.message(),1001)
  self.assertEqual(i['time'],1000000);self.assertEqual(i['heading'],247);self.assertIn('4.3 knots',i['summary'])
 def test_bad_topic_old_future_missing_and_nonfinite_time_rejected(self):
  self.assertIsNone(ships.parse('vessels-v2/status',self.message(),1001))
  for t in [None,True,float('nan'),500,1200]:
   self.assertIsNone(ships.parse('vessels-v2/273343170/location',{**self.message(),'time':t},1001))
 def test_invalid_ais_sentinels_and_outside_coverage(self):
  i=ships.parse('vessels-v2/273343170/location',{**self.message(),'cog':360,'sog':102.3},1001)
  self.assertIsNone(i['heading']);self.assertNotIn('knots',i['summary'])
  self.assertIsNone(ships.parse('vessels-v2/273343170/location',{**self.message(),'lon':0},1001))
 def test_late_positions_cannot_replace_newer_report(self):
  state={'items':{},'names':{}}
  with patch.object(ships,'STATE',state),patch.object(ships.time,'time',return_value=1001):
   ships.accept('vessels-v2/273343170/location',self.message())
   ships.accept('vessels-v2/273343170/location',{**self.message(),'time':999,'lat':60})
   self.assertEqual(state['items']['273343170']['lat'],59.8)
 def test_metadata_names_join_without_fabricating_a_location(self):
  state={'items':{},'names':{}}
  with patch.object(ships,'STATE',state):
   ships.accept('vessels-v2/273343170/metadata',{'name':' TEST SHIP '})
   self.assertEqual(state['names']['273343170'],'TEST SHIP');self.assertEqual(state['items'],{})
 def test_snapshot_shares_connection_and_excludes_old_positions(self):
  class Thread:
   created=0
   def __init__(self,**kw):Thread.created+=1
   def start(self):pass
   def is_alive(self):return True
  state={'items':{'old':{'id':'old','time':0}},'names':{},'thread':None,'connected':False,'demand':0}
  with patch.object(ships,'STATE',state),patch.object(ships.threading,'Thread',Thread):
   self.assertEqual(ships.snapshot()['items'],[]);ships.snapshot();self.assertEqual(Thread.created,1)
