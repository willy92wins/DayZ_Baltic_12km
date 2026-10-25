"""Probe reconstructed flat/slope P3Ds at fixed poses, beside the vanilla oracle."""
from pathlib import Path
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
pbo=ROOT/'build-output/water_geometry_v1/Addons/baltic_water_probe.pbo'
raw,props,entries=read_pbo(pbo)
compiled=ROOT/'build-temp/water_geometry_v1/baltic_water_probe'
assert props['prefix']=='baltic_water_probe'
assert set(entries)=={'config.bin','flat.p3d','grade01.p3d'}
assert entries=={name:(compiled/name).read_bytes() for name in entries}
assert entries['config.bin'].startswith(b'\0raP')
assert all(entries[n].startswith(b'ODOL') for n in ('flat.p3d','grade01.p3d'))
text=(ROOT/'missions/BalticWaterPoseV2.BalticTrial/init.c').read_text()
text=text.replace('baltic_water_pose_v2','baltic_water_geometry_v1').replace('BALTIC_WATER_POSE_V2','BALTIC_WATER_GEOMETRY_V1')
start=text.index('        Object a =')
end=text.index('        if (!a ||',start)
text=text[:start]+'''        Object a = GetGame().CreateStaticObjectUsingP3D("baltic_water_probe\\\\flat.p3d","450 6 4000",flat,1,false);
        Object b = GetGame().CreateStaticObjectUsingP3D("baltic_water_probe\\\\grade01.p3d","600 6 4000",flat,1,false);
        Object c = GetGame().CreateObjectEx("BalticWaterGrade01","750 6 4000",ECE_NONE);
        Object d = GetGame().CreateObjectEx("StaticObj_water_pond_50x50m","900 6 4000",ECE_NONE);
'''+text[end:]
text=text.replace('        b.SetOrientation(rotation);\n        c.SetOrientation(rotation);\n','')
target=ROOT/'missions/BalticWaterGeometryV1.BalticTrial'
assert not target.exists()
target.mkdir()
(target/'init.c').write_text(text,encoding='utf-8',newline='\n')
report={'status':'PACKED_PARITY_PREPARED_NOT_RUN','pbo_sha256':hashlib.sha256(raw).hexdigest(),
        'mission_sha256':hashlib.sha256((target/'init.c').read_bytes()).hexdigest(),
        'entries':{k:hashlib.sha256(v).hexdigest() for k,v in entries.items()}}
(ROOT/'evidence/regional-foundation-v1/water-geometry-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
