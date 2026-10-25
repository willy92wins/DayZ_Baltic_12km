from pathlib import Path
import json,hashlib,shutil,subprocess,sys
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-valley-smoothing-2026-10-08'
F=W/'evidence/v30-water-visual-fix-2026-10-08'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
name='BalticC1R3PWaterProbeV1.BalticTrial'
src=F/'missions/BalticStitchedWaterProbeV1.BalticTrial';dst=E/'missions'/name
dst.mkdir(parents=True,exist_ok=False)
code=(src/'init.c').read_text().replace('stitched_probe_v1.log','c1r3p_probe_v1.log').replace('stitched_order_v1.log','c1r3p_order_v1.log')
(dst/'init.c').write_text(code)
shutil.copyfile(src/'points.csv',dst/'points.csv')
ref=json.loads((F/'stitch-probe-reference.json').read_text())
updated=json.loads((E/'c1r3p-visual-reference.json').read_text())
for p,q in zip(ref['points'],updated['points']):
    assert (p['id'],p['x'],p['z'])==(q['id'],q['x'],q['z'])
    p['source_ground_m']=p['expected_ground_m'];p['expected_ground_m']=q['expected_ground_m']
ref['source_reference_sha256']=sha(F/'stitch-probe-reference.json')
ref['terrain_sha256']=updated['terrain_sha256']
ref['files']={p.name:sha(p) for p in dst.iterdir()}
ref['deployed']={str(p):sha(p) for p in Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons').glob('*.pbo')}
(E/'c1r3p-probe-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
lint=subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(dst)],capture_output=True,text=True)
got=json.loads(lint.stdout);assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==1
(E/'c1r3p-probe-lint.json').write_text(lint.stdout)
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name
shutil.copytree(dst,deployed)
assert all(sha(deployed/p.name)==sha(p) for p in dst.iterdir())
verify=(F/'verify_stitch_probe.py').read_text()
verify=verify.replace("E=W/'evidence/v30-water-visual-fix-2026-10-08'","E=W/'evidence/v30-valley-smoothing-2026-10-08'")
verify=verify.replace('stitch-probe-reference.json','c1r3p-probe-reference.json').replace('stitched_probe_v1.log','c1r3p_probe_v1.log').replace('stitched_order_v1.log','c1r3p_order_v1.log')
verify=verify.replace('stitch-runtime','c1r3p-runtime').replace('stitch-order','c1r3p-order').replace('PASS_STITCHED_WATER_READBACK','PASS_C1R3P_WATER_READBACK')
(E/'verify_c1r3p_probe.py').write_text(verify)
print(json.dumps(dict(mission=str(deployed),points=len(ref['points']),lint_files=1,deployed=ref['deployed'])))
