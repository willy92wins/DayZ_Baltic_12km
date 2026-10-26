"""Bound native graph results to packed dry Roadway, mandatory pieces and old F legs."""
from pathlib import Path
import argparse,hashlib,json,math,sys
import numpy as np
from shapely.geometry import LineString,shape
from shapely.ops import unary_union
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_continuity_nav_v30 import verify as verify_paths,vector,tri_sample
from prepare_patch_nav_probe_ev112 import LOCAL_NAMES

E_SHA='705196d69646f2528aa5796d26e90bab36aebd07a5a0ddb861b31b7160f4a33e'

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def check_route(query,points,corridor,exterior,dry,water):
    """Every segment is checked; a waypoint-only model hit is insufficient."""
    if len(points)<2 or not np.isfinite(points).all():
        return dict(status='FAIL',reason='At least two finite points required')
    line=LineString(np.asarray(points)[:,[0,2]])
    if line.length<=0:return dict(status='FAIL',reason='Zero horizontal length')
    allowed=unary_union([dry[k] for k in query['allowed_models']]).union(exterior)
    required={k:line.intersection(dry[k]).length for k in query['required_models']}
    uncovered=line.difference(allowed.buffer(.01)).length
    outside=line.difference(corridor.buffer(.01)).length
    wet=line.intersection(water).length
    outer=line.intersection(exterior).length
    checks=dict(dry_continuous=uncovered<1e-8,corridor_bound=outside<1e-8,
                no_water=not line.intersects(water),required_models=all(v>=.5 for v in required.values()),
                exterior_transition=query['kind']!='cap_to_land' or outer>=.5)
    return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
                uncovered_m=uncovered,outside_corridor_m=outside,water_overlap_m=wet,
                required_coverage_m=required,exterior_m=outer,length_m=line.length)

def verify(reference,text,heights,terrain_e,geometry):
    result=verify_paths(reference,text,heights)
    queries={q['name']:q for q in reference['queries']}
    if len(queries)!=607 or len(reference['queries'])!=607:raise ValueError('Expected607 unique queries')
    local=reference['local_query_names'];local_set=set(local)
    if len(local)!=562 or len(local_set)!=562 or not local_set<=set(queries):raise ValueError('Local562 coverage')
    f_names=reference['f_local_query_names']
    if len(f_names)!=8 or set(f_names)!=LOCAL_NAMES:raise ValueError('F local identity mismatch')
    if len(geometry['models'])!=139:raise ValueError('Packed139 model coverage')
    dry={k:shape(v['dry']) for k,v in geometry['models'].items()}
    wet=unary_union([shape(v['water']) for v in geometry['models'].values()])
    corridors={q['name']:q for q in reference['corridors']}
    if len(corridors)!=562 or set(corridors)!=local_set:raise ValueError('Corridor coverage')
    paths={name:[] for name in queries};samples={}
    for row in text.splitlines()[1:-1]:
        f=row.split(';')
        if f[0]=='Q':
            # Validate sampled outputs even in a NONE or disconnected case.
            samples[f[1]]=[vector(f[8]),vector(f[9])]
        elif f[0]=='P':paths[f[1]].append(vector(f[3]))
    coverage={}
    for name in local:
        q=queries[name];c=corridors[name]
        required=q['required_models'];allowed=q['allowed_models']
        if not required or len(set(required))!=len(required) or not set(required)<=set(allowed)<=set(dry):raise ValueError('Invalid required/allowed models')
        if allowed!=c['allowed_models']:raise ValueError('Corridor/model contract mismatch')
        corridor=shape(c['corridor']);exterior=shape(c['exterior'])
        if not corridor.is_valid or not exterior.is_valid:raise ValueError('Invalid corridor')
        v=check_route(q,paths[name],corridor,exterior,dry,wet)
        endpoint_ok=all(math.dist(p,q[k])<=2.1 for p,k in zip(samples[name],('start','end')))
        v['sampled_endpoints_near_request']=endpoint_ok
        if not endpoint_ok:v['status']='FAIL'
        coverage[name]=v
    f_coverage={}
    for name in sorted(f_names):
        delta=[abs(float(tri_sample(terrain_e,p[0],p[2]))-float(tri_sample(heights,p[0],p[2]))) for p in paths[name]]
        if not all(math.isfinite(d) for d in delta):raise ValueError('Nonfinite F delta')
        f_coverage[name]=dict(waypoints=len(delta),max_delta_m=max(delta,default=0.),covered=any(d>=.05 for d in delta))
    graph_pass=result['status']=='PASS_LOCAL_CONTINUITY_NAV_PATHS' and all(v['status']=='PASS' for v in coverage.values())
    f_pass=all(v['covered'] for v in f_coverage.values())
    result['upstream_status']=result['status']
    result['status']='PASS_KIT7_NATIVE_GRAPH' if graph_pass and f_pass else ('INCONCLUSIVE_F_PATCH_NOT_SAMPLED' if graph_pass else 'FAIL_KIT7_NATIVE_GRAPH')
    result.update(local_coverage=coverage,f_patch_coverage=f_coverage,local_failures=[k for k,v in coverage.items() if v['status']!='PASS'],minimum_f_delta_m=.05)
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('reference','log','terrain-e','out'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--reference-sha256',required=True)
    a=ap.parse_args()
    if a.out.exists():raise FileExistsError('Preserve previous result')
    try:
        if sha(a.reference)!=a.reference_sha256:raise ValueError('Frozen reference identity mismatch')
        ref=json.loads(a.reference.read_text())
        if sha(a.terrain_e)!=E_SHA:raise ValueError('E terrain identity mismatch')
        for p,h in ref['inputs'].items():
            if sha(p)!=h:raise ValueError('Frozen input drift: '+p)
        if sha(ref['terrain'])!=ref['terrain_sha256'] or sha(ref['geometry'])!=ref['geometry_sha256']:raise ValueError('Geometry or terrain identity mismatch')
        H=np.load(ref['terrain'])['heights'];HE=np.load(a.terrain_e)['heights']
        if H.shape!=(2048,2048) or HE.shape!=H.shape or not np.isfinite(H).all() or not np.isfinite(HE).all():raise ValueError('Invalid grids')
        result=verify(ref,a.log.read_text(encoding='utf-8-sig'),H,HE,json.loads(Path(ref['geometry']).read_text()))
        result.update(log_sha256=sha(a.log),reference_sha256=sha(a.reference),terrain_e_sha256=E_SHA,terrain_sha256=ref['terrain_sha256'],geometry_sha256=ref['geometry_sha256'])
    except (OSError,ValueError,KeyError,IndexError,TypeError) as exc:
        result=dict(status='FAIL_KIT7_PROBE_EVIDENCE',reason=str(exc))
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','height_cases','local_coverage')},indent=2))
    raise SystemExit(0 if result['status']=='PASS_KIT7_NATIVE_GRAPH' else 2 if result['status'].startswith('INCONCLUSIVE') else 1)

if __name__=='__main__':main()
