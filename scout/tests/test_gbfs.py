import unittest,time,sys
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import gbfs
class GbfsTests(unittest.TestCase):
 def setUp(self):
  self.source={'source':'Test bikes','bounds':[130,30,150,40]}
  self.info={'data':{'stations':[{'station_id':1,'name':'Station','lat':35,'lon':139}]}}
 def report(self,**kw):
  return {'station_id':'1','last_reported':time.time(),'num_bikes_available':0,'num_docks_available':10,'is_renting':False,'is_returning':True,**kw}
 def parse(self,*rows):return gbfs.parse(self.info,{'data':{'stations':list(rows)}},self.source)['items']
 def test_v2_zero_counts_and_disabled_rentals_are_preserved(self):
  item=self.parse(self.report())[0]
  self.assertEqual(item['availability']['bikes'],0);self.assertIn('Rentals disabled',item['description'])
 def test_v3_localized_names_iso_time_and_vehicle_counts(self):
  self.info['data']['stations'][0]['name']=[{'language':'ja','text':'駅'},{'language':'en','text':'Station EN'}]
  item=self.parse(self.report(last_reported=datetime.now(timezone.utc).isoformat(),num_vehicles_available=4))[0]
  self.assertEqual(item['title'],'Station EN');self.assertEqual(item['availability']['bikes'],4)
 def test_old_missing_future_and_unmatched_reports_are_omitted(self):
  self.assertEqual(self.parse(self.report(last_reported=time.time()-901),self.report(last_reported=None),self.report(last_reported=time.time()+120),self.report(station_id='missing')),[])
 def test_invalid_counts_do_not_become_false_availability(self):
  item=self.parse(self.report(num_bikes_available=-1,num_docks_available=True))[0]
  self.assertIsNone(item['availability']['bikes']);self.assertIsNone(item['availability']['docks'])
 def test_geometry_outside_coverage_is_omitted(self):
  self.info['data']['stations'][0]['lon']=0
  self.assertEqual(self.parse(self.report()),[])
 def test_station_metadata_is_cached_while_status_refreshes(self):
  source={**self.source,'stationInformation':'info','stationStatus':'status'};gbfs.INFORMATION.clear()
  with patch.object(gbfs.f,'fetch',side_effect=[self.info,{'data':{'stations':[self.report()]}},{'data':{'stations':[self.report(num_bikes_available=3)]}}]) as fetch:
   self.assertEqual(gbfs.load(source)['items'][0]['availability']['bikes'],0)
   self.assertEqual(gbfs.load(source)['items'][0]['availability']['bikes'],3)
   self.assertEqual([c.args[0] for c in fetch.call_args_list],['info','status','status'])
  gbfs.INFORMATION.clear()
