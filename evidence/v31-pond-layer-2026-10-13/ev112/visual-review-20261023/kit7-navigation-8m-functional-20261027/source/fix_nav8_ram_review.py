from pathlib import Path
import hashlib,json,subprocess,sys,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav8-ram-ab-20261027';O=R/'kit7-nav8-ram-review-20261027'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert read(O/'completion.json')['inputs_unchanged']
before=read(O/'source-hashes.json');assert all(sha(Path(k))==v for k,v in before.items())
archive=O/'reviewed-sources';archive.mkdir(exist_ok=False)
for i,(p,h) in enumerate(before.items()):
 source=Path(p);(archive/f'{i:02}-{source.name}').write_bytes(source.read_bytes())
manifest=read(D/'missions.json')
for row in manifest['passes']:
 p=Path(row['mission'])/'init.c';s=p.read_text(encoding='utf-8');old=row['profile_log'];new=old.replace('baltic_nav8_ab_','baltic_ab_',1)
 assert re.fullmatch(r'baltic_ab_\d{2}_[0-9a-f]{12}\.log',new) and s.count(old)==2
 assert not (Path('C:/temp/DayZ_MCP_130_dev/_server/profiles-130')/new).exists()
 p.write_text(s.replace(old,new),encoding='utf-8');row['profile_log']=new;row['mission_sha256']=sha(p)
write(D/'missions.json',manifest)
p=R/'orchestrate_nav8_ram.js';s=p.read_text(encoding='utf-8');assert s.count('/^[a-z0-9_]+\\.log$/')==1;s=s.replace('/^[a-z0-9_]+\\.log$/','/^baltic_ab_\\d{2}_[0-9a-f]{12}\\.log$/');p.write_text(s,encoding='utf-8')
p=R/'prepare_nav8_ram_pass.py';s=p.read_text(encoding='utf-8');s=s.replace('import hashlib,json,sys','import hashlib,json,sys,re')
needle="mission=Path(row['mission'])/'init.c';assert sha(mission)==row['mission_sha256']"
assert needle in s;s=s.replace(needle,needle+"\nassert re.fullmatch(r'baltic_ab_\\d{2}_[0-9a-f]{12}\\.log',row['profile_log'])\nassert mission.read_text(encoding='utf-8-sig').count(row['profile_log'])==2")
old="extras=[Path(p) for p in dep['packages'] if row['world']=='BalticTrial' or Path(p).name.lower()=='dayz_mcp.pbo']\nassert len(extras)==(4 if row['world']=='BalticTrial' else 1)\nfor p in extras:assert sha(p)==dep['packages'][str(p)]"
new="extra_pairs=[(Path(p),h) for p,h in dep['packages'].items() if row['world']=='BalticTrial' or Path(p).name.lower()=='dayz_mcp.pbo']\nextras=[p for p,h in extra_pairs]\nassert len(extras)==(4 if row['world']=='BalticTrial' else 1)\nfor p,h in extra_pairs:assert sha(p)==h"
assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
p=R/'test_nav8_ram_flow.cjs';s=p.read_text(encoding='utf-8');assert 'baltic_nav8_ab_01_131442df91e4.log' in s;p.write_text(s.replace('baltic_nav8_ab_01_131442df91e4.log','baltic_ab_01_131442df91e4.log'),encoding='utf-8')
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
rows=[]
for row in manifest['passes']:
 mission=Path(row['mission']);bootstrap='import runpy,sys;sys.path.insert(0,'+repr(str(validator.parent))+');sys.argv='+repr([str(validator),str(mission),'--vanilla-root','P:/scripts'])+';runpy.run_path('+repr(str(validator))+',run_name="__main__")'
 q=subprocess.run([sys.executable,'-I','-c',bootstrap],capture_output=True)
 (D/f'script-validator-{row["order"]:02}.json').write_bytes(q.stdout);(D/f'script-validator-{row["order"]:02}.stderr.log').write_bytes(q.stderr)
 v=json.loads(q.stdout);assert q.returncode in (0,2) and v['status']=='PASS' and v['info']['files_scanned']==1 and not v['errors'] and not v['warnings']
 rows.append(dict(order=row['order'],status='PASS',files=1,mission_sha256=sha(mission/'init.c')))
write(D/'mission-validation.json',dict(status='PASS_SIX_MISSION_FILES',missions=rows,native_acceptance=False))
write(O/'corrected-source-hashes.json',{p:sha(Path(p)) for p in before})
(O/'adjudication.md').write_text('Fable returned NEEDS-WORK. All three findings reproduced by source and corrected before any RAM launch. Reviewed bytes and original hashes retained. Six fresh log names now match the unchanged consumer. Coordinator and preparer enforce its exact format. Package pairs preserve original deployment keys. Consumer equivalence controls and fresh lifecycle mocks are required before sealing. These are preparation controls, not native measurements.\n',encoding='utf-8')
print('THREE_FINDINGS_FIXED_SIX_MISSIONS_VALIDATED_PENDING_CONTROLS')
