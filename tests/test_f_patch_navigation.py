"""Independent geometric and consumer controls for the frozen F navigation unit."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/navigation'))
import prepare_patch_nav_probe_ev112 as prep
from prepare_f_patch_routes_ev112 import touched_cells,dry_clearance,midpoint
from verify_patch_nav_coverage_ev112 import verify_coverage as bound_coverage,F_SHA


def verify_coverage(rb,lb,c,e,f,screen):
    return bound_coverage(rb,lb,c,e,f,screen,hashlib.sha256(screen).hexdigest())


def old_reference():
    return dict(queries=[dict(name=f'old_{i}',start=[60.,2.1,12222.],end=[66.,2.1,12222.],expect='path') for i in range(37)])


def local_reference():
    return dict(status='PREPARED_GEOMETRIC_SCREEN_NOT_NATIVE_ACCEPTANCE',queries=[
        dict(name=name,start=[60.,0.,12222.],end=[66.,0.,12222.],expect='path') for name in sorted(prep.LOCAL_NAMES)])


class ScreenControls(unittest.TestCase):
    def test_horizontal_gridline_covers_both_sides_and_caps(self):
        cells=set(touched_cells((60,12222),(72,12222)))
        self.assertTrue({(9,10),(10,10),(9,9),(10,12)}<=cells)

    def test_vertical_gridline_covers_both_sides(self):
        cells=set(touched_cells((60,12222),(60,12210)))
        self.assertTrue({(10,9),(10,10),(11,9),(11,10)}<=cells)

    def test_diagonal_covers_both_adjacent_cells(self):
        cells=set(touched_cells((60,12222),(72,12210)))
        self.assertTrue({(10,11),(11,10)}<=cells)

    def test_wet_corner_on_previous_unscreened_side_rejected(self):
        e=np.full((32,32),2.);f=e.copy();e[9,10]=.7
        plane=np.full((31,31),np.nan);field=np.zeros((31,31,4))
        self.assertLess(dry_clearance(e,f,plane,field,touched_cells((60,12222),(72,12222))),.05)

    def test_pond_level_and_nonfinite_pond_field(self):
        h=np.full((32,32),2.);plane=np.ones((31,31));field=np.full((31,31,4),1.98)
        self.assertLess(dry_clearance(h,h,plane,field,[(10,10)]),.05)
        field[10,10,0]=np.nan
        self.assertIsNone(dry_clearance(h,h,plane,field,[(10,10)]))
        self.assertIsNone(dry_clearance(h,h,plane,field,[(-1,10)]))

    def test_short_line_has_no_admissible_midpoint(self):
        h=np.zeros((32,32))
        self.assertIsNone(midpoint(h,h+1.,(60,12222),(66,12222)))

    def test_center_threshold_insufficient_when_disk_falls_below_margin(self):
        e=np.zeros((32,32));f=e.copy();f[10,10]=.1;f[9,10]=-.1
        self.assertIsNone(midpoint(e,f,(48,12222),(72,12222)))


class PreparationControls(unittest.TestCase):
    def setUp(self):
        self.h=np.full((32,32),3.);self.old=old_reference();self.local=local_reference()

    def test_exact_counts_and_full_legacy_records_preserved(self):
        self.old['queries'][0]['name']='bridge_test';self.old['queries'][0]['start'][1]=21.
        self.old['queries'][1]['custom']='preserve';before=copy.deepcopy(self.old)
        queries,_=prep.combine_queries(self.old,self.local,self.h)
        self.assertEqual(len(queries),45);self.assertEqual(queries[0]['start'][1],21.)
        self.assertEqual(queries[1]['start'][1],3.1);self.assertEqual(queries[1]['custom'],'preserve')
        self.assertEqual(self.old,before)

    def test_truncated_or_extended_legacy_rejected(self):
        for count in (36,38):
            with self.subTest(count=count):
                old=old_reference();old['queries']=(old['queries']+[dict(name='extra')])[:count]
                with self.assertRaises(ValueError):prep.combine_queries(old,self.local,self.h)

    def test_duplicate_local_names_rejected(self):
        self.local['queries'][-1]=copy.deepcopy(self.local['queries'][0])
        with self.assertRaises(ValueError):prep.combine_queries(self.old,self.local,self.h)

    def test_inconclusive_screen_rejected(self):
        self.local['status']='PREPARATION_INCONCLUSIVE'
        with self.assertRaises(ValueError):prep.combine_queries(self.old,self.local,self.h)

    def test_unexpected_legacy_field_mutation_rejected(self):
        original=prep.retarget
        def corrupt(q,h):
            result,changes=original(q,h);result[0]['expect']='none';return result,changes
        with patch.object(prep,'retarget',side_effect=corrupt):
            with self.assertRaises(ValueError):prep.combine_queries(self.old,self.local,self.h)

    def test_missing_legacy_expectation_preserves_implicit_contract(self):
        del self.old['queries'][0]['expect'];self.old['queries'][1]['name']='negative';del self.old['queries'][1]['expect']
        q,_=prep.combine_queries(self.old,self.local,self.h)
        self.assertNotIn('expect',q[0]);self.assertNotIn('expect',q[1])

    def test_historical_or_opposite_side_markers_rejected(self):
        prep.check_markers('E','baltic_patch_nav_e45.log','BALTIC_PATCH_NAV_E45')
        for name,header in [('baltic_ev112_nav_v9.log','BALTIC_EV112_NAV_V9'),('baltic_patch_nav_f45.log','BALTIC_PATCH_NAV_F45')]:
            with self.assertRaises(ValueError):prep.check_markers('E',name,header)


def evidence(outside=False,wrong_path=False):
    h=np.full((32,32),2.);old=old_reference();local=local_reference()
    if outside:
        for q in local['queries']:
            q['start']=[120.,0.,12162.];q['end']=[126.,0.,12162.]
    queries,_=prep.combine_queries(old,local,h)
    ref=dict(side='F',terrain_sha256=F_SHA,queries=queries,local_query_names=sorted(prep.LOCAL_NAMES),
             header='TEST;BalticTrial',limits=[],max_waypoint_surface_error_m=.8)
    screen=json.dumps(local).encode()
    ref['inputs']=dict(local_routes=dict(sha256=hashlib.sha256(screen).hexdigest()))
    vec=lambda p:'<'+','.join(str(x) for x in p)+'>'
    lines=[ref['header']]
    for q in queries:
        a=q['start'];b=q['end'];pa=[a[0],2.,a[2]];pb=[b[0],2.,b[2]]
        found='false' if wrong_path and q['name'].startswith('f_patch_') else 'true'
        lines.append(';'.join(['Q',q['name'],'true','true',found,'2',vec(a),vec(b),vec(pa),vec(pb)]))
        for index,p in enumerate((pa,pb)):
            lines.append(';'.join(['P',q['name'],str(index),vec(p),vec(p),vec(p)]))
    lines.append('END;45')
    rb=json.dumps(ref).encode();lb=('\n'.join(lines)+'\n').encode()
    consumer=dict(status='PASS_LOCAL_CONTINUITY_NAV_PATHS',log_sha256=hashlib.sha256(lb).hexdigest(),reference_sha256=hashlib.sha256(rb).hexdigest())
    return rb,lb,consumer,h,screen


class CoverageControls(unittest.TestCase):
    def setUp(self):
        self.e=np.full((32,32),2.);self.e[9:12,9:13]=1.8

    def test_real_p_rows_cover_all_eight_local_cases(self):
        rb,lb,c,f,screen=evidence();r=verify_coverage(rb,lb,c,self.e,f,screen)
        self.assertEqual(r['status'],'PASS_F_PATCH_WAYPOINT_COVERAGE');self.assertEqual(len(r['coverage']),8)

    def test_waypoints_outside_patch_inconclusive(self):
        rb,lb,c,f,screen=evidence(outside=True)
        self.assertEqual(verify_coverage(rb,lb,c,self.e,f,screen)['status'],'INCONCLUSIVE_PATCH_NOT_SAMPLED')

    def test_missing_case_is_malformed_not_pass(self):
        rb,lb,c,f,screen=evidence();rows=lb.decode().splitlines()
        lb=('\n'.join(row for row in rows if ';f_patch_ew_1;' not in row)+'\n').encode()
        c['log_sha256']=hashlib.sha256(lb).hexdigest()
        with self.assertRaises(ValueError):verify_coverage(rb,lb,c,self.e,f,screen)

    def test_delta_point_zero_three_is_insufficient(self):
        rb,lb,c,f,screen=evidence();self.e[9:12,9:13]=1.97
        self.assertEqual(verify_coverage(rb,lb,c,self.e,f,screen)['status'],'INCONCLUSIVE_PATCH_NOT_SAMPLED')

    def test_failed_consumer_never_passes_with_valid_delta(self):
        rb,lb,c,f,screen=evidence();c['status']='FAIL_LOCAL_CONTINUITY_NAV_PATHS'
        self.assertEqual(verify_coverage(rb,lb,c,self.e,f,screen)['status'],'FAIL_UPSTREAM_CONSUMER')

    def test_forged_pass_rechecked_against_actual_log(self):
        rb,lb,c,f,screen=evidence(wrong_path=True)
        self.assertEqual(verify_coverage(rb,lb,c,self.e,f,screen)['status'],'FAIL_UPSTREAM_REVALIDATION')

    def test_changed_log_binding_rejected(self):
        rb,lb,c,f,screen=evidence();c['log_sha256']='0'*64
        with self.assertRaises(ValueError):verify_coverage(rb,lb,c,self.e,f,screen)

    def test_local_route_hash_drift_rejected(self):
        rb,lb,c,f,screen=evidence()
        with self.assertRaises(ValueError):verify_coverage(rb,lb,c,self.e,f,screen+b' ')

    def test_moved_reference_xz_rejected_even_if_consumer_rebound(self):
        rb,lb,c,f,screen=evidence();ref=json.loads(rb);ref['queries'][-1]['start'][0]+=1
        rb=json.dumps(ref).encode();c['reference_sha256']=hashlib.sha256(rb).hexdigest()
        with self.assertRaises(ValueError):verify_coverage(rb,lb,c,self.e,f,screen)

    def test_wrong_side_rejected(self):
        rb,lb,c,f,screen=evidence();ref=json.loads(rb);ref['side']='E';rb=json.dumps(ref).encode()
        c['reference_sha256']=hashlib.sha256(rb).hexdigest()
        with self.assertRaises(ValueError):verify_coverage(rb,lb,c,self.e,f,screen)

    def test_ground_from_e_rejected_by_f_consumer(self):
        rb,lb,c,f,screen=evidence();rows=[]
        for row in lb.decode().splitlines():
            fields=row.split(';')
            if fields[0]=='P':
                fields[4]=fields[4].replace(',2.0,',',1.8,')
            rows.append(';'.join(fields))
        lb=('\n'.join(rows)+'\n').encode();c['log_sha256']=hashlib.sha256(lb).hexdigest()
        self.assertEqual(verify_coverage(rb,lb,c,self.e,f,screen)['status'],'FAIL_UPSTREAM_REVALIDATION')


if __name__=='__main__':
    unittest.main()
