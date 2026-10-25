"""Prepare the existing full-grid native consumer for the exact new preview."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-frozen-water-stitch-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    previous=json.loads((W/'evidence/v30-global-water-risk-2026-10-09/halo-r3-fullwater-reference.json').read_text())
    old=Path(previous['mission']);assert all(sha(old/name)==digest for name,digest in previous['files'].items())
    deployment=json.loads((B/'deploy.json').read_text());mods=Path(deployment['destination'])/'Addons'
    assert all(sha(mods/name)==digest for name,digest in deployment['files'].items())
    mission=B/'missions/BalticGlobalFullWaterV1.BalticTrial';mission.mkdir(parents=True,exist_ok=False)
    code=(old/'init.c').read_text().replace('BalticHaloFullWaterMission','BalticGlobalFullWaterMission').replace('baltic_halo_fullwater_v3.log','baltic_global_fullwater_v1.log')
    header='BALTIC_NATIVE_FULLWATER_V1;BalticTrial;'+previous['terrain_sha256']
    newheader='BALTIC_GLOBAL_FULLWATER_V1;BalticTrial;'+previous['terrain_sha256']
    assert code.count(header)==1;code=code.replace(header,newheader)
    (mission/'init.c').write_text(code)
    for name in ('grid.csv','risks.csv'):shutil.copyfile(old/name,mission/name)
    validator='C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py'
    lint=subprocess.run([sys.executable,validator,str(mission)],capture_output=True,text=True)
    result=json.loads(lint.stdout);assert lint.returncode==0 and result['info']['files_scanned']==1 and not result['errors']
    (B/'native-fullwater-lint.json').write_text(lint.stdout)
    destination=old.parent/mission.name;shutil.copytree(mission,destination)
    reference=dict(previous,pbo=deployment['files'],mission=str(destination),files={p.name:sha(p) for p in mission.iterdir()},
                   status='PREPARED_NOT_RUN',source_runtime_reference_sha256=sha(W/'evidence/v30-global-water-risk-2026-10-09/halo-r3-fullwater-reference.json'))
    assert all(sha(destination/name)==digest for name,digest in reference['files'].items())
    (E/'global-fullwater-reference.json').write_text(json.dumps(reference,indent=2)+'\n')
    verifier=(Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')/'verify_halo_r3_fullwater.py').read_text()
    verifier=verifier.replace("E=W/'evidence/v30-global-water-risk-2026-10-09'","E=W/'evidence/v30-frozen-water-stitch-2026-10-09'")
    verifier=verifier.replace('halo-r3','global').replace('baltic_halo_fullwater_v3','baltic_global_fullwater_v1').replace('BALTIC_NATIVE_FULLWATER_V1','BALTIC_GLOBAL_FULLWATER_V1')
    (B/'verify_global_fullwater.py').write_text(verifier)
    print(json.dumps({'status':'PREPARED_NOT_RUN','mission':str(destination),'files':reference['files'],'pbo':reference['pbo'],'lint_files':1},indent=2))

if __name__=='__main__':main()
