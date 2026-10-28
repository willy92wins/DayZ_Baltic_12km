from pathlib import Path
import math,struct,sys,unittest
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parent))
import road_consumer_discovery_ev112 as d

def lod(points,faces,assignments=None,material_names=('asphalt','gravel')):
    assignments=assignments or [list(range(len(faces)))];sections=[]
    for i,ids in enumerate(assignments):sections.append(NS(texture_index=-1,material_index=i,mat_name='',get_face_indices=lambda fs,ids=ids:ids))
    raw=b''.join(struct.pack('<fff',*p) for p in points)
    return NS(vertices=[NS(x=p[0],y=p[1],z=p[2]) for p in points],vertex_raw=raw,faces=[NS(vertex_indices=f) for f in faces],sections=sections,textures=[],materials=[NS(material_name=n) for n in material_names])

class TestRoadB0(unittest.TestCase):
    def test_two_material_strip(self):
        l=lod([(0,0,0),(4,0,0),(4,0,10),(0,0,10),(6,0,0),(6,0,10)],[[0,1,2,3],[1,4,5,2]],[[0],[1]])
        r=d.faces(l);self.assertEqual(r['face_count'],2);self.assertEqual(r['projection_area_m2'],60);self.assertEqual([m['area_m2'] for m in r['material_masks']],[40,20]);self.assertEqual(r['faces'][1]['material'],'gravel')
    def test_curve_bbox_is_not_width(self):
        l=lod([(0,0,0),(2,0,0),(2,0,8),(8,0,8),(8,0,10),(0,0,10)],[[0,1,2],[0,2,5],[2,3,4,5]])
        r=d.faces(l);self.assertEqual(r['projection_area_m2'],32);self.assertNotIn('usable_width',r);self.assertEqual(d.discovery_fields(True)['usable_width'],'UNKNOWN')
    def test_shifted_pivot_raw_preserved(self):
        l=lod([(100,3,0),(104,3,0),(104,3,10),(100,3,10)],[[0,1,2,3]])
        r=d.faces(l);self.assertEqual(r['faces'][0]['xyz'][0],[100,3,0]);self.assertEqual(d.discovery_fields(True)['pivot_convention'],'UNKNOWN')
    def test_vertical_face_retained(self):
        l=lod([(0,0,0),(0,3,0),(0,3,4),(0,0,4)],[[0,1,2,3]])
        r=d.faces(l);self.assertEqual(r['face_count'],1);self.assertEqual(r['degenerate_projection_faces'],1);self.assertEqual(r['projection_area_m2'],0)
    def test_overlap_union_not_sum(self):
        l=lod([(0,0,0),(4,0,0),(4,0,10),(0,0,10)],[[0,1,2,3],[0,1,2,3]])
        self.assertEqual(d.faces(l)['projection_area_m2'],40)
    def test_raw_mismatch(self):
        l=lod([(0,0,0),(1,0,0),(0,0,1)],[[0,1,2]]);l.vertices[0].x=1
        with self.assertRaisesRegex(ValueError,'raw_decoded'):d.faces(l)
    def test_missing_section(self):
        l=lod([(0,0,0),(1,0,0),(0,0,1)],[[0,1,2]]);l.sections=[]
        with self.assertRaisesRegex(ValueError,'unassigned'):d.faces(l)
    def test_duplicate_assignment(self):
        l=lod([(0,0,0),(1,0,0),(0,0,1)],[[0,1,2]],[[0],[0]])
        with self.assertRaisesRegex(ValueError,'overlapping'):d.faces(l)
    def test_bad_index(self):
        l=lod([(0,0,0),(1,0,0),(0,0,1)],[[0,1,3]])
        with self.assertRaisesRegex(ValueError,'face_indices'):d.faces(l)
    def test_nonfinite(self):
        l=lod([(math.nan,0,0),(1,0,0),(0,0,1)],[[0,1,2]])
        with self.assertRaisesRegex(ValueError,'nonfinite'):d.faces(l)
    def test_missing_roadway(self):
        r=d.discovery_fields(False);self.assertIs(r['roadway_present'],False);self.assertEqual(r['usable_width'],'UNKNOWN');self.assertEqual(d.status([r]),'INCONCLUSIVE_DISCOVERY')
    def test_unknown_and_missing_field(self):
        r=d.discovery_fields(True);self.assertEqual(d.status([r]),'INCONCLUSIVE_DISCOVERY');del r['consumer_observed']
        with self.assertRaisesRegex(ValueError,'missing_discovery'):d.status([r])
    def test_no_default_zero_width(self):
        r=d.discovery_fields(True);r['usable_width']=0
        with self.assertRaisesRegex(ValueError,'invalid_width'):d.status([r])
    def test_empty_and_nonbool(self):
        with self.assertRaisesRegex(ValueError,'empty'):d.status([])
        with self.assertRaisesRegex(ValueError,'boolean'):d.discovery_fields(None)
    def test_boolean_width_and_bad_consumer(self):
        r=d.discovery_fields(True);r['usable_width']=True
        with self.assertRaisesRegex(ValueError,'invalid_width'):d.status([r])
        r=d.discovery_fields(True);r['consumer_observed']='WRP'
        with self.assertRaisesRegex(ValueError,'invalid_consumer'):d.status([r])
    def test_width_without_roadway(self):
        r=d.discovery_fields(False);r['usable_width']=4
        with self.assertRaisesRegex(ValueError,'width_without_roadway'):d.status([r])
    def test_known_requires_source(self):
        r=d.discovery_fields(True);r['consumer_observed']='WRP_OBJECT'
        with self.assertRaisesRegex(ValueError,'missing_source'):d.status([r])
        r['source_evidence']=[dict(path='synthetic.wrp',offset=100,sha256='a'*64)]
        self.assertEqual(d.status([r]),'INCONCLUSIVE_DISCOVERY')
    def test_bad_crossing_type(self):
        r=d.discovery_fields(True);r['crossings_exact']=1
        with self.assertRaisesRegex(ValueError,'invalid_crossings'):d.status([r])
    def test_bowtie_is_explicit_unknown_area(self):
        l=lod([(0,0,0),(2,0,2),(0,0,2),(2,0,0)],[[0,1,2,3]])
        r=d.faces(l);self.assertEqual(r['faces'][0]['projection'],'INVALID_PROJECTION');self.assertFalse(r['projection_complete']);self.assertEqual(r['invalid_projection_faces'],1)
    def test_no_visual_not_complete(self):
        with self.assertRaisesRegex(ValueError,'no_visual'):d.visual_coverage([dict(role='Roadway',projection_complete=True)])
        self.assertFalse(d.visual_coverage([dict(role='Visual',projection_complete=False)]))
    def test_exact_installed_prefix(self):
        d.check_prefix('DZ\\structures\\roads')
        for bad in ('dz\\structures\\roads','DZ\\structures\\road',None):
            with self.assertRaisesRegex(ValueError,'prefix'):d.check_prefix(bad)
    def test_rc2_valid_and_error_not_accepted(self):
        receipt=dict(returncode=2,stop_reason=None,seconds=1,peak_sampled_tree_rss_bytes=100)
        report=dict(status='INCONCLUSIVE_DISCOVERY',models=[1,2,3]);d.accept_run_receipt(receipt,report)
        with self.assertRaisesRegex(ValueError,'invalid_discovery'):d.accept_run_receipt(receipt,dict(report,error='prefix'))
        with self.assertRaisesRegex(ValueError,'exit_status'):d.accept_run_receipt(dict(receipt,returncode=0),report)
        with self.assertRaisesRegex(ValueError,'resource'):d.accept_run_receipt(dict(receipt,stop_reason='timeout'),report)
        with self.assertRaisesRegex(ValueError,'resource'):d.accept_run_receipt(dict(receipt,seconds=121),report)
        with self.assertRaisesRegex(ValueError,'resource'):d.accept_run_receipt(dict(receipt,peak_sampled_tree_rss_bytes=2*1024**3+1),report)
        with self.assertRaisesRegex(ValueError,'invalid_discovery'):d.accept_run_receipt(receipt,dict(report,models=[1,2]))
    def test_receipt_process_and_command_binding(self):
        r=dict(observed_processes={'12@1.5':{},'13@1.6':{}});running=dict(command=['python','output'],pid=12,create_time=1.5)
        d.bind_execution_receipt(r,running,['python','output'],13)
        with self.assertRaisesRegex(ValueError,'running_command'):d.bind_execution_receipt(r,running,['python','old-output'],13)
        with self.assertRaisesRegex(ValueError,'running_identity'):d.bind_execution_receipt(r,dict(running,create_time=1.4),['python','output'],13)
        with self.assertRaisesRegex(ValueError,'report_identity'):d.bind_execution_receipt(r,running,['python','output'],17)

if __name__=='__main__':unittest.main()
