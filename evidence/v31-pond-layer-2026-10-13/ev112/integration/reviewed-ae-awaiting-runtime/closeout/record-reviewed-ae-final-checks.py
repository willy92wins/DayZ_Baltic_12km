"""Preserve final handoff checks and the external runtime blocker without altering raw gates."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,shutil,subprocess
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
A=P/'evidence/v31-pond-layer-2026-10-13/ev112/integration/reviewed-ae-awaiting-runtime'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=P,text=True).strip();assert head=='dbb9fbc60234d1cc7470e7178f3886f4beaa61a9'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=P).strip()
assert not (O/'missions-installed-ae.json').exists()
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
raw=O/'vault-link-audit-correct-baseline.log';log=raw.read_text(encoding='utf-8-sig')
metrics={k:int(v) for k,v in re.findall(r'(?m)^([a-z_]+)=(\d+)\s*$',log)}
assert 'link_audit_status=FAIL' in log and metrics['missing_session_index']==0 and metrics['baseline_pairs']==656 and metrics['new_live_pairs']==597
new=read('reviewed-ae-new-links-check.json');assert new['status']=='PASS_ALL_NEW_LOCAL_TARGETS' and new['duplicate_exact_session_targets']==0 and not new['shared_files_changed_since_own_write']
local=read('reviewed-ae-local-doc-checks.json');assert local['status']=='PASS_LOCAL_NEW_LINKS_AND_MAP_FRESHNESS'
block=read('runtime-blocker-ae-final-observation.json');assert block['box']['occupied'] and not block['own_run_launched']
out=dict(status='REVIEWED_BUILD_COMPLETE_RUNTIME_BLOCKED',time_utc=datetime.now(timezone.utc).isoformat(),
 source_commit='845295f7b9b0a3ea225ba675755f34efa67a548b',build_archive_commit=head,
 initial_vault_audit=dict(exit_code=1,tool_response_chunk='864123',baseline='AI/20_Runbooks/scripts/baseline-control.json',baseline_schema='skill-drift-control/v1',baseline_pairs=0,new_live_pairs=597,missing_session_index=0,scope='Command prescribed by the runbook completed FAIL; the referenced file belongs to skill drift, not the line-pair link baseline. Full original tool output was observed; this is a summary, not a copied full log.'),
 correct_baseline_audit=dict(exit_code=1,status='FAIL',tool_completion_chunk='4e7e61',baseline='AI/20_Runbooks/scripts/baselines/vault-link-audit-broken-2026-08-29.txt',baseline_sha256='9ed4d3c53f33a36721ad3366e8cac3c3d8643f821f2565c3093756fa95d605b3',metrics=metrics,log_sha256=hashlib.sha256(raw.read_bytes()).hexdigest()),
 local_links=new,local_map_checks=local,runtime=block,
 scope='No global vault PASS. Existing link baseline and verifier were not modified. New links from this update resolve; current session index is unique. The complete global failure list is not attributed per pair to this task. Source/PBO acceptance is separate from documentation checks and runtime remains unexecuted.')
receipt=O/'reviewed-ae-final-checks.json';assert not receipt.exists();receipt.write_text(json.dumps(out,indent=2)+'\n')
for source in (Path(__file__),receipt,raw,O/'check-reviewed-ae-new-links.py',O/'reviewed-ae-new-links-check.json',O/'runtime-blocker-ae-final-observation.json'):
 dest=A/'closeout'/source.name;assert not dest.exists();shutil.copyfile(source,dest);assert dest.read_bytes()==source.read_bytes()
summary=A/'README.md';before=summary.read_bytes();backup=O/'readme-before-final-handoff-checks.md';assert not backup.exists();backup.write_bytes(before)
add='''\n## Comprobaciones del handoff\n\nLos enlaces nuevos de las notas compartidas pasan (nueve destinos), los 17 enlaces del resumen/mapa existen y el índice tiene una sola entrada de esta sesión, sin duplicados exactos. Los 342 archivos de evidencia copiados coinciden con sus hashes y con los blobs preparados para Git.\n\nLa auditoría global del vault conserva **FAIL**: 597 pares vivos nuevos frente al baseline de enlaces existente; cero sesiones sin indexar. El primer comando del runbook apuntaba por error a un baseline de otra auditoría; ambos resultados se conservan, sin cambiar el baseline ni el verificador. El pin global del generador PROJECT-MAP también tiene una divergencia previa; la actualidad de ambos mapas locales se comprobó aparte. [Resultados y alcance](closeout/reviewed-ae-final-checks.json).\n'''
assert summary.read_bytes()==before;summary.write_bytes(before+add.encode())
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-18-dayz-baltic-ev112-ot1-execution.md');before=session.read_bytes()
entry=f'''\n### Cierre verificable {datetime.now().astimezone().strftime('%H:%M')} — runtime aún bloqueado\n\nFuentes845295f y archivo/handoff dbb9fbc, sin push.342 archivos archivados verificados byte a byte contra SHA256 y blobs de Git; el diff de fuentes/documentos pasa. Se conservan sin limpiar espacios de dos logs G1 y líneas de contexto del diff original, porque son evidencia cruda.\n\nNueve destinos nuevos de notas y17 enlaces de resumen/mapa válidos; una entrada de esta sesión y cero duplicados exactos de sesiones en el índice. Relectura de diez destinos compartidos sin escritor posterior, prefacio de la parada Baltic preservado. Mapas raíz/worktree actualizados. El pin global del generador sigue INCONCLUSIVE por divergencia previa, sin editarlo.\n\nAuditoría global ejecutada: primer comando del runbook usa baseline-control.json, que es skill-drift-control/v1 y produce0pares; FAIL. Repetición diagnóstica contra el baseline de enlaces existente del29-08 (656pares) también FAIL,597pares vivos nuevos y0sesiones sin indexar. No se ha alterado baseline/verificador ni arreglado deuda global fuera del encargo. Log completo de la segunda ejecución y recibos en el closeout del archivo. No se declara el vault global verde.\n\nLa última lectura MCP estándar mantiene el banco ocupado por @LFDeathRagdoll; la lectura130 observó un nuevo runajeno3f028cf8-e2f5-4fd7-ad92-4d4731909680 con uso humano. El run previo868d... no se ha cerrado por esta sesión. No hay lease/run propios ni instalación de misiones; sonda4114 NO EJECUTADA. Picker de disponibilidad sin respuesta. Reanudar solo tras comprobar caja libre; las fuentes y el paquete ya tienen cierre OT7 sin mayores.\n'''
backup=O/'session-before-final-handoff-checks.md';assert not backup.exists();backup.write_bytes(before)
assert session.read_bytes()==before;session.write_bytes(before+entry.encode());assert session.read_bytes()==before+entry.encode()
print('Final receipts preserved; runtime remains blocked; global vault FAIL is explicit')
