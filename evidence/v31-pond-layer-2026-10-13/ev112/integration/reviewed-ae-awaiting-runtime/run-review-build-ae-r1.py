from pathlib import Path
import subprocess,time,json,hashlib
O=Path(__file__).parent;dest=O/'review-build-ae-r1.json';assert not dest.exists()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
deploy=json.loads((O/'deploy.json').read_text());assert deploy['forest_tag']=='ae' and deploy['offline_status']=='PASS'
mod=Path(deploy['mod']);assert sha(mod/'Addons/narva_trial.pbo')==deploy['world_sha256'] and sha(mod/'Addons/baltic_water_v30.pbo')==deploy['water_sha256']
binding={k:deploy[k] for k in ('mod','world_sha256','water_sha256','terrain_sha256','footprint_sha256','compiled_wrp_sha256','forest_records_sha256')}
binding['deploy_sha256']=sha(O/'deploy.json')
prompt=O/'review-build-ae-r1-prompt.md';body=prompt.read_text(encoding='utf-8')+'\n\nBinding verificado antes de la revision:\n'+json.dumps(binding,indent=2)
(O/'review-build-ae-r1-binding.json').write_bytes((json.dumps(binding,indent=2)+'\n').encode())
cmd=['C:/Users/guill/.local/bin/claude.exe','-p','--safe-mode','--no-session-persistence','--tools','Read,Grep,Glob','--allowedTools','Read','Grep','Glob','--add-dir',str(O.parent),'--output-format','json'];t=time.time()
with dest.open('w',encoding='utf-8') as out,(O/'review-build-ae-r1.stderr').open('w',encoding='utf-8') as err:
 r=subprocess.run(cmd,input=body,text=True,encoding='utf-8',stdout=out,stderr=err,cwd='P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c',timeout=1200)
meta={'rc':r.returncode,'seconds':time.time()-t,'command':cmd,'prompt_sha256':sha(prompt),'complete_prompt_sha256':hashlib.sha256(body.encode()).hexdigest(),'binding':binding,'scope':'OT7 final deployed build review round1 of max2; runtime pending'}
(O/'review-build-ae-r1-run.json').write_bytes((json.dumps(meta,indent=2)+'\n').encode());print(json.dumps(meta))
