from pathlib import Path
import hashlib,json,shutil
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');E=W/'evidence/navigation/bank-source-rejected-apron-20261027';E.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def cp(src,dst):
 p=E/dst;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p);assert sha(src)==sha(p)
for filename in ['attribute_bank_source.py','pilot_dry_apron.py','test_dry_apron_pilot.py','run_dry_apron_pilot.py','plot_dry_apron_pilot.py','review_bank_source_plan.py','review_bank_attribution_and_pilot.py','review_dry_apron_code.py','review_dry_bank_domain_plan.py','checkpoint_bank_source_and_apron.py']:cp(R/filename,'source/'+filename)
for folder,label,filenames in [
 ('bank-source-attribution-20261027','attribution',['result.json','budget.json']),
 ('dry-apron-linear-pilot-20261027','pilot',['result.json','budget.json','profiles.png']),
 ('dry-apron-linear-run-20261027','execution',['completion.json','tests.stdout.log','tests.stderr.log','stdout.log','stderr.log'])]:
 for n in filenames:cp(R/folder/n,label+'/'+n)
for folder,label in [('bank-source-plan-review-20261027','attribution-plan-review'),('bank-attribution-pilot-review-20261027','attribution-pilot-review'),('dry-apron-code-review-20261027','pilot-code-review'),('dry-bank-domain-plan-review-20261027','next-plan-review')]:
 for n in ['brief.md','source-hashes.json','response.json','completion.json','stderr.log']:cp(R/folder/n,label+'/'+n)
 response=read(R/folder/'response.json');assert not response['is_error'] and not response.get('permission_denials') and 'FIN_REVISION' in response['result'] and 'claude-fable-5-1' in response['modelUsage'];assert read(R/folder/'completion.json')['inputs_unchanged']
for n in ['ev112-bank-source-attribution-20261027.md','ev112-dry-apron-offline-pilot-20261027.md','ev112-dry-bank-domain-pilot-20261027.md']:cp(W/'plans'/n,'plan-snapshots/'+n)
source=R/'river-kit7-a-on-f-20261026/kit-7-surfaces.npz';candidate=R/'dry-apron-linear-pilot-20261027/candidate-surfaces.npz';a=np.load(source);b=np.load(candidate);cap=np.minimum(a['station'],a['station'][-1]-a['station'])<6;delta=b['bed'][cap,:,1]-a['bed'][cap,:,1];assert np.count_nonzero(delta)==201 and float(delta.min())==-0.025390625
pilot=read(E/'pilot/result.json');assert pilot['status']=='REJECTED_OFFLINE';assert not pilot['gates']['curvature_nonincreasing'];receipt=read(E/'execution/completion.json');assert receipt['returncode']==0 and not receipt['timeout'] and receipt['source_unchanged']
post=dict(status='REJECTED_OFFLINE_CONFIRMED',additional_failure='CAP_NOT_PRESERVED',source_sha256=sha(source),candidate_sha256=sha(candidate),cap_changed_points=int(np.count_nonzero(delta)),cap_delta_range_m=[float(delta.min()),float(delta.max())],definition='rows with min(station,station[-1]-station)<6, independent of author free mask',original_gate_scope='fixed_exact only checked ~free, not the promised complete CAP region',adjudication=['Keep original pilot result unchanged and rejected; no rerun or weight sweep.','Next consumer must derive CAP/wet/borders from original arrays, and reject explicit mutations.','The rejection is not a defect of the historical author: the new pilot promised a larger fixed domain than it implemented.','No build or native/RAM trial for this rejected candidate.'])
(E/'cap-postcheck.json').write_text(json.dumps(post,indent=2)+'\n')
attr=read(E/'attribution/result.json');maxres=max(abs(r['source_minus_native_m']) for r in attr['rows']);geometry_deltas=[abs(v['y']-r['native_roadway_y']) for r in attr['rows'] for v in r['archived_lods'] if abs(v['resolution']-1e13)/1e13<1e-6]
checks=dict(attribution_status=attr['status'],native_waypoints=14,original_failed=7,pass_controls=7,max_source_native_residual_m=maxres,geometry_roadway_delta_range_m=[min(geometry_deltas),max(geometry_deltas)],pilot_tests=10,pilot_solver_iterations=pilot['solver']['iterations'],pilot_status=pilot['status'],extra_cap_failure=True,dayz_runs=0,generations=0,deployed=False,next_plan_status='REVIEWED_PENDING_IMPLEMENTATION',known_harness_limit='run_dry_apron_pilot wrapper can return exit0 after timeout (rcNone); consumers must use explicit timeout/returncode receipt. This run timeout=false,returncode0,resultREJECTED. Do not reuse this wrapper without correcting that status propagation.')
(E/'adjudication.json').write_text(json.dumps(checks,indent=2)+'\n')
(E/'README.md').write_text('''# Orillas de kit-7: atribución y piloto rechazado

Los14puntos archivados (7FAIL/7PASS) se atribuyen al delantal exterior q≈±6.
La altura fuente coincide con el Roadway nativo con error máximo4.84e-7m.
q es parámetro, no distancia física cuando la curvatura comprime el perfil.
La atribución localiza la superficie; PASS y FAIL comparten banda y no aísla
por sí sola la causa del generador. Se preservan Geometry, Roadway y agua aparte.

El único piloto de delantal4<|q|<18 queda **REJECTED_OFFLINE**. La energía discreta
de curvatura pasa561.733059→562.120487 (peor), aunque la pendiente máxima de
cara baja0.523794→0.510528. Solver345iter,97.84s de ejecución total,10testsPASS.
Bajada máxima7.8125cm. Las comparaciones con la navmesh vieja son descriptivas,
no una predicción ni prueba nativa. Ningún modelo, PBO, NM o despliegue nuevo.

La comprobación posterior descubre otra causa de rechazo:201puntos CAP que
debían permanecer exactos bajan hasta2.539cm. La puerta fixed_exact validaba
su propia máscara y no la promesa de conservar toda la transición de6m.
cap-postcheck.json contiene repro y hashes. No se reescribe el resultado ni se
repite el candidato. Ese falso alcance debe quedar entre los casos del council.

![Perfiles del piloto rechazado](pilot/profiles.png)

Fable5.1 revisó atribución, plan y código; revisión/adjudicación conservadas.
El fix previo del lector de floor incluye desplazamientoXZ por cuantización,
usando gradientes de las caras nativas. No cambia el floor del solver ni0.801.
Hay una limitación adicional del wrapper ante timeout, registrada explícitamente
en adjudication.json; este run terminó sin timeout y el candidato fue rechazado.

La siguiente hipótesis, revisada pero todavía SINimplementar, abarca toda la
orilla seca2.25<|q|<18 y conserva el lecho/lámina4.5m, protecciones yCAP≤6m.
Usará consumidor de ficheros guardados con mutantesCAP/lecho/water/XY/borde,
independiente de free. Plan: plans/ev112-dry-bank-domain-pilot-20261027.md.
Mantiene un solo candidato, peso.002 y500iter; sin barrido ni tolerancias menores.

Nav8 sigue607PASS/RAMFAIL; Load1RAM incompleto no se reabre. Los pendientes de
relieve, navegación, cliente/FPS/capacidad y council ampliado siguen abiertos.
''',encoding='utf-8')
for name,status in [('ev112-bank-source-attribution-20261027.md','EJECUTADO_SOURCE_ATTRIBUTION_ONLY'),('ev112-dry-apron-offline-pilot-20261027.md','EJECUTADO_REJECTED_OFFLINE')]:
 p=W/'plans'/name;s=p.read_text(encoding='utf-8');s=s.replace('Estado: REVISADO_SOUND_WITH_FIXES.',f'Estado: {status}.');s+='\nEvidencia: evidence/navigation/bank-source-rejected-apron-20261027. No relanzar scripts consumidos. Nuevo plan dry-bank-domain está revisado, pendiente de implementación.\n';p.write_text(s,encoding='utf-8')
hp=W/'HANDOFF.md';lines=hp.read_text(encoding='utf-8').splitlines();updates={'updated:':'updated: 2026-10-27 (7fallos atribuidos a orilla; piloto delantal rechazado por curvatura y CAP; nuevo dominio seco revisado)','plan:':'plan: plans/ev112-dry-bank-domain-pilot-20261027.md REVISADO_SOUND_WITH_FIXES_PENDIENTE_IMPLEMENTACION. Es un único candidato offline, no build/NMG/DayZ.','next:':'next: Implementar el plan dry-bank-domain con consumidor de ficheros independiente de free y mutantesCAP/lecho/agua/XY/borde. Baselineoriginal9d8caf0f; nunca continuar el piloto rechazado. Consultar ACTIVE-WORK.md.','handoff:':'handoff: evidence/navigation/bank-source-rejected-apron-20261027/README.md.14puntos7FAIL/7PASS enq±6. Piloto previo REJECTED:curvatura peor y201CAPmutados;10tests no prueban dominioCAP. Sin integración/nuevasondas.'};inside=False
for i,line in enumerate(lines):
 if line=='<!-- LIVE-STATE:START -->':inside=True
 if line=='<!-- LIVE-STATE:END -->':inside=False
 if inside:
  for key,value in updates.items():
   if line.startswith(key):lines[i]=value
hp.write_text('\n'.join(lines)+'\n',encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(E.rglob('*')) if p.is_file()};(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print('CHECKPOINT',len(manifest),checks)
