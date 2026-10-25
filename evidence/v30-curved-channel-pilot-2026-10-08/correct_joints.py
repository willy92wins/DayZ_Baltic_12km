"""The single allowed correction: align pitched native edges and overlap by 1 cm."""
from pathlib import Path
import copy,json,math,sys
import numpy as np
import shapely
from shapely.geometry import Point,Polygon,box
E=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-curved-channel-pilot-2026-10-08')
sys.path.insert(0,str(E))
import curved_pilot as g
assert not (E/'correction.json').exists(),'Only one correction'
poses=copy.deepcopy(json.loads((E/'A-poses.json').read_text()))
def edge(p,key):
    f=g.lib[p['type']][key]
    return np.array([f['mid'][0],f['y'],f['mid'][1]])@np.array(p['matrix'][:9]).reshape(3,3)+np.array(p['matrix'][9:])
translations=[]
for i in range(1,len(poses)):
    prev,cur=poses[i-1],poses[i]
    ang=prev['yaw']+math.radians(g.lib[prev['type']]['start']['heading_deg'])
    down=-np.array([math.sin(ang),math.cos(ang)])
    delta=edge(prev,'start')[[0,2]]-edge(cur,'end')[[0,2]]-.01*down
    cur['matrix'][9]+=float(delta[0]);cur['matrix'][11]+=float(delta[1])
    translations.append(dict(piece=i,dx_m=float(delta[0]),dz_m=float(delta[1])))
# WRP consumer precision, not just high-precision authoring.
for p in poses:p['matrix']=np.asarray(p['matrix'],dtype=np.float32).astype(float).tolist()
geo=g.geometric(poses)
control=json.loads((E/'baseline-samples.json').read_text())
rows=g.physical_samples(poses)
phys=g.screen(rows,control)
u=shapely.union_all(g.polys(poses))
pond_overlap_all=float(u.intersection(g.pond).area)
# Fixed 3 m lattice over the changed placement's bounds: vertices and centers.
lo=u.bounds
new_pieces=[g.ewm.Piece(p['type'],p['matrix']) for p in poses]
old_pieces=[g.ewm.Piece(p['type'],p['matrix']) for p in g.a['pieces']]
dry_bad=[];checked=0
for x in np.arange(math.floor(lo[0]/6)*6,lo[2]+.01,3):
    for z in np.arange(math.floor(lo[1]/6)*6,lo[3]+.01,3):
        if not u.covers(Point(x,z)):continue
        ground=float(g.tri_sample(g.h,x,z))
        old=[q.level(x,ground+.01,z) for q in old_pieces]
        old += [y for poly,y,_ in g.retained if poly.covers(Point(x,z))]
        old=[v for v in old if v is not None]
        before=max(old) if old else None
        new=[q.level(x,ground+.01,z) for q in new_pieces]
        new += [y for poly,y,_ in g.retained if poly.covers(Point(x,z))]
        new=[v for v in new if v is not None]
        after=max(new) if new else None
        checked+=1
        if (before is None or before<=ground) and after is not None and after>ground+1e-6:
            dry_bad.append(dict(x=float(x),z=float(z),ground=ground,old=before,new=after))
# Real positive/negative consumers; previous initial checks were not sufficient
# because both uncorrected candidates failed. Keep their record as history.
positive=geo['geometry_pass'] and phys['pass_local']
removed=g.geometric(poses[:2])
duplicate=g.geometric(poses+[poses[1]])
mutant=copy.deepcopy(g.lib);mutant[poses[0]['type']]['sha256']='0'*64
try:g.validate_native_models(mutant);hash_rejected=False
except AssertionError:hash_rejected=True
depth_bad=copy.deepcopy(rows);depth_bad[0]['level']=depth_bad[0]['ground']-1
depth_rejected=not g.screen(depth_bad,control)['pass_local']
negative=dict(positive_candidate=positive,removed_piece_rejected=not removed['geometry_pass'],
              duplicated_piece_rejected=duplicate['multi_share']>.01,altered_hash_rejected=hash_rejected,
              dry_depth_rejected=depth_rejected)
out=dict(status='CORRECTION_EVALUATED',correction_budget_used=1,poses=poses,translations=translations,
         geometry=geo,physical=phys,new_wet_sample_count=len(dry_bad),new_wet_samples=dry_bad[:20],
         lattice_checked=checked,lattice_step_m=3,retained_pond_overlap_total_m2=pond_overlap_all,
         negative_controls=negative,
         local_pass=positive and not dry_bad and all(negative.values()),
         limits=['The full retained-pond overlap still requires integration treatment; piece-only <=1% is not total-water acceptance.',
                 'Three-meter lattice does not certify every point of mixed shore triangles.',
                 'No engine or visual acceptance; source geometry only, matrices rounded to WRP float32.'])
(E/'A1-poses.json').write_text(json.dumps(poses,indent=2)+'\n',encoding='utf-8')
(E/'A1-samples.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
(E/'correction.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('poses','new_wet_samples')},indent=2))
