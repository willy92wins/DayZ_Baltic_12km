"""Freeze native path queries before generating/observing the new navmesh.

Preserve the 13 historical XY requests, then sample changed dry banks rather
than selecting locations from successful runtime paths. Does not deploy or run.
AI API: P:/scripts/3_game/AI/aiworld.c:65,98,122.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import sys

import numpy as np
from scipy.ndimage import maximum_filter, minimum_filter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/terrain'))
from v30_common import tri_sample, cell_planes, vertex_plane_bounds

OLD = Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')
OLD_SHA = 'a84dfff053523b94717b2068a96845193d01a21f0ea7ff01e0f9111280630081'
CURRENT_SHA = '40d8cfd9874e9260464f9e3c38c07d81a15c8aed374083a52c98f042c0161c2e'
PREVIOUS = ROOT/'evidence/v30-delta-fairways-2026-10-02/navmesh/path-reference.json'
MISSION = ROOT/'missions/BalticV30ContinuityNavV1.BalticTrial'
HEADER = 'BALTIC_V30_CONTINUITY_NAV_V1;'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists() and not MISSION.exists(), 'Fresh output only'
    assert sha(a.candidate) == CURRENT_SHA and sha(OLD) == OLD_SHA
    parent = json.loads(PREVIOUS.read_text())
    oldmission = Path(parent['mission'])
    assert sha(oldmission/'init.c') == parent['code_sha256']
    assert sha(oldmission/'queries.csv') == parent['queries_sha256']
    t, old = np.load(a.candidate), np.load(OLD)
    h, before = t['heights'].astype(float), old['heights'].astype(float)
    plane = cell_planes(t['cls'], t['level'])
    _, upper = vertex_plane_bounds(plane)
    water_max = np.maximum(np.nan_to_num(upper, nan=1.), 1.)
    dry = (t['cls'] == 0) & (h > water_max + .10)
    # Require a full surrounding cell of dry vertices and gentle triangle faces.
    nw, ne, sw, se = h[:-1,:-1], h[:-1,1:], h[1:,:-1], h[1:,1:]
    slope = np.maximum(np.hypot(ne-nw,se-ne), np.hypot(se-sw,sw-nw))/6.
    steep = np.zeros_like(h, dtype=bool)
    for dr, dc in ((0,0),(0,1),(1,0),(1,1)):
        steep[dr:dr+2047,dc:dc+2047] |= slope > np.tan(np.deg2rad(30))
    eligible = minimum_filter(dry.astype(np.uint8), size=3, mode='constant') > 0
    eligible &= ~maximum_filter(steep, size=3, mode='constant')
    eligible &= before-h >= .15
    eligible[:5,:] = False; eligible[-5:,:] = False
    eligible[:,:5] = False; eligible[:,-5:] = False
    indices = np.flatnonzero(eligible)
    # Highest change first, deterministic index tie-break; geographic spacing.
    delta = (before-h).ravel()
    indices = indices[np.lexsort((indices, -delta[indices]))]
    queries = copy.deepcopy(parent['queries'])
    retargeted = []
    for q in queries:
        if q['name'].startswith('bridge_'):
            continue  # Physical deck query, not terrain Y.
        for endpoint in ('start','end'):
            x,y,z = q[endpoint]
            shift = float(tri_sample(h,x,z)-tri_sample(before,x,z))
            q[endpoint][1] = y+shift
            if shift:
                retargeted.append(dict(name=q['name'], endpoint=endpoint, delta_y_m=shift))
    assert len(queries) == 13
    selected = []
    directions = [(1,0),(0,1),(-1,0),(0,-1),(1,1),(-1,1),(-1,-1),(1,-1)]
    for index in indices:
        r,c = divmod(int(index),2048)
        x,z = c*6.,12282-r*6.
        if any(np.hypot(x-s['x'],z-s['z']) < 200 for s in selected):
            continue
        chosen = None
        for dx,dz in directions:
            v = np.array([dx,dz],float); v *= 24/np.linalg.norm(v)
            along = np.linspace(0,1,49)
            xs,zs = x+along*v[0],z+along*v[1]
            ys = tri_sample(h,xs,zs)
            rr = np.clip(np.floor((12282-zs)/6).astype(int),0,2046)
            cc = np.clip(np.floor(xs/6).astype(int),0,2046)
            localwater = np.maximum(np.nan_to_num(plane[rr,cc],nan=1.),1.)
            if np.any(ys <= localwater+.1) or np.any(slope[rr,cc] > np.tan(np.deg2rad(30))):
                continue
            chosen = dict(name=f'changed_bank_{len(selected):02d}',
                          start=[x,float(h[r,c])+.2,z],
                          end=[float(xs[-1]),float(ys[-1])+.2,float(zs[-1])],
                          expect='path')
            break
        if chosen is None:
            continue
        queries.append(chosen)
        selected.append(dict(x=x,z=z,delta_y_m=float(h[r,c]-before[r,c]),
                             minimum_path_freeboard_m=float(np.min(ys-localwater))))
        if len(selected) == 24:
            break
    assert selected, 'No suitable changed dry-bank samples; do not fabricate coverage'
    code = (oldmission/'init.c').read_text()
    replacements = {
        'BalticV30DeltaNavMission':'BalticV30ContinuityNavMission',
        'baltic_v30_delta_nav_v1.log':'baltic_v30_continuity_nav_v1.log',
        'BALTIC_V30_ACCEPTANCE_V1;':HEADER,
    }
    for source,target in replacements.items():
        assert source in code
        code = code.replace(source,target)
    csv = ''.join(q['name']+';'+' '.join(f'{v:.8f}' for v in q['start'])+';'+
                  ' '.join(f'{v:.8f}' for v in q['end'])+'\n' for q in queries)
    MISSION.mkdir(); a.out.mkdir(parents=True)
    (MISSION/'init.c').write_text(code,encoding='utf-8',newline='\n')
    (MISSION/'queries.csv').write_text(csv,encoding='ascii',newline='\n')
    reference = dict(status='PREPARED_NATIVE_PATHS_NOT_RUN',mission=str(MISSION),
        header=HEADER+'BalticTrial',terrain=str(a.candidate),terrain_sha256=CURRENT_SHA,
        old_terrain_sha256=OLD_SHA,previous_reference_sha256=sha(PREVIOUS),
        code_sha256=sha(MISSION/'init.c'),queries_sha256=sha(MISSION/'queries.csv'),
        generator_sha256=sha(Path(__file__)),queries=queries,retargeted_y=retargeted,
        changed_bank_selection=selected,eligible_bank_vertices=int(eligible.sum()),
        max_waypoint_surface_error_m=.801,
        limits=['Native path graph only, not actor locomotion or player capacity.',
                'Local dry-bank coverage, not all map connectivity; references frozen before runtime.',
                '0.8m diagnostic surface-distance threshold retained from earlier local native consumer.',
                'Exact deployed WRP/water/new NM identity must be recorded separately at launch.'])
    (a.out/'reference.json').write_text(json.dumps(reference,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in reference.items() if k not in ('queries','changed_bank_selection')},indent=2))


if __name__ == '__main__':
    main()
