"""Check the fresh engine record against the frozen pilot, keeping motion separate."""
import argparse
import json
from pathlib import Path
import numpy as np
import rasterio
from shapely.geometry import shape
from waterway_common import ROOT, sha, read_base, sample
from verify_narva_navigation import intersecting_triangles


def truth(s):
    if s.casefold() in ('true','1'): return True
    if s.casefold() in ('false','0'): return False
    raise ValueError('Unexpected bool '+s)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    folder=ROOT/'tests/narva_navigation_v3'
    design=json.loads((folder/'design.json').read_text())
    asc=folder/'narva_navigation_v1.asc'
    if sha(asc)!=design['candidate_sha256']: raise ValueError('Candidate drift')
    text=args.log.read_text(encoding='utf-8-sig')
    lines=text.splitlines()
    complete=bool(lines and lines[-1].startswith('END;'))
    expected={(200000+6*c,12282-6*r) for tri in intersecting_triangles(shape(design['depth_check_polygon_tb'])) for r,c in tri}
    grounds=[line.split(';') for line in lines if line.startswith('G;')]
    coords=[(float(g[1])+200000,float(g[2])) for g in grounds]
    gx=np.array([p[0] for p in coords]);gz=np.array([p[1] for p in coords])
    actual=np.array([float(g[3]) for g in grounds])
    with rasterio.open(asc) as ds: h=ds.read(1)
    error=float(np.max(abs(actual-sample(h,gx,gz)))) if len(actual) else None
    old_error=float(np.max(abs(actual-sample(read_base(),gx,gz)))) if len(actual) else None
    waters=[line.split(';') for line in lines if line.startswith('W;')]
    water=[float(x) for x in waters[0][1:]] if len(waters)==1 else []
    objects=[line.split(';') for line in lines if line.startswith('O;')]
    decks=[]
    for obj in objects:
        if 'bridge_metal_25' in obj[1].lower():
            deck=[float(x) for x in obj[4].strip('<>').replace(',',' ').split()]
            decks.append(deck)
    checks={
        'correct_header':bool(lines) and lines[0] in {'BALTIC_BOAT_PROBE_V3','BALTIC_BOAT_ROUTE_INPUT_V1'},
        'correct_ASC_marker':'ASC='+design['candidate_sha256'] in lines,
        'terminated_record':complete,
        'coordinates_exact_and_unique':len(coords)==len(expected) and len(set(coords))==len(coords) and set(coords)==expected,
        'terrain_error_le_5_1mm':error is not None and error<=.0051,
        'old_terrain_rejected':old_error is not None and old_error>.0051,
        'all_channel_points_flagged_sea':bool(grounds) and all(truth(g[5]) for g in grounds),
        'measured_water_range_matches_design':water[:2]==design['water_min_max_m'],
        'conservative_depth_ge_3m':bool(water) and len(actual)>0 and water[0]-float(actual.max())>=3,
        'three_decks_at_9m':len(decks)==3 and max(abs(p[1]-9) for p in decks)<=.0051,
    }
    rows=[line.split(';') for line in lines if line.startswith('B;')]
    motion={'status':'INCONCLUSIVE_NO_MOTION_RECORD','samples':len(rows),
            'end_reason':lines[-1][4:] if complete else None}
    if rows:
        pos=np.array([[float(r[2]),float(r[3]),float(r[4])] for r in rows])
        health=np.array([float(r[7]) for r in rows])
        motion.update({'horizontal_distance_from_first_m':float(np.linalg.norm((pos[-1]-pos[0])[[0,2]])),
            'maximum_horizontal_step_m':float(np.max(np.linalg.norm(np.diff(pos[:,[0,2]],axis=0),axis=1))) if len(pos)>1 else 0,
            'health_first_min_last': [float(health[0]),float(health.min()),float(health[-1])],
            'engine_on_samples':sum(truth(r[9]) for r in rows),
            'max_speed_m_s':max(float(r[6]) for r in rows),
            'max_reported_throttle':max(float(r[14]) for r in rows),
            'highest_target_index':max(int(r[15]) for r in rows),
            'first_position':pos[0].tolist(),'last_position':pos[-1].tolist()})
        motion['status']='EMPTY_BOAT_OUTWARD_ONLY' if motion['end_reason']=='OUTWARD_ROUTE_REACHED_EMPTY_BOAT_ONLY' else 'INCONCLUSIVE_CONTROL_OR_PHYSICS'
    report={'geometry_status':'PASS_SAMPLED_CHANNEL_AND_DECKS' if all(checks.values()) else 'FAIL_OR_INCOMPLETE',
            'checks':checks,'log_sha256':sha(args.log),'candidate_sha256':sha(asc),
            'terrain_samples':len(grounds),'max_terrain_error_m':error,'old_ASC_max_error_m':old_error,
            'water_min_max_current':water,'deck_world_points':decks,'motion':motion,
            'limits':['No native TB persistence proof.',
                      'Ground is measured at channel support vertices; collision mesh was not queried.',
                      'Boat is empty; no crew, return journey, whole-river or AI acceptance.',
                      'Bootstrap navmesh is stale for this geometry.']}
    args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__=='__main__': main()
