"""OT3 independent check: native terrain, pinned delta, real roadway and Livonia end exposure.
No dam producer/gate/probe helpers are imported. Usage: script.py regate_root output.json
The current accepted kit is also checked locally; final integrated terrain still needs OT7 validation.
"""
import csv,hashlib,json,pathlib,sys
import numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,'C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts')
from odol_reader import ODOL
B=pathlib.Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013')
WT=pathlib.Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
run,out=map(pathlib.Path,sys.argv[1:3]);dam=run/'dam'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((B/'handoff-20261018/wip/ev112-dam-r3-top/deliver-manifest-9.json').read_text())
source_checks={r['dst']:sha(pathlib.Path(r['dst']))==r['sha256'] for r in manifest}
base=np.load(B/'ev110/terrain-ev110.npz');z=np.load(dam/'terrain-dam-buried.npz')
H0=base['heights'].astype(float);H=z['heights'].astype(float)
contract=json.loads((WT/'evidence/v31-pond-layer-2026-10-13/dam/frozen-exception-narva.json').read_text())
want={(v['r'],v['c']):v for v in contract['vertices']}
moved={tuple(map(int,p)) for p in np.argwhere(H!=H0)}
checks=dict(sources_delivered=all(source_checks.values()),exact_21_vertices=moved==set(want) and len(moved)==21,
            old_heights=all(H0[k]==v['old'] for k,v in want.items()),
            new_heights=all(abs(H[k]-v['new'])<=1e-4 for k,v in want.items()),
            no_lowering=bool((H>=H0).all()),
            masks_unchanged=all(np.array_equal(base[k],z[k],equal_nan=True) for k in base.files if k!='heights'),
            changed_mask=bool(np.array_equal(z['v31_dam'],H!=H0)))
water={}
for name,oldp,newp in [('cover',B/'ev110/kit/cover-ev108.npy',dam/'cover-dam.npy'),
                       ('envelope',B/'ev110/bridges/envelope-br.npy',dam/'envelope-dam.npy')]:
 a,b=np.load(oldp),np.load(newp);both=np.isfinite(a)&np.isfinite(b)
 removed={tuple(map(int,p)) for p in np.argwhere(np.isfinite(a)&~np.isfinite(b))}
 cut={(v['r'],v['c']) for v in contract['cut_cells']}
 water[name]=dict(removed=len(removed),added=int((~np.isfinite(a)&np.isfinite(b)).sum()),
                  kept_levels_equal=bool(np.array_equal(a[both],b[both])))
 checks[name+'_contract']=removed==cut and len(cut)==33 and water[name]['added']==0 and water[name]['kept_levels_equal']

def terrain(H,x,z,step=6.,top=12282.):
 c=x/step;r=(top-z)/step if top is not None else z/step
 ci,ri=int(np.floor(c)),int(np.floor(r));u,v=c-ci,r-ri
 nw,ne,sw,se=H[ri,ci],H[ri,ci+1],H[ri+1,ci],H[ri+1,ci+1]
 if top is not None:return nw+u*(ne-nw)+v*(se-ne) if u>=v else nw+v*(sw-nw)+u*(se-sw)
 return nw+u*(ne-nw)+v*(sw-nw) if u+v<1 else se+(1-u)*(sw-se)+(1-v)*(ne-se)

model=pathlib.Path('P:/DZ/structures/industrial/dams/dam_stone_40.p3d')
od=ODOL.from_file(str(model));rw=[l for l in od.lods if abs(l.resolution-3e15)<=3e9]
assert len(rw)==1 and not od.lod_errors
V=np.array([(v.x,v.y,v.z) for v in rw[0].vertices])
tri=np.array([V[[f.vertex_indices[0],f.vertex_indices[k],f.vertex_indices[k+1]]]
              for f in rw[0].faces for k in range(1,len(f.vertex_indices)-1)])
records=json.loads((dam/'dam-records.json').read_text())
assert len(records)==2
world=[]
for rec in records:
 m=np.asarray(rec['matrix'],dtype=np.float32).astype(float)
 world.extend(tri@m[:9].reshape(3,3)+m[9:12])
world=np.asarray(world)
def roadway(q):
 heights=[]
 for t in world:
  matrix=np.vstack((t[:,[0,2]].T,np.ones(3)))
  if abs(np.linalg.det(matrix))<1e-9:continue
  w=np.linalg.solve(matrix,np.r_[q,1.])
  if w.min()>=-1e-8:heights.append(float(w@t[:,1]))
 return max(heights) if heights else None
points=json.loads((dam/'probe/points.json').read_text())['points']
ground_errors=[];crest_errors=[];bad_class=[]
plane=np.load(dam/'bury-work/fp0/footprint.npz')['plane']
for p in points:
 t=terrain(H,p['x'],p['z']);ground_errors.append(abs(t-p['terrain_y']))
 if p['kind']=='crest':
  road=roadway([p['x'],p['z']]);assert road is not None
  crest_errors.append(abs(road-p['expect_roadway_y']))
 level=plane[int((12282-p['z'])//6),int(p['x']//6)]
 pond='none' if not np.isfinite(level) or level-t<=-.1 else ('wet' if level-t>=.1 else 'edge')
 tide='always_sea' if t<.45 else ('never_sea' if t>1.05 else 'tidal')
 if pond!=p['pond_class'] or tide!=p['tide_class']:bad_class.append(p['id'])
checks.update(probe_ground=max(ground_errors)<.001,probe_roadway=max(crest_errors)<.001,probe_classes=not bad_class)

# Reference endpoint exposure on the actual Livonia height grid and CSV transforms.
data=pathlib.Path('E:/DayZ-Baltic-Build/vanilla-tricks-20261013/data')
LH=np.load(data/'enoch_height.npy');meta=json.loads((data/'enoch_meta.json').read_text())
liv=[];n_liv=0;top=float(V[:,1].max())
for rec in csv.DictReader((data/'enoch_objects.csv').open(encoding='utf-8')):
 if 'dam_stone_40' not in rec['shape']:continue
 n_liv+=1
 M=np.array([[float(rec['ax_x']),float(rec['ay_x']),float(rec['az_x'])],
             [float(rec['ax_y']),float(rec['ay_y']),float(rec['az_y'])],
             [float(rec['ax_z']),float(rec['ay_z']),float(rec['az_z'])]])
 T=np.array([float(rec[k]) for k in ('x','y','z')])
 assert np.allclose(M[1],[0,1,0],atol=1e-5) and np.allclose(M[:,1],[0,1,0],atol=1e-5),M.tolist()
 for end in (-20.,20.):
  for zz in (-2.04,0.,2.04):
   p=M@np.array([end,0.,zz])+T
   liv.append(T[1]+top-terrain(LH,p[0],p[2],meta['step'],None))
ends=[]
for k,rec in enumerate(records):
 m=np.asarray(rec['matrix'],np.float32).astype(float)
 # Narva's two pieces join at their inner ends; only the outside end is free.
 assert np.allclose(m[:9].reshape(3,3),np.eye(3),atol=1e-6)
 side=-20. if m[9]==min(r['matrix'][9] for r in records) else 20.
 for zz in (-2.04,0.,2.04):
  p=np.array([side,0.,zz])@m[:9].reshape(3,3)+m[9:12]
  ends.append(m[10]+top-terrain(H,p[0],p[2]))
checks['end_exposure_reference']=n_liv==7 and min(ends)>=min(liv) and max(ends)<=max(liv)

# The final kit is read here, not the old kit prototype used by nbhd.py.
kit=np.load(B/'ev112-ot1-20261018/run-l/terrain-ev108.npz')
r,c=np.mgrid[0:2048,0:2048];box=np.hypot(6*c-2428,12282-6*r-6942)<=110
checks['current_kit_same_near_dam']=bool(np.array_equal(kit['heights'][box],base['heights'][box]))
checks={k:bool(v) for k,v in checks.items()}
result=dict(passed=all(checks.values()),checks=checks,sources=source_checks,water=water,
            model_sha256=sha(model),moved_vertices=len(moved),max_raise_m=float((H-H0).max()),
            probe=dict(points=len(points),crest_points=len(crest_errors),max_ground_error=max(ground_errors),
                       max_roadway_error=max(crest_errors),classification_mismatches=bad_class),
            end_exposure=dict(livonia_dams=n_liv,reference_range=[min(liv),max(liv)],narva=ends,margin_m=max(liv)-max(ends)),
            limits='Offline EV110-based regate; remeasure on the final integrated EV112 chain and in OT8.')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k!='sources'},indent=2))
sys.exit(0 if result['passed'] else 1)
