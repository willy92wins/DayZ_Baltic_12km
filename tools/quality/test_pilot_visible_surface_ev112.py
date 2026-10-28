"""Adversarial fixtures for Visual201 lineage, faces and NPZ/CAP mapping."""
import importlib.util,unittest,types,io,hashlib
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('surface',Path(__file__).with_name('pilot_visible_surface_ev112.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def fixture():
    grid=np.array([[[float(c),.3*float(r),-float(r)] for c in range(3)] for r in range(19)])
    triangles=np.array([[r*3+c,(r+1)*3+c,(r+1)*3+c+1] if side==0 else
                        [r*3+c,(r+1)*3+c+1,r*3+c+1]
                        for r in range(18) for c in range(2) for side in (0,1)])
    water=grid[8:11][:,[0,2]].copy()
    return [grid.reshape(-1,3),triangles,np.arange(3.),grid[8:11].copy(),water,water.copy(),[0.,2.]]

class Faces(unittest.TestCase):
    def setUp(self):
        self.f=np.array([[0.,0,0],[1,0,0],[1,0,1]])
    def test_cycle_and_order(self):
        self.assertTrue(v.equivalence([self.f,np.roll(self.f,1,axis=0)],[self.f,self.f])['exact_oriented_faces'])
    def test_winding_distinguished(self):
        r=v.equivalence([self.f],[self.f[::-1]])
        self.assertTrue(r['exact_faces']); self.assertFalse(r['exact_oriented_faces'])
    def test_multiplicity_not_set(self):
        self.assertFalse(v.equivalence([self.f,self.f],[self.f])['exact_faces'])
    def test_same_vertices_different_diagonal(self):
        p=np.array([[0.,0,0],[1,0,0],[1,0,1],[0,0,1]])
        self.assertFalse(v.equivalence([p[[0,1,2]],p[[0,2,3]]],[p[[0,1,3]],p[[1,2,3]]])['exact_faces'])
    def test_tiny_change_not_rounded_away(self):
        g=self.f.copy();g[1,1]=1e-14
        self.assertFalse(v.equivalence([self.f],[g])['exact_faces'])
    def test_nonfinite_fails(self):
        g=self.f.copy();g[0,1]=np.nan
        with self.assertRaisesRegex(ValueError,'invalid_face'):v.key(g)
    def test_material_and_texture_both_required(self):
        self.assertEqual(v.visual_role(v.BED_MAT,v.BED_TEX),'bed')
        self.assertEqual(v.visual_role(v.BED_MAT,'wrong.paa'),'unknown')
        self.assertEqual(v.visual_role('',v.BED_TEX),'unknown')
        self.assertEqual(v.visual_role('',''),'unknown')

class Mapping(unittest.TestCase):
    def test_caps_not_in_npz_but_mapped(self):
        result=v.strip_mapping(*fixture())
        self.assertEqual(result[0].shape,(19,3,3))
        self.assertEqual(dict(zip(*np.unique(result[5],return_counts=True))),{'BODY':8,'CAP_START':32,'CAP_END':32})
        self.assertTrue(all(not c['retrograde'] for c in result[6]))
    def test_body_mismatch_rejected(self):
        x=fixture();x[3][0,0,1]+=.001
        with self.assertRaisesRegex(ValueError,'npz_body_not_source'):v.strip_mapping(*x)
    def test_water_mismatch_rejected(self):
        x=fixture();x[5][0,0,1]+=.001
        with self.assertRaisesRegex(ValueError,'npz_water_not_source'):v.strip_mapping(*x)
    def test_missing_face(self):
        x=fixture();x[1]=x[1][:-1]
        with self.assertRaisesRegex(ValueError,'source_strip_topology'):v.strip_mapping(*x)
    def test_duplicate_face(self):
        x=fixture();x[1][0]=x[1][1]
        with self.assertRaisesRegex(ValueError,'source_strip_topology'):v.strip_mapping(*x)
    def test_different_triangulation_not_same_grid(self):
        x=fixture();x[1][0]=[0,3,1];x[1][1]=[3,4,1]
        with self.assertRaisesRegex(ValueError,'source_strip_topology'):v.strip_mapping(*x)
    def test_cap_retrograde_recorded(self):
        x=fixture();x[0].reshape(19,3,3)[7,:,2]=-9
        result=v.strip_mapping(*x)
        self.assertTrue(result[6][0]['retrograde'])
    def test_unknown_station_rejected(self):
        x=fixture();x[-1]=[.1,2]
        with self.assertRaisesRegex(ValueError,'station_anchor'):v.strip_mapping(*x)
    def test_missing_cap_rows_rejected(self):
        x=fixture();x[0]=x[0][3:]
        with self.assertRaisesRegex(ValueError,'source_strip_size'):v.strip_mapping(*x)
    def test_no_cap_interior_chunk(self):
        x=fixture();grid=x[0].reshape(19,3,3)[8:11]
        tri=x[1][32:40]-24
        water=grid[:,[0,2]]
        arrays=np.zeros((5,3,3));arrays[1:4]=grid
        w=np.zeros((5,2,3));w[1:4]=water
        r=v.strip_mapping(grid.reshape(-1,3),tri,np.arange(5.),arrays,w,water,[1.,3.])
        self.assertTrue(np.all(r[5]=='BODY'));self.assertEqual(r[6],[])

class Coverage(unittest.TestCase):
    def data(self):
        author=[];catalog=[]
        for site,n in v.SITES.items():
            for i in range(n):
                name=f'{site}/{i}.p3d'
                author.append(dict(model=name,site=site))
                catalog.append(dict(name=name,index=len(catalog),group='custom_pilot'))
        return author,catalog,np.arange(201),np.arange(201)
    def test_full_four_sites(self): self.assertEqual(len(v.coverage_guard(*self.data())),201)
    def test_instance_missing(self):
        a,c,ids,mi=self.data()
        with self.assertRaisesRegex(ValueError,'pilot_instance_coverage'):v.coverage_guard(a,c,ids[:-1],mi[:-1])
    def test_duplicate_instance(self):
        a,c,ids,mi=self.data();ids[1]=ids[0]
        with self.assertRaisesRegex(ValueError,'duplicate_instance'):v.coverage_guard(a,c,ids,mi)
    def test_wrong_author_site(self):
        a,c,ids,mi=self.data();a[0]['site']='kit-118'
        with self.assertRaisesRegex(ValueError,'site_coverage'):v.coverage_guard(a,c,ids,mi)
    def test_extra_author(self):
        a,c,ids,mi=self.data();a.append(a[-1])
        with self.assertRaisesRegex(ValueError,'author_coverage'):v.coverage_guard(a,c,ids,mi)

class ReaderBoundary(unittest.TestCase):
    def test_unknown_roadway_retained(self):
        S=types.SimpleNamespace
        points=[S(x=0,y=0,z=0),S(x=1,y=0,z=0),S(x=0,y=0,z=1)]
        visual=S(resolution=0,lod_end_ok=True,proxies=[],vertices=points,faces=[S(vertex_indices=[0,1,2])]*2)
        road=S(resolution=3e15,lod_end_ok=True,proxies=[],vertices=points,faces=[S(vertex_indices=[0,1,2])]*3)
        def sections(lod):
            rows=[dict(material=v.BED_MAT,texture=v.BED_TEX),dict(material=v.WATER_MAT,texture=v.WATER_TEX)] if lod is visual else [dict(material='',texture=v.BED_ROAD),dict(material='',texture=v.WATER_ROAD),dict(material='',texture='unexpected.paa')]
            return np.arange(len(rows)),rows
        helper=S(select_lods=lambda r:(0,1),sections=sections,transform=lambda p,m:p)
        groups,ids,ss=v.odol_faces(S(lod_errors=[],resolutions=[0,3e15],lods=[visual,road]),helper,np.zeros(12))
        self.assertEqual(len(groups['road_unknown']),1)
        self.assertEqual(ids['road_unknown'],[(2,2)])
        self.assertEqual(len(groups['road_water']),1)
    def test_payload_hash_rejected(self):
        spec=importlib.util.spec_from_file_location('helper',Path(__file__).with_name('deployed_surface_inventory_ev112.py'))
        h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
        entry=dict(mime=0,offset=0,size=3)
        with self.assertRaisesRegex(ValueError,'payload_hash'):h.read_payload(io.BytesIO(b'abc'),entry,'0'*64)
        self.assertEqual(h.read_payload(io.BytesIO(b'abc'),entry,hashlib.sha256(b'abc').hexdigest()),b'abc')
    def test_source_row_indices_explicit(self):
        r=v.strip_mapping(*fixture())
        self.assertEqual(r[7:],(0,8,8))

if __name__=='__main__':unittest.main()
