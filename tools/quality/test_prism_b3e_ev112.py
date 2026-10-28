"""B3E fixtures: independent corners, complete census, control ordering and CLI."""
from pathlib import Path
import copy,json,subprocess,sys,tempfile,unittest
from unittest import mock
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prism_b3e_compiled_ev112 as g
import build_prism_b3e_ev112 as build
from test_prism_b3_binary_ev112 import pair_fixture,IDENTITY

def fixture():
    od,ml=pair_fixture();ml[1].faces=[f for s in ml[1].selections.values() for f in s.faces]
    return od,ml

class Census(unittest.TestCase):
    def setUp(self):self.od,self.ml=fixture();self.geo=self.od.lods[1]
    def check(self):return g.census(self.ml[1],self.geo,np.zeros(3),IDENTITY,np.zeros(3))[0]
    def sync(self):self.geo.vertex_raw=g.old.old.xyz(self.geo.vertices).astype('<f4').tobytes()
    def test_complete_positive(self):
        r=self.check();self.assertEqual(r['status'],'EXACT_CENSUS');self.assertEqual(r['compared_components'],2);self.assertFalse(r['global_errors'])
    def test_two_one_ulp_errors_are_both_reported(self):
        for i in (3,7):self.geo.vertices[i].y=float(np.nextafter(np.float32(self.geo.vertices[i].y),np.float32(np.inf)))
        self.sync();r=self.check();self.assertEqual(r['status'],'REJECTED_CENSUS');self.assertEqual(r['geometric_failures'],['component0001','component0002']);self.assertEqual(r['compared_components'],2)
        self.assertTrue(all(row['world_actual_only'] and row['local_actual_only'] for row in r['components']))
    def test_signed_zero_keys_and_local_raw(self):
        a=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,0.,1.]]],'<f4');b=a.copy();b[0,0,0]=-0.
        self.assertNotEqual(g.face_bits(a),g.face_bits(b))
        self.geo.vertices[0].x=-0.;self.sync();self.assertEqual(self.check()['status'],'REJECTED_CENSUS')
    def test_cyclic_permutation_allowed(self):
        f=self.geo.faces[0];f.vertex_indices=f.vertex_indices[1:]+f.vertex_indices[:1];self.assertEqual(self.check()['status'],'EXACT_CENSUS')
    def test_inverted_face_fails_and_full_census_kept(self):
        self.geo.faces[0].vertex_indices.reverse();r=self.check();self.assertEqual(r['geometric_failures'],['component0001']);self.assertEqual(r['compared_components'],2)
    def test_missing_face_is_inconclusive(self):
        self.geo.faces.pop();r=self.check();self.assertEqual(r['status'],'INCONCLUSIVE_CENSUS');self.assertEqual(r['visited_components'],2)
    def test_duplicate_face_and_component_members(self):
        self.geo.named_selections[0].selected_faces[-1]=0;r=self.check();self.assertEqual(r['status'],'INCONCLUSIVE_CENSUS');self.assertIn('coverage_compiled_faces',r['global_errors'])
    def test_duplicate_name_not_silently_collapsed(self):
        self.geo.named_selections[1].name='component0001';r=self.check();self.assertEqual(r['status'],'INCONCLUSIVE_CENSUS');self.assertIn('duplicate_component_name',r['global_errors'])
    def test_missing_source_component(self):
        del self.ml[1].selections['Component0002'];r=self.check();self.assertEqual(r['status'],'INCONCLUSIVE_CENSUS');self.assertEqual(r['visited_components'],2)
    def test_face_outside_component(self):
        self.geo.faces[0].vertex_indices[0]=8;r=self.check();self.assertEqual(r['status'],'INCONCLUSIVE_CENSUS')
    def test_raw_decode_bits_fail_closed(self):
        self.geo.vertices[0].x=-0.
        with self.assertRaisesRegex(g.Inconclusive,'raw_decode_bits'):self.check()
    def test_nan_is_inconclusive(self):
        self.geo.vertices[0].y=float('nan');self.sync()
        with self.assertRaises(g.Inconclusive):self.check()
    def test_truncated_raw_is_inconclusive(self):
        self.geo.vertex_raw=self.geo.vertex_raw[:-1]
        with self.assertRaisesRegex(g.Inconclusive,'raw_coordinate_length'):self.check()
    def test_rejection_retains_complete_rows(self):
        self.geo.faces[0].vertex_indices.reverse();r=self.check()
        with self.assertRaises(ValueError) as e:g.require_census(r)
        self.assertEqual(len(e.exception.details['components']),2)
        with self.assertRaises(g.Inconclusive):g.require_census(r,control=True)

class ControlAndContacts(unittest.TestCase):
    def setUp(self):
        self.od,self.ml=fixture();self.patch=mock.patch.object(g.old,'EXPECTED_COUNTS',(12,16,2));self.patch.start();self.addCleanup(self.patch.stop)
    def control(self,od=None):
        rows=[];r=g.gate_control(self.od,self.od if od is None else od,self.ml,IDENTITY,[0,0,0],[dict(id=700,x=.25,z=.25)],rows.append);return r,rows
    def test_control_without_any_candidate(self):
        r,rows=self.control();self.assertEqual(r['status'],'CONTROL_B3E_CERTIFIED');self.assertEqual(rows[0]['compared_components'],2)
    def test_changed_control_centre_is_inconclusive(self):
        c=copy.deepcopy(self.od);c.model_info.bounding_center.y=.01
        with self.assertRaises(g.Inconclusive):self.control(c)
    def test_control_wrong_winding_stops_candidate_creation(self):
        self.od.lods[1].faces[0].vertex_indices.reverse()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);actions=[]
            def candidate():actions.append('candidate');(root/'candidate').mkdir()
            with self.assertRaises(g.Inconclusive):build.sequence(lambda:actions.append('control'),self.control,candidate,lambda:actions.append('final'))
            self.assertEqual(actions,['control']);self.assertFalse((root/'candidate').exists())
    def test_sequence_after_green_control(self):
        actions=[];build.sequence(*[lambda i=i:actions.append(i) for i in range(4)]);self.assertEqual(actions,[0,1,2,3])
    def contact(self,x=.25,z=.25,margin=.25,name='Component0001'):
        world=g.old.old.xyz(self.od.lods[1].vertices).astype('<f4')
        return g.contact_witness(self.od.lods[1],world,[dict(id=700,x=x,z=z)],self.ml[1].selections,dict(contacts=[dict(id=700,world_float32_margin_m=margin,witness_component=name)]),['Component0001'])
    def test_contact_preserves_margin_and_names_face(self):
        r=self.contact()[0];self.assertEqual(r['margin_m'],.25);self.assertEqual(r['witness_component'],'Component0001');self.assertIsInstance(r['compiled_face_index'],int)
    def test_contact_on_boundary_rejected(self):
        with self.assertRaisesRegex(ValueError,'compiled_contact_boundary'):self.contact(1,1)
    def test_one_double_ulp_margin_or_component_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'contact_proof_changed'):self.contact(margin=np.nextafter(.25,1.))
        with self.assertRaisesRegex(ValueError,'contact_proof_changed'):self.contact(name='Component0002')
    def test_reordered_faces_do_not_change_contact(self):
        geo=self.od.lods[1];geo.faces=list(reversed(geo.faces))
        for s in geo.named_selections:s.selected_faces=[len(geo.faces)-1-i for i in s.selected_faces]
        self.assertEqual(self.contact()[0]['margin_m'],.25)

class BindingsAndCLI(unittest.TestCase):
    def test_reader_valueerror_is_not_a_geometric_rejection(self):
        with mock.patch.object(g.old,'read_pbo',side_effect=ValueError('compressed entry unsupported')):
            with self.assertRaises(g.Inconclusive) as e:g.payload(Path('unused'),'control',{})
            self.assertIn('ValueError',str(e.exception))
    def make(self,root):
        def put(name,v):p=root/name;p.write_text(json.dumps(v),encoding='utf-8');return str(p)
        source=root/'source';source.write_bytes(b'source');candidate=root/'candidate';candidate.write_bytes(b'candidate');baseline=root/'baseline';baseline.write_bytes(b'baseline');pbo=root/'pbo';pbo.write_bytes(b'pbo');original=root/'original';original.write_bytes(b'{}');poses=root/'poses.npz';np.savez(poses,ids=np.array([19394363]),matrix=np.array([IDENTITY]))
        inherited={str(p):g.meter.sha(p) for p in (source,baseline,pbo,original,poses)}
        d=dict(reference=str(source),original_result=str(original),origin=[0,0,0],matrix=IDENTITY,centre=[0,0,0],targets=[dict(id=700,x=.25,z=.25)],selected_components=['Component0001'],pins=inherited)
        dp=put('d.json',d);prior=dict(baseline_odol=str(baseline),baseline_pbo=str(pbo),poses=str(poses),pins=inherited);pp=put('prior.json',prior)
        proof=dict(status='OFFLINE_CANDIDATE_ONLY',candidate_sha256=g.meter.sha(candidate),contract_sha256=g.meter.sha(dp),exact_mlod_pairs=4560);fp=put('proof.json',proof)
        pins={**inherited,**{p:g.meter.sha(p) for p in (dp,pp,fp,str(candidate))}}
        c=dict(schema='B3E_COMPILED_V1',offline_contract=dp,offline_proof=fp,prior_contract=pp,source_control=str(source),candidate_mlod=str(candidate),baseline_odol=str(baseline),baseline_pbo=str(pbo),poses=str(poses),original_result=str(original),pins=pins)
        for k in ('origin','matrix','centre','targets','selected_components'):c[k]=d[k]
        path=Path(put('contract.json',c));return c,path,dict(CANDIDATE=pins[str(candidate)],OFFLINE=pins[dp],PROOF=pins[fp],PRIOR=pins[pp])
    def test_saved_contract_context_and_wrong_target(self):
        with tempfile.TemporaryDirectory() as td:
            c,p,anchors=self.make(Path(td))
            with mock.patch.multiple(g,**anchors),mock.patch.object(g.old,'original_controls'):
                self.assertEqual(g.context(p)[0]['schema'],'B3E_COMPILED_V1')
                c['targets']=[];p.write_text(json.dumps(c))
                with self.assertRaisesRegex(g.Inconclusive,'context:targets'):g.context(p)
    def test_transitive_pin_changed(self):
        with tempfile.TemporaryDirectory() as td:
            c,p,anchors=self.make(Path(td));Path(c['source_control']).write_bytes(b'changed');c['pins'][c['source_control']]=g.meter.sha(c['source_control']);p.write_text(json.dumps(c))
            with mock.patch.multiple(g,**anchors),self.assertRaisesRegex(g.Inconclusive,'transitive_pins'):g.context(p)
    def test_no_default_for_missing_proof_field(self):
        with tempfile.TemporaryDirectory() as td:
            c,p,anchors=self.make(Path(td));q=Path(c['offline_proof']);v=json.loads(q.read_bytes());del v['exact_mlod_pairs'];q.write_text(json.dumps(v));c['pins'][str(q)]=g.meter.sha(q);anchors['PROOF']=g.meter.sha(q);p.write_text(json.dumps(c))
            with mock.patch.multiple(g,**anchors),self.assertRaises(KeyError):g.context(p)
    def test_cli_malformed_contract_is_inconclusive(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);contract=root/'bad.json';contract.write_text('{broken');out=root/'out'
            p=subprocess.run([sys.executable,'-I',str(Path(g.__file__)),'control',str(contract),str(root/'pair'),str(root/'reader'),str(out)],capture_output=True,timeout=15)
            r=json.loads((out/'report.json').read_bytes());self.assertEqual(p.returncode,2);self.assertEqual(r['status'],'INCONCLUSIVE_BINARY');self.assertIn('traceback',r)
    def test_output_reuse_refused_without_rewrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'out';out.mkdir();marker=out/'report.json';marker.write_bytes(b'original')
            p=subprocess.run([sys.executable,'-I',str(Path(g.__file__)),'control',str(root/'missing'),str(root/'pair'),str(root/'reader'),str(out)],capture_output=True,timeout=15)
            self.assertNotEqual(p.returncode,0);self.assertEqual(marker.read_bytes(),b'original')

class CandidateGate(unittest.TestCase):
    def setUp(self):
        self.base,self.ml=fixture();self.control=copy.deepcopy(self.base);self.candidate=copy.deepcopy(self.base)
        self.patch=mock.patch.multiple(g.old,EXPECTED_COUNTS=(12,16,2),EXPECTED_SELECTED_VERTICES=6);self.patch.start();self.addCleanup(self.patch.stop)
        self.c=dict(centre=[0,0,0],matrix=IDENTITY,origin=[0,0,0],targets=[dict(id=700,x=.25,z=.25)],selected_components=['Component0001'])
        self.proof=dict(contacts=[dict(id=700,world_float32_margin_m=.25,witness_component='Component0001')]);self.censuses=[]
    def run_gate(self):return g.gate_candidate(self.base,self.control,self.candidate,self.ml,self.ml,self.c,self.proof,self.censuses.append)
    def test_full_candidate_gate_positive(self):
        r=self.run_gate();self.assertEqual(r['status'],'COMPILED_B3E_CONDITIONAL');self.assertEqual(self.censuses[0]['compared_components'],2);self.assertTrue(all(r['overlay']['checks'].values()))
        # The actual normalized face_area NaN is bit-encoded and serializable.
        with tempfile.TemporaryDirectory() as td:g.meter.dump(Path(td)/'report.json',r)
    def test_internal_buffer_error_is_inconclusive(self):
        self.candidate.lods[1].normal_raw=bytes(13)
        with self.assertRaises(ValueError) as e:self.run_gate()
        self.assertEqual(g.failure_status(e.exception),'INCONCLUSIVE_BINARY')
    def test_serialization_error_is_inconclusive(self):
        with self.assertRaises(ValueError) as e:json.dumps(dict(metric=float('nan')),allow_nan=False)
        self.assertEqual(g.failure_status(e.exception),'INCONCLUSIVE_BINARY')
    def test_explicit_geometry_rejection_stays_rejected(self):
        with self.assertRaises(ValueError) as e:g.need(False,'geometric')
        self.assertEqual(g.failure_status(e.exception),'REJECTED_BINARY')
    def test_protected_lods_water_uv(self):
        for i in (0,2,3):
            self.candidate=copy.deepcopy(self.base);self.candidate.lods[i].uv=[(0.,0.)]
            with self.subTest(lod=i),self.assertRaisesRegex(g.Inconclusive,'protected_lod_changed'):self.run_gate()
        self.candidate=copy.deepcopy(self.base);self.candidate.lods[0].material='changed-water'
        with self.assertRaises(g.Inconclusive):self.run_gate()
    def test_unknown_none_and_mass(self):
        self.candidate.lods[1].new_field=None
        with self.assertRaisesRegex(g.Inconclusive,'geometry_metadata_changed'):self.run_gate()
        self.candidate=copy.deepcopy(self.base);self.candidate.model_info.mass=2.
        with self.assertRaisesRegex(g.Inconclusive,'model_info_changed'):self.run_gate()
    def test_pose_rotation_or_centre(self):
        self.c['matrix']=IDENTITY.copy();self.c['matrix'][0]=-1
        with self.assertRaises(g.Inconclusive):self.run_gate()
        self.c['matrix']=IDENTITY;self.candidate.model_info.bounding_center.y=.5
        with self.assertRaises(g.Inconclusive):self.run_gate()
    def test_census_precedes_later_gate(self):
        self.candidate.lods[1].faces[0].vertex_indices.reverse();self.candidate.lods[0].material='also-bad'
        with self.assertRaisesRegex(ValueError,'compiled_geometry_discrepancies'):self.run_gate()
        self.assertEqual(self.censuses[0]['compared_components'],2)
    def test_overlay_is_not_waived_by_exact_geometry(self):
        ml=copy.deepcopy(self.ml)
        # Keep Geometry independent of Visual so only the bed moves.
        ml[0]=copy.deepcopy(self.ml[0])
        for p in ml[0].points:p.coords=(p.coords[0],p.coords[1]+.03,p.coords[2])
        with self.assertRaisesRegex(ValueError,'compiled_overlay'):
            g.gate_candidate(self.base,self.control,self.candidate,ml,self.ml,self.c,self.proof,self.censuses.append)

class ReviewRegressions(unittest.TestCase):
    def test_optional_executable_denied_does_not_abort_child(self):
        with tempfile.TemporaryDirectory() as td,mock.patch.object(build.psutil.Process,'exe',side_effect=build.psutil.AccessDenied(1)):
            r=build.run_tree([sys.executable,'-c','import time; time.sleep(.5)'],Path(td),Path(td)/'run.log',10)
            self.assertEqual(r['returncode'],0);self.assertTrue(r['observed_processes']);self.assertTrue(all(v['executable'] is None for v in r['observed_processes'].values()))
    def test_memory_denied_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as td,mock.patch.object(build.psutil.Process,'memory_info',side_effect=build.psutil.AccessDenied(1)):
            with self.assertRaises(build.psutil.AccessDenied):build.run_tree([sys.executable,'-c','import time; time.sleep(10)'],Path(td),Path(td)/'run.log',10)
            receipt=json.loads((Path(td)/'run.running.json').read_bytes())
            self.assertFalse(build.psutil.pid_exists(receipt['pid']))
    def test_reference_metric_drift_is_inconclusive(self):
        od,ml=fixture();c=dict(selected_components=['Component0001'],targets=[dict(id=700,x=.25,z=.25)],origin=[0,0,0]);proof=dict(contacts=[dict(id=700,local_margin_m=.25,world_float32_margin_m=.25,witness_component='Component0001')])
        r=g.source_contact_reference(ml[1],c,proof);self.assertEqual(r['status'],'HISTORICAL_METRIC_REPRODUCED')
        proof['contacts'][0]['world_float32_margin_m']=np.nextafter(.25,1.)
        with self.assertRaisesRegex(g.Inconclusive,'reference_contact_metric_not_reproduced'):g.source_contact_reference(ml[1],c,proof)
    def test_unselected_overlapping_roof_does_not_change_reference_domain(self):
        od,ml=fixture();world=g.old.old.xyz(od.lods[1].vertices).astype('<f4');world[6:,[0,2]]=[[ -1,-1],[4,-1],[-1,4],[-1,-1],[4,-1],[-1,4]]
        proof=dict(contacts=[dict(id=700,world_float32_margin_m=.25,witness_component='Component0001')])
        r=g.contact_witness(od.lods[1],world,[dict(id=700,x=.25,z=.25)],ml[1].selections,proof,['Component0001']);self.assertEqual(r[0]['witness_component'],'Component0001')

if __name__=='__main__':unittest.main()
