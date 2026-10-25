#!/usr/bin/env python
"""Meaningful no-solver contract fixtures for EV93 layer-one author."""
import importlib.util, json, os, tempfile, unittest
from pathlib import Path
import numpy as np

SOURCE=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/fairing-layer1/author.py')

def load_author():
 spec=importlib.util.spec_from_file_location('ev93_layer1_author_fixture',SOURCE)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

class AuthorContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.a=load_author();cls.a.require_pins();cls.mods=cls.a.runtime_modules();cls.base=cls.a.load_npz(cls.a.BASE)
 def test_window17_coordinate_order_is_normalized_and_checked(self):
  self.assertEqual(self.a.normalize_window17([10,20,27,37]),(10,27,20,37))
  with self.assertRaises(ValueError):self.a.normalize_window17([10,20,26,37])
 def test_actual_q0000_reconstructs_frozen_preflight(self):
  path=self.a.G/'preflight/window-details/q0000.json'
  detail=json.loads(path.read_text(encoding='utf-8'));pre=detail['preflight']
  e={'queue_id':0,'seed_id':0,'center_rc':detail['center_rc'],'window_rc':pre['window'],'core_rc':pre['core'],'detail_path':str(path)}
  local=self.a.reconstruct(e,{},self.base,self.mods)
  self.assertEqual(len(local['nodes']),len(pre['domain']['eligible_after_face_freeze_nodes']))
  self.assertEqual(len(local['stencils']),pre['guard_d8']['stencil_count'])
  self.assertEqual(len(local['guard']),pre['guard_d8']['guard_count'])
  self.assertEqual(list(local['C'].shape),pre['guard_d8']['descent_matrix_shape'])
  self.assertEqual(self.a._d8_sha(local['C'],local['d']),(
   pre['guard_d8']['descent_matrix_sha256_f64'],pre['guard_d8']['descent_rhs_sha256_f64']))
  self.assertTrue(self.mods[1].witnesses_hold(self.base['heights'],local['witnesses']))
  geometry=self.a.local_physics(self.mods[4],self.base['heights'],self.base['heights'],local['window'],local['nodes'])
  self.assertEqual(geometry['slope_gate'],'PASS');self.assertEqual(geometry['hinge_gate'],'PASS')
 def test_partial_ledger_is_rejected_before_prepare(self):
  partial=self.a.G/'preflight/window-ledger.jsonl'
  _header,rows=self.a.parse_jsonl(partial)
  self.assertNotEqual(rows[-1].get('status'),'COMPLETE_READONLY_PREFLIGHT')
  with self.assertRaisesRegex(ValueError,'no complete terminal record'):
   self.a.validate_complete_ledger(partial,[])
 def test_complete_resumed_ledger_reconciles_all_703_rows_without_writes(self):
  manifest=self.a.prepared_manifest(self.a.G/'preflight-segment02/window-ledger.jsonl')
  states=[x['preflight_state'] for x in manifest['entries']]
  self.assertEqual(len(states),703)
  self.assertEqual(states.count('PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW'),651)
  self.assertEqual(states.count('PREFLIGHT_INFEASIBLE'),49)
  self.assertEqual(states.count('PREFLIGHT_INCONCLUSIVE'),3)
  self.assertEqual(manifest['preflight_ledger_sha256'],'63af108d80d7232d8b919c3940da64e76839d8f0d4c74d42ca8d569117913d3a')
 def test_final_cast_is_exactly_one_float64_interpolation_then_float32(self):
  b=np.asarray([[1.,-3.]],dtype=np.float32);h=np.asarray([[4.,2.]],dtype=np.float32);alpha=.375
  got=self.a.interpolate_float32(b,h,alpha)
  expected=np.asarray(b.astype(np.float64)+alpha*(h.astype(np.float64)-b.astype(np.float64)),dtype=np.float32)
  self.assertTrue(np.array_equal(got,expected))
  with self.assertRaises(ValueError):self.a.interpolate_float32(b.astype(np.float64),h,alpha)
 def test_exclusive_marker_blocks_duplicate_solve_attempt(self):
  with tempfile.TemporaryDirectory() as d:
   marker=Path(d)/'window.started.json';fd=self.a.lock_exclusive(marker);os.close(fd)
   with self.assertRaises(FileExistsError):self.a.lock_exclusive(marker)
 def test_real_result_and_started_marker_filename_parsers(self):
  self.assertEqual(self.a.result_qid('window-0000.json'),0)
  self.assertEqual(self.a.marker_qid('window-0702.started.json'),702)
  for parser,name in ((self.a.result_qid,'window-0000.started.json'),(self.a.marker_qid,'window-0000.json'),(self.a.marker_qid,'window-x000.started.json')):
   with self.assertRaises(ValueError):parser(name)
 def test_stencil_serialization_preserves_large_coordinates(self):
  stencils=[('xx',1234,2345),('xz',1000,999)]
  got=self.a.stencil_bytes(stencils).tobytes()
  self.assertEqual(json.loads(got.decode('utf-8')),[['xx',1234,2345],['xz',1000,999]])
 def test_postsolve_artifact_is_written_before_gate_classification(self):
  with tempfile.TemporaryDirectory() as d:
   marker=Path(d)/'window-0000.started.json';marker.write_text('{}')
   local={'nodes':[(1,1),(1,2)],'lo':np.asarray([0.,0.],dtype=np.float32),'hi':np.asarray([2.,2.],dtype=np.float32),'solverlo':np.asarray([0.,0.],dtype=np.float32),'solverhi':np.asarray([2.,2.],dtype=np.float32),'guard':[(1,2)],'stencils':[('xx',1234,2345)],'witnesses':[],'A':np.eye(2),'rhs':np.asarray([.3,.6]),'C':np.empty((0,2)),'d':np.empty((0,))}
   base={'heights':np.ones((4,4),dtype=np.float32)};result={'queue_id':0,'prepared_sha256':'a'*64}
   artifact=self.a.record_solver_direction(local,{'x':np.asarray([.5,.6]),'nit':3,'cost':1.25},base,result,marker)
   self.assertTrue(artifact.is_file());self.assertEqual(result['solution_sha256'],self.a.sha(artifact))
   self.assertEqual(result['solution_path'],str(artifact));self.assertIn('matrix_sha256_f64',result)
   with np.load(artifact,allow_pickle=False) as z:
    self.assertEqual(json.loads(z['stencils_json'].tobytes().decode('utf-8')),[['xx',1234,2345]])
    np.testing.assert_array_equal(z['solver_x_float64'],[.5,.6])
 def _resume_fixture(self,d,state,with_event=True,with_solution=True,with_delta=False):
  out=Path(d);(out/'results').mkdir(parents=True,exist_ok=True);(out/'attempts').mkdir(exist_ok=True);(out/'deltas').mkdir(exist_ok=True)
  prepared={'schema':'fixture','author_sha256':'f'*64,'entries':[{'queue_id':i,'preflight_state':('PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW' if i==0 else 'PREFLIGHT_INFEASIBLE')} for i in range(703)]}
  self.a.atomic_json(out/'prepared.json',prepared);prepared_sha=self.a.sha(out/'prepared.json')
  result={'queue_id':0,'seed_id':0,'center_rc':[10,10],'window_rc':[1,18,1,18],'core_rc':[3,16,3,16],'preflight_state':prepared['entries'][0]['preflight_state'],'solve_calls':0,'state':state,'reason':None,'prepared_sha256':prepared_sha}
  if with_solution:
   marker=out/'attempts'/'window-0000.started.json';self.a.atomic_json(marker,{'queue_id':0,'prepared_sha256':prepared_sha,'author_sha256':prepared['author_sha256']});result['solve_calls']=1
   result.update({'attempt_marker_path':str(marker),'attempt_marker_sha256':self.a.sha(marker)})
   local={'nodes':[(1,1),(1,2)],'lo':np.asarray([0.,0.],dtype=np.float32),'hi':np.asarray([2.,2.],dtype=np.float32),'solverlo':np.asarray([0.,0.],dtype=np.float32),'solverhi':np.asarray([2.,2.],dtype=np.float32),'guard':[(1,2)],'stencils':[('xx',1234,2345)],'witnesses':[],'A':np.eye(2),'rhs':np.asarray([.3,.6]),'C':np.empty((0,2)),'d':np.empty((0,))}
   self.a.record_solver_direction(local,{'x':np.asarray([.5,.6]),'nit':3,'cost':1.25},{'heights':np.ones((4,4),dtype=np.float32)},result,marker)
  if with_delta:
   path=out/'deltas'/'window-0000.npz';nodes=np.asarray([[1,1],[1,2]],dtype=np.int32)
   self.a.atomic_npz(path,queue_id=np.asarray([0],dtype=np.int32),prepared_sha256=np.frombuffer(prepared_sha.encode('ascii'),dtype=np.uint8),variables_rc=nodes,B_values_float32=np.ones(2,dtype=np.float32),bounds_float32_inward=np.asarray([[0.,2.],[0.,2.]],dtype=np.float32),solver_bounds_float32=np.asarray([[0.,2.],[0.,2.]],dtype=np.float32),guard_rc=np.asarray([[1,2]],dtype=np.int32),direction_float32=np.asarray([.5,.6],dtype=np.float32),final_float32=np.asarray([.75,.8],dtype=np.float32),stencils_json=self.a.stencil_bytes([('xx',1234,2345)]),descent_witnesses_json=np.frombuffer(b'[]',dtype=np.uint8))
   result.update({'delta_path':str(path),'delta_sha256':self.a.sha(path)})
  rp=out/'results'/'window-0000.json';self.a.atomic_json(rp,result)
  if with_event:self.a.append_jsonl(out/'ledger.jsonl',{'event':'result','queue_id':0,'state':state,'result_path':str(rp),'result_sha256':self.a.sha(rp),'prepared_sha256':prepared_sha})
  return out,prepared,result
 def test_resume_requires_exact_result_event_and_file_pairing(self):
  with tempfile.TemporaryDirectory() as d:
   out,prepared,_=self._resume_fixture(d,'not_authored',with_solution=False,with_event=False)
   self.assertIsNone(self.a.resume_or_mark_incomplete(prepared,out))
   receipt=json.loads((out/'authoring.json').read_text(encoding='utf-8'))
   self.assertEqual(receipt['status'],'INCOMPLETE');self.assertIn('orphan result file',receipt['reason'])
  with tempfile.TemporaryDirectory() as d:
   out,prepared,_=self._resume_fixture(d,'not_authored',with_solution=False)
   ledger=out/'ledger.jsonl';events=self.a._jsonl_objects(ledger);events[0]['result_sha256']='0'*64
   self.a.atomic_json(out/'ledger.jsonl',events[0])
   with self.assertRaisesRegex(ValueError,'ledger/result identity or SHA'):
    self.a.validate_resume_state(prepared,out)
  with tempfile.TemporaryDirectory() as d:
   out,prepared,_=self._resume_fixture(d,'not_authored',with_solution=False,with_event=False)
   (out/'results'/'window-0000.json').unlink()
   self.a.atomic_json(out/'attempts'/'window-0000.started.json',{'queue_id':0,'prepared_sha256':self.a.sha(out/'prepared.json'),'author_sha256':prepared['author_sha256']})
   with self.assertRaisesRegex(ValueError,'orphan attempt marker'):
    self.a.validate_resume_state(prepared,out)
 def test_resume_validates_marker_solution_and_delta_artifacts(self):
  with tempfile.TemporaryDirectory() as d:
   out,prepared,_=self._resume_fixture(d,'rejected')
   self.assertEqual(set(self.a.validate_resume_state(prepared,out)[0]),{0})
   (out/'attempts'/'window-0000.solution.npz').unlink()
   with self.assertRaisesRegex(ValueError,'solution artifact missing'):
    self.a.validate_resume_state(prepared,out)
  with tempfile.TemporaryDirectory() as d:
   out,prepared,_=self._resume_fixture(d,'accepted',with_delta=True)
   self.assertEqual(set(self.a.validate_resume_state(prepared,out)[0]),{0})
   (out/'deltas'/'window-0000.npz').write_bytes(b'drift')
   with self.assertRaisesRegex(ValueError,'delta artifact missing/path/SHA mismatch'):
    self.a.validate_resume_state(prepared,out)
  with tempfile.TemporaryDirectory() as d:
   out,prepared,_=self._resume_fixture(d,'rejected',with_event=False)
   with self.assertRaisesRegex(ValueError,'orphan result file'):
    self.a.validate_resume_state(prepared,out)
 def test_terminal_receipt_or_terminal_final_event_blocks_all_reentry(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);receipt=out/'authoring.json';self.a.atomic_json(receipt,{'status':'AUTHORED_PENDING_GLOBAL_CONSUMER','candidate_sha256':'abc'})
   before=receipt.read_bytes()
   with self.assertRaisesRegex(RuntimeError,'terminal authoring receipt'):
    self.a.assert_not_terminal(out)
   self.assertEqual(receipt.read_bytes(),before)
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);self.a.append_jsonl(out/'ledger.jsonl',{'event':'final','status':'COMPLETE','candidate_sha256':'abc'})
   with self.assertRaisesRegex(RuntimeError,'terminal authoring ledger event'):
    self.a.assert_not_terminal(out)
 def test_occupied_execute_lock_prevents_recovery_writes(self):
  with tempfile.TemporaryDirectory() as d:
   out,prepared,_=self._resume_fixture(d,'not_authored',with_solution=False,with_event=False)
   lock=out/'execute.lock';fd=self.a.lock_exclusive(lock)
   result_path=out/'results'/'window-0000.json';result_sha=self.a.sha(result_path)
   try:
    with self.assertRaises(FileExistsError):self.a.lock_exclusive(lock)
    self.assertFalse((out/'authoring.json').exists())
    self.assertFalse(any(x.get('event')=='final' for x in self.a._jsonl_objects(out/'ledger.jsonl')))
    self.assertEqual(self.a.sha(result_path),result_sha)
   finally:
    os.close(fd);lock.unlink(missing_ok=True)
 def test_readset_and_detail_hashes_are_rechecked(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'input.bin';source.write_bytes(b'original')
   prepared={'preflight_header':{'read_set_sha256':{str(source):self.a.sha(source)}}}
   self.a.verify_header_read_set(prepared)
   entry={'queue_id':7,'detail_path':str(source),'detail_sha256':self.a.sha(source)}
   self.a.verify_detail_pin(entry)
   source.write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'read-set drift'):
    self.a.verify_header_read_set(prepared)
   with self.assertRaisesRegex(ValueError,'detail drift q7'):
    self.a.verify_detail_pin(entry)
 def test_spawn_solver_uses_importable_pinned_ev91_module(self):
  ev91=self.mods[1]
  self.assertEqual(Path(ev91.__file__).resolve(),self.a.EV91.resolve())
  solved=ev91.solve_once(np.eye(2),np.asarray([.1,.2]),np.asarray([-1.,-1.]),np.asarray([1.,1.]),np.eye(2),np.asarray([.4,.6]),np.asarray([0.,0.]))
  np.testing.assert_allclose(solved['x'],[.4,.6],atol=1e-6)
  self.assertEqual(solved['scipy_version'],'1.18.1')
 def _delta(self,d,node,value,queue_id=0):
  p=Path(d)/f'delta-{queue_id}.npz';rc=np.asarray([node],dtype=np.int32)
  np.savez_compressed(p,variables_rc=rc,B_values_float32=np.asarray([1.],dtype=np.float32),bounds_float32_inward=np.asarray([[0.,2.]],dtype=np.float32),solver_bounds_float32=np.asarray([[0.,2.]],dtype=np.float32),guard_rc=np.empty((0,2),dtype=np.int32),direction_float32=np.asarray([value],dtype=np.float32),final_float32=np.asarray([value],dtype=np.float32))
  return {'state':'accepted','queue_id':queue_id,'delta_path':str(p),'delta_sha256':self.a.sha(p)}
 def test_composition_preserves_single_owner_and_rejects_overlap(self):
  base={'heights':np.ones((4,4),dtype=np.float32),'plane':np.arange(16,dtype=np.float32).reshape(4,4)}
  with tempfile.TemporaryDirectory() as d:
   x=self._delta(d,(1,1),.75,0);y=self._delta(d,(2,2),.5,1)
   h,owners=self.a.compose_candidate(base,[x,y])
   self.assertEqual(owners,{(1,1):0,(2,2):1});self.assertEqual(h[1,1],.75);self.assertEqual(h[2,2],.5)
   self.assertEqual(base['plane'][1,1],5.)
   dup=self._delta(d,(1,1),.25,2)
   with self.assertRaisesRegex(ValueError,'overlapping ownership'):
    self.a.compose_candidate(base,[x,dup])

if __name__=='__main__':unittest.main(verbosity=2)
