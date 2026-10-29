import io
import json
import sys
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import streamfeeds as s
import fields
import routes
import satellites
import transit
import ships


class ExpansionTests(unittest.TestCase):
    def test_stream_packet_fragmentation_and_large_lengths(self):
        raw=s.packet(0x30,b'x'*300)
        messages,left=s.packets(raw[:20]);self.assertEqual(messages,[])
        messages,left=s.packets(left+raw[20:]);self.assertEqual(messages,[(0x30,b'x'*300)]);self.assertEqual(left,b'')

    def test_train_and_balloon_reject_old_invalid_observations(self):
        row={'trainNumber':3,'departureDate':'2026-10-28','timestamp':time.time(),'location':{'coordinates':[24,61]}}
        self.assertIsNotNone(s.train(row));self.assertIsNone(s.train({**row,'timestamp':time.time()-400}))
        balloon={'serial':'x','datetime':time.time(),'lat':10,'lon':20,'alt':30000}
        self.assertIsNotNone(s.balloon(balloon));self.assertIsNone(s.balloon({**balloon,'alt':float('nan')}))
        self.assertIsNone(s.balloon({**balloon,'datetime':time.time()+120}))

    def test_stream_retains_intermediate_positions_and_rejects_reordering(self):
        collector=s.Stream('test','wss://example.test','batch',s.balloon)
        row={'serial':'x','datetime':time.time()-60,'lat':10,'lon':20,'alt':30000}
        collector.accept([{**row,'datetime':row['datetime']+n,'lat':10+n*.0001} for n in range(60)])
        collector.accept(row)
        self.assertEqual(len(collector.history['x']),60);self.assertGreater(collector.items['x']['lat'],10)

    def test_credential_layers_do_not_call_network_without_keys(self):
        with patch.dict('os.environ',{},clear=True),patch('fields.f.fetch') as fetch:
            self.assertTrue(fields.traffic((-123,37,-122,38))['configurationRequired'])
            self.assertTrue(transit.load({'endpoint':'https://example.test','keyEnv':'SF511_API_KEY'})['configurationRequired'])
            self.assertTrue(ships.snapshot_view((-10,35,0,45))['configurationRequired']);fetch.assert_not_called()

    def test_wind_direction_is_to_not_from_and_null_is_rejected(self):
        rows=[{'current':{'wind_speed_10m':10,'wind_direction_10m':90,'time':time.time()}} for _ in range(36)]
        with patch('fields.f.fetch',return_value=rows):
            field=fields.wind((170,-10,-170,10))['field'];self.assertAlmostEqual(field['vectors'][0][0],-10)
            rows[0]['current']['wind_speed_10m']=None
            with self.assertRaises(ValueError):fields.wind((170,-10,-170,10))

    def test_route_table_and_projection_reject_distant_points(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            z.writestr('trips.txt','trip_id,shape_id\nt,s\n')
            z.writestr('shapes.txt','shape_id,shape_pt_sequence,shape_pt_lat,shape_pt_lon\ns,2,0.001,0\ns,1,0,0\ns,3,0.001,0.001\n')
        trips,shapes=routes.parse(b.getvalue());self.assertEqual(trips['t'],'s')
        self.assertAlmostEqual(routes.project({'lat':.001,'lon':0},shapes['s']),111.195,places=2)
        self.assertIsNone(routes.project({'lat':1,'lon':1},shapes['s']))

    def test_ais_global_parser_accepts_lisbon_and_rejects_invalid_coordinates(self):
        row={'MessageType':'PositionReport','MetaData':{'MMSI':123456789},'Message':{'PositionReport':{'Latitude':38.7,'Longitude':-9.1}}}
        self.assertIsNone(ships.parse_message(row));self.assertEqual(ships.parse_message(row,global_view=True)[0],'global')
        row['Message']['PositionReport']['Latitude']=91;self.assertIsNone(ships.parse_message(row,global_view=True))

    def test_ais_viewport_splits_date_line_and_filters_shared_records(self):
        class Running:
            def is_alive(self):return True
        now=time.time()*1000
        tracks={('global','a'):{'id':'a','lat':0,'lon':179,'time':now},('global','b'):{'id':'b','lat':0,'lon':0,'time':now}}
        with patch.dict('os.environ',{'AISSTREAM_API_KEY':'fixture'}),patch.object(ships,'THREAD',Running()),patch.object(ships,'TRACKS',tracks),patch.object(ships,'DEMANDS',{}):
            value=ships.snapshot_view((170,-5,-170,5));self.assertEqual([i['id'] for i in value['items']],['a']);self.assertEqual(len(ships.DEMANDS),2)
            self.assertTrue(ships.snapshot_view((-180,-80,180,80))['zoomRequired'])

    def test_cached_expired_orbits_are_not_republished_as_current(self):
        with patch.object(satellites,'EXPIRES',time.time()+100),patch.object(satellites,'ELEMENTS',[('old',(None,'old',(time.time()-15*86400)*1000))]):
            self.assertEqual(satellites.load()['items'],[])


if __name__=='__main__':unittest.main()
