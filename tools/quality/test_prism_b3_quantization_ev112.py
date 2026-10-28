"""Independent rational/analytic fixtures; no project models or compiler needed."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace as N
import copy,sys,unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prism_b3_quantization_ev112 as q
from test_prism_b3_binary_ev112 import prism,IDENTITY

def model_fixture(count=1):
    points=[];faces=[];sels={};decoded=[];dfaces=[];dsels=[];tops=[]
    for n in range(count):
        ml,geo=prism();base=len(points);offset=np.array([3.*n,0.,0.])
        for i,p in enumerate(ml.points):
            v=np.asarray(p.coords,float)+offset;v[1]=.5 if i<3 else .5-q.T;p.coords=tuple(v)
        fs=list(ml.selections['Component0001'].faces)
        for f in fs:
            f.material='bed'
            for v in f.vertices:v.point_index+=base
        points.extend(ml.points);faces.extend(fs);name=f'component{n+1:04d}'
        sels[name]=N(points=ml.points,faces=fs);tops.append(fs[0])
        decoded.extend([N(x=float(p.coords[0]),y=float(p.coords[1]),z=float(p.coords[2])) for p in ml.points])
        dfaces.extend(N(vertex_indices=[v.point_index for v in f.vertices][::-1]) for f in fs)
        dsels.append(N(name=name,selected_vertices=list(range(base,base+6)),selected_faces=list(range(n*8,n*8+8))))
    ml=N(points=points,faces=faces,selections=sels);xyz=q.binary.old.xyz(decoded)
    geo=N(vertices=decoded,vertex_raw=xyz.astype('<f4').tobytes(),faces=dfaces,named_selections=dsels)
    v=lambda a:N(x=float(a[0]),y=float(a[1]),z=float(a[2]))
    od=N(lods=[None,geo],model_info=N(bounding_center=v([0,0,0]),bbox_min=v(xyz.min(0)),bbox_max=v(xyz.max(0))))
    lods=[N(points=points,faces=tops),ml,N(points=[]),N(points=[])]
    return lods,od

class RationalAndDomain(unittest.TestCase):
    def test_manual_tie_even_odd(self):
        self.assertEqual(int(q.bits(q.round_fraction32(F(1)+F(1,2**24)))),0x3f800000)
        self.assertEqual(int(q.bits(q.round_fraction32(F(1)+F(3,2**24)))),0x3f800002)

    def test_negative_ties(self):
        self.assertEqual(int(q.bits(q.round_fraction32(-F(1)-F(1,2**24)))),0xbf800000)
        self.assertEqual(int(q.bits(q.round_fraction32(-F(1)-F(3,2**24)))),0xbf800002)

    def test_exponent_crossings_4_and_8(self):
        self.assertEqual(int(q.bits(q.round_fraction32(F(4)-F(1,2**23)))),0x40800000)
        self.assertEqual(int(q.bits(q.round_fraction32(F(8)-F(1,2**22)))),0x41000000)

    def test_subnormal_ties(self):
        self.assertEqual(int(q.bits(q.round_fraction32(F(1,2**150)))),0)
        self.assertEqual(int(q.bits(q.round_fraction32(F(3,2**150)))),2)

    def test_float64_difference_not_universally_exact(self):
        exact=F(2**100)-1;machine=F(float(2**100)-1.)
        self.assertNotEqual(exact,machine)
        self.assertTrue(q.same_bits(q.round_fraction32(exact),np.float32(float(machine))))

    def test_signed_zero_comparisons_report_different_questions(self):
        self.assertTrue(np.array_equal([0.],[-0.]));self.assertFalse(q.same_bits([0.],[-0.]))
        self.assertEqual(q.bits(q.domain(-0.,0.)).tolist(),[0x80000000,0])

    def test_oracle_signed_zero_arithmetic(self):
        for a,b,subtract,expected in [(-0.,0.,True,0x80000000),(-0.,-0.,False,0x80000000),(-0.,-0.,True,0),(0.,-0.,False,0),(1.,1.,True,0)]:
            self.assertEqual(int(q.bits(q.oracle_op(a,b,subtract))),expected)
        self.assertTrue(q.same_bits(q.y_frames(-0.,0.,0.,0.),q.oracle_frames(-0.,0.,0.,0.)))

    def test_domain_boundaries_exact_and_halfway(self):
        u=2**-23
        self.assertEqual(q.bits(q.domain(1,1+2*u)).tolist(),[0x3f800000,0x3f800001,0x3f800002])
        self.assertEqual(q.bits(q.domain(1+u/2,1+2*u)).tolist(),[0x3f800001,0x3f800002])

    def test_negative_ordered_domain(self):
        self.assertEqual(q.bits(q.domain(-1-2**-22,-1)).tolist(),[0xbf800002,0xbf800001,0xbf800000])

    def test_domain_budget_not_unsat(self):
        with self.assertRaises(q.DomainBudget):q.domain(-1e-6,1e-6)

    def test_manual_double_rounding_case(self):
        m=q.float_at(0x337fffff);o=q.float_at(0x3f800001);c=.5;t=q.float_at(0x3fc00001)
        local,source,compiled=q.y_frames(m,c,o,t)
        self.assertEqual(int(q.bits(source)),0x3f800001);self.assertEqual(int(q.bits(compiled)),0x3f800002)
        self.assertTrue(q.same_bits((local,source,compiled),q.oracle_frames(m,c,o,t)))

class Census(unittest.TestCase):
    def test_analytic_control_complete(self):
        lods,od=model_fixture(2);r,m=q.census(lods[1],od,[0,0,0],IDENTITY)
        self.assertEqual(r['summary']['components'],2);self.assertEqual(r['summary']['world_bit_differences'],0);self.assertEqual(len(m),12)

    def test_all_components_after_prefix_censused(self):
        lods,od=model_fixture(2);r,_=q.census(lods[1],od,[0,0,0],IDENTITY,'component0001')
        self.assertEqual(r['summary']['new_local_components'],1);self.assertEqual(r['summary']['comparable'],2)

    def test_empirical_local_mismatch_is_not_hidden(self):
        lods,od=model_fixture();od.lods[1].vertices[0].y+=.125;od.lods[1].vertex_raw=q.binary.old.xyz(od.lods[1].vertices).astype('<f4').tobytes()
        r,_=q.census(lods[1],od,[0,0,0],IDENTITY)
        self.assertEqual(r['status'],'CENSUS_INCONCLUSIVE');self.assertEqual(r['summary']['noncomparable'],1)

    def test_duplicate_local_mapping_is_not_nearest_neighbor(self):
        lods,od=model_fixture();od.lods[1].vertices[0]=copy.deepcopy(od.lods[1].vertices[1]);od.lods[1].vertex_raw=q.binary.old.xyz(od.lods[1].vertices).astype('<f4').tobytes()
        r,_=q.census(lods[1],od,[0,0,0],IDENTITY)
        self.assertEqual(r['summary']['noncomparable'],1)

    def test_reversed_face_topology_detected(self):
        lods,od=model_fixture();od.lods[1].faces[0].vertex_indices.reverse()
        r,_=q.census(lods[1],od,[0,0,0],IDENTITY)
        self.assertFalse(r['summary']['topology_exact_all'])

    def test_manual_world_mismatch_with_exact_local_prediction(self):
        lods,od=model_fixture();m=q.float_at(0x337fffff);o=q.float_at(0x3f800001);t=q.float_at(0x3fc00001)
        for i,p in enumerate(lods[1].points):p.coords=(p.coords[0],float(np.float32(m+(.5 if i<3 else 0))),p.coords[2])
        xyz=np.array([p.coords for p in lods[1].points]);local=(xyz-[0,.5,0]).astype('<f4')
        od.model_info.bounding_center=N(x=0.,y=.5,z=0.);od.lods[1].vertex_raw=local.tobytes();od.lods[1].vertices=[N(x=float(x),y=float(y),z=float(z)) for x,y,z in local]
        matrix=IDENTITY.copy();matrix[10]=t
        r,_=q.census(lods[1],od,[0,o,0],matrix)
        self.assertEqual(r['summary']['local_bit_differences'],0);self.assertEqual(r['summary']['world_value_differences'],3)
        self.assertTrue(all(x['kind']=='base' for x in r['mismatches']))

class Feasibility(unittest.TestCase):
    def test_no_unapproved_local_thickness_filter(self):
        top=-0.42000097036361694;base=top-q.T
        r=q.solve_pair([base,top],-.42,.396484375,7.,7.396484375,[-10,10])
        self.assertEqual(r['eligible'],30);self.assertEqual(r['domain_size'],67)
        self.assertEqual(r['after'],[base,top]);self.assertEqual(top-base,q.T)
        self.assertNotEqual(r['reported_local_thickness'],q.T)
        self.assertEqual(r['reported_world_thickness'],q.T)
        self.assertEqual(r['rational_domain_values_verified'],134)

    def test_discarded_value_oracle_mismatch_is_inconclusive(self):
        original=q.oracle_frames
        def mutant(y,*args):
            r=original(y,*args)
            return (r[0]+.125,r[1],r[2]) if y!=.5 and y!=.5-q.T else r
        with patch.object(q,'oracle_frames',side_effect=mutant):
            with self.assertRaisesRegex(ValueError,'rational_domain_disagreement'):
                q.solve_pair([.5-q.T,.5],.5,0,0,0,[.5-q.T,.5])

    def test_control_frame_gate(self):
        lods,od=model_fixture();r,_=q.census(lods[1],od,[0,0,0],IDENTITY)
        self.assertTrue(q.control_gate(r))
        for key,value in [('world_bit_differences',1),('local_bit_differences',1),('face_bit_missing',1),('noncomparable',1),('topology_exact_all',False)]:
            changed=copy.deepcopy(r);changed['summary'][key]=value
            self.assertFalse(q.control_gate(changed),key)

    def test_pair_exact_thickness_and_oracle(self):
        m=q.float_at(0x337fffff);o=q.float_at(0x3f800001);t=q.float_at(0x3fc00001)
        r=q.solve_pair([m,float(np.float32(m+q.T))],m+q.T,.5,o,t,[-10,10])
        self.assertEqual(r['status'],'PAIR_WITNESS');self.assertEqual(r['after'][1]-r['after'][0],q.T)
        self.assertTrue(r['rational_frames_verified']);self.assertLess(r['domain_size'],100)

    def test_closed_domain_conflict_is_conditional(self):
        r=q.solve_pair([0.,q.T],.5,0,0,0,[0.,0.])
        self.assertEqual(r['status'],'NO_WITNESS_IN_THIS_PAIR_DOMAIN');self.assertEqual(r['eligible'],0)

    def test_bbox_extremum_not_moved(self):
        r=q.solve_pair([.5-q.T,.5],.5,0,0,0,[.5-q.T,.5])
        self.assertEqual(r['after'],[.5-q.T,.5])

    def test_complete_witness_is_analysis_only(self):
        lods,od=model_fixture(12);r,_=q.census(lods[1],od,[0,0,0],IDENTITY)
        result=q.feasibility(lods,lods,od,np.zeros(3),IDENTITY,list(lods[1].selections),r)
        self.assertEqual(result['status'],'FEASIBILITY_ONLY');self.assertEqual(result['changed_vertices'],0)
        self.assertTrue(all(result['overlay']['checks'].values()));self.assertTrue(result['world_frames_bit_exact'])

    def test_complete_nontrivial_witness_with_nonzero_frames(self):
        lods,od=model_fixture(12);bad_base=q.float_at(0xbed90e97);bad_top=bad_base+q.T
        for n in range(12):
            top=bad_top if n==1 else (-1. if n==0 else 1.)
            for i in range(6):
                p=lods[1].points[n*6+i];p.coords=(p.coords[0],top if i<3 else top-q.T,p.coords[2])
        xyz=np.asarray([p.coords for p in lods[1].points]);local=(xyz-[0,.396484375,0]).astype('<f4')
        od.model_info.bounding_center=N(x=0.,y=.396484375,z=0.)
        od.lods[1].vertex_raw=local.tobytes();od.lods[1].vertices=[N(x=float(x),y=float(y),z=float(z)) for x,y,z in local]
        matrix=IDENTITY.copy();matrix[10]=7.396484375;origin=np.array([0.,7.,0.])
        r,_=q.census(lods[1],od,origin,matrix)
        self.assertGreater(r['summary']['world_bit_differences'],0);self.assertEqual(r['summary']['local_bit_differences'],0)
        before=copy.deepcopy([p.coords for p in lods[1].points])
        result=q.feasibility(lods,lods,od,origin,matrix,list(lods[1].selections),r)
        self.assertEqual(result['status'],'FEASIBILITY_ONLY');self.assertGreater(result['changed_vertices'],0)
        self.assertTrue(all(result['overlay']['checks'].values()));self.assertTrue(result['world_frames_bit_exact'])
        self.assertTrue(all(p['rational_frames_verified'] for p in result['pairs']))
        self.assertEqual(before,[p.coords for p in lods[1].points])

    def test_xz_failure_not_solved_with_y(self):
        lods,od=model_fixture(12);r,_=q.census(lods[1],od,[0,0,0],IDENTITY)
        r['mismatches']=[dict(component='component0001',world_bit_difference=[True,False,False])]
        self.assertEqual(q.feasibility(lods,lods,od,np.zeros(3),IDENTITY,list(lods[1].selections),r)['status'],'INCONCLUSIVE_Y_DOMAIN')

if __name__=='__main__':unittest.main()
