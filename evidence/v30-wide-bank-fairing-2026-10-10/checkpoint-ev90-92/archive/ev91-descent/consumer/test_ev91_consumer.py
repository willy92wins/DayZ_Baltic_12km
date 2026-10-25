import importlib.util
import json
from pathlib import Path
import unittest
import numpy as np

SOURCE=Path(__file__).with_name('verify_ev91.py')
spec=importlib.util.spec_from_file_location('ev91_under_test',SOURCE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class Geometry:
    WINDOW=(0,7,0,7)
    CORE=(2,5,2,5)

class Geometry87:
    @staticmethod
    def edge_vertex_slices(mask,kind):
        if kind=='diag': return (mask[:-1,:-1],mask[:-1,1:],mask[1:,:-1],mask[1:,1:])
        if kind=='vertical': return (mask[:-1,:-2],mask[:-1,1:-1],mask[1:,1:-1],mask[1:,2:])
        return (mask[:-2,:-1],mask[1:-1,:-1],mask[1:-1,1:],mask[2:,1:])
    @classmethod
    def incident_any(cls,mask,kind):
        return np.logical_or.reduce(cls.edge_vertex_slices(mask,kind))
    @staticmethod
    def _ev87_hinge_vertices(kind,r,c):
        if kind=='diag': return ((r,c),(r,c+1),(r+1,c),(r+1,c+1))
        if kind=='vertical': return ((r,c),(r,c+1),(r+1,c+1),(r+1,c+2))
        return ((r,c),(r+1,c),(r+1,c+1),(r+2,c+1))

def stencil_rows(window):
    r0,r1,c0,c1=window
    collar={(r,c) for r in range(r0,r1) for c in range(c0,c1)
            if r<r0+2 or r>=r1-2 or c<c0+2 or c>=c1-2}
    out=[]
    def add(nodes):
        if any((r,c) in collar for r,c in nodes):
            out.append({'nodes':nodes,'collar':True})
    for r in range(r0,r1):
        for c in range(c0,c1-2): add(((r,c),(r,c+1),(r,c+2)))
    for r in range(r0,r1-2):
        for c in range(c0,c1): add(((r,c),(r+1,c),(r+2,c)))
    for r in range(r0,r1-2):
        for c in range(c0,c1-2): add(((r,c),(r,c+2),(r+2,c),(r+2,c+2)))
    return out

class Ev91ConsumerFixtures(unittest.TestCase):
    def test_real_pinned_population_reconciliation_schema(self):
        path=mod.POPULATION_RECONCILIATION
        self.assertEqual(mod.sha(path),mod.PINNED[str(path)])
        census=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(census['eligible_wet_support'],65955)
        self.assertEqual(census['eligible_outside_bank_interior'],65955)
        self.assertTrue(census['outside_equals_wet_support_overlap'])

    def test_real_BH_wet_support_diagnostic_artifact(self):
        path=mod.HERE/'runs/wet-support-diagnostic-real.json'
        report=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(report['status'],'WET_SUPPORT_DIAGNOSTIC_ONLY')
        self.assertEqual(report['candidate_sha256'],
            '865901ab24aa3736da57847f9112d3c73181085213f89b48ef2e3e7a9f6ee702')
        self.assertEqual(report['source_hashes'][str(mod.POPULATION_RECONCILIATION)],mod.PINNED[str(mod.POPULATION_RECONCILIATION)])
        metrics=report['metrics']
        self.assertEqual(metrics['eligible_wet_support_nodes'],65955)
        self.assertEqual(metrics['B']['n'],775)
        self.assertEqual(metrics['H']['n'],775)
        self.assertEqual(metrics['B_p99_brackets_deg'],[37.11284255981445,37.706443786621094])
        self.assertTrue(metrics['p99_nonworse'] and metrics['bracket_counts_nonworse'])
        self.assertEqual(metrics['new_over30_count'],0)

    def test_d8_tie_uses_lexicographic_neighbor_and_plateau_is_valid(self):
        b=np.ones((7,7),dtype=np.float32); nodes=[(3,3)]
        centers,witnesses,exempt=mod.independent_d8(b,nodes)
        self.assertEqual(len(centers),9); self.assertEqual(len(witnesses),9); self.assertEqual(exempt,[])
        center=next(x for x in witnesses if x['center']==[3,3])
        self.assertEqual(center['witness'],[2,2])
        self.assertTrue(mod.check_d8_candidate(b,witnesses)['pass'])
        flat=b.copy(); flat[3,3]=np.nextafter(np.float32(1),np.float32(0))
        self.assertFalse(mod.check_d8_candidate(flat,witnesses)['pass'])

    def test_original_strict_minimum_is_exempt(self):
        b=np.ones((7,7),dtype=np.float32); b[3,3]=0.0
        _,witnesses,exempt=mod.independent_d8(b,[(3,3)])
        self.assertIn([3,3],exempt)
        self.assertNotIn([3,3],[w['center'] for w in witnesses])

    def test_collar_guard_uses_all_four_vertex_incident_any(self):
        nodes=[(r,c) for r in range(2,5) for c in range(2,5)]
        stencils=stencil_rows(Geometry.WINDOW)
        domain={'variables':np.asarray(nodes,dtype=np.int32), 'stencils':stencils,
                'collar_stencils':stencils}
        guard,n_all,n_collar=mod.independent_collar_guard(Geometry,Geometry87,domain)
        self.assertEqual(n_all,n_collar)
        self.assertEqual(len(guard),9)
        self.assertIn((3,3),guard)
        self.assertEqual(set(guard),set(nodes))

if __name__=='__main__':
    unittest.main(verbosity=2)

