import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
import road_b2_recipe_ev112 as r
ROOT=Path('E:/DayZ-Baltic-Build/shape-repair-20261025/road-b2-recipe-inputs-r1-20261029')
class Recipe(unittest.TestCase):
    def setUp(self):self.recipe=r.read(ROOT/'recipe.json');self.fixture=r.read(ROOT/'fixtures.json')
    def test_closed_form_literals(self):self.assertEqual(len(r.fixtures(self.recipe,self.fixture)['distinctions']),6)
    def test_literal_not_generated(self):
        self.fixture['provenance']='GENERATED'
        with self.assertRaisesRegex(ValueError,'provenance'):r.fixtures(self.recipe,self.fixture)
    def test_literal_wrong_axis(self):
        self.fixture['expected'][1][0][0]=302
        with self.assertRaisesRegex(ValueError,'fixture_mismatch'):r.fixtures(self.recipe,self.fixture)
    def test_transpose_matrix(self):
        self.recipe['instances'][1]['matrix']=np.array(self.recipe['instances'][1]['matrix']).T.tolist()
        with self.assertRaisesRegex(ValueError,'fixture_mismatch'):r.fixtures(self.recipe,self.fixture)
    def test_bad_rotation(self):
        self.recipe['instances'][1]['matrix'][0][2]=2
        with self.assertRaisesRegex(ValueError,'rotation'):r.fixtures(self.recipe,self.fixture)
    def test_finite(self):
        self.recipe['instances'][1]['translation'][0]=float('nan')
        with self.assertRaisesRegex(ValueError,'frame'):r.fixtures(self.recipe,self.fixture)
    def test_no_ids_assigned(self):
        self.recipe['instances'][0]['id']=7
        with self.assertRaisesRegex(ValueError,'not_placed'):r.predict(self.recipe,self.fixture)
    def test_hash_changed(self):
        self.recipe['instances'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'face_pin'):r.fixtures(self.recipe,self.fixture)
    def test_derivation_binding(self):
        self.recipe['derivation_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'derivation_pin'):r.predict(self.recipe,self.fixture)
    def test_shift_center_breaks_literals(self):
        with tempfile.TemporaryDirectory() as t:
            row=self.recipe['instances'][0];m=r.read(row['faces']);m['bounding_center'][2]+=1
            p=Path(t)/'m.json';p.write_text(json.dumps(m));row.update(faces=str(p),sha256=r.sha(p))
            with self.assertRaisesRegex(ValueError,'fixture_mismatch'):r.fixtures(self.recipe,self.fixture)
    def test_missing_roadway(self):
        with tempfile.TemporaryDirectory() as t:
            row=self.recipe['instances'][0];m=r.read(row['faces']);m['lods']=[x for x in m['lods'] if x['role']=='Visual']
            p=Path(t)/'m.json';p.write_text(json.dumps(m));row.update(faces=str(p),sha256=r.sha(p))
            with self.assertRaisesRegex(ValueError,'required_roles'):r.predict(self.recipe,self.fixture)
    def test_complete_masks_not_box_width(self):
        report,private=r.predict(self.recipe,self.fixture)
        self.assertEqual(report['status'],'RECIPE_HYPOTHESES_READY');self.assertEqual(len(private),24)
        for p in report['footprints']:self.assertEqual(p['usable_width'],'UNDETERMINED')
        # Independent B0 area measurements for straight pieces; no clipping to 8m.
        for p in report['footprints']:
            if p['instance']=='straight_identity':self.assertAlmostEqual(p['area_m2'],300,places=4)
            if p['instance']=='straight_90':self.assertAlmostEqual(p['area_m2'],225,places=4)
        curve=next(x for x in report['footprints'] if x['instance']=='curve_90' and x['hypothesis']=='raw_row' and x['role']=='Visual')
        b=curve['bounds_for_extent_only'];self.assertGreater((b[2]-b[0])*(b[3]-b[1]),curve['area_m2'])
        self.assertIn('Accesses and connections',report['not_observed'])
        # New curve area metric only: polygon displacement bound from this
        # footprint's measured float32 ULP. Existing straight checks unchanged.
        for p in report['footprints']:
            if p['instance']=='curve_90':
                self.assertLessEqual(abs(p['area_m2']-209.4229046319747),p['perimeter_m']*p['world_ulp_m']+4*p['world_ulp_m']**2)
    def test_all_face_materials_preserved(self):
        _,private=r.predict(self.recipe,self.fixture)
        for row in self.recipe['instances']:
            model=r.read(row['faces'])
            for lod in model['lods']:
                original=[(f['face'],f['material'],f['texture'],f['vertex_indices']) for f in lod['faces']]
                for p in private:
                    if p['instance']==row['name'] and p['role']==lod['role']:
                        self.assertEqual(original,[(f['face'],f['material'],f['texture'],f['vertex_indices']) for f in p['faces']])
if __name__=='__main__':unittest.main()
