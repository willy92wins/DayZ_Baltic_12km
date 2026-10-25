from pathlib import Path
import subprocess,time,json,hashlib
O=Path(__file__).parent;dest=O/'review-runtime-b-r2.json';assert not dest.exists()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
deploy=json.loads((O/'deploy-runtime-b.json').read_text());assert deploy['terrain_revision']=='runtime-b'
assert deploy['offline_status']=='PASS_AFFECTED_CONSUMERS_WITH_INHERITED_BASELINE'
mod=Path(deploy['mod']);assert sha(mod/'Addons/narva_trial.pbo')==deploy['world_sha256'] and sha(mod/'Addons/baltic_water_v30.pbo')==deploy['water_sha256']
assert all(sha(p)==h for p,h in deploy['evidence'].items())
binding={k:deploy[k] for k in ('mod','world_sha256','water_sha256','terrain_sha256','footprint_sha256','compiled_wrp_sha256','forest_records_sha256')}
binding['deploy_sha256']=sha(O/'deploy-runtime-b.json')
prompt=O/'review-runtime-b-r2-prompt.md';body=prompt.read_text(encoding='utf-8')+'\n\nBinding verificado antes de la revisión:\n'+json.dumps(binding,indent=2)
(O/'review-runtime-b-r2-binding.json').write_text(json.dumps(binding,indent=2)+'\n')
cmd=['C:/Users/guill/.local/bin/claude.exe','-p','--safe-mode','--no-session-persistence','--tools','Read,Grep,Glob','--allowedTools','Read','Grep','Glob','--add-dir',str(O.parent),'--output-format','json'];t=time.time()
with dest.open('w',encoding='utf-8') as out,(O/'review-runtime-b-r2.stderr').open('w',encoding='utf-8') as err:
 r=subprocess.run(cmd,input=body,text=True,encoding='utf-8',stdout=out,stderr=err,cwd='P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c',timeout=1200)
meta={'rc':r.returncode,'seconds':time.time()-t,'command':cmd,'prompt_sha256':sha(prompt),'complete_prompt_sha256':hashlib.sha256(body.encode()).hexdigest(),'binding':binding,'scope':'OT7 deployed four-vertex correction review R2 of max2; candidate runtime pending'}
(O/'review-runtime-b-r2-run.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
