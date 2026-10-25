"""Freeze exactly 37 inherited plus 8 pre-screened F-patch queries for E or F."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_current_nav_probe_ev112 import retarget

LOCAL_NAMES = {f'f_patch_{axis}_{leg}' for axis in ('ew','ns','ne_sw','nw_se') for leg in (1,2)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_markers(side, log_name, header_marker):
    if side not in ('E','F') or log_name!=f'baltic_patch_nav_{side.lower()}45.log' or header_marker!=f'BALTIC_PATCH_NAV_{side}45':
        raise ValueError('Unique side-specific patch log and header required')


def checked_queries(queries, count):
    if not isinstance(queries,list) or len(queries)!=count:
        raise ValueError('Wrong exact query count')
    names=set()
    for q in queries:
        name=q['name']
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_]+',name) or name in names:
            raise ValueError('Invalid or duplicate query name')
        names.add(name)
        if q.get('expect','none' if name=='negative' else 'path') not in ('none','path','disconnected'):
            raise ValueError('Invalid expectation')
        for end in ('start','end'):
            if len(q[end])!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in q[end]):
                raise ValueError('Invalid endpoint')
            if not (0<=q[end][0]<=12282 and 0<=q[end][2]<=12282):
                raise ValueError('Endpoint outside native terrain')
    return names


def combine_queries(old, local, heights):
    old_names=checked_queries(old['queries'],37)
    if local['status']!='PREPARED_GEOMETRIC_SCREEN_NOT_NATIVE_ACCEPTANCE':
        raise ValueError('Local geometric preparation did not pass')
    names=checked_queries(local['queries'],8)
    if names!=LOCAL_NAMES or names & old_names or any(q['expect']!='path' for q in local['queries']):
        raise ValueError('Local route contract mismatch')
    original=copy.deepcopy(old['queries'])
    inherited,changes=retarget(original,heights)
    # Full-record comparison after restoring only permitted terrain-derived Y.
    if len(inherited)!=37:
        raise ValueError('Inherited routes truncated or extended')
    restored=copy.deepcopy(inherited)
    for index in range(37):
        for end in ('start','end'):
            restored[index][end][1]=original[index][end][1]
            if original[index]['name'].startswith('bridge_') and inherited[index][end][1]!=original[index][end][1]:
                raise ValueError('Bridge deck Y changed')
    if restored!=original:
        raise ValueError('Inherited query contract changed')
    extra,extra_changes=retarget(local['queries'],heights)
    combined=inherited+extra
    checked_queries(combined,45)
    return combined,changes+extra_changes


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('previous-reference','local-routes','source-mission','terrain'):
        ap.add_argument('--'+name,type=Path,required=True)
        ap.add_argument('--'+name+'-sha256',required=True)
    ap.add_argument('--side',choices=('E','F'),required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--mission',type=Path,required=True)
    ap.add_argument('--log-name',required=True)
    ap.add_argument('--header-marker',required=True)
    a=ap.parse_args()
    if a.out.exists() or a.mission.exists():
        raise FileExistsError('Fresh output and mission required')
    check_markers(a.side,a.log_name,a.header_marker)
    inputs={}
    for name in ('previous_reference','local_routes','source_mission','terrain'):
        path=getattr(a,name);digest=sha(path)
        if digest!=getattr(a,name+'_sha256'):
            raise ValueError('Input identity mismatch: '+name)
        inputs[name]=dict(path=str(path.resolve()),sha256=digest)
    old=json.loads(a.previous_reference.read_text());local=json.loads(a.local_routes.read_text())
    if local['inputs']['terrain_'+a.side.lower()]['sha256']!=a.terrain_sha256:
        raise ValueError('Terrain differs from frozen geometric screen')
    heights=np.load(a.terrain)['heights']
    if heights.shape!=(2048,2048) or not np.isfinite(heights).all():
        raise ValueError('Invalid native terrain grid')
    queries,changes=combine_queries(old,local,heights)
    code=a.source_mission.read_text(encoding='utf-8')
    if code.count('baltic_v30_continuity_nav_v1.log')!=1 or code.count('BALTIC_V30_CONTINUITY_NAV_V1;')!=1:
        raise ValueError('Expected unique canonical mission markers')
    code=code.replace('baltic_v30_continuity_nav_v1.log',a.log_name).replace('BALTIC_V30_CONTINUITY_NAV_V1;',a.header_marker+';')
    csv='\n'.join(q['name']+';'+';'.join(' '.join(f'{v:.8f}' for v in q[k]) for k in ('start','end')) for q in queries)+'\n'
    a.out.mkdir(parents=True);a.mission.mkdir(parents=True)
    (a.mission/'init.c').write_bytes(code.encode('ascii'))
    (a.mission/'queries.csv').write_bytes(csv.encode('ascii'))
    ref=dict(status='PREPARED_NOT_RUN',header=a.header_marker+';BalticTrial',side=a.side,
        terrain=str(a.terrain.resolve()),terrain_sha256=a.terrain_sha256,
        source_mission_sha256=a.source_mission_sha256,code_sha256=sha(a.mission/'init.c'),
        queries_sha256=sha(a.mission/'queries.csv'),mission=str(a.mission.resolve()),log_name=a.log_name,
        local_query_names=sorted(LOCAL_NAMES),queries=queries,inputs=inputs,
        max_waypoint_surface_error_m=old['max_waypoint_surface_error_m'],
        limits=old['limits']+['Exactly 37 inherited contracts and 8 local legs frozen before either native run; no actor locomotion acceptance.'])
    (a.out/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    (a.out/'endpoint-updates.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(queries=45,side=a.side,mission=str(a.mission),reference_sha256=sha(a.out/'reference.json'))))


if __name__=='__main__':
    main()
