import unittest
import numpy as np
import tempfile
from pathlib import Path
import hashlib
import assess_rejected_diagnostic as v
import verify_polished_diagnostic as helper

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class RejectedDiagnosticAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.path='E:/fixture/rejected-diagnostic.npz'; self.sha='a'*64
        self.receipt={
          'schema':'candidate-only-f32-lattice.real-run.v1','status':'REJECTED_EXACT_POSTGATES',
          'accepted':False,'terrain_written':False,'solver_invoked':True,'solver_status':0,
          'exact_fraction_rows_pass':True,
          'exact_fraction_gates':{k:True for k in ('bounds','crossings','d8','fixed','shape','signs')},
          'direct_executor_gates':{'bounds':True,'PF_signs':True,'closure_energy_and_improvement':False},
          'rejected_diagnostic':{'accepted':False,'terrain_written':False,'path':self.path,'sha256':self.sha}}

    def test_pinned_energy_rejected_receipt_accepts_as_diagnostic(self):
        self.assertTrue(v.validate_rejected_envelope_fields(self.receipt,self.path,self.sha))

    def test_acceptance_or_wrong_artifact_is_rejected(self):
        for mutate in (lambda r:r.update(accepted=True),
                       lambda r:r['rejected_diagnostic'].update(sha256='b'*64),
                       lambda r:r['direct_executor_gates'].update(closure_energy_and_improvement=True),
                       lambda r:r['exact_fraction_gates'].update(d8=False)):
            r={**self.receipt,'rejected_diagnostic':dict(self.receipt['rejected_diagnostic']),
               'direct_executor_gates':dict(self.receipt['direct_executor_gates']),
               'exact_fraction_gates':dict(self.receipt['exact_fraction_gates'])}
            mutate(r)
            with self.assertRaises(ValueError):v.validate_rejected_envelope_fields(r,self.path,self.sha)

    def test_readset_growth_is_distinguished_from_drift(self):
        start={'a':'1','b':'2'}
        v.require_readset_subset(start,{'a':'1','b':'2','c':'3'})
        with self.assertRaises(ValueError):v.require_readset_subset(start,{'a':'9','b':'2','c':'3'})
        with self.assertRaises(ValueError):v.require_readset_subset(start,{'a':'1'})

    def test_exact_core_delta_accepts_and_outside_collar_rejects(self):
        base=np.ones((15,15),dtype=np.float32)
        vars_rc=np.asarray([(r,c) for r in range(857,868) for c in range(1181,1192)],dtype=np.int32)
        prep={'base_heights_context':base.copy(),'variables_rc':vars_rc}
        ctx=base.copy()
        for i,(r,c) in enumerate(vars_rc[:114]): ctx[r-855,c-1179]=np.float32(1.0+(i+1)/1000)
        lattice=np.zeros(121,dtype=np.int64)
        out=v.validate_diag_arrays(ctx,base,vars_rc,lattice,prep,base)
        self.assertEqual(int(out[1].sum()),114)
        bad=ctx.copy(); bad[0,0]=np.float32(2.0)
        with self.assertRaises(v.Stop):v.validate_diag_arrays(bad,base,vars_rc,lattice,prep,base)

    def test_npz_loader_returns_real_assessment_contract(self):
        base=np.ones((15,15),dtype=np.float32)
        vars_rc=np.asarray([(r,c) for r in range(857,868) for c in range(1181,1192)],dtype=np.int32)
        prep={'base_heights_context':base.copy(),'variables_rc':vars_rc}
        ctx=base.copy()
        for i,(r,c) in enumerate(vars_rc[:114]): ctx[r-855,c-1179]=np.float32(1.0+(i+1)/1000)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'diagnostic.npz'
            np.savez(path,context_grid=ctx,lattice_m=np.zeros(121,dtype=np.int64),
                     variables_rc=vars_rc,source_base_context=base)
            full=np.ones((2048,2048),dtype=np.float32)
            loaded=v.validate_npz(path,prep,full)
        self.assertEqual(len(loaded),5)
        out_ctx,out_vars,changed,changed_rc,lattice=loaded
        self.assertEqual(out_ctx.shape,(15,15)); self.assertEqual(out_vars.shape,(121,2))
        self.assertEqual(int(changed.sum()),114); self.assertEqual(changed_rc.shape,(114,2))
        self.assertEqual(lattice.shape,(121,))

    def test_wrong_npz_contract_types_are_rejected(self):
        base=np.ones((15,15),dtype=np.float32)
        vars_rc=np.asarray([(r,c) for r in range(857,868) for c in range(1181,1192)],dtype=np.int32)
        prep={'base_heights_context':base.copy(),'variables_rc':vars_rc}
        ctx=base.copy()
        for i,(r,c) in enumerate(vars_rc[:114]): ctx[r-855,c-1179]=np.float32(1.0+(i+1)/1000)
        with self.assertRaises(v.Stop):v.validate_diag_arrays(ctx.astype(np.float64),base,vars_rc,np.zeros(121,dtype=np.int64),prep,base)
        with self.assertRaises(v.Stop):v.validate_diag_arrays(ctx,base,vars_rc,np.zeros(120,dtype=np.int64),prep,base)

    def test_npz_loader_rejects_missing_or_extra_payload(self):
        base=np.ones((2048,2048),dtype=np.float32)
        prep={'base_heights_context':np.ones((15,15),dtype=np.float32),
              'variables_rc':np.asarray([(r,c) for r in range(857,868) for c in range(1181,1192)],dtype=np.int32)}
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'bad.npz'
            np.savez(path,context_grid=np.ones((15,15),dtype=np.float32),lattice_m=np.zeros(121,dtype=np.int64),
                     variables_rc=prep['variables_rc'],source_base_context=prep['base_heights_context'],extra=np.array([1]))
            with self.assertRaises(v.Stop):v.validate_npz(path,prep,base)

    def test_energy_failure_never_becomes_acceptance(self):
        other={'bounds':True,'water':True}
        self.assertEqual(v.status_for(other,False),'DIAGNOSTIC_ASSESSMENT_COMPLETE_ENERGY_FAIL')
        self.assertNotIn('PASS',v.status_for(other,False))
        both=v.status_for({'bounds':True,'water':False},False)
        self.assertEqual(both,'DIAGNOSTIC_ASSESSMENT_ENERGY_AND_OTHER_GATES_FAIL')
        self.assertNotIn('PASS',both)
        self.assertEqual(v.status_for({'bounds':True,'water':False},True),'DIAGNOSTIC_ASSESSMENT_OTHER_GATES_FAIL')

    def test_real_read_only_identity_mode_checks_all_pins_and_approval_links(self):
        result=v.validate_identity()
        self.assertEqual(result['status'],'READ_ONLY_IDENTITY_PASS')
        self.assertFalse(result['geometry_executed'])
        self.assertFalse(result['accepted'])
        self.assertEqual(result['pins_checked'],len(v.PINNED))
        receipt=v.load_json(v.DIAG_RECEIPT)
        expected={'plan':v.PINNED[v.DIAG_PLAN],'model':v.PINNED[v.DIAG_MODEL],
                  'driver':v.PINNED[v.DIAG_DRIVER],'control_receipt':v.PINNED[v.DIAG_CONTROL_RECEIPT]}
        self.assertTrue(v.validate_approved_identity(receipt['approved_hashes'],expected))
        bad=dict(receipt['approved_hashes'],approved_control_sha=v.PINNED[v.DIAG_CONTROL])
        with self.assertRaises(v.Stop):v.validate_approved_identity(bad,expected)

    def test_control_receipt_rejects_solver_or_readset_drift(self):
        real=v.load_json(v.DIAG_CONTROL_RECEIPT)
        self.assertFalse(v.validate_baseline_control(real,v.PINNED[v.DIAG_MODEL])['real_solver_invoked'])
        bad=dict(real,real_solver_invoked=True)
        with self.assertRaises(v.Stop):v.validate_baseline_control(bad,v.PINNED[v.DIAG_MODEL])

    def test_logical_preparation_keys_resolve_via_pinned_producer(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'selection.json'; p.write_text('{"selection":1}',encoding='utf-8')
            q=Path(td)/'retained.json'; q.write_text('{"retained":1}',encoding='utf-8')
            digest=_sha(p)
            class Producer:
                PATHS={'selection':p,'retained_selection':q}
                EXPECTED={'selection':digest}
            source={'selection':digest,'retained_selection':_sha(q)}
            self.assertEqual(helper.verify_logical_source_readset(source,Producer),2)
            with self.assertRaises(helper.ConsumerStop):
                helper.verify_logical_source_readset({'selection':digest},Producer)
            with self.assertRaises(helper.ConsumerStop):
                helper.verify_logical_source_readset(dict(source,selection='0'*64),Producer)

    def test_retained_keys_are_real_absolute_paths_and_rehashed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'retained.json'; p.write_text('{}',encoding='utf-8')
            digest=_sha(p)
            self.assertEqual(helper.verify_retained_path_readset({str(p.resolve()):digest}),1)
            with self.assertRaises(helper.ConsumerStop):
                helper.verify_retained_path_readset({'logical-name':digest})
            with self.assertRaises(helper.ConsumerStop):
                helper.verify_retained_path_readset({str(p.resolve()):'0'*64})

if __name__=='__main__':unittest.main(verbosity=2)
