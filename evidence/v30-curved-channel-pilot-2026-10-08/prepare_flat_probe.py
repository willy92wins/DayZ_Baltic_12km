"""Freeze server water/bed readback and the existing R1 boat consumer before launch."""
from pathlib import Path
import hashlib,json,math,shutil,subprocess,sys
import numpy as np
from shapely.geometry import LineString,Point
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008');E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from v30_common import tri_sample,cell_planes
from verify_channel_reaches_v30 import retained_pond_surface
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
terrain=B/'r3-transition-proposal/terrain_flat.npz';t=np.load(terrain);h=t['heights'].astype(float)
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
manifest=json.loads((B/'flat-water/water/pieces.json').read_text())
rows=json.loads((E/'flat-samples.json').read_text());selected=[]
for name,a in axes.items():
    possibles=[p for p in rows if p['reach']==name and p['new'] is not None and p['new']-float(tri_sample(h,p['x'],p['z']))>=.25]
    for fraction in (.2,.5,.8):
        s=a['s_lo']+fraction*(a['s_hi']-a['s_lo']);xz=np.array([np.interp(s,a['s'],a['x']),np.interp(s,a['s'],a['z'])])
        point=min(possibles,key=lambda p:np.linalg.norm(np.array([p['x'],p['z']])-xz))
        selected.append((point['x'],point['z'],'high_pond_control',name))
for p in json.loads((E/'flat-verification.json').read_text())['wet_failures']:
    selected.append((p['x'],p['z'],'high_pond_control','R3_repaired_shallow'))
for x,z in [(1992,6432),(1836,6384)]:selected.append((x,z,'high_pond_control','previous_repair_control'))
selected.append((2207.5,7080.5,'frozen_shallow_failure','previous_gap_repair'))
base=np.load('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz')['heights'].astype(float)
for name,a in axes.items():
    rc=sorted({(r+dr,c+dc) for r,c in a['removed_cells'] for dr in (0,1) for dc in (0,1) if t['cls'][r+dr,c+dc]==0})
    r,c=max(rc,key=lambda rc:abs(h[rc]-base[rc]))
    selected.append((c*6,12282-r*6,'changed_outline_dry_control',name))
points=[]
for x,z,role,reach in selected:
    if any(p['x']==x and p['z']==z for p in points):continue
    lv,models=retained_pond_surface(B/'flat-water',manifest,x,z);ground=float(tri_sample(h,x,z))
    if role=='high_pond_control':assert lv is not None and lv-ground>.2,(x,z,lv,ground)
    elif role=='frozen_shallow_failure':assert lv is not None and lv-ground>.1,(x,z,lv,ground)
    else:assert lv is None or ground>lv+.04,(x,z,lv,ground)
    points.append(dict(id=5001+len(points),x=float(x),z=float(z),role=role,reach=reach,expected_ground_m=ground,actual_pond_level_m=lv,models=models))
mission=E/'missions/BalticFlatWaterProbeV1.BalticTrial';mission.mkdir(parents=True)
source=W/'missions/BalticJunctionProbeV1.BalticTrial/init.c'
text=source.read_text().replace('junction_probe_v1.log','flat_probe_v1.log').replace('junction_order_v1.log','flat_order_v1.log')
assert text.count('m_Rows.Count() == 3')==1 and text.count('END;62;3')==2
text=text.replace('m_Rows.Count() == 3',f'm_Rows.Count() == {len(points)}').replace('END;62;3',f'END;62;{len(points)}')
(mission/'init.c').write_text(text,encoding='utf-8',newline='\n')
(mission/'points.csv').write_text(''.join(f"{p['id']};{p['x']:.9f} 0 {p['z']:.9f}\n" for p in points),encoding='ascii')
reference=dict(header='BALTIC_V30_WATER_TEMPORAL_V3;BalticTrial',fields=17,samples=62,interval_s=2,points=points,
               required_control_roles=['high_pond_control','changed_outline_dry_control'],
               phases=[dict(name='calm',first=0,count=31,overcast=.1,wind_mps=.1),dict(name='storm',first=31,count=31,overcast=1,wind_mps=20)],
               files={p.name:sha(p) for p in mission.iterdir()},terrain_sha256=sha(terrain),source_mission_sha256=sha(source))
(E/'flat-probe-reference.json').write_text(json.dumps(reference,indent=2)+'\n')
# Same powered boat consumer and historical route span, now against restored planes.
a=axes['R1'];s=np.asarray(a['s']);keep=(s>=a['s_lo']+10)&(s<=a['s_hi']-10)
line=LineString(np.column_stack([np.asarray(a['x'])[keep],np.asarray(a['z'])[keep]]));d=np.linspace(0,line.length,math.ceil(line.length/4)+1)
pts=np.asarray([line.interpolate(v).coords[0] for v in d]);levels=[]
for x,z in pts:
    lv,_=retained_pond_surface(B/'flat-water',manifest,x,z)
    assert lv is not None and lv-float(tri_sample(h,x,z))>=.95
    levels.append(lv)
boat=E/'missions/BalticFlatBoatV1.BalticTrial';boat.mkdir()
boatsource=W/'missions/BalticV30LugaBoatV1.BalticTrial/init.c'
code=boatsource.read_text().replace('baltic_v30_luga_boat_v1.log','baltic_flat_boat_v1.log').replace('if (m_Case >= 8)','if (m_Case >= 2)')
(boat/'init.c').write_text(code,encoding='utf-8',newline='\n')
csv=[];cases=[]
for case,reverse in ((0,False),(1,True)):
    ix=np.arange(len(pts))[::-1] if reverse else np.arange(len(pts))
    csv.extend(f'{case};{seq};{pts[j,0]:.9g};{levels[j]:.9g};{pts[j,1]:.9g}' for seq,j in enumerate(ix))
    cases.append(dict(case=case,river='Narva_28 (flat R1)',reverse=reverse,waypoints_xz=pts[ix].tolist(),water_levels=np.asarray(levels)[ix].tolist(),length_m=line.length))
(boat/'routes.csv').write_text('\n'.join(csv)+'\n',encoding='ascii')
asc=B/'flat-terrain.asc'
with asc.open('x',encoding='ascii',newline='\n') as stream:
    stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(stream,h,fmt='%.9g')
oldref=json.loads((W/'evidence/v30-vanilla-channel-pilot-2026-10-04/boat/reference.json').read_text())
boatref=dict(oldref,cases=cases,log='baltic_flat_boat_v1.log',terrain=str(asc),terrain_sha256=sha(asc),
             mission={str(p):sha(p) for p in boat.iterdir()},source_mission_sha256=sha(boatsource),fit_axes_sha256=sha(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json')))
(E/'flat-boat-reference.json').write_text(json.dumps(boatref,indent=2)+'\n')
for target in (mission,boat):
    lint=subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(target)],capture_output=True,text=True)
    got=json.loads(lint.stdout);assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==1
    (E/(target.name.split('.')[0]+'-lint.json')).write_text(lint.stdout,encoding='utf-8')
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/target.name
    shutil.copytree(target,deployed);assert all(sha(deployed/p.name)==sha(p) for p in target.iterdir())
print(json.dumps(dict(probe_points=len(points),boat_waypoints=len(pts),boat_length_m=line.length),indent=2))
