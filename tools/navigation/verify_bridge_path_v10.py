"""Check complete native bridge paths, not merely a boolean FindPath result."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import rasterio
from verify_regional_chase import vec
from waterway_common import sample

def verify(reference,text,height):
    lines=text.splitlines();queries={};points={}
    if lines[0]!='BALTIC_BRIDGE_PATH_V10;BalticTrial' or lines[-1]!='END;9':
        raise ValueError('Wrong/incomplete query log')
    for line in lines[1:-1]:
        f=line.split(';')
        if f[0]=='Q' and len(f)==10:
            if f[1] in queries or any(x not in ('true','false') for x in f[2:5]):raise ValueError('Bad/duplicate query')
            queries[f[1]]=dict(sample_start=f[2]=='true',sample_goal=f[3]=='true',found=f[4]=='true',count=int(f[5]),vectors=[vec(x) for x in f[6:]])
        elif f[0]=='P' and len(f)==6:
            group=points.setdefault(f[1],[])
            if int(f[2])!=len(group):raise ValueError('Nonsequential path')
            group.append([vec(x) for x in f[3:]])
        else:raise ValueError('Unknown record')
    if set(queries)!={c['name'] for c in reference['cases']} or set(points)-set(queries):raise ValueError('Wrong query identities')
    bridge=reference['bridge'];criteria=reference['criteria'];center=np.array(bridge['center_xz']);axis=np.array(bridge['axis_xz']);normal=np.array([-axis[1],axis[0]])
    reports=[]
    for case in reference['cases']:
        name=case['name'];q=queries[name];p=points.get(name,[])
        checks=dict(request_start=float(np.linalg.norm(q['vectors'][0]-case['start']))<.000002,request_goal=float(np.linalg.norm(q['vectors'][1]-case['goal']))<.000002,count=q['count']==len(p))
        details={}
        if name=='negative':checks['negative_filter']=not q['sample_start'] and not q['sample_goal'] and not q['found'] and not p
        else:
            checks['found']=q['sample_start'] and q['sample_goal'] and q['found'] and len(p)>=2
            if len(p)>=2:
                data=np.asarray(p);path=data[:,0,:];ground=data[:,1,:];road=data[:,2,:]
                lateral=(path[:,[0,2]]-center)@normal
                expected=sample(height,path[:,0]+200000,path[:,2]);delta=np.max(abs(expected-ground[:,1]))
                checks.update(endpoints=np.linalg.norm(path[0]-case['start'])<=criteria['max_sample_distance_m'] and np.linalg.norm(path[-1]-case['goal'])<=criteria['max_sample_distance_m'],
                    corridor=max(abs(lateral))<=criteria['max_lateral_m'],
                    road_height=max(abs(path[:,1]-road[:,1]))<=criteria['max_height_error_m'],
                    heightfield=delta<=criteria['maximum_heightfield_error_m'],
                    same_surface_xz=np.max(abs(ground[:,[0,2]]-path[:,[0,2]]))<.000002 and np.max(abs(road[:,[0,2]]-path[:,[0,2]]))<.000002)
                details=dict(maximum_lateral_m=float(max(abs(lateral))),maximum_road_error_m=float(max(abs(path[:,1]-road[:,1]))),maximum_heightfield_error_m=float(delta),
                    path_length_m=float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum()),path=path.tolist())
        checks={k:bool(v) for k,v in checks.items()}
        reports.append(dict(name=name,status='PASS' if all(checks.values()) else 'FAIL',checks=checks,**details))
    return dict(status='PASS_NATIVE_BRIDGE_GRAPH_QUERIES' if all(r['status']=='PASS' for r in reports) else 'FAIL_NATIVE_BRIDGE_GRAPH_QUERIES',cases=reports,limits=reference['limits'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--log',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve prior evidence')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    ref=json.loads(a.reference.read_text());terrain=Path(ref['terrain'])
    if sha(terrain)!=ref['terrain_sha256']:raise ValueError('Terrain identity changed')
    with rasterio.open(terrain) as ds:height=ds.read(1)
    try:result=verify(ref,a.log.read_text(encoding='utf-8-sig'),height)
    except (ValueError,KeyError,IndexError) as exc:result=dict(status='FAIL_INVALID_EVIDENCE',reason=str(exc))
    result.update(reference_sha256=sha(a.reference),log_sha256=sha(a.log))
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
