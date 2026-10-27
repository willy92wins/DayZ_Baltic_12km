from pathlib import Path
import importlib.util,json,struct,unittest,hashlib
R=Path(__file__).parent
spec=importlib.util.spec_from_file_location('cost',R/'census_kit7_nav_payload_cost.py');cost=importlib.util.module_from_spec(spec);spec.loader.exec_module(cost)

def fixture(coords=((1,0),(0,0))):
 records=[]
 for i,(x,z) in enumerate(coords):
  n=0 if i==0 else 1;v=0 if i==0 else 4
  h=bytearray(104);struct.pack_into('<15I',h,0,0x444e4156,12,x,z,0,0,n,v,0,0,0,0,0,0,0)
  body=h+bytes(v*12+n*32+16)
  records.append(struct.pack('<QII',(1<<48)|(i<<20),len(body),0)+body)
 header=bytearray(48);struct.pack_into('<5I',header,0,0x4d534554,9,2,2,1);struct.pack_into('<f',header,32,8);struct.pack_into('<I',header,40,2)
 return header+struct.pack('<2I',0,len(records[0]))+b''.join(records)

class Controls(unittest.TestCase):
 def test_unordered_coverage_and_accounting(self):
  data=fixture();r=cost.census(data)
  self.assertEqual((r['tiles'],r['zero_polygon_tiles'],r['one_polygon_tiles'],r['declared_vertices'],r['declared_polygons']),(2,1,1,4,1))
  self.assertEqual(r['accounting'],dict(global_header_and_offsets=56,tile_record_prefixes=32,tile_headers=208,declared_vertex_prefixes=48,declared_polygon_prefixes=32,remaining_payload=32))
  self.assertEqual(sum(r['accounting'].values()),408)
 def test_duplicate_coordinates(self):
  with self.assertRaises(AssertionError):cost.census(fixture(((0,0),(0,0))))
 def test_coordinate_out_of_bounds(self):
  with self.assertRaises(AssertionError):cost.census(fixture(((2,0),(0,0))))
 def test_offsets(self):
  d=fixture();struct.pack_into('<I',d,52,0)
  with self.assertRaises(AssertionError):cost.census(d)
 def test_truncated(self):
  with self.assertRaises((AssertionError,struct.error)):cost.census(fixture()[:-1])
 def test_tile_version(self):
  d=fixture();struct.pack_into('<I',d,56+16+4,13)
  with self.assertRaises(AssertionError):cost.census(d)
 def test_count(self):
  d=fixture();struct.pack_into('<I',d,40,3)
  with self.assertRaises(AssertionError):cost.census(d)
 def test_oversized_declared_prefix(self):
  d=fixture();struct.pack_into('<I',d,56+16+28,1000)
  with self.assertRaises(AssertionError):cost.census(d)
 def test_independent_archived_inspector_totals(self):
  rows=json.loads((R/'kit7-nav-payload-cost-20261027-v2/result.json').read_text())['artifacts']
  for r,(_,path,digest) in zip(rows,cost.ARTIFACTS):
   if r['label']=='chernarus_50m':old=json.loads((path.parent/'result.json').read_text());self.assertEqual(old['navmesh_sha256'],digest)
   else:old=json.loads((path.parent/'inspection.json').read_text());self.assertEqual(old['sha256'],digest);self.assertEqual(old['bytes'],r['bytes'])
   for k in ('tiles','declared_polygons','declared_vertices'):self.assertEqual(old[k],r[k])
   self.assertEqual(sum(r['accounting'].values()),r['bytes'])

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 out=dict(status='PASS_CENSUS_CONTROLS' if result.wasSuccessful() else 'FAIL_CENSUS_CONTROLS',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),source_sha256=hashlib.sha256((R/'census_kit7_nav_payload_cost.py').read_bytes()).hexdigest(),test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (R/'kit7-nav-payload-cost-20261027-v2/controls.json').write_text(json.dumps(out,indent=2)+'\n')
 raise SystemExit(not result.wasSuccessful())
