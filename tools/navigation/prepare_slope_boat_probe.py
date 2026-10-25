"""Isolate constructor rotation units and actual boat response on a 1% water grade."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'missions/BalticElevatedWaterV1.BalticTrial/init.c'
target = ROOT / 'missions/BalticSlopeBoatV3.BalticTrial'
assert not target.exists(), 'Fresh mission required'
text = source.read_text(encoding='utf-8')
text = text.replace('baltic_elevated_water_v1', 'baltic_slope_boat_v3').replace('BALTIC_ELEVATED_WATER_V1', 'BALTIC_SLOPE_BOAT_V3')
text = text.replace('vector pos = Vector(xx,6,zz);', 'float level = 6 + 0.01 * (zz - 3000);\n                vector pos = Vector(xx,level,zz);')
old = 'Object pond = GetGame().CreateObjectEx("StaticObj_water_pond_50x50m",pos,ECE_NONE);'
assert text.count(old) == 1
text = text.replace(old, 'vector radians = "0 0.0099996667 0";\n                Object pond = GetGame().CreateStaticObjectUsingP3D("dz\\\\water\\\\ponds\\\\pond_50x50.p3d",pos,radians,1,false);')
text = text.replace('                pond.SetPosition(pos);', '                // Constructor pose only: no orientation mutation or per-frame writes.')
text = text.replace('if (!isPond || levelError > 0.1)', 'FPrintln(m_Log,"POND_CLASSIFICATION;" + isPond);\n        if (levelError > 0.1)')
target.mkdir()
(target / 'init.c').write_text(text, encoding='utf-8', newline='\n')
report = {'status':'PREPARED_NOT_EXECUTED', 'water_grade':0.01, 'constructor_pitch_radians':0.0099996667,
          'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'mission_sha256':hashlib.sha256((target/'init.c').read_bytes()).hexdigest(),
          'classification':'Recorded independently; false does not bypass the later acceptance decision.',
          'scope':'Dynamic consumer only. Not a regional or persisted-water acceptance.'}
(ROOT/'evidence/regional-foundation-v1/slope-boat-v3-preparation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
