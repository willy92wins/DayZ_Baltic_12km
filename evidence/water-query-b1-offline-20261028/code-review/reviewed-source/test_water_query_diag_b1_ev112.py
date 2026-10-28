"""Analytic external log fixtures and deliberate corruption, not native acceptance."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import water_query_diag_b1_ev112 as d


def inputs():
    # Analytic scene: H=10, solid B=12, static water=11 and fake surface=11.1.
    rows = []
    for i in range(2658):
        p = dict(id=i, x=8200.+i*.125, z=9000., ground=10., roadway=12., effective_bed=12., water_ext=11., expect='wet')
        states = {k:'PASS' for k in d.STATE_KEYS}
        if 47 <= i < 94:
            states['water'] = 'FAIL'
        elif 94 <= i < 115:
            states['water'] = 'INCONCLUSIVE'
        rows.append(dict(id=i, expected=p, states=states))
    orig = dict(status='FAIL', points=2658, rows=rows, failures=[dict(id=i, channel='water') for i in range(47,94)], inconclusive=[dict(id=i, channel='water') for i in range(94,115)])
    selected = [dict(id=r['id'], expected=copy.deepcopy(r['expected']), original_states=dict(r['states'])) for r in rows[:115]]
    return selected, orig


def log_fixture():
    # Literal analytic values: do not call the production origin or CSV generator.
    lines = ['BALTIC_WATER_QUERY_B1;BalticTrial', 'BEGIN;115;3']
    for rnd in range(3):
        for ident in range(115):
            x = 8200.+ident*.125
            clock = 10000+(rnd*115+ident)*200
            fields = ['Q',str(rnd),str(ident),str(clock),str(clock),'0.1','0.1',f'<{x}, 10, 9000>','10','12','false','true','1',f'<{x}, 10.01, 9000>',f'<{x}, 12.01, 9000>',f'<{x}, 12.25, 9000>',f'<{x}, 110, 9000>',f'<{x}, 14, 9000>','11','11.1','11','11.1','1.09','-0.91','-1.15','false']
            lines.append(';'.join(fields))
            lines.append(f'O;{rnd};{ident};0;true;fixture/tree.p3d;<8000, 10, 8900>')
            for index,(sx,sz) in enumerate(((2400,7000),(2430,7020),(2410,7040))):
                lines.append(f'S;{rnd};{ident};{index};<{sx}, 100, {sz}>;true;false;0.75;0.85;<{sx}, 1, {sz}>;-0.15')
    return '\n'.join(lines+['END;345'])+'\n'


class B1ContractTests(unittest.TestCase):
    def setUp(self):
        self.selected,self.orig=inputs()
        self.points=d.source_points(self.selected,self.orig)
        self.log=log_fixture()

    def mutated(self,index,value,line=2):
        lines=self.log.splitlines();fields=lines[line].split(';');fields[index]=value;lines[line]=';'.join(fields)
        return '\n'.join(lines)+'\n'

    def report(self,log=None,points=None):
        pts=points or self.points
        return d.evaluate(pts,d.parse(log or self.log,pts))

    def test_complete_345_analytic_residuals_preserve_failure(self):
        r=d.consume(self.log,d.csv_for(self.points),self.selected,self.orig)
        self.assertEqual(r['rows'],345)
        self.assertEqual(r['status'],'CAPTURE_COMPLETE_DIAGNOSTIC_ONLY')
        self.assertEqual(r['original_native_verdict'],'FAIL')
        self.assertEqual(r['details'][47]['original_states']['water'],'FAIL')
        self.assertEqual(r['product_reference'],'INCONCLUSIVE_PRODUCT_REFERENCE')
        self.assertTrue(all(abs(v)<1e-12 for v in r['details'][0]['depth_surface_residuals']['fake_high']))
        self.assertTrue(all(abs(v-.1)<1e-12 for v in r['details'][0]['depth_surface_residuals']['nf_high']))
        self.assertEqual(r['details'][0]['measured']['depths'],[1.09,-.91,-1.15])

    def test_invalid_boolean(self):
        with self.assertRaisesRegex(ValueError,'boolean'):d.parse(self.mutated(10,'1'),self.points)

    def test_bad_vectors(self):
        for value in ('<8200,10>','8200 10 9000','<8200,10,nan>'):
            with self.subTest(value=value),self.assertRaises(ValueError):d.parse(self.mutated(7,value),self.points)

    def test_nonfinite_each_numeric_domain(self):
        for column in (5,6,8,9,18,19,20,21,22,23,24):
            for value in ('nan','inf','-inf'):
                with self.subTest(column=column,value=value),self.assertRaises(ValueError):d.parse(self.mutated(column,value),self.points)

    def test_missing_point_duplicate_unknown_id_round_order(self):
        lines=self.log.splitlines()
        for changed in ('\n'.join(lines[:2]+lines[7:]),self.mutated(2,'9999'),self.mutated(1,'3'),'\n'.join(lines[:7]+lines[2:7]+lines[7:]),'\n'.join(lines[:2]+lines[7:12]+lines[2:7]+lines[12:])):
            with self.subTest(),self.assertRaises(ValueError):d.parse(changed,self.points)

    def test_header_counts_footer_trailing_data(self):
        for changed in (self.log.replace('BEGIN;115;3','BEGIN;114;3'),self.log.replace('END;345','END;344'),self.log.replace('END;345',''),self.log+'X\n',self.log.replace(d.HEADER,'OLD_PROBE')):
            with self.subTest(),self.assertRaises(ValueError):d.parse(changed,self.points)

    def test_clock_reversal_rejected(self):
        with self.assertRaisesRegex(ValueError,'clock_order'):d.parse(self.mutated(4,'9999'),self.points)
        with self.assertRaisesRegex(ValueError,'clock_order'):d.parse(self.mutated(3,'9999',line=7),self.points)

    def test_clock_change_is_confounder(self):
        r=self.report(self.mutated(4,'10001'))
        self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC')
        self.assertTrue(r['confounders'])

    def test_phase_change_is_confounder(self):
        self.assertEqual(self.report(self.mutated(6,'0.1001'))['status'],'INCONCLUSIVE_DIAGNOSTIC')

    def test_bad_origin_and_coordinates(self):
        for column,value in ((7,'<8201,10,9000>'),(13,'<8200,10.2,9000>'),(14,'<8200,11,9000>'),(15,'<8200,12.5,9000>'),(16,'<8200,100,9000>'),(17,'<8200,15,9000>')):
            with self.subTest(column=column),self.assertRaises(ValueError):self.report(self.mutated(column,value))

    def test_ground_reference_mismatch_invalidates_whole_capture(self):
        pts=copy.deepcopy(self.points);pts[0]['ground']=10.02
        r=self.report(points=pts)
        self.assertEqual(r['status'],'REFERENCE_MISMATCH')
        self.assertEqual(len(r['reference_mismatches']),3)

    def test_roadway_reference_mismatch(self):
        r=self.report(self.mutated(9,'12.04'))
        self.assertEqual(r['status'],'REFERENCE_MISMATCH')

    def test_uncertain_roadway_never_becomes_pass(self):
        pts=copy.deepcopy(self.points);pts[0]['original_states']['roadway']='INCONCLUSIVE'
        r=self.report(points=pts)
        self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC')
        self.assertEqual(r['details'][0]['original_states']['roadway'],'INCONCLUSIVE')

    def test_round_state_drift(self):
        r=self.report(self.mutated(11,'false',line=2+115*5))
        self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC')
        self.assertTrue(any(c['reason'].startswith('round_state_drift') for c in r['confounders']))

    def test_missing_object_snapshot_or_sea_control(self):
        for removed in (3,4):
            lines=self.log.splitlines();del lines[removed]
            with self.subTest(removed=removed),self.assertRaises(ValueError):d.parse('\n'.join(lines),self.points)

    def test_null_and_empty_shape_confounder(self):
        s=self.log.replace('O;0;0;0;true;fixture/tree.p3d;<8000, 10, 8900>','O;0;0;0;false;;<0, 0, 0>')
        self.assertEqual(self.report(s)['status'],'INCONCLUSIVE_DIAGNOSTIC')
        s=self.log.replace('O;0;0;0;true;fixture/tree.p3d;','O;0;0;0;true;;')
        self.assertEqual(self.report(s)['status'],'INCONCLUSIVE_DIAGNOSTIC')

    def test_sea_control_origin_and_flags(self):
        with self.assertRaisesRegex(ValueError,'sea_origin'):self.report(self.mutated(9,'<2400, 2, 7000>',line=4))
        self.assertEqual(self.report(self.mutated(5,'false',line=4))['status'],'INCONCLUSIVE_DIAGNOSTIC')

    def test_numeric_match_never_identifies_object(self):
        p=dict(water_ext=12.,effective_bed=12.)
        c=d.surface_class(12.,p,12.)
        self.assertEqual(c['label'],'AMBIGUOUS')
        self.assertEqual(c['identity'],'NOT_DETERMINED')
        self.assertEqual(len(c['matches']),3)
        self.assertEqual(d.surface_class(13.,p,10.)['label'],'OTHER')

    def test_low_origin_below_water_ref(self):
        pts=copy.deepcopy(self.points);pts[0]['water_ext']=15.
        rows=d.parse(self.log,pts)
        for r in rows:
            if r['id']==0:r['depth_origins'][2][1]=15.25;r['low_below_ref']=True
        result=d.evaluate(pts,rows)
        self.assertEqual(result['status'],'INCONCLUSIVE_DIAGNOSTIC')
        self.assertTrue(any(c['reason']=='low_origin_below_static_reference' for c in result['confounders']))

    def test_csv_rehashed_wrong_source_rejected(self):
        csv=d.csv_for(self.points)
        with self.assertRaisesRegex(ValueError,'csv_source_binding'):d.check_csv(csv.replace('8200 0 9000','8201 0 9000'),self.points)

    def test_selected_source_relabel_and_coordinate_drift(self):
        for path,value in (('original_states','PASS'),('expected',8201)):
            a=copy.deepcopy(self.selected)
            if path=='original_states':a[47][path]['water']=value
            else:a[0][path]['x']=value
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'source_binding'):d.source_points(a,self.orig)

    def test_float32_csv_preserves_zero_and_missing(self):
        pts=copy.deepcopy(self.points);pts[0]['effective_bed']=0.;pts[0]['water_ext']=None
        self.assertEqual(d.csv_for(pts).splitlines()[0],'0;8200 0 9000;0;0;1;0')


if __name__=='__main__':
    unittest.main()
