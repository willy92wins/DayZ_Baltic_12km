from pathlib import Path
import hashlib,json,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');V=R/'kit7-post-load1-plan-review-20261027';E=W/'evidence/performance/kit7-nav8load1-ram-interrupted-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=read(V/'response.json');assert not review['is_error'] and not review.get('permission_denials') and 'claude-fable-5-1' in review['modelUsage'] and review['result'].strip().endswith('FIN_REVISION')
assert read(V/'completion.json')['returncode']==0 and read(V/'adjudication.json')['status']=='ACCEPTED_AFTER_REVIEW'
for p,h in read(V/'adjudication.json')['inputs'].items():assert sha(Path(p))==h,p
manifest=read(E/'MANIFEST.json');assert all(sha(E/p)==v['sha256'] for p,v in manifest.items())
def save(p,name):
 t=E/name;t.parent.mkdir(parents=True,exist_ok=True);assert not t.exists();t.write_bytes(p.read_bytes())
for name in ['completion.json','source-hashes.json','adjudication.json','tests.stdout.log','tests.stderr.log']:save(V/name,'next-plan-review/'+name)
(E/'next-plan-review/fable-review.md').write_text(review['result'],encoding='utf-8')
for n in ['verify_nav8_load1_config_ev112.py','test_nav8_load1_config_ev112.py']:save(W/'tools/navigation'/n,'cli-fix/'+n)
save(W/'plans/ev112-kit7-post-load1-diagnostic-20261027.md','next-plan-review/reviewed-plan.md')
save(Path(__file__),'source/'+Path(__file__).name)
p=W/'plans/ev112-kit7-onload-numeric-pilot-20261027.md';old=p.read_text(encoding='utf-8');anchor='Estado: PLAN_REVISADO_SOUND_WITH_FIXES.';assert anchor in old
old=old.replace(anchor,'Estado: SONDA_PASS_RAM_INCONCLUSO. La ejecución de esta variante terminó: config+607 PASS; dos medidas RAM válidas y tercera admisión rechazada por puerto ajeno, sin run. Bloque incompleto conservado, no aceptación RAM ni repetición automática. Continuación: plans/ev112-kit7-post-load1-diagnostic-20261027.md. Estado previo del plan: PLAN_REVISADO_SOUND_WITH_FIXES.',1)
p.write_text(old,encoding='utf-8')
p=W/'HANDOFF.md';old=p.read_text(encoding='utf-8');new=old
updates={'updated':'2026-10-27 (Nav8Load1 config+607PASS publicado; RAM interrumpido, sin aceptación; CLI aislada corregida)','plan':'plans/ev112-kit7-post-load1-diagnostic-20261027.md. Diagnóstico offline revisado antes de otro candidato; cero runs/generaciones, no otro ancho ni cambios de tolerancia.','blocker':'RAM sigue abierta. Nav8Load1 conserva607PASS; bloque RAM incompleto por rechazo port_in_use_foreign en tercera admisión sin run. Dos medidas válidas no bastan para agregar ni aceptar. Nav8 anterior mantiene FAILRAM; Nav12 mantiene tresFAILaltura.','next':'Ejecutar únicamente el diagnóstico offline revisado según ACTIVE-WORK.md. Bloque RAM Nav8Load1 detenido, no completar huecos ni relanzarlo. Revisar cualquier nuevo experimento antes de generar/probar.','cleanup':'Runs RAMde5ff5ec-c9c6-4d60-a102-ed198c7f9bac y2057fa24-8857-4b53-922f-34b3a85e9e72 cerrados oficialmente/liberados. Tercera admisión no creórun. Estado final propio selfnone,0pending,sinruns.','handoff':E.relative_to(W).as_posix()+'/README.md. Fuentes históricas archivadas porhash; lectorCLI actual corregido después de cerrar el bloque,9tests con3subprocesosrealesPASS.','performance':'Nav8Load1: INCONCLUSIVE_INTERRUPTED_RAM_BLOCK,2/6medidas; Baltic4254.57/4649.21MiB,Chernarus3349.37/3733.76MiB descriptivos. Sincomparaciónagregada. Original12.5 PASSRAMdiagnóstico pero4FAILaltura; Nav8anterior FAILRAM1.265913/1.241333. SinFPS/capacidad.'}
for k,v in updates.items():new,count=re.subn('^'+k+':.*$',lambda _:k+': '+v,new,count=1,flags=re.M);assert count==1,k
assert p.read_text(encoding='utf-8')==old;p.write_text(new,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'};(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='INTERRUPTED_RAM_AND_CLI_FIX_CHECKPOINTED',files=len(manifest))))
