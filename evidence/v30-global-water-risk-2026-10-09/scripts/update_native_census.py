from pathlib import Path
import json,hashlib,shutil,subprocess,sys
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09'
ref=json.loads((B/'native-census-reference.json').read_text());dst=Path(ref['mission'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(dst/k)==v for k,v in ref['files'].items())
(E/'native-census-preparation-before-compile-repair.json').write_text(json.dumps({k:v for k,v in ref.items() if k!='points'},indent=2)+'\n')
for path in [dst/'init.c',B/'missions/BalticNativeCensusV1.BalticTrial/init.c',E/'BalticNativeCensus.c']:
    shutil.copyfile(B/'BalticNativeCensus.c',path)
ref['files']['init.c']=sha(dst/'init.c')
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(dst)],capture_output=True,text=True)
got=json.loads(lint.stdout);assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==1
(E/'native-census-lint.json').write_text(lint.stdout)
(B/'native-census-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
(E/'native-census-preparation.json').write_text(json.dumps({k:v for k,v in ref.items() if k!='points'},indent=2)+'\n')
print(json.dumps(dict(files=ref['files'],lint=got['status'])))
