from pathlib import Path
import json,shutil,sys,subprocess
from discover_components import sha
B=Path(__file__).parent
ref=json.loads((B/'probe-B.json').read_text());old=Path(ref['mission']);assert all(sha(old/name)==digest for name,digest in ref['files'].items())
source=(old/'init.c').read_text();assert source.count('m_Next=GetGame().GetTime()+5000;')==1
code=source.replace('m_Next=GetGame().GetTime()+5000;','m_Next=GetGame().GetTime()+60000;').replace('baltic_basin_translate_B.log','baltic_basin_translate_Bstable.log')
new=B/'missions/BalticBasinTranslateBStableV1.BalticTrial';new.mkdir(exist_ok=False)
(new/'init.c').write_text(code);shutil.copyfile(old/'points.csv',new/'points.csv')
cmd=[sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(new)]
lint=subprocess.run(cmd,capture_output=True,text=True);result=json.loads(lint.stdout);assert lint.returncode==0 and result['info']['files_scanned']==1 and not result['errors'];(B/'lint-Bstable.json').write_text(lint.stdout)
dest=old.parent/new.name;shutil.copytree(new,dest);ref['mission']=str(dest);ref['files']={p.name:sha(p) for p in new.iterdir()}
(B/'probe-Bstable.json').write_text(json.dumps(ref,indent=2)+'\n');print(str(dest))
