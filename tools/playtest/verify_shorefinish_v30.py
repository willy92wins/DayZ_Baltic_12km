"""Check the frozen shore readback fixture; never promote visual/NM acceptance."""
from pathlib import Path
import argparse
import hashlib
import json
import math


def verify(ref, text):
    lines=text.splitlines()
    terminal=ref.get('terminal_record',f'END;{ref["site_count"]}')
    if not lines or lines[0]!=ref['header'] or lines[-1]!=terminal or lines.count(terminal)!=1:
        raise ValueError('Wrong header/world or missing terminal record')
    if lines.count(ref['header'])!=1 or lines.count(f'QBEGIN;{ref["query_count"]}')!=1 or lines.count(f'QEND;{ref["query_count"]}')!=1:
        raise ValueError('Missing/duplicate query boundary')
    begin=lines.index(f'QBEGIN;{ref["query_count"]}');end=lines.index(f'QEND;{ref["query_count"]}')
    if begin>=end:raise ValueError('Query boundaries reversed')
    actual={}
    allowed={'MOVE','READY','SEA','W','STABLE','WX'}
    for line_no,line in enumerate(lines[1:-1],1):
        f=line.split(';')
        if f[0] in ('QBEGIN','QEND'):
            if line not in (f'QBEGIN;{ref["query_count"]}',f'QEND;{ref["query_count"]}'):
                raise ValueError('Unexpected query boundary')
            continue
        if f[0]!='Q':
            if f[0] not in allowed:raise ValueError('Unexpected record '+f[0])
            continue
        field_count=ref.get('query_fields',9)
        if len(f)!=field_count or not begin<line_no<end:raise ValueError('Bad query shape/order')
        ident=int(f[1])
        if ident in actual or f[3] not in ('true','false') or f[4] not in ('true','false'):
            raise ValueError('Duplicate query or invalid boolean')
        values=[float(f[i]) for i in ((2,5,6,7,8,9) if field_count==10 else (2,5,6,7,8))]
        if not all(math.isfinite(v) for v in values):raise ValueError('Nonfinite readback')
        actual[ident]=(values,f[4]=='true')
    if set(actual)!={p['id'] for p in ref['points']}:raise ValueError('Frozen point coverage differs')
    checks=[]
    for p in ref['points']:
        values,pond_flag=actual[p['id']]
        ground,surface,depth,sea_min,sea_max=values[:5]
        error=abs(ground-p['expected_ground_m'])
        row=dict(id=p['id'],kind=p['kind'],height_error_m=error,
                 height_ok=error<=ref['tolerances']['height_m'],
                 sea_envelope_ok=abs(sea_min-.5)<=.02 and abs(sea_max-1.)<=.02)
        if len(values)==6:
            row['sea_now_m']=values[5]
            row['sea_now_ok']=sea_min-.02<=values[5]<=sea_max+.02
        if p['kind']=='wet':
            plane=p['pond_plane_m']
            low=sea_min if plane is None else max(sea_min,plane)
            high=sea_max if plane is None else max(sea_max,plane)
            tol=ref['tolerances']['water_plane_m']
            row['water_surface_ok']=low-tol<=surface<=high+tol
            row['positive_depth']=depth>0
            # A low pond may be hidden by global sea. Neither positive depth
            # nor a level inside the sea envelope proves that pond exists.
            # Do not turn an absent pond flag into a physical FAIL: retain an
            # inconclusive presence result until the engine distinguishes it.
            row['pond_presence_unresolved']=plane is not None and plane<=sea_max+tol and not pond_flag
        elif p['kind']=='dry':
            row['dry_depth_ok']=depth<=ref['tolerances']['dry_depth_max_m']
        elif p['kind']!='transition':raise ValueError('Unknown frozen kind')
        row['pass']=all(v for k,v in row.items() if k.endswith('_ok') or k=='positive_depth')
        checks.append(row)
    failures=[r for r in checks if not r['pass']]
    unresolved=[r['id'] for r in checks if r.get('pond_presence_unresolved',False)]
    status=('FAIL_SHORE_ENGINE_READBACK' if failures else
            'INCONCLUSIVE_POND_PRESENCE' if unresolved else 'PASS_SHORE_ENGINE_READBACK')
    return dict(status=status,
                query_count=len(checks),max_height_error_m=max(r['height_error_m'] for r in checks),
                kind_counts={k:sum(p['kind']==k for p in ref['points']) for k in ('wet','dry','transition')},
                failing_count=len(failures),failures=failures,
                unresolved_low_pond_ids=unresolved,
                limits=['Readback only: no visual, traversal, navmesh or multiplayer-capacity verdict.',
                        'The deployed PBO hashes must be recorded separately before launching.',
                        'Transitional points constrain height only; no full tidal time-series acceptance.'])


def controls():
    ref=dict(header='BALTIC_V30_SHOREFINISH_V2;BalticTrial',site_count=7,query_count=5,query_fields=10,
             tolerances=dict(height_m=.02,water_plane_m=.04,dry_depth_max_m=.03),
             points=[dict(id=0,kind='wet',expected_ground_m=-1,pond_plane_m=None),
                     dict(id=1,kind='dry',expected_ground_m=2,pond_plane_m=1.4),
                     dict(id=2,kind='transition',expected_ground_m=.8,pond_plane_m=None),
                     dict(id=3,kind='wet',expected_ground_m=.5,pond_plane_m=.825),
                     dict(id=4,kind='wet',expected_ground_m=2,pond_plane_m=3)])
    good=ref['header']+'\nQBEGIN;5\nQ;0;-1;true;false;0.75;1.74;0.5;1;0.75\nQ;1;2;false;false;1.4;-0.61;0.5;1;0.75\nQ;2;0.8;false;false;0.75;-0.06;0.5;1;0.75\nQ;3;0.5;false;true;0.825;0.315;0.5;1;0.75\nQ;4;2;false;false;3;0.99;0.5;1;0.75\nQEND;5\nEND;7\n'
    assert verify(ref,good)['status']=='PASS_SHORE_ENGINE_READBACK'
    broken={
      'missing_end':good.replace('END;7\n',''),
      'duplicate_query':good.replace('QEND;5','Q;1;2;false;false;1.4;-0.61;0.5;1;0.75\nQEND;5'),
      'nonfinite':good.replace('Q;0;-1;','Q;0;nan;'),
      'wrong_ground':good.replace('Q;0;-1;','Q;0;-1.5;'),
      'dry_flood':good.replace('1.4;-0.61;','1.4;0.5;'),
      'wet_no_water':good.replace('0.75;1.74;','0.75;0;'),
      'wrong_surface':good.replace('0.75;1.74;','1.4;1.74;'),
      'wrong_envelope':good.replace(';0.5;1;0.75\n',';0.5;2;0.75\n'),
      'missing_low_pond':good.replace('Q;3;0.5;false;true;0.825;0.315;', 'Q;3;0.5;false;false;0.75;0.24;'),
      'missing_high_pond':good.replace('Q;4;2;false;false;3;0.99;', 'Q;4;2;false;false;0.75;0;'),
      'extra_wrong_boundary':good.replace('QEND;5','QBEGIN;1\nQEND;5'),
    }
    rejected=[]
    for name,text in broken.items():
        try:result=verify(ref,text)
        except (ValueError,IndexError):rejected.append(name)
        else:
            if result['status'].startswith('FAIL'):rejected.append(name)
            else:raise AssertionError('False pass: '+name)
    masked=good.replace('Q;3;0.5;false;true;0.825;0.315;0.5;1;0.75',
                        'Q;3;0.5;true;false;0.9;0.39;0.5;1;0.9')
    assert verify(ref,masked)['status']=='INCONCLUSIVE_POND_PRESENCE'
    return dict(status='PASS_VERIFIER_CONTROLS',positive=1,negatives=rejected,
                inconclusive_controls=['low_pond_masked_by_sea'],
                limit='Synthetic parser/criterion controls, not an engine run.')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path)
    ap.add_argument('--log',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--controls',action='store_true')
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve prior evidence')
    if a.controls:result=controls()
    else:
        if not a.reference or not a.log:raise ValueError('Reference and log required')
        result=verify(json.loads(a.reference.read_text()),a.log.read_text(encoding='utf-8-sig'))
        result['reference_sha256']=hashlib.sha256(a.reference.read_bytes()).hexdigest()
        result['log_sha256']=hashlib.sha256(a.log.read_bytes()).hexdigest()
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if result['status'].startswith('PASS') else 2 if result['status'].startswith('INCONCLUSIVE') else 1


if __name__=='__main__':raise SystemExit(main())
