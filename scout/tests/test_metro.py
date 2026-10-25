import sys,time,unittest,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import metro
class MetroTests(unittest.TestCase):
 def message(self,t=1000):
  return {'id':'123','vehicle':{'timestamp':str(t),'position':{'latitude':34.05,'longitude':-118.25,'bearing':90}},'route_code':'4'}
 def test_fresh_stream_observation_and_public_route_label(self):
  i=metro.parse(self.message(),'LACMTA',now=1001)
  self.assertEqual(i['time'],1000000);self.assertEqual(i['routeLabel'],'4');self.assertEqual(i['heading'],90)
 def test_missing_old_future_nonfinite_times_and_bad_coordinates_rejected(self):
  for t in [None,'nan',500,1200,True]:
   d=self.message();d['vehicle']['timestamp']=t
   self.assertIsNone(metro.parse(d,'LACMTA',now=1001))
  d=self.message();d['vehicle']['position']['latitude']=0
  self.assertIsNone(metro.parse(d,'LACMTA',now=1001))
 def test_unknown_agency_rejected(self):
  with self.assertRaises(ValueError):metro.snapshot('unreviewed')
 def test_out_of_order_reports_do_not_replace_newer_positions(self):
  state={'lock':threading.Lock(),'items':{}}
  with patch.dict(metro.STATES,{'LACMTA':state}),patch.object(metro.time,'time',return_value=1000):
   metro.receive('LACMTA',{'id':'x','time':999000,'lat':34})
   metro.receive('LACMTA',{'id':'x','time':998000,'lat':33})
   self.assertEqual(state['items']['x']['lat'],34)
 def test_viewers_share_one_live_thread_and_expired_positions_are_hidden(self):
  class FakeThread:
   created=0
   def __init__(self,**kw):FakeThread.created+=1
   def start(self):pass
   def is_alive(self):return True
  state={'lock':threading.Lock(),'thread':None,'items':{'old':{'id':'old','time':0}},'connected':False,'demand':0}
  with patch.dict(metro.STATES,{'LACMTA':state}),patch.object(metro.threading,'Thread',FakeThread):
   self.assertEqual(metro.snapshot('LACMTA')['items'],[])
   metro.snapshot('LACMTA');self.assertEqual(FakeThread.created,1)
 def test_idle_stream_demand_expires(self):
  state={'lock':threading.Lock(),'demand':0}
  with patch.object(metro.time,'monotonic',return_value=121):self.assertFalse(metro.wanted(state))
