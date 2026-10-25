"""Post-build geometric invariants and profile self-consistency for a continuity fix."""
from pathlib import Path
import argparse
import json

import numpy as np
import rasterio
import shapely
from shapely.geometry import shape

from audit_fairway_triangles_v30 import save,sha
from finish_shores_v30 import protect_corridors
from review_pond_recovery_v30 import face_angles
from v30_common import cell_planes,grid_xz,vertex_plane_bounds

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('E:/DayZ-Baltic-Build/v30-pond-recovery/terrain_v30.npz')
SOURCE_SHA='2f954ad52893a78181df0f607ddd5e490a470fe9c634bcf30736ed1aef4c179a'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--audit-name',default='small-watercourses-v2.json')
    ap.add_argument('--road-name',default='road-gates-historical.json')
    ap.add_argument('--legacy-name',default='legacy-terrain-gates-v2.json')
    a=ap.parse_args();assert not a.out.exists() and sha(SOURCE)==SOURCE_SHA
    old=np.load(SOURCE);new=np.load(a.candidate)
    oh,nh=old['heights'].astype(float),new['heights'].astype(float)
    cls=old['cls'];changed=oh!=nh
    nature=np.load(ROOT/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
    plane=cell_planes(cls,old['level']);pmin,pmax=vertex_plane_bounds(plane)
    _,margin,channels,_=protect_corridors(plane)
    water=ROOT/'tests/water_v3/water_v3.geojson';streams=ROOT/'tests/water_v3/streams_candidates.geojson'
    feats=[f for f in json.loads(water.read_text())['features'] if f['properties']['class']=='river']
    feats += [f for f in json.loads(streams.read_text())['features'] if f['properties']['tier_m']>=2500]
    # Independent authoring bound: support vertices are <= one native cell
    # diagonal from an approved polygon. This does not reuse the saved mask.
    envelope=shapely.union_all([shape(f['geometry']) for f in feats]).buffer(8.486)
    xx,zz=grid_xz();within=shapely.covers(envelope,shapely.points(xx[changed],zz[changed]))
    secondary=np.isin(cls,(5,6));dry=cls==0
    fixed=old['platform']|old['reserve']|old['narva']|old['beach']|margin
    fixed|=nature&~secondary
    boundary=(xx<12)|(zz<12)|(xx>12270)|(zz>12270)
    newsteep=worsened=0
    for oa,na in zip(face_angles(oh),face_angles(nh)):
        newsteep+=int(((na>35.0001)&(oa<=35.0001)).sum())
        worsened+=int(((na>35.0001)&(na>oa+.0001)).sum())
    before=json.loads((SOURCE.parent/a.audit_name).read_text())
    after=json.loads((a.candidate.parent/a.audit_name).read_text())
    assert before['terrain_sha256']==SOURCE_SHA and after['terrain_sha256']==sha(a.candidate)
    assert before['sources']==after['sources'] and before['code']==after['code']
    assert before['schema_version']==after['schema_version']==2
    assert before['target_depth_m']==after['target_depth_m']==.05
    diagnostics={k:dict(before_dry_unreserved_km=before['summary'][k]['dry_unreserved_km'],
                        after_dry_unreserved_km=after['summary'][k]['dry_unreserved_km'],
                        remaining_breaks_over_6m=after['summary'][k]['breaks_over_6m']) for k in ('river','stream')}
    checks=dict(nonempty=bool(changed.any()),finite=bool(np.isfinite(nh).all()),
                within_approved_watercourse_support=bool(within.all()),
                changed_only_small_water_or_land=bool(np.all((secondary|dry)[changed])),
                all_fixed_heights_exact=not bool((changed&fixed).any()),
                border_exact=not bool((changed&boundary).any()),
                nature_dry_land_exact=not bool((changed&nature&~secondary).any()),
                bounded_lowering_only=bool(np.all(nh<=oh) and (oh-nh).max()<=3.00001),
                altered_water_bed_depth_bound=bool(np.all(nh[changed&secondary]>=np.nan_to_num(pmin[changed&secondary],nan=.5)-1.20001)),
                altered_dry_floor=bool(np.all(nh[changed&dry]>=1.4)),
                altered_dry_piece_freeboard=bool(np.all(nh[changed&dry]>=np.nan_to_num(pmax[changed&dry],nan=-np.inf)+.05-1e-5)),
                no_new_or_worsened_steep_faces=worsened==0,
                correct_channel_count=len(channels)==23,
                profile_axis_coverage_improves=all(d['after_dry_unreserved_km']<d['before_dry_unreserved_km'] for d in diagnostics.values()))
    for k in old.files:
        if k!='heights':checks['field_'+k+'_exact']=bool(np.array_equal(old[k],new[k],equal_nan=True))
    with rasterio.open(a.candidate.parent/'baltic_terrain_v30.asc') as ds:
        checks['asc_exact']=bool(np.array_equal(ds.read(1),new['heights']))
    roads=json.loads((a.candidate.parent/a.road_name).read_text())
    legacy=json.loads((a.candidate.parent/a.legacy_name).read_text())
    checks['gate_provenance_matches_candidate']=roads['terrain_sha256']==legacy['terrain_sha256']==sha(a.candidate)
    checks['original_76536_road_stations_pass']=roads['status']=='PASS' and roads['samples']==76536 and roads['chains']==100
    checks['road_eligibility_source_is_original_v30']=roads['sources'].get(roads['water_spec'].split('::')[0])=='365c2a9400be80791e38c0c406152c87247e663205f1bc818604f05ea150c360'
    checks['legacy_geometry_except_documented_narva_pass']=all(legacy[k]['fail']==0 for k in (
        'water_depth','banks','land_floor','slopes','pieces','bed_floor')) and legacy['land_floor']['beach_fail']==0
    result=dict(status='PASS_SCOPED_CONTINUITY_IMPROVEMENT' if all(checks.values()) else 'FAIL',checks=checks,
                source_sha256=SOURCE_SHA,candidate_sha256=sha(a.candidate),changed_vertices=int(changed.sum()),
                changed_nature_water_vertices=int((changed&nature).sum()),
                new_steep_faces=newsteep,new_or_worsened_steep_faces=worsened,diagnostics=diagnostics,
                limits=['Residual interruptions are explicit: this is not full watercourse continuity acceptance.',
                        'Old full Narva circle differs only by the separately checked four-pond repair, inherited unchanged here.',
                        'No new water model or level: existing pond recovery pieces remain the geometry source.',
                        'Engine readback, visuals, native import/export and new navmesh remain required.'])
    save(a.out,result);print(json.dumps(result,indent=2))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':raise SystemExit(main())
