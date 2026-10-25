"""Freeze traceable overlapping full-river routes without changing terrain or water."""
from pathlib import Path
import hashlib
import heapq
import json
import math
import shutil
import numpy as np
import rasterio
from shapely import STRtree, points
from shapely.geometry import LineString, Point, shape
from shapely.ops import substring, unary_union
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def join(lines):
    result=[]
    for line in lines:
        coords=list(line.coords)
        if result and math.dist(result[-1],coords[0])>.002:
            raise ValueError('Disconnected full route')
        result.extend(coords if not result else coords[1:])
    return LineString(result)


def shortest_trace(lines, start, finish):
    """Node source overlaps/intersections; retain only existing line fragments."""
    network=unary_union(lines)
    pieces=list(network.geoms) if hasattr(network,'geoms') else [network]
    graph={}
    for piece in pieces:
        coordinates=list(piece.coords)
        for a,b in zip(coordinates,coordinates[1:]):
            if a==b:continue
            length=math.dist(a,b)
            graph.setdefault(a,[]).append((b,length));graph.setdefault(b,[]).append((a,length))
    queue=[(0.,tuple(start))];costs={tuple(start):0.};parents={}
    while queue:
        cost,node=heapq.heappop(queue)
        if cost!=costs[node]:continue
        if node==tuple(finish):break
        for end,length in graph.get(node,[]):
            if cost+length<costs.get(end,math.inf):
                costs[end]=cost+length;parents[end]=node;heapq.heappush(queue,(cost+length,end))
    if tuple(finish) not in costs:raise ValueError('Disconnected source trace')
    nodes=[tuple(finish)]
    while nodes[-1]!=tuple(start):nodes.append(parents[nodes[-1]])
    route=LineString(nodes[::-1])
    if not route.is_simple or route.difference(network).length>.00001:
        raise ValueError('Shortest trace left source linework')
    return route


def main():
    ev=ROOT/'evidence/overnight-2026-10-01/full-river-v1'
    mission=ROOT/'missions/BalticFullRiverV1.BalticTrial'
    if ev.exists() or mission.exists():raise ValueError('Fresh outputs required')
    parent=ROOT/'evidence/overnight-2026-10-01/regional-boat-v3/reference.json'
    previous=json.loads(parent.read_text())
    for path,digest in previous['inputs'].items():assert sha(Path(path))==digest,path
    terrain=Path(previous['terrain']);assert sha(terrain)==previous['terrain_sha256']
    with rasterio.open(terrain) as ds:h=ds.read(1)
    features=json.loads((ROOT/'evidence/regional-foundation-v1/fairways-main-game.json').read_text())['features']
    axes=[shape(f['geometry']) for f in features]
    bridge_lane=LineString(previous['cases'][0]['waypoints_xz'])
    fixed=[];selected=[]
    for index,feature in enumerate(features):
        if feature['properties']['river']!='Narva':continue
        selected.append(index)
        axis=axes[index]
        if index==30:
            start=axis.project(Point(bridge_lane.coords[0]));end=axis.project(Point(bridge_lane.coords[-1]))
            axis=join([substring(axis,0,start),bridge_lane,substring(axis,end,axis.length)])
        fixed.append(axis)
    narva=shortest_trace(fixed,(1020.,4650.),(1920.,7440.))
    channels=[('Luga principal',join([axes[i] for i in (34,32,31)]),[34,32,31]),
              ('Narva principal',narva,selected),
              ('Neva principal',axes[35],[35]),
              ('Delta norte',join([axes[42],axes[37]]),[42,37]),
              ('Delta norte corto',join([axes[42],axes[41],axes[39]]),[42,41,39]),
              ('Delta occidental',axes[38],[38]),('Delta ramal40',axes[40],[40])]
    surface=ROOT/'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson'
    water=json.loads(surface.read_text())['features']
    ocean=ROOT/'evidence/regional-foundation-v1/ocean-game.json'
    geometries=[shape(f['geometry']) for f in water]+[shape(json.loads(ocean.read_text())['features'][0]['geometry'])]
    levels=np.r_[[f['properties']['level_m'] for f in water],.5];tree=STRtree(geometries)
    def query(xz):
        hits=tree.query(points(xz),predicate='intersects');lev=np.full(len(xz),-np.inf)
        np.maximum.at(lev,hits[0],levels[hits[1]])
        ground=sample(h,xz[:,0]+200000,xz[:,1])
        return lev,ground
    cases=[];csv=[];audits=[];channel_report=[]
    for name,line,source_ids in channels:
        original_length=line.length
        if not line.is_simple:
            line=shortest_trace([line],line.coords[0],line.coords[-1])
        count=math.ceil(line.length/3500)
        starts=np.linspace(0,line.length,count+1)
        intervals=[]
        for part in range(count):
            begin=max(0,starts[part]-20);end=min(line.length,starts[part+1]+20)
            sub=substring(line,begin,end);intervals.append([float(begin),float(end)])
            ds=np.linspace(0,sub.length,math.ceil(sub.length/4)+1)
            coords=np.asarray([sub.interpolate(d).coords[0] for d in ds],dtype='float32').astype(float)
            dense=np.asarray([sub.interpolate(d).coords[0] for d in np.linspace(0,sub.length,math.ceil(sub.length/.5)+1)],dtype='float32').astype(float)
            tangent=np.gradient(dense,axis=0);length=np.linalg.norm(tangent,axis=1)
            normal=np.column_stack([-tangent[:,1],tangent[:,0]])/length[:,None]
            tested=np.vstack([dense,dense+4*normal,dense-4*normal]);lev,ground=query(tested)
            failed=(~np.isfinite(lev))|(lev-ground<3)
            audit=dict(channel=name,part=part,samples=len(tested),failed=int(failed.sum()),
                       minimum_depth_m=float(np.min((lev-ground)[np.isfinite(lev)])),
                       missing_water=int((~np.isfinite(lev)).sum()),first_failed_xz=tested[failed][:10].tolist())
            audits.append(audit)
            w,g=query(coords);ident=len(cases)
            for seq,(xz,water_y) in enumerate(zip(coords,w)):
                csv.append(f'{ident};{seq};{xz[0]:.9g};{water_y:.9g};{xz[1]:.9g}')
            cases.append(dict(case=ident,river=name,reverse=False,part=part,source_ids=source_ids,
                              source_interval_m=[float(begin),float(end)],length_m=float(sub.length),
                              waypoints_xz=coords.tolist(),water_levels=w.tolist(),
                              minimum_dense_center_depth_m=float(np.min(query(dense)[0]-query(dense)[1]))))
        channel_report.append(dict(channel=name,length_m=float(line.length),original_trace_length_m=float(original_length),source_ids=source_ids,intervals=intervals,
                                   covered=intervals[0][0]==0 and intervals[-1][1]==line.length and all(a[1]>=b[0] for a,b in zip(intervals,intervals[1:]))))
    ev.mkdir(parents=True)
    geometry=dict(status='PASS_FROZEN_CHANNEL_GEOMETRY' if not any(a['failed'] for a in audits) else 'FAIL_FROZEN_CHANNEL_GEOMETRY',
                  audits=audits,channels=channel_report,cases=len(cases),
                  total_channel_m=sum(c['length_m'] for c in channel_report),
                  limit='Selected main-channel coverage, not all secondary river branches or physical engine acceptance.')
    (ev/'geometry.json').write_text(json.dumps(geometry,indent=2)+'\n')
    if geometry['status'].startswith('FAIL'):
        print(json.dumps(geometry,indent=2));return
    mission.mkdir(parents=True)
    source=ROOT/'missions/BalticRegionalBoatV3.BalticTrial/init.c'
    assert sha(source)=='66e3515497ece9ace70b782c90acf2bddae378ae854c112f2f473abd6604e1e6'
    code=source.read_text()
    start=code.index('class BalticRegionalBoatMission: MissionServer')
    end=code.index('Mission CreateCustomMission')
    code=code[start:end].replace('class BalticRegionalBoatMission: MissionServer','class BalticFullRiverRunner')
    code=code.replace('EMPTY_BOAT_INDEPENDENT_OUTWARD_AND_REVERSE_NO_TURN_OR_CREW_ACCEPTANCE',
                      'EMPTY_BOAT_SINGLE_DIRECTION_OVERLAPPING_SEGMENT_NO_TURN_OR_CREW_ACCEPTANCE')
    code=code.replace('override void OnInit()','void Start(int caseIndex)').replace('        super.OnInit();','        m_Case=caseIndex;')
    code=code.replace('"$profile:baltic_regional_boat_v3.log"','"$profile:baltic_fullriver_v1_"+m_Case+".log"')
    code=code.replace('CallLater(BeginNext,30000,false)','CallLater(BeginNext,30000+60000*m_Case,false)')
    a=code.index('        m_Case++;');b=code.index('        m_Route.Clear();',a);code=code[:a]+code[b:]
    code=code.replace('for (int i=0;i<last;i++)','for (int i=Math.Max(0,m_Target - 12);i<Math.Min(last,m_Target + 12);i++)')
    code=code.replace('seconds>450','seconds>4200')
    code=code.replace('        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginNext,2000,false);',
                      '        if (m_Log) { FPrintln(m_Log,"END;ALL_CASES_COMPLETE"); CloseFile(m_Log); m_Log=null; }')
    last=code.rfind('}')
    code=code[:last]+'''    void Cancel()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BeginNext);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BoatTick);
        if (m_Active) EndCase("ABORTED_MISSION_FINISH");
        else if (m_Log) { CloseFile(m_Log); m_Log=null; }
    }
'''+code[last:]
    wrapper='''void main() { Print("BALTIC_FULL_RIVER_V1"); }
class BalticFullRiverMission: MissionServer
{
    protected ref array<ref BalticFullRiverRunner> m_Runners;
    override void OnInit()
    {
        super.OnInit();
        m_Runners=new array<ref BalticFullRiverRunner>;
        for (int i=0;i<CASECOUNT;i++)
        {
            BalticFullRiverRunner runner=new BalticFullRiverRunner;
            m_Runners.Insert(runner); runner.Start(i);
        }
    }
    override void OnMissionFinish()
    {
        if (m_Runners) foreach (BalticFullRiverRunner runner:m_Runners) runner.Cancel();
        super.OnMissionFinish();
    }
}
Mission CreateCustomMission(string path) { return new BalticFullRiverMission(); }
'''.replace('CASECOUNT',str(len(cases)))
    (mission/'init.c').write_text(code+wrapper)
    (mission/'routes.csv').write_text('\n'.join(csv)+'\n',encoding='ascii')
    destination=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    if destination.exists():raise ValueError('Fresh deployment required')
    shutil.copytree(mission,destination)
    ref=dict(status='FROZEN_DEPLOYED_ENGINE_PENDING',terrain=str(terrain),terrain_sha256=sha(terrain),
             inputs=previous['inputs'],deployment=previous['deployment'],mission={str(p):sha(p) for p in mission.iterdir()},
             parent_reference_sha256=sha(parent),parent_mission_sha256=sha(source),cases=cases,
             log_version=2,criteria=previous['criteria'],channels=channel_report,
             start_spacing_s=60,timeout_per_case_s=4200,
             limits=['Empty independently spawned boats; no crew or medium-vessel acceptance.',
                     'Overlapping continuous segments provide coverage; not one boat traveling end-to-end.',
                     'One direction only; selected main channels and four delta routes, not every side branch.',
                     'Same V3 controller except bounded route-distance scan and timeout; independent whole-route verifier unchanged.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(status=ref['status'],cases=len(cases),total_channel_m=geometry['total_channel_m'],
                         longest_case_m=max(c['length_m'] for c in cases),geometry=geometry['status'],
                         mission_sha256=sha(mission/'init.c')),indent=2))


if __name__=='__main__':main()
