"""Classify packed surface hits at the fixed Nav12 diagnostic corner."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from prepare_visual_probe_v31 import height
from attach_navmesh import read_pbo
from odol_reader import ODOL
import odol_reader
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
G=R/'kit7-packed-nav-discovery-20261026'
geo=json.loads((G/'geometry.json').read_text())
model='baltic_stream_pilot\\cs_kit_7_1392.p3d'
meta=geo['models'][model];path=G/'cs_kit_7_1392.p3d'
pilot=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav12/Addons/baltic_stream_pilot.pbo')
assert sha(pilot)=='3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6'
assert sha(odol_reader.__file__)=='fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57'
_,_,entries=read_pbo(pilot)
assert path.read_bytes()==entries[path.name] and sha(path)==meta['odol_sha256']
od=ODOL.from_file(str(path),strict=True)
assert not getattr(od,'lod_errors',{}) and all(l.lod_end_ok for l in od.lods)
matrix=np.array(meta['pose']['matrix']);assert matrix[:9].tolist()==[1,0,0,0,1,0,0,0,1]
rows=[]
for lod in od.lods:
    xyz=(np.array([(v.x,v.y,v.z) for v in lod.vertices])+matrix[9:]).astype(np.float32).astype(float)
    for section in lod.sections:
        for i in section.get_face_indices(lod.faces):
            ids=lod.faces[i].vertex_indices;assert len(ids)==3
            tri=xyz[ids];ab=tri[1,[0,2]]-tri[0,[0,2]];ac=tri[2,[0,2]]-tri[0,[0,2]]
            if ab[0]*ac[1]-ab[1]*ac[0]==0:continue
            y=height(tri[None,:,:],np.array([9132.,11280.]))
            if y is None:continue
            assert np.isfinite(y)
            tex=lod.textures[section.texture_index] if 0<=section.texture_index<len(lod.textures) else None
            rows.append(dict(resolution=lod.resolution,face=i,indices=ids,xyz=tri.tolist(),y=y,texture=tex,material_index=section.material_index,material_name=section.mat_name))
O=R/'kit7-corner-faces-20261027';O.mkdir(exist_ok=False)
result=dict(status='READ_ONLY_FACE_CLASSIFICATION',point=[9132.,11280.],model=model,hits=rows,inputs={str(p):sha(p) for p in [Path(__file__),pilot,path,Path(odol_reader.__file__)]},limits=['One offline diagnostic corner; no acceptance query changes or native corner proof.'])
(O/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps(result,indent=2))
