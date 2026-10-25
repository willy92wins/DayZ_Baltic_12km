"""Fail-closed regional water/nav consumers tied to frozen per-version inputs."""
from pathlib import Path
import argparse,csv,hashlib,json,math
from verify_regional_nav import check as check_nav,vector,boolean
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def read_reference(raw):
    result={}
    for row in csv.reader(raw.splitlines(),delimiter=';'):
        if len(row)!=7 or row[0] not in ('W','L'):raise ValueError('Invalid reference row')
        kind,index,xyz,ground,water,depth,group=row;index=int(index)
        if index in result:raise ValueError('Duplicate reference')
        result[index]=dict(kind=kind,xyz=vector(xyz),ground=float(ground),water=float(water) if water else None,depth=float(depth),group=group)
    if not result:raise ValueError('Empty reference')
    return result

def check_water(raw,reference,manifest):
    rows=list(csv.reader(raw.splitlines(),delimiter=';'))
    typed_contract=manifest.get('probe_version') in ('v4','v5','v6','v7')
    if typed_contract and (manifest.get('liquid_water_mask')!=8259072 or manifest.get('type_surface_tolerance_m')!=.25):
        raise ValueError('Wrong typed surface classification contract')
    if rows[:2]!=[['BALTIC_FOUNDATION_WATER_'+manifest.get('probe_version','v2').upper()],['world=BalticTrial']]:raise ValueError('Wrong header or world')
    if rows[-1]!=['BALTIC_FOUNDATION_WATER_COMPLETE',str(len(reference))]:raise ValueError('Missing/wrong completion')
    if len(rows[2])!=3 or rows[2][0]!='SEA':raise ValueError('Missing sea limits')
    lo,hi=map(float,rows[2][1:])
    if not math.isfinite(lo+hi) or abs(lo-.5)>.001 or abs(hi-1)>.001:raise ValueError('Sea configuration differs from frozen design')
    seen=set();groups={};failures=[];fail_count=0;max_error=0;min_depth=float('inf')
    for row in rows[3:-1]:
        if len(row)!=(12 if typed_contract else 8) or row[0]!='S':raise ValueError('Malformed sample')
        index=int(row[1])
        if index in seen or index not in reference:raise ValueError('Duplicate/unexpected sample')
        seen.add(index);ref=reference[index];p=vector(row[2]);ground,surface=float(row[3]),float(row[4]);sea,pond=boolean(row[5]),boolean(row[6]);depth=float(row[7])
        if not all(math.isfinite(v) for v in (ground,surface,depth)):raise ValueError('Nonfinite measurement')
        typed_water=False;type_height=None;surface_type=None;liquid=False;liquid_type=0
        if typed_contract:
            type_height=float(row[8]);surface_type=row[9];liquid=boolean(row[10]);liquid_type=int(row[11])
            if not math.isfinite(type_height) or not surface_type or liquid_type<0:raise ValueError('Malformed surface classification')
            typed_water=bool(liquid and liquid_type & manifest['liquid_water_mask'] and surface_type!='empty' and abs(type_height-surface)<=manifest['type_surface_tolerance_m'])
        if abs(p[0]-ref['xyz'][0])>.01 or abs(p[2]-ref['xyz'][2])>.01:raise ValueError('Moved query')
        query_y=max(1.5,ref['water']+.25) if ref['kind']=='W' else ground+1
        if abs(p[1]-query_y)>.01:raise ValueError('Wrong query elevation')
        errors=[];height_error=abs(ground-ref['ground']);max_error=max(max_error,height_error)
        if height_error>manifest['height_tolerance_m']:errors.append('terrain_height')
        tol=manifest['pond_surface_tolerance_m']
        if ref['kind']=='W':
            if not (sea or pond or typed_water):errors.append('missing_water')
            if ref['water']>hi+tol:
                if not (pond or typed_water):errors.append('missing_pond')
                if abs(surface-ref['water'])>tol:errors.append('water_level')
            elif not max(lo,ref['water'])-tol<=surface<=hi+tol:errors.append('water_level')
            actual_depth=surface-ground;min_depth=min(min_depth,actual_depth)
            # Numerical comparison tolerance is separate from the design depth.
            if actual_depth<ref['depth']-.01:errors.append('insufficient_depth')
            if depth<=0:errors.append('depth_api_not_wet')
        else:
            if sea or pond or typed_water:errors.append('water_classification_on_dry_reference')
            if depth>tol or surface>ground+tol:errors.append('flooded_dry_reference')
            if ground<hi+.25-.001:errors.append('dry_freeboard')
        group=groups.setdefault(ref['group'],dict(total=0,passed=0));group['total']+=1;group['passed']+=int(not errors)
        if errors:
            fail_count+=1
            if len(failures)<50:failures.append(dict(index=index,group=ref['group'],reasons=errors,position=p,ground=ground,expected_ground=ref['ground'],surface=surface,expected_water=ref['water'],sea=sea,pond=pond,depth=depth,type_height=type_height,surface_type=surface_type,liquid=liquid,liquid_type=liquid_type))
    if seen!=set(reference):raise ValueError('Missing samples')
    return dict(status='PASS_RUNTIME_WATER_AND_DRY_SAMPLES' if not fail_count else 'FAIL',samples=len(seen),failed_samples=fail_count,maximum_terrain_error_m=max_error,minimum_sampled_water_depth_m=min_depth if math.isfinite(min_depth) else None,groups=groups,failure_examples=failures,limits=['Fixed water/dry points, not boat propulsion, full shoreline coverage or client rendering.'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--water-log',type=Path,required=True);ap.add_argument('--nav-log',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--version',choices=['v2','v3','v4','v5','v6','v7'],default='v3');args=ap.parse_args()
    assert not args.out.exists(),'Preserve evidence'
    manifest_path=EV/f'consumer-reference-{args.version}.json';manifest=json.loads(manifest_path.read_text())
    frozen={'v2':'e7c81a37757a592eea70e8c70a7319a5d704568db419778d637c93af3a3e38fd',
            'v3':'25a79815f5ad64b0fcd5a0dbedd3497ae3e70c32b9cd57a202bbd46db82635ea',
            'v4':'44f798527c4f6c04e95267ba17df75eae58ae9b8cceede8fad26715d601457cf',
            'v5':'78fd406f340efcc8b3de2218ee8b8ae14b25b36ef8bf13eb9d3c206078d21b0c',
            'v6':'61558f9a888d73c5026b09af23e18c0fd5a30c07eea389a35d70512c8e70d8b5',
            'v7':'18bb4058793a69d7ac941e250a07aff54dce17c1d0378856ef96d094c7f7b975'}
    if sha(manifest_path)!=frozen[args.version]:raise ValueError('Frozen manifest changed')
    mission=ROOT/f'missions/BalticFoundationConsumer{args.version.upper()}.BalticTrial'
    paths={'water_file':mission/'water-points.csv','nav_file':mission/'nav-points.csv','nav_reference':EV/f'foundation-nav-reference-{args.version}.json','mission':mission/'init.c'}
    for key,path in paths.items():
        if sha(path)!=manifest[key+'_sha256']:raise ValueError('Frozen input changed: '+key)
    expected=read_reference(paths['water_file'].read_text())
    if len(expected)!=manifest['water_points']:raise ValueError('Reference count differs')
    result={}
    for name,path in [('water',args.water_log),('navigation',args.nav_log)]:
        try:
            raw=path.read_text(encoding='utf-8-sig')
            result[name]=check_water(raw,expected,manifest) if name=='water' else check_nav(raw,json.loads(paths['nav_reference'].read_text()))
        except (ValueError,IndexError,KeyError,OSError) as e:result[name]=dict(status='FAIL',error=str(e))
        if path.exists():result[name]['log_sha256']=sha(path)
    result['status']='PASS_RUNTIME_REGIONAL_CONSUMERS' if all(result[k]['status'].startswith('PASS') for k in ('water','navigation')) else 'FAIL'
    result['manifest_sha256']=sha(manifest_path);result['asc_sha256']=manifest['asc_sha256']
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v if k not in ('water','navigation') else {kk:vv for kk,vv in v.items() if kk not in ('groups','failure_examples','sample_failures','routes')} for k,v in result.items()},indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)
if __name__=='__main__':main()
