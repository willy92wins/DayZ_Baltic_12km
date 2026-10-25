from pathlib import Path
import hashlib,json,shutil,re
G=Path(__file__).resolve().parent
P=G/'global-operator-prototype'
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OUT=W/'evidence/v30-global-bank-extension-2026-10-10/underlay-preflight-checkpoint'
FIX=G/'G/wet-bank-pilot/postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1'
LOD=G/'water-lod-discriminator-plan'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
groups={
 'd8-fixed':(FIX,['PLAN.md','lattice_milp.py','candidate_model.py','run_candidate_once.py','real-run-01/receipt.json']),
 'subcell-analysis':(G/'build-wide-slope/subcell-flag-probe/runtime-v2/analysis',['analyze_probe.py','runtime-v2-analysis.json','analysis.md']),
 'underlay':(LOD,['PLAN-v2.md','v2/exact_tile_clearance.py','v2/exact-clearance.json','v2/build_diagnostic.py','v2/build/stage.json','v2/build/deploy.json','v2/prepare_runtime.py','v2/runtime-mission.json','v2/runtime-mission/init.c','v2/runtime/A/runtime-receipt.json','v2/runtime/A/native-heights.log','v2/runtime/A/scene.log','v2/runtime/A/render-settings.log']),
 'neighbor-mechanism':(G/'G/wet-bank-pilot/postsolve-consumer/diagnostic-polish-consumer-v1/analysis-v2-recovery',['inspect_no_neighbor.py','mechanism.json','README.md']),
}
for name in ('energy-neighbor-polish-v1','energy-neighbor-polish-v1-recovery','energy-neighbor-polish-v2-recovery'):
 groups[name]=(FIX/name,['PLAN.md','energy_neighbor_polish.py','test_energy_neighbor_polish.py','run-01/enumeration.started.json','run-01/receipt.json','run-01/neighbors.jsonl'])
CON=P/'global-dry-rollback/postsolve-consumer'
groups['global-original']=(CON/'complete-consumer',['PLAN.md','verify_global_dry_rollback.py','test_verify_global_dry_rollback.py','runs/attempt-02/report.json'])
groups['global-instrumented']=(CON/'instrumented-v2',['PLAN.md','verify_global_dry_rollback_v2.py','verify_global_dry_rollback_v2.py.before-testpath','test_verify_global_dry_rollback_v2.py','instrumentation-review.json','admission-audit-02.json','runs/attempt-01/report.json','runs/attempt-02/report.json','runs/attempt-02/report.json.progress.json'])
for folder,names in groups.values():
 for name in names:
  if not(folder/name).is_file():raise FileNotFoundError(folder/name)
OUT.mkdir(parents=True,exist_ok=False)
copies=[]
for label,(folder,names) in groups.items():
 for name in names:
  src=folder/name;dst=OUT/label/name;digest=sha(src)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  if sha(src)!=digest or sha(dst)!=digest:raise ValueError('Copy drift')
  copies.append({'source':str(src),'copy':str(dst.relative_to(OUT)),'sha256':digest})
refs=[]
for src in [FIX/'real-run-01/rejected-diagnostic.npz',LOD/'v2/build/terrain.npz',*sorted((LOD/'v2/runtime/A').glob('capture_*.jpg'))]:
 refs.append({'path':str(src),'sha256':sha(src),'bytes':src.stat().st_size})
(OUT/'manifest.json').write_text(json.dumps({'copied':copies,'external':refs},indent=2)+'\n',encoding='utf-8')
note='''# Underlay diagnostic, local closure and full-map consumer

The production map remains unaccepted. No global candidate has been promoted.

The local physically feasible float32 result still fails the unchanged energy allowance. The completed bounded recovery checks all 242 single-coordinate neighbors and finds no eligible neighbor. Two earlier execution errors were handler defects, preserved separately. The two energy-improving neighbors fail crossing or lower-bound gates; this does not prove full-domain infeasibility.

The independent global consumer first timed out at 600s without phase metrics. Instrumented V2 preserves all mathematical gates, hashes 14,212 inputs in 8.586s, then refuses admission because the required 9GiB free reserve is unavailable while DayZ is open. No geometry acceptance was evaluated in that attempt. Run it only after the game memory is released.

The isolated underlay diagnostic modifies 1089 source heights by -6.10m. Only the WRP differs among 6827 world PBO entries; the water PBO is byte-identical. It is deliberately unsuitable for production. Fresh baseline A run0013bf35 captures the gray-water defect and 1225 native heights, then closes orderly and releases its lease. B could not launch because another session is testing LFSkateboard on port2302. No takeover or alternate-port parallel run was attempted.

The render_frozen_signal field is a warning, not a proof of frozen render (mcp_capture.py:817-828). The new same-scene pan/restore is a positive 3D liveness control; an independent image/native comparison is pending. Shadow setting integer0 is recorded as integer0, without assuming its enum meaning.

Subcell analysis confirms that water flags can remain false where compiled physical/visible water faces exist. These server samples do not certify client render or the full wave envelope. BASE1.0, artistic relief, navigation, Terrain Builder and navmesh remain open.
'''
(OUT/'README.md').write_text(note,encoding='utf-8')
shutil.copyfile(__file__,OUT/Path(__file__).name)
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8')
updates={
 'runtime_lock':'20:21 UTC: nuestro run de referencia underlay 0013bf35 cerrado ordenadamente y lease liberada. Banco ocupado por prueba ajena LFSkateboard, puerto2302/perfil130; no tocarla. B rechazado sin run_id; reanudar con estado fresco.',
 'wet_bank':'D8 corregido deja diagnóstico2209df75 físicamente válido, energía rechazada. Recovery2 de vecinos completa242/242 en3.657s:0 admisibles, sin artefacto. Dos errores de handlers previos preservados. Dos vecinos pasan energía pero violan cruces P/F o lowerbound; no ampliar a ciegas ni afirmar inviabilidad global.',
 'global_operator':'Recovery1bd6b67d:2.502.853 alturas secas,27rollbacks,objetivo69217.203→68784.240,NOaceptado. Consumidororiginal timeout600s. V2instrumentado8ab83e18:16fixtures,14.212hashes/1.16GB en8.586s;attempt02 rechaza RAM tras23.869s, sin gatesgeométricos. Reintentar idéntico solo cuando DayZ libere RAM≥9GiB, mantener6GiBreserva/3GiBpico.',
 'render':'ReferenciaA underlayrun0013bf35 reproduce recuadros con terreno cargado; cámara2417/65/6745 y3frames+pancontrol. Diagnóstico desechable world28a7509f/terrain3e12ced7 baja1089vértices6.1m; agua3946db8b exacta y6826entradas intactas. Bpendiente bancoajeno. La causa sigue sin aislar; warningrender_frozen no es veredicto.',
 'next':'Completar underlay B/A-prime cuando banco disponible; verificar1225alturas/cámara/liveness/ROI. Consumidor globalV2 pendiente RAM libre, no promoverhastaPASS. Local1ULP terminado sin solución; siguiente diseño exige mecanismo coordinado/revisión sin relajargates. Continuar pendientes toda superficie/TB/navmesh.',
 'git':'Branch claude/codex-handoff-review-74f290, underlay-preflight-checkpoint preparado; consultarHEAD. Sinpush.'}
for key,value in updates.items():
 if len(re.findall('^'+key+':.*$',s,re.M))!=1:raise ValueError(key)
 s=re.sub('^'+key+':.*$',key+': '+value,s,flags=re.M)
p.write_text(s,encoding='utf-8',newline='\n')
for dest in (G/'WORKING_STATE.md',Path(r'C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-10-dayz-baltic-bank-relief.md')):
 with dest.open('a',encoding='utf-8') as f:f.write('\n\n### 2026-10-10 20:23 UTC — underlay and independent consumer\n\n'+note)
print(json.dumps({'copies':len(copies),'references':len(refs),'path':str(OUT)}))
