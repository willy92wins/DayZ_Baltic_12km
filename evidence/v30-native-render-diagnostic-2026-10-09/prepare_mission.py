from pathlib import Path
import json,hashlib,subprocess,sys,shutil
B=Path(__file__).parent;root=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
old=root/'BalticRenderNavControlV1.BalticTrial/init.c';code=old.read_text()
changes={'BalticRenderNavControlV1Mission':'BalticRenderLayerProbeV1Mission','pos = "6081 0 4966";':'pos = "2185 0 7350";','weather.SetWindFunctionParams(0, 0, 1);':'weather.SetWindFunctionParams(1, 1, 1);','weather.SetWindSpeed(0.1);':'weather.SetWindSpeed(20);','        FollowWeather();':'        // Fixed 20 m/s wind for this renderer discriminator.','baltic_tide_probe_v2.log':'baltic_render_layer_v1.log'}
for x,y in changes.items():assert x in code;code=code.replace(x,y)
local=B/'mission';local.mkdir(exist_ok=False);(local/'init.c').write_text(code,encoding='utf-8',newline='\n')
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(local)],capture_output=True,text=True)
result=json.loads(lint.stdout);assert lint.returncode==0 and result['info']['files_scanned']==1 and not result['errors'];(B/'mission-lint.json').write_text(lint.stdout)
dest=root/'BalticRenderLayerProbeV1.BalticTrial';assert not dest.exists();shutil.copytree(local,dest)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(local/'init.c')==sha(dest/'init.c')
(B/'mission-receipt.json').write_text(json.dumps(dict(source=str(old),source_sha256=sha(old),deployed=str(dest),init_sha256=sha(dest/'init.c'),wind_m_s=20,time='2026-10-02 12:00 fixed',spawn=[2185,7350]),indent=2)+'\n')
print(str(dest))
