"""Keep historical XZ/path expectations, freeze requests against the current terrain."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'terrain'))
from v30_common import tri_sample


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def retarget(queries,h):
    queries=json.loads(json.dumps(queries));changes=[]
    for q in queries:
        for end in ('start','end'):
            p=q[end];before=p[1]
            # These requests refer to the protected physical bridge deck.
            deck=q['name'].startswith('bridge_')
            if not deck:p[1]=float(tri_sample(h,p[0],p[2]))+.1
            changes.append(dict(case=q['name'],endpoint=end,x=p[0],z=p[2],old_y=before,new_y=p[1],basis='preserved_physical_deck' if deck else 'current_native_terrain'))
    return queries,changes


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--previous-reference',type=Path,required=True)
    ap.add_argument('--expected-previous-sha256',required=True)
    ap.add_argument('--source-mission',type=Path,required=True)
    ap.add_argument('--expected-source-sha256',required=True)
    ap.add_argument('--terrain',type=Path,required=True)
    ap.add_argument('--expected-terrain-sha256',required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--mission',type=Path,required=True)
    a=ap.parse_args()
    if sha(a.source_mission)!=a.expected_source_sha256 or sha(a.terrain)!=a.expected_terrain_sha256 or sha(a.previous_reference)!=a.expected_previous_sha256:
        raise ValueError('Input identity mismatch')
    if a.out.exists() or a.mission.exists():raise FileExistsError('Fresh output and mission required')
    old=json.loads(a.previous_reference.read_text())
    h=np.load(a.terrain)['heights']
    queries,changes=retarget(old['queries'],h)
    if len({q['name'] for q in queries})!=len(queries):raise ValueError('Duplicate route names')
    if not all(q['start'][::2]==o['start'][::2] and q['end'][::2]==o['end'][::2]
               and q.get('expect')==o.get('expect') for q,o in zip(queries,old['queries'])):raise ValueError('Route contract drift')
    code=a.source_mission.read_text(encoding='utf-8')
    if 'baltic_v30_continuity_nav_v1.log' not in code or 'BALTIC_V30_CONTINUITY_NAV_V1;' not in code:raise ValueError('Historical mission markers absent')
    code=code.replace('baltic_v30_continuity_nav_v1.log','baltic_ev112_nav_v9.log')
    code=code.replace('BALTIC_V30_CONTINUITY_NAV_V1;','BALTIC_EV112_NAV_V9;')
    a.out.mkdir(parents=True);a.mission.mkdir(parents=True)
    (a.mission/'init.c').write_text(code,encoding='ascii',newline='\n')
    csv='\n'.join(q['name']+';'+';'.join(' '.join(f'{v:.8f}' for v in q[k]) for k in ('start','end')) for q in queries)+'\n'
    (a.mission/'queries.csv').write_text(csv,encoding='ascii',newline='\n')
    ref=dict(status='PREPARED_NOT_RUN',header='BALTIC_EV112_NAV_V9;BalticTrial',
             terrain=str(a.terrain.resolve()),terrain_sha256=sha(a.terrain),previous_reference_sha256=sha(a.previous_reference),
             source_mission_sha256=sha(a.source_mission),code_sha256=sha(a.mission/'init.c'),
             queries_sha256=sha(a.mission/'queries.csv'),mission=str(a.mission),queries=queries,
             max_waypoint_surface_error_m=old['max_waypoint_surface_error_m'],
             limits=old['limits']+['XZ, expectations and tolerances inherited; physical bridge deck Y preserved, other request Y uses current native terrain +0.1m. No actor acceptance.'])
    (a.out/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    (a.out/'endpoint-updates.json').write_text(json.dumps(changes,indent=2)+'\n')
    print(json.dumps(dict(queries=len(queries),mission=str(a.mission),terrain_sha256=sha(a.terrain))))


if __name__=='__main__':
    main()
