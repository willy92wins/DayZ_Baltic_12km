"""Read-only height discrimination against every packed model LOD at failed paths."""
from pathlib import Path
import hashlib,json,sys,subprocess
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from prepare_visual_probe_v31 import height
from attach_navmesh import read_pbo
from odol_reader import ODOL
import odol_reader
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
O=R/'kit7-nav-layer-diagnostic-20261026-v2';O.mkdir(exist_ok=False)
G=R/'kit7-packed-nav-discovery-20261026';D=R/'kit7-nav-consumer-20261026'
mod=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7NavV9/Addons')
world=mod/'narva_trial.pbo';pilot=mod/'baltic_stream_pilot.pbo'
assert sha(world)=='a2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c'
assert sha(pilot)=='3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6'
assert sha(Path(odol_reader.__file__))=='fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57'
_,_,entries=read_pbo(world);config=entries['config.bin'];del entries
(O/'config.bin').write_bytes(config)
converter=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe')
p=subprocess.run([str(converter),'-txt','-dst',str(O/'config.cpp'),str(O/'config.bin')],capture_output=True,text=True)
(O/'decode.log').write_text(p.stdout+p.stderr);assert p.returncode==0
_,_,entries=read_pbo(pilot)
geometry=read(G/'geometry.json');queries={q['name']:q for q in read(D/'reference.json')['queries']}
samples=read(R/'kit7-nav-height-diagnostic-20261026/result.json')['samples'];cache={};rows=[]
for s in samples:
    found=[];xz=np.array(s['nav'])[[0,2]]
    for model in queries[s['query']]['allowed_models']:
        if model not in cache:
            name=model.split('\\')[-1];blob=entries[name];meta=geometry['models'][model]
            assert hashlib.sha256(blob).hexdigest()==meta['odol_sha256']
            path=G/name;assert path.read_bytes()==blob
            od=ODOL.from_file(str(path),strict=True)
            assert not getattr(od,'lod_errors',{}) and all(l.lod_end_ok for l in od.lods)
            matrix=np.array(meta['pose']['matrix']);assert matrix[:9].tolist()==[1,0,0,0,1,0,0,0,1]
            lods=[]
            for l in od.lods:
                if not l.faces:continue
                xyz=(np.array([(v.x,v.y,v.z) for v in l.vertices])+matrix[9:]).astype(np.float32).astype(float)
                faces=np.array([f.vertex_indices for f in l.faces]);assert faces.shape[1]==3
                tri=xyz[faces]
                lods.append((l.resolution,tri))
            cache[model]=lods
        for res,tri in cache[model]:
            y=height(tri,xz)
            if y is not None:
                found.append(dict(model=model,resolution=res,y=y,nav_minus_lod_m=s['nav'][1]-y,road_minus_lod_m=s['engine_roadway'][1]-y))
    rows.append(dict(query=s['query'],index=s['index'],nav=s['nav'],road_y=s['engine_roadway'][1],ground_y=s['terrain'][1],failed=s['excess_m']>0,lods=found))
report=dict(status='DIAGNOSTIC_ONLY',samples=rows,inputs={str(p):sha(p) for p in [Path(__file__),world,pilot,G/'geometry.json',D/'reference.json',D/'runtime.log',Path(odol_reader.__file__),converter]},config_sha256=hashlib.sha256(config).hexdigest(),limits='Point samples at eight existing waypoints, no new native acceptance or source changes.')
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],samples=rows),indent=2))
