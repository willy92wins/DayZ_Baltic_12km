from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import subprocess

root=Path('P:/DayZ_Baltic_12km_dev')
vault=Path('C:/Users/guill/ObsidianVault/AI')
out=root/'evidence/foundation-followup-2026-10-01/handoff-complete-v29'
canonical=vault/'30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md'
receipt=out/'verification.json'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
changes=json.loads((out/'document-changes.json').read_text('utf-8'))
issues=[]
docs=[Path(c['path']) for c in changes['changes'] if c['path'].endswith('.md')]+[canonical,root/'PROJECT-MAP.md']
for c in changes['changes']:
    if sha(Path(c['path']))!=c['after_sha256']:issues.append('Concurrent post-write change:'+c['path'])
links=[]
legacy_missing=[]
backups={str(root/'HANDOFF.md'):'HANDOFF.md',str(root/'BUGS.md'):'BUGS.md',str(root/'product-spec.md'):'product-spec.md',str(root/'evidence/foundation-followup-2026-10-01/outline-v33-checkpoint.md'):'outline-v33-checkpoint.md',str(vault/'10_Projects/DayZ_Baltic_12km/project-brief.md'):'project-brief.md',str(vault/'10_Projects/DayZ_Baltic_12km/validation-matrix.md'):'validation-matrix.md',str(vault/'30_Sessions/2026-10-01-dayz-baltic-continuacion-base.md'):'continuation.md',str(vault/'30_Sessions/index.md'):'index.md',str(vault/'10_Projects/_estado-proyectos.md'):'_estado-proyectos.md',str(root/'PROJECT-MAP.md'):'PROJECT-MAP.md'}
for p in docs:
    for match in re.finditer(r'\[[^\]]*\]\((<[^>]+>|[^)]+)\)',p.read_text('utf-8-sig')):
        raw=match.group(1).strip().strip('<>')
        if raw.startswith(('https:','http:','app:','codex:','#')):continue
        target=raw.split('#')[0]
        if not target:continue
        q=Path(target) if re.match(r'^[A-Za-z]:[/\\]',target) else p.parent/target
        exists=q.exists() or q==receipt
        links.append({'source':str(p),'target':str(q),'exists':exists})
        if not exists:
            before=out/'before'/backups[str(p)] if str(p) in backups else None
            if before and before.exists() and match.group(0) in before.read_text('utf-8-sig'):
                legacy_missing.append({'source':str(p),'target':str(q),'evidence':'Exact Markdown link already exists in saved before snapshot; not introduced by this handoff.'})
            else:issues.append('Missing new link:'+str(q))

handoff=(root/'HANDOFF.md').read_text('utf-8')
old=(out/'before/HANDOFF.md').read_text('utf-8-sig')
anchor='## Histórico — navegación local de Narva'
history_preserved=old[old.index(anchor):]==handoff[handoff.index(anchor):]
if not history_preserved:issues.append('Prior history changed')
index=(vault/'30_Sessions/index.md').read_text('utf-8-sig')
index_count=index.count('./'+canonical.name)
if index_count!=1:issues.append('Canonical session index count:'+str(index_count))
state=json.loads((root/'evidence/foundation-followup-2026-10-01/state.json').read_text('utf-8'))
if state['active_run'] is not None or state['run_id'] is not None:issues.append('State still active')
end_line=next(i for i,s in enumerate(handoff.splitlines(),1) if '<!-- LIVE-STATE:END -->' in s)
maptext=(root/'PROJECT-MAP.md').read_text('utf-8')
map_ok=f'**línea {end_line}**' in maptext and (root/'PROJECT-MAP.md').stat().st_mtime >= (root/'HANDOFF.md').stat().st_mtime
if not map_ok:issues.append('PROJECT-MAP stale')

expected={
 'P:/Mods/@DayZ_Baltic_RoadV29/Addons/narva_trial.pbo':'b3418f927f6cc4adf8ba03b86de0ce1491f32adf87f3a124120c62eff20f856e',
 'P:/Mods/@DayZ_Baltic_RoadV29/Addons/baltic_water.pbo':'f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3',
 'P:/Mods/@DayZ_Baltic_FoundationV10Native/Addons/narva_trial.pbo':'d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577',
 'P:/Mods/@DayZ_Baltic_OutlineV33/Addons/narva_trial.pbo':'38ebe847b5dd553ac31bd0d51bd9d1c192965352a8a04188b7bdcef5c8eaea0c',
 str(root/'tests/regional_road_network_v29/baltic_road_network_v29.asc'):'ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6',
 str(root/'tb/regional_road_network_v29/r2.wrp'):'1763faccb9e8947027232a3c4f8a5ce91c793c06cb407252849239081ac92824',
 str(root/'tb/regional_road_network_v29/r3.wrp'):'9cd943347729b59c4e9997ca9b9fbd0ff74d194cf0d45359477ee0ef155942b3',
 str(root/'tb/regional_road_network_v29/navmesh/road_v29.nm'):'facaf1e386c6e19a9253c929ddd829bf93d670542ae8f504ee327c9b1b18ecef',
 str(root/'evidence/recorte-v0.kml'):'e23255baee8df3c87cbe8736ab8cee846e70c1d647549f7157845fb008dcd5cc',
 'C:/Users/guill/.codex/skills/dayz-terrain-workflow/references/regional-relief.md':'61e52ae3b54c0a5db5d859e4f8485935a95fcd463d22b76c33cb548d6f0bde8b',
}
manifest=[]
mem_config=vault/'10_Projects/_memory-exceptions.json'
mem_before=json.loads((out/'before/_memory-exceptions.json').read_text('utf-8-sig'))
mem_after=json.loads(mem_config.read_text('utf-8-sig'))
before_other={k:v for k,v in mem_before.items() if k!='projects'}
after_other={k:v for k,v in mem_after.items() if k!='projects'}
before_projects=[x for x in mem_before['projects'] if x['project']!='DayZ_Baltic_12km']
after_projects=[x for x in mem_after['projects'] if x['project']!='DayZ_Baltic_12km']
if before_other!=after_other or before_projects!=after_projects:issues.append('Unrelated memory declaration changed')
baltic=next(x for x in mem_after['projects'] if x['project']=='DayZ_Baltic_12km')
if baltic['live_bugs']['status']!='present':issues.append('Baltic registry declaration still stale')
memory_log=(out/'project-memory-check.txt').read_text('utf-8-sig')
if 'memory_status=PASS' not in memory_log:issues.append('Memory structural check did not pass')
for name,e in expected.items():
    p=Path(name);actual=sha(p)
    manifest.append({'path':str(p),'bytes':p.stat().st_size,'sha256':actual,'expected_sha256':e,'matches':actual==e})
    if actual!=e:issues.append('Hash mismatch:'+name)
for p in [root/'tb/regional_road_network_v29/road_v29.tv4p',root/'tb/regional_road_network_v29/road_v29.asc',root/'tb/regional_road_network_v29/road_v29.grid.000.v4w',canonical,mem_config,out/'project-memory-check.txt',*docs]:
    if not any(x['path']==str(p) for x in manifest):manifest.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
for p in (root/'evidence/foundation-followup-2026-10-01/road-v29-load/runtime-complete').iterdir():
    if p.is_file():manifest.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
(out/'manifest.json').write_text(json.dumps({'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'purpose':'Identity of critical artifacts and documents; not a portable backup.','files':manifest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['continuous-outline.json','joint-hydrology.json','independent-consumer.json','landmarks-controls-physical-contract.json']:
    p=root/'tests/regional_road_network_v29'/name
    if not p.exists():issues.append('Missing named acceptance:'+str(p))

load=json.loads((root/'evidence/foundation-followup-2026-10-01/road-v29-load/runtime-complete/verification.json').read_text('utf-8'))
samples={}
for role in ['server','client']:
    p=root/f'evidence/foundation-followup-2026-10-01/road-v29-load/runtime-complete/{role}-process.jsonl'
    samples[role]=len(p.read_text('utf-8-sig').splitlines())
    if samples[role]!=420:issues.append('Incomplete host sampler:'+role)
cleanup=json.loads((root/'evidence/foundation-followup-2026-10-01/road-v29-load/cleanup.json').read_text('utf-8'))
if cleanup['close']['stop_method']!='orderly_close' or cleanup['status']['occupied']:issues.append('Runtime not released')
git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=root,text=True).strip()
generator=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/tools/gen-project-map.ps1')
known_pin='81976ba2b354c04acfe2225ff67ae44769c986a8fed603abaec5bc76be573030'
audit=out/'vault-link-audit.txt'
audit_summary=[]
if audit.exists():
    txt=audit.read_text('utf-8-sig',errors='replace')
    audit_summary=[line for line in txt.splitlines() if any(k in line for k in ['status=','missing_session_index=','new_live_pairs=','duplicate_exact_session_targets='])]
result={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'PASS_OWN_HANDOFF_CHECKS' if not issues else 'FAIL_OWN_HANDOFF_CHECKS','issues':issues,'canonical_handoff':str(canonical),'canonical_sha256':sha(canonical),'checked_local_links':len(links),'links':links,'session_index_count':index_count,'previous_handoff_history_preserved':history_preserved,'project_map':{'local_freshness':map_ok,'live_state_end_line':end_line,'generator_sha256':sha(generator),'known_shared_pin':known_pin,'shared_pin_matches':sha(generator)==known_pin,'global_status':'INCONCLUSIVE_GENERATOR_PIN_MISMATCH; shared pin unchanged'},'runtime':cleanup,'load_status':load['status'],'load_issues':load['issues'],'host_samples':samples,'git_head':git_head,'staged_paths':staged.splitlines(),'commit':'None; shared prior changes preserved, evidence identified by hashes.','vault_global_audit':{'summary':audit_summary,'log':str(audit),'scope':'Global debt is not own handoff acceptance; do not modify unrelated sessions or link baseline.'},'manifest_sha256':sha(out/'manifest.json'),'limits':['No terrain1.0 or capacity claim.','Visual V29 pending and load inconclusive.','This verifies identity/closure/docs, not rerun of terrain consumers.']}
receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result['unchanged_missing_links']=legacy_missing
result['new_missing_links']=len([i for i in issues if i.startswith('Missing new link:')])
result['scope_note']='Full-document links inspected; inherited missing links compared literally against before snapshots and reported separately from this change. Initial broad failure preserved in verification-first-all-links.json.'
result['memory_structural_check']={'status':'PASS' if 'memory_status=PASS' in memory_log else 'FAIL','projects':47,'only_baltic_declaration_changed':before_other==after_other and before_projects==after_projects,'config_sha256':sha(mem_config),'log_sha256':sha(out/'project-memory-check.txt')}
receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','issues','checked_local_links','session_index_count','previous_handoff_history_preserved','load_status','host_samples','git_head','staged_paths','vault_global_audit']},ensure_ascii=False))
raise SystemExit(bool(issues))
