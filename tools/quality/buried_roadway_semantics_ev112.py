"""Bounded diagnostic of a previously unmeasured native-query domain."""
from pathlib import Path
import collections,hashlib,math,sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'water'))
from eval_visual_probe_v31 import parse

def require(ok,why):
    if not ok:raise ValueError(why)

def verify_frozen(mapping):
    for path,digest in mapping.items():
        with Path(path).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        require(actual==digest,'input_drift:'+path)

def verify_package_set(expected,actual):
    norm=lambda d:{str(Path(p).resolve()).casefold():h for p,h in d.items()}
    require(norm(actual)==norm(expected),'package_binding')
    verify_frozen(expected)

def observe(points,rows):
    require(len(points)==16 and {p['id'] for p in points}==set(range(16)),'sample_universe')
    require(collections.Counter(p['group'] for p in points)=={'buried_changed':4,'buried_unchanged':4,'exposed_unchanged':8},'sample_strata')
    require(set(rows)==set(range(16)),'measurement_universe')
    result=[];failures=[];inconclusive=[]
    for p in points:
        r=rows[p['id']];why=[]
        require(all(math.isfinite(p[k]) for k in ('x','z','ground','bed')),'nonfinite_expectation')
        buried=p['group'].startswith('buried')
        require(p['ground']-p['bed']>.08 if buried else p['bed']-p['ground']>.08,'nonseparating_predictions')
        if abs(r['ground']-p['ground'])>.01:why.append('ground_disagrees')
        if r['sea'] or r['pond'] or r['depth']>0:why.append('dry_control_has_water')
        h=abs(r['road']-p['ground'])<=.03;b=abs(r['road']-p['bed'])<=.03
        classification='GROUND' if h and not b else 'BED' if b and not h else 'INCONCLUSIVE'
        if not buried:
            if classification!='BED':why.append('exposed_roadway_disagrees')
            if not r['rv'] or 'baltic_stream_pilot\\cs_kit_118_0000.p3d' not in r['rv_shapes'] or abs(r['rv_pos'][1]-p['bed'])>.03:why.append('exposed_RV_control_failed')
        if classification=='INCONCLUSIVE':inconclusive.append(p['id'])
        if why:failures.append(dict(id=p['id'],reasons=why))
        result.append(dict(id=p['id'],group=p['group'],roadway=classification,expected_ground=p['ground'],expected_bed=p['bed'],measured=r))
    return dict(status='FAIL_DIAGNOSTIC_CONTROLS' if failures else 'INCONCLUSIVE_SEMANTICS' if inconclusive else 'SEMANTICS_OBSERVED_AT_SAMPLES',count=len(result),failures=failures,inconclusive=inconclusive,observed_by_group={group:dict(collections.Counter(x['roadway'] for x in result if x['group']==group)) for group in sorted({p['group'] for p in points})},rows=result,limits=['Only16selected samples, no global native or visual acceptance.','No Bullet collision acceptance without fresh vanilla margin calibration.','Buried Roadway classification is evidence for a later validator contract, not a preselected pass condition.'])
