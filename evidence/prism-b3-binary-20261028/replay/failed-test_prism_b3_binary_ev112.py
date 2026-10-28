"""Analytic independent primitives and adversarial binary-gate fixtures."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace as N
import unittest
from unittest import mock
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prism_b3_binary_ev112 as g

IDENTITY=[1,0,0,0,1,0,0,0,1,0,0,0]

def prism():
    # Six independently specified corners and eight triangles. ODOL reverses winding.
    xyz=np.array([[0,0,0],[2,0,0],[0,0,2],[0,-.5,0],[2,-.5,0],[0,-.5,2]],dtype='<f4')
    faces=[[0,1,2],[3,5,4],[0,3,4],[0,4,1],[1,4,5],[1,5,2],[2,5,3],[2,3,0]]
    points=[N(coords=tuple(v)) for v in xyz]
    fs=[N(vertices=[N(point_index=i) for i in f]) for f in faces]
    mlod=N(points=points,selections={'Component0001':N(points=points,faces=fs)})
    geo=N(vertices=[N(x=float(x),y=float(y),z=float(z)) for x,y,z in xyz],vertex_raw=xyz.tobytes(),faces=[N(vertex_indices=list(reversed(f))) for f in faces],named_selections=[N(name='component0001',selected_vertices=list(range(6)),selected_faces=list(range(8)))])
    return mlod,geo

def lod():
    return N(resolution=0.,lod_end_ok=True,size_of_rest_data=24,declared_end=120,parsed_end=120,rest_data_offset_probe=100,vertices=[N(x=0.,y=0.,z=0.)],material='water',uv=[(.25,.5)])

class BinaryGate(unittest.TestCase):
    def test_control_exact(self):
        a=N(version=71,model_info=N(mass=1.),lods=[lod()])
        g.control_identity(a,copy.deepcopy(a))

    def test_control_header_or_mass_or_protected_content(self):
        a=N(version=71,model_info=N(mass=1.),lods=[lod()])
        for field in ('version','mass','uv','material','vertices'):
            b=copy.deepcopy(a)
            if field=='version':b.version=70
            elif field=='mass':b.model_info.mass=2.
            elif field=='vertices':b.lods[0].vertices[0].y=.1
            else:setattr(b.lods[0],field,'changed')
            with self.subTest(field=field),self.assertRaises(g.Inconclusive):g.control_identity(a,b)

    def test_lod_offsets_may_relocate(self):
        a=lod();b=copy.deepcopy(a)
        b.declared_end+=40;b.parsed_end+=40;b.rest_data_offset_probe+=40
        self.assertEqual(g.lod_value(a),g.lod_value(b))

    def test_wrong_lod_boundary(self):
        a=lod();a.size_of_rest_data+=1
        with self.assertRaisesRegex(ValueError,'lod_boundary'):g.lod_value(a)

    def test_unknown_fields_and_mass_rejected(self):
        for b in ({'mass':2.},{'mass':1.,'new_flag':True},{'mass':1.,'new_field':None}):
            with self.assertRaises(g.Inconclusive):g.unchanged({'mass':1.},b,{'center_of_mass'},'meta')

    def test_nan_metadata_bit_identity(self):
        self.assertEqual(g.unchanged({'face_area':float('nan')},{'face_area':float('nan')},set(),'meta'),[])

    def test_pose_identity(self):g.pose_check(IDENTITY,[0,0,0],[0,0,0])

    def test_pose_rotation_and_translation_fail(self):
        for ix in (0,9):
            m=IDENTITY.copy();m[ix]+=1
            with self.assertRaises(ValueError):g.pose_check(m,[0,0,0],[0,0,0])

    def test_prism_matches_oriented_faces(self):
        ml,geo=prism();result,world=g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))
        self.assertEqual(result['components'],1);self.assertEqual(result['maximum_vertex_error_m'],0.)
        self.assertEqual(world.shape,(6,3))

    def test_cyclic_order_allowed(self):
        ml,geo=prism();geo.faces[0].vertex_indices=[1,0,2]
        g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))

    def test_inverted_face_fails(self):
        ml,geo=prism();geo.faces[0].vertex_indices.reverse()
        with self.assertRaisesRegex(ValueError,'compiled_face_counter'):g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))

    def test_missing_face_fails(self):
        ml,geo=prism();geo.faces.pop()
        with self.assertRaisesRegex(ValueError,'component_indices'):g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))

    def test_face_outside_component_fails(self):
        ml,geo=prism();geo.faces[0].vertex_indices[0]=9
        with self.assertRaisesRegex(ValueError,'face_outside_component'):g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))

    def test_wrong_corner_fails_prediction(self):
        ml,geo=prism();geo.vertices[0].x=.125
        geo.vertex_raw=g.old.xyz(geo.vertices).astype('<f4').tobytes()
        with self.assertRaisesRegex(ValueError,'local_recentering_prediction'):g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))

    def test_raw_and_decoded_inconsistency(self):
        ml,geo=prism();geo.vertices[0].x=.125
        with self.assertRaisesRegex(ValueError,'vertex_raw_decode'):g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))

    def test_duplicate_component_vertices(self):
        ml,geo=prism();geo.named_selections[0].selected_vertices[-1]=0
        with self.assertRaisesRegex(ValueError,'component_counts'):g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))

    def test_interior(self):
        tri=np.array([[[0,0,0],[0,0,2],[2,0,0]]],float)
        r=g.strict_contacts(tri,[dict(id=700,x=.25,z=.25)])
        self.assertEqual(r[0]['margin_m'],.25)

    def test_edge_vertex_outside_not_interior(self):
        tri=np.array([[[0,0,0],[0,0,2],[2,0,0]]],float)
        for x,z in ((1,1),(0,0),(2,2)):
            with self.subTest(x=x,z=z),self.assertRaisesRegex(ValueError,'boundary_or_outside'):g.strict_contacts(tri,[dict(id=700,x=x,z=z)])

    def test_wrong_winding_not_roof(self):
        tri=np.array([[[0,0,0],[2,0,0],[0,0,2]]],float)
        with self.assertRaises(ValueError):g.strict_contacts(tri,[dict(id=700,x=.25,z=.25)])

    def test_positive_sub_ulp_interior_not_artificially_rejected(self):
        u=1/1024;tri=np.array([[[8192,0,8192],[8192,0,8192+3*u],[8192+3*u,0,8192]]])
        r=g.strict_contacts(tri,[dict(id=700,x=8192+u,z=8192+u)])
        self.assertGreater(r[0]['margin_m'],0);self.assertLess(r[0]['margin_ulps'],1)

    def context(self):
        c=dict(candidate_sha256='candidate',source_control='source',source='source',targets=[dict(id=700,x=1,z=2),dict(id=723,x=3,z=4)],origin=[8262.,7.,8934.],selected_components=['Component1'],original_result='original',pins={'original':'original-sha','source':'source-sha'})
        proof=dict(status='OFFLINE_CANDIDATE_ONLY',candidate_sha256='candidate',contract_sha256='447d4a767183bdf95064387a7e0ef45d14a5e040aba6941c5584428e0829ff48',selected_components=['Component1'])
        return c,copy.deepcopy(c),proof

    def test_offline_context_bound(self):g.bind_context(*self.context())

    def test_moved_original_relabelled_origin_components(self):
        for field in ('targets','origin','selected_components','original_result'):
            c,b,p=self.context();c[field]=[]
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'offline_context_changed'):g.bind_context(c,b,p)

    def test_substituted_original_or_proof_rejected(self):
        c,b,p=self.context();c['pins']['original']='wrong'
        with self.assertRaisesRegex(ValueError,'original_result_binding'):g.bind_context(c,b,p)
        c,b,p=self.context();p['candidate_sha256']='wrong'
        with self.assertRaisesRegex(ValueError,'offline_proof_binding'):g.bind_context(c,b,p)

    def package(self):
        before={'config.bin':b'config',g.NAME:b'old'}
        before.update({f'model{i}.p3d':b'unmodified' for i in range(200)})
        after=before.copy();after[g.NAME]=b'new'
        return {'prefix':'baltic_stream_pilot'},before,after

    def test_exact_package(self):
        p,a,b=self.package();r=g.old.package_identity(p,a,p,b,b'new')
        self.assertEqual(r['unchanged_model_entries'],200)

    def test_package_reordered_or_other_entry_changed(self):
        p,a,b=self.package();b=dict(reversed(list(b.items())))
        with self.assertRaises(ValueError):g.old.package_identity(p,a,p,b,b'new')
        p,a,b=self.package();b['config.bin']=b'changed'
        with self.assertRaises(ValueError):g.old.package_identity(p,a,p,b,b'new')

def pair_fixture():
    ml,geo=prism();m2,g2=prism()
    for p in m2.points:p.coords=(p.coords[0]+5,p.coords[1],p.coords[2])
    for f in m2.selections['Component0001'].faces:
        for v in f.vertices:v.point_index+=6
    for p in g2.vertices:p.x+=5
    for f in g2.faces:f.vertex_indices=[v+6 for v in f.vertex_indices]
    ml.points=ml.points+m2.points;ml.selections['Component0002']=m2.selections['Component0001']
    geo.vertices+=g2.vertices;geo.faces+=g2.faces
    geo.named_selections.append(N(name='component0002',selected_vertices=list(range(6,12)),selected_faces=list(range(8,16))))
    geo.vertex_raw=g.old.xyz(geo.vertices).astype('<f4').tobytes()
    geo.normal_raw=bytes(12*4);geo.normals=[(0.,1.,0.)]*12
    for k,v in vars(lod()).items():
        if k not in ('vertices','resolution'):setattr(geo,k,v)
    geo.resolution=1e13;geo.b_radius=5.;geo.b_center=N(x=0.,y=0.,z=0.);geo.face_area=float('nan')
    visual=lod();memory=lod();memory.resolution=1e15;road=lod();road.resolution=3e15
    road.faces=[];road.sections=[];road.textures=[];road.materials=[];road.named_selections=[];road.proxies=[]
    od=N(version=71,model_info=N(bounding_center=N(x=0.,y=0.,z=0.),mass=1.,center_of_mass=(0.,0.,0.),inv_inertia=(1.,1.,1.)),lod_errors=[],lods=[visual,geo,memory,road])
    fs=[list(sel.faces)[0] for sel in ml.selections.values()]
    for f in fs:f.material='bed'
    mlods=[N(points=ml.points,faces=fs),ml,None,None]
    return od,mlods

class PairGate(unittest.TestCase):
    def setUp(self):
        self.control,self.mlod=pair_fixture();self.baseline=copy.deepcopy(self.control);self.candidate=copy.deepcopy(self.control)
        self.patch=mock.patch.multiple(g,EXPECTED_COUNTS=(12,16,2),EXPECTED_SELECTED_VERTICES=6);self.patch.start();self.addCleanup(self.patch.stop)

    def verify(self,selected=None):
        return g.verify_pair(self.baseline,self.control,self.candidate,self.mlod,self.mlod,IDENTITY,[0.,0.,0.],[dict(id=700,x=.25,z=.25)],['Component0001'] if selected is None else selected)

    def test_complete_pair_route(self):
        r=self.verify();self.assertEqual(r['status'],'COMPILED_B3_CONDITIONAL');self.assertTrue(all(r['overlay']['checks'].values()))

    def test_protected_visual_memory_roadway_and_uv(self):
        for i in (0,2,3):
            self.candidate=copy.deepcopy(self.control);self.candidate.lods[i].uv=[(0.,0.)]
            with self.subTest(lod=i),self.assertRaisesRegex(g.Inconclusive,'protected_lod_changed'):self.verify()

    def test_protected_water_material(self):
        self.candidate.lods[0].material='other-water'
        with self.assertRaisesRegex(g.Inconclusive,'protected_lod_changed'):self.verify()

    def test_unknown_geometry_null_field(self):
        self.candidate.lods[1].new_field=None
        with self.assertRaisesRegex(g.Inconclusive,'geometry_metadata_changed'):self.verify()

    def test_nonselected_point_changed(self):
        b=self.candidate.lods[1];b.vertices[6].y=.125;b.vertex_raw=g.old.xyz(b.vertices).astype('<f4').tobytes()
        with self.assertRaisesRegex(g.Inconclusive,'nonselected_compiled_data_changed'):self.verify()

    def test_selected_domain_not_complete(self):
        with self.assertRaisesRegex(g.Inconclusive,'selected_vertex_domain'):self.verify([])

    def test_wrong_winding_control_is_inconclusive(self):
        self.baseline.lods[1].faces[0].vertex_indices.reverse();self.control=copy.deepcopy(self.baseline)
        with self.assertRaisesRegex(g.Inconclusive,'control_source_geometry'):self.verify()

    def test_failure_retains_geometric_residual(self):
        ml,geo=prism();geo.vertices[0].x=.125;geo.vertex_raw=g.old.xyz(geo.vertices).astype('<f4').tobytes()
        with self.assertRaises(ValueError) as e:g.source_faces(ml,geo,np.zeros(3),IDENTITY,np.zeros(3))
        self.assertIn('ulp_m',e.exception.details);self.assertGreater(max(e.exception.details['error_m'].values()),0.)

if __name__=='__main__':unittest.main()
