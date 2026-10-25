import sys, time, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import orbit

class OrbitTests(unittest.TestCase):
 def data(self):
  return {'id':25544,'units':'kilometers','timestamp':time.time(),'latitude':20,'longitude':179.9,'altitude':420,'velocity':27000}
 def test_timestamped_model_not_gps(self):
  data=self.data();item=orbit.parse(data)['items'][0]
  self.assertEqual(item['time'],int(data['timestamp']*1000))
  self.assertIn('not live on-board GPS',item['description'])
  self.assertIn('420.0 km',item['description'])
 def test_invalid_time_identity_units_and_coordinates(self):
  for update in [{'timestamp':time.time()-121},{'timestamp':time.time()+61},{'timestamp':None},{'timestamp':True},{'timestamp':float('nan')},{'id':1},{'units':'miles'},{'latitude':91},{'longitude':float('nan')}]:
   with self.subTest(update=update),self.assertRaises(ValueError):orbit.parse({**self.data(),**update})
 def test_missing_optional_metadata_does_not_invent_values(self):
  data=self.data();data['altitude']=None;data['velocity']=float('nan')
  description=orbit.parse(data)['items'][0]['description']
  self.assertNotIn('Altitude:',description);self.assertNotIn('Orbital speed:',description)
