from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-navv9diag-ram-ab-20261027';O=R/'kit7-navv9diag-ram-review-20261027';O.mkdir(exist_ok=False)
names=['setup_navv9diag_ram.py','prepare_navv9diag_ram_files.py','navv9diag_gate.py','prepare_navv9diag_ram_pass.py','finish_navv9diag_ram_pass.py','finalize_navv9diag_ram_ab.py','orchestrate_navv9diag_ram.js','test_navv9diag_gate.py','test_navv9diag_ram_conditions.py','test_navv9diag_ram_flow.cjs','test_navv9diag_ram_command.cjs']
paths=[R/n for n in names]+[W/'plans/ev112-kit7-navv9-ram-diagnostic-20261027.md']+[D/n for n in ['deployment.json','missions.json','mission-validation.json','diagnostic-gate-controls.json','conditions-controls.json','coordinator-controls.json','command-flow-controls.json']]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión acotada READ ONLY de plan y diferencial de corredor diagnóstico. Fable 5.1 nativo, una lane. SOLO Read/Glob/Grep, ninguna escritura, subagente, Git, proceso, MCP ni petición al usuario. Codex integra. Máximo 900 palabras, SOUND / SOUND-with-fixes / NEEDS-WORK, bugs concretos con ancla, no repetir controles ya probados.
R=E:/DayZ-Baltic-Build/shape-repair-20261025. W y todos los archivos exactos están en R/kit7-navv9diag-ram-review-20261027/source-hashes.json. Lee primero el plan ev112-kit7-navv9-ram-diagnostic-20261027.md y los cambios con respecto a los scripts homólogos nav12. La implementación es copia aislada: nunca modifica la preparación sellada de Nav12, que sigue bloqueada por FAIL funcional.
Nav8 pasa607 pero fallaRAM1.266/1.241. Nav12 falla3alturas nuevas, no RAM. El control original12.5 preserva4FAIL y se medirá SOLO DIAGNÓSTICO. Plan anterior condicionaba12.5 aRAM12FAIL; condición no cumplida, por eso este es replanteo explícito autorizado por autonomía, no eludir gate deaceptación. La esquina física tieneVisualgrava/Roadway1.910 yGeometry1.908, aguaVisual2.151/Roadwayagua1.901; noes defectodegrava. No se alterageometría.
Verifica el gate nuevo navv9diag_gate.py, preparación/consumo y agregado: conocidoFAIL porhash,4fallos exactos,607,4paquetesexactos,misiones nuevas,aceptacióninelegible. Paquetesoriginalesrestauradosporcopiahash,archivoconservado. Se añaden10controles delgate.14lifecycle+3mutantes,8comandos,12compatibilidad pasan; seisvalidator1filePASS. Una corrección de fixture apuntaba aNavV9Diag inexistente, yaesperaNavV9exacto; coordinadorno cambió. Verifica diferencia lógica real, no cantidadtests.
FIFOdirecto on_busyqueue/600/takeoverfalse, sinprelease niocupación. Solo despuésownrunlease, PID/creación/executable/misión, bridgeBOUND, sampler anteshashpesado,30+120s,closepropio/liberar. Misma misión normalizada,ABBAAB1.10/5%. Sin generación ni cliente. Ningúnreintento favorable: bloqueuno,invalidapara. ResultadoRAMno concedeaceptaciónfuncional. TampocoFAILRAMdemuestracausaexclusivakit. Revisa si los scripts conservan estas fronteras y si existe algún bypass accidental o referenciaantigua. accepted.json se creaDESPUÉSdeestu revisión, sellando fuentesoperativas/heredadas/plan/misiones/deployment. No esentrada faltante hoy. No ejecutes nada ni declaresRAMmedida. Comprueba nivel de lasrutas de fixtures si influye. Devuelve un dictamen sobre si puede comenzar el bloque diagnóstico; no propone otra variante automáticamente.
'''
(O/'brief.md').write_text(brief,encoding='utf-8')
args=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
start=time.monotonic()
with (O/'response.json').open('wb') as out,(O/'stderr.log').open('wb') as err:
    p=subprocess.Popen(args,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
    try:p.communicate(brief.encode(),timeout=300)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=30);raise
assert all(sha(Path(k))==v for k,v in before.items())
(O/'completion.json').write_text(json.dumps(dict(returncode=p.returncode,seconds=time.monotonic()-start,inputs_unchanged=True),indent=2)+'\n')
print('FABLE_EXIT',p.returncode);raise SystemExit(p.returncode)
