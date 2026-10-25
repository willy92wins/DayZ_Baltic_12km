"""Isolated flat/reconstructed/sloped water mesh experiment; never production.

The reference is installed vanilla pond_50x50. No original file is modified.
Both model shapes share geometry/properties/materials; only Y and normals vary.
"""
from pathlib import Path
import hashlib
import json
import sys
import struct
import math

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,r'C:\Users\guill\DayZ-Modding-Knowledge-Pack\tools\py3d')
sys.path.insert(0,r'C:\Users\guill\.agents\skills\dayz-p3d-debinarizer\scripts')
import py3d
from odol_reader import ODOL
from odol_to_mlod import convert_odol_to_mlod

assert py3d.IS_DAYZ_FORK and tuple(map(int,py3d.__version__.split('.'))) >= (1,5,0)
source=Path('P:/dz/water/ponds/pond_50x50.p3d')
raw=source.read_bytes()
assert raw[:4]==b'ODOL' and struct.unpack_from('<I',raw,4)[0]==54
odol=ODOL.from_file(str(source))
assert not odol.lod_errors and all(l is not None for l in odol.lods)
out=ROOT/'tests/water_geometry_v1/source/baltic_water_probe'
assert not out.exists(), 'Fresh source required'
out.mkdir(parents=True)
report={'status':'PREPARED_NOT_COMPILED','source_sha256':hashlib.sha256(raw).hexdigest(),'py3d_version':py3d.__version__,'models':{}}
for name,grade in [('flat',0.),('grade01',.01)]:
    model=convert_odol_to_mlod(odol)
    for lod in model.lods:
        for point in lod.points:
            x,y,z=point.coords
            point.coords=(x,y+grade*z,z)
        for i,(nx,ny,nz) in enumerate(lod.facenormals):
            # Inverse transpose for the shear y'=y+grade*z.
            vec=(nx,ny,nz-grade*ny)
            length=math.sqrt(sum(v*v for v in vec))
            lod.facenormals[i]=tuple(v/length for v in vec) if length else vec
    path=out/f'{name}.p3d'
    model.save(str(path))
    with path.open('rb') as handle:
        check=py3d.P3D(handle)
    assert len(check.lods)==len(model.lods)
    report['models'][name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'lods':[{'resolution':l.resolution,'points':len(l.points),'faces':len(l.faces),'properties':l.properties,
                 'materials':sorted({f.material for f in l.faces}),'textures':sorted({f.texture for f in l.faces})} for l in check.lods]}
(out/'$PBOPREFIX$').write_text('baltic_water_probe',encoding='ascii')
(out/'config.cpp').write_text('''class CfgPatches
{
    class Baltic_Water_Probe
    {
        units[]={"BalticWaterFlat","BalticWaterGrade01"};
        weapons[]={};
        requiredVersion=0.1;
        requiredAddons[]={"DZ_Water"};
    };
};
class CfgVehicles
{
    class HouseNoDestruct;
    class BalticWaterFlat: HouseNoDestruct
    {
        scope=1;
        model="\\\\baltic_water_probe\\\\flat.p3d";
    };
    class BalticWaterGrade01: BalticWaterFlat
    {
        model="\\\\baltic_water_probe\\\\grade01.p3d";
    };
};
''',encoding='utf-8')
(ROOT/'evidence/regional-foundation-v1/water-geometry-preparation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
