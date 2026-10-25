"""Clip actual compiled physical/visible triangles against native terrain, including outside P/F cells."""
from pathlib import Path
from collections import defaultdict
import sys,json,hashlib,time
import numpy as np
import shapely
from shapely.geometry import Polygon

B=Path(__file__).parent;R=B.parent;S=R/'v30-strict-dry-composition-20261009'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain'),str(R/'v30-native-turn-optimizer-20261009')]
from engine_water_model import ODOL
from wrp0wzd import read
from verify_native_turns import clip,UNIT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=S/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';assert sha(src)=='931dd215fcb211bf233e18dd4e7fd0ce7a64f772d7294d28abbc5b1a6fbd3107'
h=np.load(S/'candidate/terrain.npz')['heights'].astype(float);v=np.load(B/'candidate/terrain.npz')['heights'].astype(float);p=np.load(B/'candidate/plane.npy');changed=h!=v
shifts={int(k):z for k,z in json.loads((B/'authoring.json').read_text())['object_translations'].items()}
bounds={o['id']:o['bounds'] for o in json.loads((R/'v30-low-water-components-20261009/compiled-instance-bounds.json').read_text())['objects']}
objects=[]
for o in read(src)['objects']:
    if o['id'] not in bounds:continue
    x0,z0,x1,z1=bounds[o['id']];r0,r1=max(0,int(np.floor((12282-z1)/6))-1),min(2048,int(np.ceil((12282-z0)/6))+2);c0,c1=max(0,int(np.floor(x0/6))-1),min(2048,int(np.ceil(x1/6))+2)
    if o['id'] in shifts or changed[r0:r1,c0:c1].any():objects.append(o)
def wet_native(r,c,ground,levels):
    xy=np.array([[c*6,12282-r*6],[(c+1)*6,12282-r*6],[c*6,12282-(r+1)*6],[(c+1)*6,12282-(r+1)*6]])
    gh=ground[r:r+2,c:c+2].ravel();polys=[]
    for tri in [[0,1,3],[0,2,3]]:
        weights=clip(UNIT,levels[tri]-gh[tri])
        if len(weights)>=3:polys.append(Polygon(weights@xy[tri]))
    return shapely.union_all(polys,grid_size=1e-6)
full=wet_native(0,0,np.zeros((2,2)),np.ones(4));dry=wet_native(0,0,np.ones((2,2))*2,np.ones(4))
assert full.area==36 and dry.is_empty and full.difference(dry).area==36
started=time.monotonic();reports={};failures=[]
for typ,target in [('physical',3e15),('visible',1)]:
    cells=defaultdict(lambda:[[],[]]);faces=0
    for o in objects:
        name=o['name'].replace('\\','/').split('/')[-1];od=ODOL.from_file(str(R/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'/name));lod=min(od.lods,key=lambda l:abs(l.resolution-target));m=np.array(o['matrix']);assert np.array_equal(m[:9].reshape(3,3),np.eye(3))
        verts=np.array([(a.x,a.y,a.z) for a in lod.vertices])+m[9:]
        dy=float(np.float32(m[10]+shifts.get(o['id'],0)))-m[10]
        for face in lod.faces:
            assert len(face.vertex_indices)==3
            q=verts[face.vertex_indices];xz=q[:,[0,2]];poly=Polygon(xz)
            if poly.area<=1e-12:continue
            slope=np.linalg.solve(xz[1:]-xz[0],q[1:,1]-q[0,1]);x0,z0,x1,z1=poly.bounds
            r0,r1=max(0,int(np.floor((12282-z1)/6))),min(2047,int(np.ceil((12282-z0)/6)));c0,c1=max(0,int(np.floor(x0/6))),min(2047,int(np.ceil(x1/6)))
            for r in range(r0,r1):
                for c in range(c0,c1):
                    xy=np.array([[c*6,12282-r*6],[(c+1)*6,12282-r*6],[c*6,12282-(r+1)*6],[(c+1)*6,12282-(r+1)*6]])
                    levels=q[0,1]+(xy-xz[0])@slope
                    for k,(terrain,offset) in enumerate([(h,0),(v,dy)]):
                        geom=wet_native(r,c,terrain,levels+offset).intersection(poly)
                        if geom.area>1e-12:cells[(r,c)][k].append(geom)
            faces+=1
    plus=minus=outside=0.;bad=[]
    for (r,c),(old,new) in cells.items():
        a=shapely.union_all(old,grid_size=1e-6);b=shapely.union_all(new,grid_size=1e-6);gain=b.difference(a).area;loss=a.difference(b).area;plus+=gain;minus+=loss
        if not np.isfinite(p[r,c]):outside+=gain
        if gain+loss>.00001:bad.append(dict(row=r,col=c,gained_m2=gain,lost_m2=loss,outside_field=not np.isfinite(p[r,c])))
    reports[typ]=dict(faces=faces,cells=len(cells),newly_exposed_m2=plus,newly_hidden_m2=minus,symmetric_difference_m2=plus+minus,new_outside_field_m2=outside,largest=sorted(bad,key=lambda x:-(x['gained_m2']+x['lost_m2']))[:20])
    print(json.dumps(dict(kind=typ,**{k:v for k,v in reports[typ].items() if k!='largest'})),flush=True)
gates={k:r['symmetric_difference_m2']<.002 for k,r in reports.items()}
report=dict(status='PASS_COMPILED_EXPOSURE' if all(gates.values()) else 'FAIL_COMPILED_EXPOSURE',gates=gates,objects=len(objects),translated_objects=len(shifts),reports=reports,terrain_sha256=sha(B/'candidate/terrain.npz'),source_wrp_sha256=sha(src),seconds=time.monotonic()-started,controls=['native_quad_36m2_wet','same_quad_dry','new_exposure_36m2_detected'],limits=['Reads actual compiled model triangles and serialized object Y, independent of finite P/F extent.','Native shader displacement and ocean are separate from this static triangle test.'])
(B/'compiled-exposure.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
