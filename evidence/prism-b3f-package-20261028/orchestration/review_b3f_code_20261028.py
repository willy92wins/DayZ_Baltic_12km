from pathlib import Path
import hashlib,json,subprocess,time
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');O=R/'b3f-code-review-20261028';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[W/'tools/quality'/n for n in ('prism_b3f_package_ev112.py','preflight_b3f_ev112.py','test_prism_b3f_ev112.py')]+[W/'plans/ev112-b3f-package-composition-20261028.md',R/'run_b3f_execution_20261028.py']
pins={str(p):sha(p) for p in files};(O/'inputs.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
for p in files:(O/p.name).write_bytes(p.read_bytes())
brief='''Delegar JUICIO codigo B3F. Una lane Claude Fable5.1 CLI nativo confirmado hoy2.1.310, identidad modelUsage requerida. Codex executor/integrator adjudica. Read-only sin tools/hijos/escrituras/git. <=180s850palabras SOUND/SOUND-with-fixes/NEEDS-WORK con lineas/fixes y FIN_REVISION. Plan ya revisado62.812s. Nuevo codigo solo composicion201 de ODOL2581 aprobadoB3E2 y baseline ef229 target3514 config20157d0. No geometry authoring/binarize/DayZ/deploy.22tests inicialesPASS5.734s; nuevos tres tests agregados esperan suitefinal. Pure package_identity sellado compara beforeprops==afterprops, prefix, list(before)==list(after),201P3D+config, changed==[NAME],aftertarget==expectedbytes; no consulta CANDIDATE_SHA/ANCHORS, test contrafactual. read_pbo compartido cuerpos limite declarado. Nuevo header guard independiente antesdict detecta duplicados/orden. gate.context sellado revalida pins externos B3D/proof/prior/candidate/transitivos, originalcontrols/pose; no recomputa censos. runtime.run_process (B3E2 sellado) run_tree con Popen oculta/psutil7.2.2 PIDcreate_time, muestreo0.1s RSSdescendientes propios, mata soloidentidadespropias siagotado, guarda running/receipt, retorno0tardio rechaza. No certifica hijos noobservados. Preflight official.run es primitiva reutilizada, noCLI consumido: officialchecks warnNone mas hardgatesP,toolsroot/hash,vanilla dirs,Modsjunction; literalfixsyntax213 archivadoydiffverificado;60s. NuevohijoB3F stdlib usa esa primitiva, agregaPboUtils/disk yreportepropio; no skillgobernadaedit. Padrepreparaciontotal60/pack120/consumer120/2GiB, outer300s techo suma protegiendo RSSparent+child sin ampliar fases. Controles/noislands/moves intactos,47FAIL21inciertos abiertos. Revisa falsosPASS/rechazos/mutacion/manifiestocontratos/primitivas/transitivos; no plantear segundo parsercompleto ni redisenarirrestricto. Presupuesto una composicion, sin reintentos. Si faltan pruebas especificas indicar observables, no tests espejo de texto. Fuentes incluidas son codigo ejecutable salvoplanDESIGN.'''
capsule=brief+'\n\n'+'\n\n'.join('FILE '+str(p)+'\n'+'\n'.join(f'{i+1}: {s}' for i,s in enumerate(p.read_text(encoding='utf-8').splitlines())) for p in files);(O/'capsule.md').write_text(capsule,encoding='utf-8')
t=time.monotonic();timeout=False
with (O/'events.jsonl').open('wb') as out,(O/'stderr.log').open('wb') as err:
 p=subprocess.Popen(['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--output-format','stream-json','--verbose','--include-partial-messages','--no-session-persistence','--tools',''],cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
 (O/'running.json').write_text(json.dumps(dict(pid=p.pid,max_seconds=180)),encoding='utf-8')
 try:p.communicate(capsule.encode(),timeout=180)
 except subprocess.TimeoutExpired:timeout=True;p.terminate();p.wait(timeout=20)
events=[]
for line in (O/'events.jsonl').read_text(encoding='utf-8-sig').splitlines():
 try:events.append(json.loads(line))
 except json.JSONDecodeError:pass
result=next((e for e in reversed(events) if e.get('type')=='result'),{});elapsed=time.monotonic()-t
c=dict(returncode=p.returncode,timeout=timeout,seconds=elapsed,within_budget=elapsed<=180,models=list(result.get('modelUsage',{})),complete='FIN_REVISION' in result.get('result',''),inputs_unchanged=all(sha(Path(p))==h for p,h in pins.items()),denials=result.get('permission_denials',[]))
(O/'review.md').write_text(result.get('result',''),encoding='utf-8');(O/'completion.json').write_text(json.dumps(c,indent=2),encoding='utf-8');print(json.dumps(c))
