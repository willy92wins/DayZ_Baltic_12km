"""Verify a complete bounded Baltic delta engine log against frozen points."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def verify(text, reference):
    failures=[];queries={};begin=[];end=[];tour_end=[];headers=0
    for raw in text.splitlines():
        parts=raw.strip().split(';')
        if parts[0]=='BALTIC_V30_DELTA_V1': headers+=int(parts==['BALTIC_V30_DELTA_V1','BalticTrial'])
        elif parts[0] in ('QBEGIN','QEND','END'):
            try:
                assert len(parts)==2
                value=int(parts[1])
                if parts[0]=='QBEGIN' and (headers!=1 or begin or queries or end): failures.append('Query begin order')
                if parts[0]=='QEND' and (not begin or end or len(queries)!=value): failures.append('Query end order')
                if parts[0]=='END' and (not end or tour_end): failures.append('Tour end order')
                {'QBEGIN':begin,'QEND':end,'END':tour_end}[parts[0]].append(value)
            except (AssertionError,ValueError): failures.append('Malformed terminal: '+raw)
        elif parts[0]=='FAIL': failures.append(raw)
        elif parts[0]=='Q':
            try:
                assert len(begin)==1 and not end and not tour_end
                assert len(parts)==9
                ident=int(parts[1]); ground=float(parts[2])
                assert parts[3] in ('true','false') and parts[4] in ('true','false')
                values=[ground]+[float(v) for v in parts[5:]]
                assert all(math.isfinite(v) for v in values)
                assert ident not in queries
                queries[ident]=dict(ground=ground,sea=parts[3]=='true',pond=parts[4]=='true',surface=values[1],dynamic=values[2],sea_min=values[3],sea_max=values[4])
            except (AssertionError,ValueError): failures.append('Malformed, duplicate or nonfinite query: '+raw)
    expected={p['id']:p for p in reference['points']};n=reference['query_count'];limits=reference['limits']
    if len(expected)!=n or len(reference['points'])!=n: failures.append('Invalid reference identity/count')
    if headers!=1 or begin!=[n] or end!=[n] or tour_end!=[3]:failures.append('Missing, duplicate or incorrect header/terminal')
    if set(queries)!=set(expected): failures.append('Query identity/coverage mismatch')
    max_error=0.;min_nominal=float('inf');min_dynamic=float('inf');min_dry=float('inf')
    for ident in sorted(set(queries)&set(expected)):
        q=queries[ident];p=expected[ident]
        error=abs(q['ground']-p['expected_ground_m']);max_error=max(max_error,error)
        if error>limits['height_error_m']:failures.append(f'Height mismatch {ident}: {error}')
        if abs(q['sea_min']-limits['sea_min_m'])>.001 or abs(q['sea_max']-limits['sea_max_m'])>.001:failures.append(f'Sea range {ident}')
        if p['kind']=='water':
            nominal=q['sea_min']-q['ground'];min_nominal=min(min_nominal,nominal);min_dynamic=min(min_dynamic,q['dynamic'])
            if nominal<limits['nominal_min_depth_m']:failures.append(f'Shallow nominal water {ident}: {nominal}')
            if not (q['sea'] or q['pond']) or q['dynamic']<=0:failures.append(f'Water classification/depth {ident}')
            if not (q['sea_min']-.01<=q['surface']<=q['sea_max']+.01):failures.append(f'Unexpected water surface {ident}')
        elif p['kind']=='dry':
            margin=q['ground']-q['sea_max'];min_dry=min(min_dry,margin)
            if margin<limits['dry_freeboard_m'] or q['sea'] or q['pond'] or q['dynamic']>0:failures.append(f'Wet dry control {ident}')
        else: failures.append(f'Unknown reference kind {ident}')
    return dict(status='PASS_ENGINE_QUERIES' if not failures else 'FAIL',queries=len(queries),expected=n,
        max_height_error_m=max_error,min_nominal_depth_m=None if not math.isfinite(min_nominal) else min_nominal,
        min_dynamic_depth_observed_m=None if not math.isfinite(min_dynamic) else min_dynamic,
        min_dry_freeboard_m=None if not math.isfinite(min_dry) else min_dry,fail_count=len(failures),failures=failures[:40],
        limits=['Pointwise engine readback only; not physical boat traversal, continuous dynamic wave envelope, visual or navmesh acceptance.'])


def controls():
    ref=dict(query_count=3,points=[dict(id=0,kind='water',expected_ground_m=-2.55),dict(id=1,kind='water',expected_ground_m=-4.),dict(id=2,kind='dry',expected_ground_m=1.4)],
        limits=dict(height_error_m=.02,sea_min_m=.5,sea_max_m=1.,nominal_min_depth_m=2.99,dry_freeboard_m=.25))
    good='BALTIC_V30_DELTA_V1;BalticTrial\nQBEGIN;3\nQ;0;-2.55;true;false;0.8;3.3;0.5;1\nQ;1;-4;true;false;0.8;4.7;0.5;1\nQ;2;1.4;false;false;0.8;-0.6;0.5;1\nQEND;3\nEND;3\n'
    assert verify(good,ref)['status']=='PASS_ENGINE_QUERIES'
    bad=dict(missing_query=good.replace('Q;1;-4;true;false;0.8;4.7;0.5;1\n',''),duplicate_query=good.replace('QEND;3','Q;0;-2.55;true;false;0.8;3.3;0.5;1\nQEND;3'),
      no_query_end=good.replace('QEND;3',''),no_tour_end=good.replace('\nEND;3\n','\n'),wrong_count=good.replace('QBEGIN;3','QBEGIN;2'),
      wrong_world=good.replace('BalticTrial','ChernarusPlus'),wrong_height=good.replace('Q;1;-4;','Q;1;-3;'),nonfinite=good.replace('Q;1;-4;','Q;1;nan;'),
      water_absent=good.replace('Q;0;-2.55;true;false','Q;0;-2.55;false;false'),dry_flood=good.replace('Q;2;1.4;false;false','Q;2;1.4;true;false'),
      invalid_surface=good.replace('Q;0;-2.55;true;false;0.8','Q;0;-2.55;true;false;8'),sea_drift=good.replace(';0.5;1',';0.3;1'),
      negative_wet_depth=good.replace(';3.3;',';-3.3;'),truncated=good.split('QEND;')[0],
      premature_query_end=good.replace('QEND;3\n','').replace('Q;0;','QEND;3\nQ;0;'),
      premature_tour_end=good.replace('\nEND;3\n','\n').replace('Q;0;','END;3\nQ;0;'))
    for name,log in bad.items():assert verify(log,ref)['status']=='FAIL',name
    shallow=json.loads(json.dumps(ref));shallow['points'][0]['expected_ground_m']=-2.
    assert verify(good.replace('Q;0;-2.55;','Q;0;-2;'),shallow)['status']=='FAIL'
    return dict(status='PASS_UNIT_CONTROLS',positive='Three independent analytic point values; synthetic, not a runtime claim.',negative_count=len(bad)+1,negative_names=list(bad)+['shallow_with_matching_reference'])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--log',type=Path);ap.add_argument('--reference',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--controls',action='store_true');a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh evidence path required')
    if a.controls:result=controls()
    else:
        if not a.log or not a.reference:raise ValueError('Log and frozen reference required')
        result=verify(a.log.read_text(encoding='utf-8-sig'),json.loads(a.reference.read_text()))
        result['inputs']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.log,a.reference,Path(__file__)]}
    a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(0 if result['status'].startswith('PASS') else 1)


if __name__=='__main__':main()
