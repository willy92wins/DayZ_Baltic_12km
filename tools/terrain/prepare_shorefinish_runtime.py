"""Freeze an engine readback/visual mission for the completed shore candidate.

Server owns the readbacks and temporary player placement; no new RPC or client
state. APIs are retained from the already executed DeltaV1 fixture and verified
in P:/scripts/3_game/global/game.c:1162-1185, entities/object.c:300,317.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from scipy.ndimage import distance_transform_edt
from v30_common import cell_planes, tri_sample

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = Path('E:/DayZ-Baltic-Build/v30-shore-finish-tidal/terrain_v30.npz')
OLD = Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')
ATLAS = CANDIDATE.parent/'atlas/sites.json'
PARENT = ROOT/'missions/BalticV30DeltaV1.BalticTrial/init.c'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def replace_once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--expected-sha256', required=True)
    ap.add_argument('--atlas', type=Path, required=True)
    ap.add_argument('--world-pbo-sha256', required=True)
    ap.add_argument('--water-pbo-sha256', required=True)
    ap.add_argument('--detail-baseline', type=Path,
                    help='Also read every vertex changed since this local baseline and its two triangle interiors.')
    ap.add_argument('--extra-points',type=Path,
                    help='Frozen candidate-bound local cases, at most 4096 additional coordinates.')
    ap.add_argument('--version', type=int, default=2)
    ap.add_argument('--headless', action='store_true')
    a = ap.parse_args()
    assert a.version >= 2, 'V1 evidence remains immutable'
    suffix=f'V{a.version}' + ('Headless' if a.headless else '')
    tag=f'v{a.version}' + ('_headless' if a.headless else '')
    mission = ROOT/f'missions/BalticV30ShoreFinish{suffix}.BalticTrial'
    assert not a.out.exists() and not mission.exists(), 'Fresh paths required'
    assert sha(a.candidate) == a.expected_sha256.lower()
    t,old = np.load(a.candidate),np.load(OLD)
    h,cls=t['heights'].astype(float),t['cls']
    changed=h!=old['heights']
    _,near=distance_transform_edt(cls==0,return_indices=True)
    nearcls=cls[near[0],near[1]]
    locations=[]
    for code in range(1,8):
        for wet in (False,True):
            rr,cc=np.nonzero(changed&(nearcls==code)&((cls>0)==wet))
            if not len(rr): continue
            for i in np.unique(np.linspace(0,len(rr)-1,min(len(rr),24)).astype(int)):
                r,c=int(rr[i]),int(cc[i])
                if not (1<=r<2047 and 1<=c<2047): continue
                x,z=c*6.,12282-r*6.
                # Vertex plus one interior point from each native triangle of
                # the south-east cell; do not measure only grid vertices.
                locations.extend([(x,z),(x+4,z-2),(x+2,z-4)])
    detail=None
    if a.detail_baseline:
        detailed=np.load(a.detail_baseline)
        rr,cc=np.nonzero(h!=detailed['heights'])
        assert len(rr)<=4096, 'Detailed local readback has a bounded point budget'
        for r,c in zip(rr,cc):
            if not (1<=r<2047 and 1<=c<2047):continue
            x,z=float(c*6),float(12282-r*6)
            locations.extend([(x,z),(x+4,z-2),(x+2,z-4)])
        detail=dict(path=str(a.detail_baseline),sha256=sha(a.detail_baseline),vertices=len(rr))
    extra=None
    if a.extra_points:
        extra_data=json.loads(a.extra_points.read_text(encoding='utf-8'))
        assert extra_data['schema_version']==1 and extra_data['terrain_sha256']==a.expected_sha256.lower()
        assert len(extra_data['points'])<=4096
        for row in extra_data['points']:
            x,z=float(row['x']),float(row['z'])
            assert np.isfinite([x,z]).all() and 0<x<12282 and 0<z<12282
            locations.append((x,z))
        extra=dict(path=str(a.extra_points),sha256=sha(a.extra_points),points=len(extra_data['points']))
    atlas=json.loads(a.atlas.read_text())
    assert atlas['candidate_sha256']==a.expected_sha256.lower()
    sites=[s for s in atlas['sites'] if s['status']=='PREPARED']
    assert len(sites)==7
    locations.extend(tuple(s['view_xz']) for s in sites)
    q=np.unique(np.asarray(locations),axis=0)
    y=tri_sample(h,q[:,0],q[:,1]);previous=tri_sample(old['heights'].astype(float),q[:,0],q[:,1])
    planes=cell_planes(cls,t['level'])
    rr=np.clip(np.floor((12282-q[:,1])/6).astype(int),0,2046)
    cc=np.clip(np.floor(q[:,0]/6).astype(int),0,2046)
    p=planes[rr,cc]
    refs=[]
    for i,((x,z),ground,oldground,plane) in enumerate(zip(q,y,previous,p)):
        pond=bool(np.isfinite(plane))
        low=float(plane) if pond else .5
        high=float(plane) if pond else 1.
        kind='transition'
        # An exact cell boundary can resolve to either adjacent pond piece in
        # the opaque engine. Keep its height check; water acceptance uses the
        # two strict triangle-interior samples, never a guessed SE-cell owner.
        boundary=bool(abs(x/6-round(x/6))<1e-9 or abs(z/6-round(z/6))<1e-9)
        if not boundary:
            if ground < low-.05:kind='wet'
            elif ground > high+.05:kind='dry'
        refs.append(dict(id=i,x=float(x),z=float(z),expected_ground_m=float(ground),
                         previous_ground_m=float(oldground),kind=kind,on_cell_boundary=boundary,
                         pond_plane_m=float(plane) if pond else None))
    source_sha=sha(PARENT)
    text=PARENT.read_text(encoding='utf-8')
    text=text.replace('BalticV30DeltaMission',f'BalticV30ShoreFinish{suffix}Mission')
    text=text.replace('baltic_v30_delta_v1.log',f'baltic_v30_shorefinish_{tag}.log')
    header=f'BALTIC_V30_SHOREFINISH_{tag.upper()};BalticTrial'
    text=text.replace('BALTIC_V30_DELTA_V1',f'BALTIC_V30_SHOREFINISH_{tag.upper()}')
    text=replace_once(text,'m_BalticSites.Count() == 3 && m_BalticQueries.Count() == 1682',
                      f'm_BalticSites.Count() == 7 && m_BalticQueries.Count() == {len(q)}')
    text=replace_once(text,'LogTour("END;3")','LogTour("END;7")')
    first=sites[0]['view_xz']
    text=replace_once(text,'pos = "8346 0 10294"',f'pos = "{first[0]:.5f} 0 {first[1]:.5f}"')
    # This new fixture reuses its scratch collections. The executed parent is
    # preserved; no unrelated mission refactoring.
    text=replace_once(text,'    protected bool m_BalticQueriesDone;',
      '    protected bool m_BalticQueriesDone;\n    protected ref array<string> m_BalticParts = new array<string>;\n    protected ref array<string> m_BalticFields = new array<string>;\n    protected ref array<Man> m_BalticObservers = new array<Man>;')
    text=replace_once(text,'            array<string> parts = new array<string>;',
                      '            array<string> parts = m_BalticParts;\n            parts.Clear();')
    text=replace_once(text,'        array<Man> observers = new array<Man>;',
                      '        array<Man> observers = m_BalticObservers;\n        observers.Clear();')
    text=replace_once(text,'        array<string> fields = new array<string>;\n        m_BalticSites[stage]',
                      '        array<string> fields = m_BalticFields;\n        fields.Clear();\n        m_BalticSites[stage]')
    # The native compiler rejects the extended ten-field concatenation as
    # "Formula too complex". Preserve the record schema with short statements.
    text=replace_once(text,
      '            LogTour("Q;" + parts[0] + ";" + ground + ";" + sea + ";" + pond + ";" + noWave + ";" + depth + ";" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax());',
      '''            string queryRow = "Q;" + parts[0];
            queryRow = queryRow + ";" + ground;
            queryRow = queryRow + ";" + sea;
            queryRow = queryRow + ";" + pond;
            queryRow = queryRow + ";" + noWave;
            queryRow = queryRow + ";" + depth;
            queryRow = queryRow + ";" + GetGame().SurfaceGetSeaLevelMin();
            queryRow = queryRow + ";" + GetGame().SurfaceGetSeaLevelMax();
            queryRow = queryRow + ";" + GetGame().SurfaceGetSeaLevel();
            LogTour(queryRow);''')
    terminal='END;7'
    if a.headless:
        terminal=f'END_READBACK;{len(q)}'
        start=text.index('    override void OnUpdate(float timeslice)')
        finish=text.index('\n}\n\nMission CreateCustomMission',start)
        text=text[:start]+'''    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_BalticReady || m_BalticComplete) return;
        m_BalticElapsed = m_BalticElapsed + timeslice;
        if (m_BalticElapsed < 3) return;
        ReadQueryBatch();
        if (m_BalticQueriesDone)
        {
            m_BalticComplete = true;
            LogTour("'''+terminal+'''");
        }
    }
'''+text[finish:]
    mission.mkdir();a.out.mkdir(parents=True)
    (mission/'init.c').write_text(text,encoding='utf-8',newline='\n')
    rows=[]
    for s in sites:
        x,z=s['view_xz'];tx,tz=s['target_xz'];wx,wz=s['water_xz']
        rows.append(f'shore_{s["code"]};{x:.5f} 0 {z:.5f};{s["yaw"]:.5f} 0 0;{tx:.5f} 0 {tz:.5f};{wx:.5f} 0 {wz:.5f}')
    (mission/'sites.csv').write_text('\n'.join(rows)+'\n',encoding='ascii',newline='\n')
    (mission/'queries.csv').write_text(''.join(f'{r["id"]};{r["x"]:.5f} 0 {r["z"]:.5f}\n' for r in refs),encoding='ascii',newline='\n')
    assert sha(PARENT)==source_sha
    result=dict(status='FROZEN_BEFORE_RUNTIME',header=header,terminal_record=terminal,
                headless=a.headless,query_fields=10,
                mission=str(mission),query_count=len(refs),site_count=len(sites),sites=sites,points=refs,
                terrain_sha256=sha(a.candidate),parent_mission_sha256=source_sha,
                world_pbo_sha256=a.world_pbo_sha256.lower(),
                water_pbo_sha256=a.water_pbo_sha256.lower(),detail_baseline=detail,extra_cases=extra,
                scope='Changed vertices and both native triangle interiors, seven representative shore views.',
                tolerances=dict(height_m=.02,water_plane_m=.04,dry_depth_max_m=.03),
                files={str(p):sha(p) for p in mission.iterdir() if p.is_file()},
                limits=['Provisional old navmesh; this fixture makes no AI/path acceptance claim.',
                        'Temporary player placement is instrumentation, not traversal proof.',
                        'Low ponds need positive pond identification; sea covering a missing pond is not a presence proof.',
                        'Exact cell boundaries test ground only; water ownership there is not assumed.',
                        'Transition points test ground only: full dynamic tidal envelope is separate.',
                        'Images require independent observation and matched pose; logs alone do not pass visuals.'])
    (a.out/'reference.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],mission=str(mission),queries=len(refs),sites=len(sites),
                         changed_height_discriminators=sum(abs(r['expected_ground_m']-r['previous_ground_m'])>.04 for r in refs)),indent=2))


if __name__=='__main__':main()
