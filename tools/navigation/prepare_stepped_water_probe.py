"""Worst permitted 5cm step between half-scale horizontal vanilla ponds."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'missions/BalticElevatedWaterV1.BalticTrial/init.c'
text=source.read_text()
text=text.replace('baltic_elevated_water_v1','baltic_stepped_water_v1').replace('BALTIC_ELEVATED_WATER_V1','BALTIC_STEPPED_WATER_V1')
text=text.replace('xx = 450; xx <= 550; xx += 50','xx = 475; xx <= 525; xx += 25')
text=text.replace('zz = 2950; zz <= 3150; zz += 50','zz = 2975; zz <= 3125; zz += 25')
text=text.replace('vector pos = Vector(xx,6,zz);','float level = 6 + 0.002 * (zz - 3000);\n                vector pos = Vector(xx,level,zz);')
text=text.replace('Object pond = GetGame().CreateObjectEx("StaticObj_water_pond_50x50m",pos,ECE_NONE);','vector flat = "0 0 0";\n                Object pond = GetGame().CreateStaticObjectUsingP3D("dz\\\\water\\\\ponds\\\\pond_50x50.p3d",pos,flat,0.5,false);')
text=text.replace('                pond.SetPosition(pos);','                // Fixed constructor pose and scale; no later pose writes.')
target=ROOT/'missions/BalticSteppedWaterV1.BalticTrial'
assert not target.exists()
target.mkdir()
(target/'init.c').write_text(text,encoding='utf-8',newline='\n')
report={'status':'PREPARED_NOT_RUN','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'mission_sha256':hashlib.sha256((target/'init.c').read_bytes()).hexdigest(),
        'centres_x':[475,500,525],'centres_z':list(range(2975,3126,25)),'model_scale':.5,'joint_step_m':.05,
        'decision':'Require positive water classification and actual uphill propulsion through four joints before regional adoption.'}
(ROOT/'evidence/regional-foundation-v1/stepped-water-preparation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
