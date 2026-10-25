"""Require a bound passing F consumer and real waypoints in every changed local leg."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_patch_nav_probe_ev112 import LOCAL_NAMES, checked_queries
from verify_continuity_nav_v30 import verify as verify_consumer, vector, tri_sample

E_SHA='705196d69646f2528aa5796d26e90bab36aebd07a5a0ddb861b31b7160f4a33e'
F_SHA='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_coverage(reference_bytes, log_bytes, consumer, he, hf, local_bytes, local_sha256):
    reference=json.loads(reference_bytes)
    if reference.get('side')!='F' or reference['terrain_sha256']!=F_SHA:
        raise ValueError('Expected frozen F reference')
    names=checked_queries(reference['queries'],45)
    local=reference['local_query_names']
    if len(local)!=8 or set(local)!=LOCAL_NAMES or not LOCAL_NAMES<=names:
        raise ValueError('Local case identity mismatch')
    if sha(local_bytes)!=local_sha256 or reference['inputs']['local_routes']['sha256']!=local_sha256:
        raise ValueError('Frozen local routes identity mismatch')
    screen=json.loads(local_bytes)
    if screen['status']!='PREPARED_GEOMETRIC_SCREEN_NOT_NATIVE_ACCEPTANCE' or checked_queries(screen['queries'],8)!=LOCAL_NAMES:
        raise ValueError('Invalid geometric screen')
    by_name={q['name']:q for q in reference['queries']}
    for query in screen['queries']:
        actual=by_name[query['name']]
        if query['expect']!='path' or actual['expect']!='path' or any(actual[end][::2]!=query[end][::2] for end in ('start','end')):
            raise ValueError('Local XZ/expectation differs from frozen screen')
    if consumer.get('log_sha256')!=sha(log_bytes) or consumer.get('reference_sha256')!=sha(reference_bytes):
        raise ValueError('Consumer is not bound to supplied evidence')
    if consumer.get('status')!='PASS_LOCAL_CONTINUITY_NAV_PATHS':
        return dict(status='FAIL_UPSTREAM_CONSUMER',coverage={})
    text=log_bytes.decode('utf-8-sig')
    fresh=verify_consumer(reference,text,hf)
    if fresh['status']!='PASS_LOCAL_CONTINUITY_NAV_PATHS':
        return dict(status='FAIL_UPSTREAM_REVALIDATION',coverage={})
    coverage={name:dict(waypoints=0,max_delta_m=0.,covered=False) for name in sorted(LOCAL_NAMES)}
    for row in text.splitlines()[1:-1]:
        fields=row.split(';')
        if fields[0]!='P' or fields[1] not in coverage:
            continue
        point=vector(fields[3]);entry=coverage[fields[1]]
        delta=abs(float(tri_sample(he,point[0],point[2]))-float(tri_sample(hf,point[0],point[2])))
        if not np.isfinite(delta):
            raise ValueError('Nonfinite terrain sample')
        entry['waypoints']+=1;entry['max_delta_m']=max(entry['max_delta_m'],delta)
        entry['covered']=entry['covered'] or delta>=.05
    return dict(status='PASS_F_PATCH_WAYPOINT_COVERAGE' if all(x['covered'] for x in coverage.values()) else 'INCONCLUSIVE_PATCH_NOT_SAMPLED',
                coverage=coverage,minimum_delta_m=.05,
                limits=['Waypoints sample the changed terrain; no proof of actor locomotion or traversal between waypoints.',
                        'Navmesh identity depends on the SHA of the loaded PBO recorded at launch; terrain delta alone does not identify the navmesh.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('reference','log','consumer','terrain-e','terrain-f','local-routes','out'):
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--reference-sha256',required=True)
    ap.add_argument('--local-routes-sha256',required=True)
    a=ap.parse_args()
    if a.out.exists():
        raise FileExistsError('Fresh output required')
    result={}
    try:
        rb=a.reference.read_bytes();lb=a.log.read_bytes();cb=a.consumer.read_bytes()
        if sha(rb)!=a.reference_sha256 or sha(a.terrain_e.read_bytes())!=E_SHA or sha(a.terrain_f.read_bytes())!=F_SHA:
            raise ValueError('Frozen input identity mismatch')
        he=np.load(a.terrain_e)['heights'];hf=np.load(a.terrain_f)['heights']
        if he.shape!=(2048,2048) or hf.shape!=he.shape or not np.isfinite(he).all() or not np.isfinite(hf).all():
            raise ValueError('Invalid native terrain grid')
        result=verify_coverage(rb,lb,json.loads(cb),he,hf,a.local_routes.read_bytes(),a.local_routes_sha256)
        result.update(reference_sha256=sha(rb),log_sha256=sha(lb),consumer_sha256=sha(cb),terrain_e_sha256=E_SHA,terrain_f_sha256=F_SHA,local_routes_sha256=a.local_routes_sha256)
    except (OSError,ValueError,IndexError,KeyError,TypeError) as exc:
        result=dict(status='FAIL_PATCH_EVIDENCE',reason=str(exc))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PASS_F_PATCH_WAYPOINT_COVERAGE' else 2 if result['status'].startswith('INCONCLUSIVE') else 1)


if __name__=='__main__':
    main()
