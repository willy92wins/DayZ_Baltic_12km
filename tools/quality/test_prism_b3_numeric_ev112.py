"""Saved-file fixtures and negative contracts for B3D; no production models."""
from pathlib import Path
import copy,io,struct,sys,tempfile,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_prism_contact_b3_ev112 import fixture
from prism_b3_numeric_author_ev112 import author,bind_contract as author_bind,save_checked
import verify_prism_b3_numeric_ev112 as v
from review_compact_collision_v31 import load,py3d

class SavedConsumer(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);d=Path(self.tmp.name)
        self.source=d/'source.p3d';self.candidate=d/'candidate.p3d';fixture(self.source,(.125,-.25))
        _,ls,_=load(self.source);xyz=np.array([p.coords for p in ls[1].points]);ids=[i for i,p in enumerate(xyz) if p[0]==p[2]==0]
        self.witness=dict(status='FEASIBILITY_ONLY',witness=[dict(source_index=i,before=xyz[i].tolist(),after=(xyz[i]+[0,2**-25,0]).tolist()) for i in ids])
        self.assertEqual(len(ids),2)
        self.selected=['Component0001'];self.origin=np.array([8262.,7.,8934.]);self.centre=np.array([0.,.396484375,0.]);self.matrix=[1,0,0,0,1,0,0,0,1,8262.,7.396484375,8934.]
        self.targets=[dict(id=700,x=8262.25,z=8934.25),dict(id=723,x=8262.125,z=8934.125)]
        self.previous=dict(contacts=[dict(id=700,local_margin_m=.25,world_float32_margin_m=.25,witness_component='Component0001'),dict(id=723,local_margin_m=.125,world_float32_margin_m=.125,witness_component='Component0001')])
        self.write()

    def write(self,witness=None):
        witness=self.witness if witness is None else witness
        blob,r=author(self.source,witness,self.selected,len(witness['witness']));self.candidate.write_bytes(blob);return r

    def check(self,**kw):
        args=dict(source=self.source,candidate=self.candidate,reference=self.source,witness=self.witness,selected=self.selected,origin=self.origin,centre=self.centre,matrix=self.matrix,targets=self.targets,previous=self.previous,expected_counts=(18,24,3),expected_changes=2);args.update(kw)
        return v.verify(**args)

    def mutate(self,path,fn):
        _,ls,_=load(path);fn(ls);m=py3d.P3D();m.lods=ls;stream=io.BytesIO();m.write(stream);path.write_bytes(stream.getvalue())

    def test_saved_nontrivial_pass(self):
        r=self.check();self.assertEqual(r['status'],'OFFLINE_CANDIDATE_ONLY');self.assertEqual(r['exact_mlod_pairs'],9);self.assertEqual(r['changed_y'],2)
        self.assertTrue(r['world_frames_bit_exact']);self.assertTrue(all(r['overlay']['checks'].values()))
        self.assertNotEqual(self.source.read_bytes(),self.candidate.read_bytes())

    def test_noop_entry_rejected_by_both(self):
        w=copy.deepcopy(self.witness);w['witness'][0]['after']=w['witness'][0]['before']
        with self.assertRaises(ValueError):author(self.source,w,self.selected,2)
        with self.assertRaises(ValueError):self.check(witness=w)

    def test_duplicate_index_rejected_by_both(self):
        w=copy.deepcopy(self.witness);w['witness'][1]=w['witness'][0]
        with self.assertRaisesRegex(ValueError,'witness_index'):author(self.source,w,self.selected,2)
        with self.assertRaisesRegex(ValueError,'witness_index'):self.check(witness=w)

    def test_index_outside_component(self):
        w=copy.deepcopy(self.witness);w['witness'][0]['source_index']=8
        with self.assertRaisesRegex(ValueError,'witness_index'):author(self.source,w,self.selected,2)
        with self.assertRaisesRegex(ValueError,'witness_index'):self.check(witness=w)

    def test_wrong_before(self):
        w=copy.deepcopy(self.witness);w['witness'][0]['before'][1]+=.125
        with self.assertRaisesRegex(ValueError,'witness_before'):author(self.source,w,self.selected,2)
        with self.assertRaisesRegex(ValueError,'witness_saved_values'):self.check(witness=w)

    def test_nonrepresentable_after(self):
        w=copy.deepcopy(self.witness);w['witness'][0]['after'][1]+=1e-15
        with self.assertRaisesRegex(ValueError,'witness_not_float32'):author(self.source,w,self.selected,2)
        with self.assertRaisesRegex(ValueError,'witness_not_float32'):self.check(witness=w)

    def test_nan_rejected(self):
        w=copy.deepcopy(self.witness);w['witness'][0]['after'][1]=float('nan')
        with self.assertRaisesRegex(ValueError,'witness_finite_shape'):author(self.source,w,self.selected,2)
        with self.assertRaisesRegex(ValueError,'witness_finite_shape'):self.check(witness=w)

    def test_xz_witness_not_permitted(self):
        w=copy.deepcopy(self.witness);w['witness'][0]['after'][0]=.125
        with self.assertRaisesRegex(ValueError,'witness_not_y_change'):author(self.source,w,self.selected,2)
        with self.assertRaises(ValueError):self.check(witness=w)

    def test_omitted_base_fails_exact_thickness_below_old_tolerance(self):
        w=copy.deepcopy(self.witness);w['witness']=[r for r in w['witness'] if r['before'][1]==0.]
        self.assertEqual(len(w['witness']),1);self.write(w)
        with self.assertRaisesRegex(ValueError,'exact_mlod_thickness'):self.check(witness=w,expected_changes=1)

    def test_missing_witness_record(self):
        w=copy.deepcopy(self.witness);w['witness'].pop()
        with self.assertRaisesRegex(ValueError,'witness_count'):self.check(witness=w)

    def test_point_flag_untouched(self):
        h,ls,bs=load(self.candidate);g=bytearray(bs[1]);g[28+12]^=1;bs[1]=bytes(g);self.candidate.write_bytes(h+b''.join(bs))
        with self.assertRaisesRegex(ValueError,'unauthorized_bytes_changed'):self.check()

    def test_visual_changed(self):
        self.mutate(self.candidate,lambda ls:setattr(ls[0].points[0],'coords',(0.,.1,0.)))
        with self.assertRaisesRegex(ValueError,'non_geometry_changed'):self.check()

    def test_tagg_byte_changed(self):
        self.mutate(self.candidate,lambda ls:setattr(ls[1].points[0],'mass',3.))
        with self.assertRaisesRegex(ValueError,'unauthorized_bytes_changed'):self.check()

    def test_normal_inverted(self):
        self.mutate(self.candidate,lambda ls:ls[1].facenormals.__setitem__(0,tuple(-np.array(ls[1].facenormals[0]))))
        with self.assertRaisesRegex(ValueError,'normal_error'):self.check()

    def test_unrelated_normal_bytes_changed(self):
        def edit(ls):
            n=np.asarray(ls[1].facenormals[20],'<f4');before=n.tobytes();n[0]=np.nextafter(n[0],np.float32(np.inf),dtype=np.float32)
            self.assertNotEqual(before,n.tobytes());ls[1].facenormals[20]=tuple(n)
        self.mutate(self.candidate,edit)
        with self.assertRaisesRegex(ValueError,'unauthorized_bytes_changed'):self.check()

    def test_receipt_margin_one_ulp_changed(self):
        receipt=copy.deepcopy(self.previous);receipt['contacts'][0]['local_margin_m']=float(np.nextafter(np.float64(.25),np.float64(1)))
        with self.assertRaisesRegex(ValueError,'contact_receipt_changed'):self.check(previous=receipt)

    def test_original_labels_and_positions(self):
        original=dict(rows=[dict(id=t['id'],expected=dict(**t,expect='dry' if t['id']==700 else 'wet')) for t in self.targets])
        v.original_controls(original,self.targets,self.origin.tolist())
        changed=copy.deepcopy(original);changed['rows'][1]['expected']['expect']='dry'
        with self.assertRaisesRegex(ValueError,'original_controls_changed'):v.original_controls(changed,self.targets,self.origin.tolist())
        moved=copy.deepcopy(self.targets);moved[1]['x']+=.001
        with self.assertRaisesRegex(ValueError,'original_controls_changed'):v.original_controls(original,moved,self.origin.tolist())

    def test_overlay_violation_with_identical_visual_lods(self):
        def raise_visual(ls):
            for p in ls[0].points:p.coords=tuple(np.array(p.coords)+[0,.03,0])
        self.mutate(self.source,raise_visual);self.write()
        with self.assertRaisesRegex(ValueError,'overlay'):self.check()

    def test_bad_counts_inconclusive(self):
        with self.assertRaises(v.Inconclusive):self.check(expected_counts=(19,24,3))

    def test_trailer_inconclusive(self):
        with self.candidate.open('ab') as f:f.write(b'X')
        with self.assertRaises(v.Inconclusive):self.check()

    def test_pose_mismatch_inconclusive(self):
        matrix=self.matrix.copy();matrix[10]+=.01
        with self.assertRaises(v.Inconclusive):self.check(matrix=matrix)

    def test_bbox_extremum_rejected(self):
        _,ls,_=load(self.source);xyz=np.array([p.coords for p in ls[1].points]);ids=[i for i,p in enumerate(xyz) if p[0]==-10 and p[2]==-20]
        w=dict(status='FEASIBILITY_ONLY',witness=[dict(source_index=i,before=xyz[i].tolist(),after=(xyz[i]+[0,2**-20,0]).tolist()) for i in ids])
        self.assertEqual(len(ids),2);selected=['Component0002'];blob,_=author(self.source,w,selected,2);self.candidate.write_bytes(blob)
        with self.assertRaisesRegex(ValueError,'bbox_changed'):self.check(witness=w,selected=selected)

    def test_exact_thickness_still_rejects_world_discrepancy(self):
        base=struct.unpack('<f',struct.pack('<I',0xbed90e97))[0];top=base+180/512
        def flatten_first(ls):
            for i,p in enumerate(ls[1].points[:6]):p.coords=(p.coords[0],top if i<3 else base,p.coords[2])
            for p in ls[0].points[:3]:p.coords=(p.coords[0],top,p.coords[2])
            for f in ls[1].faces:
                tri=np.array([ls[1].points[x.point_index].coords for x in f.vertices]);n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=np.linalg.norm(n)
                for x in f.vertices:ls[1].facenormals[x.normal_index]=tuple(n)
        self.mutate(self.source,flatten_first);_,ls,_=load(self.source);xyz=np.array([p.coords for p in ls[1].points]);ids=[i for i,p in enumerate(xyz) if p[0]==1 and p[2]==0]
        w=dict(status='FEASIBILITY_ONLY',witness=[dict(source_index=i,before=xyz[i].tolist(),after=(xyz[i]+[0,2**-25,0]).tolist()) for i in ids])
        self.write(w)
        with self.assertRaisesRegex(ValueError,'world_frames'):self.check(witness=w)

    def test_authoritative_contract_binding(self):
        prior=dict(candidate_mlod='S',source_control='R',offline_proof='P',original_result='O',origin=self.origin.tolist(),matrix=self.matrix,targets=self.targets,selected_components=self.selected,pins={x:x+'hash' for x in 'SRPO'})
        witness=dict(centre_fixed=self.centre.tolist(),translation_fixed=self.matrix[9:])
        contract=dict(source='S',reference='R',previous_report='P',original_result='O',witness='W',prior_contract='C',centre=self.centre.tolist(),origin=self.origin.tolist(),matrix=self.matrix,targets=self.targets,selected_components=self.selected,pins={**prior['pins'],'C':'5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244','W':'6e3653bb35321a72eee1c583c9345e7c8e27cc1d63340f192da4c0a238ce7028'})
        for check in (v.bind_contract,author_bind):
            check(contract,witness,prior)
            for field,value in [('source','R'),('selected_components',['Component0002']),('centre',[0,0,0])]:
                bad=copy.deepcopy(contract);bad[field]=value
                with self.assertRaises(ValueError):check(bad,witness,prior)
            for key in ('C','W'):
                bad=copy.deepcopy(contract);bad['pins'][key]='bad'
                with self.assertRaises(ValueError):check(bad,witness,prior)

    def test_unexpected_type_failure_is_inconclusive(self):
        w=copy.deepcopy(self.witness);w['witness'][0]['before']={}
        with self.assertRaises(TypeError) as ctx:self.check(witness=w)
        self.assertEqual(v.failure_status(ctx.exception),'INCONCLUSIVE')
        for e in [IndexError(),AttributeError(),MemoryError(),struct.error(),v.Inconclusive(),KeyError(),OSError()]:
            self.assertEqual(v.failure_status(e),'INCONCLUSIVE')
        self.assertEqual(v.failure_status(ValueError('exact_mlod_thickness')),'REJECTED_MLOD')

    def test_failed_input_recheck_keeps_only_pending_bytes(self):
        output=Path(self.tmp.name)/'pending-test';output.mkdir()
        def failed():raise ValueError('input_changed_after:fixture')
        with self.assertRaisesRegex(ValueError,'input_changed_after'):save_checked(b'synthetic fixture bytes',output,failed)
        self.assertFalse((output/'candidate.p3d').exists());self.assertEqual((output/'candidate.p3d.tmp').read_bytes(),b'synthetic fixture bytes')

    def test_successful_input_recheck_promotes_bytes_once(self):
        output=Path(self.tmp.name)/'promote-test';output.mkdir();calls=[]
        dest,digest=save_checked(b'synthetic fixture bytes',output,lambda:calls.append(True))
        self.assertEqual(calls,[True]);self.assertEqual(dest.read_bytes(),b'synthetic fixture bytes');self.assertFalse((output/'candidate.p3d.tmp').exists())
        with self.assertRaisesRegex(ValueError,'candidate_already_exists'):save_checked(b'replacement',output,lambda:None)
        self.assertEqual(dest.read_bytes(),b'synthetic fixture bytes')
if __name__=='__main__':unittest.main()
