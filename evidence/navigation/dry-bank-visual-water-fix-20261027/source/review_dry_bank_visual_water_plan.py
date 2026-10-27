from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'dry-bank-visual-water-plan-review-20261027';O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-dry-bank-visual-water-fix-20261027.md',W/'tools/water/continuous_stream_pilot_v31.py',
       R/'pilot_dry_bank_domain.py',R/'verify_dry_bank_domain.py',R/'run_dry_bank_domain.py',
       R/'dry-bank-water-reference-diagnosis-20261027/result.json',R/'dry-bank-domain-run-20261027/result.json',
       R/'dry-bank-domain-analysis-20261027/visual-water-freeboard.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
brief='''READ ONLY Fable5.1 por CLI nativo, revisión de plan y sustitución concreta ANTES de implementar. No editar/Bash/Git/MCP/hijos. Máximo650palabras SOUND/SOUND-with-fixes/NEEDS-WORK; FIN_REVISION. Codex ejecutor/integrador autorizado es receptor y verificará tus citas. Una ronda/una nueva candidata; no barridos ni nueva autorización humana rutinaria. Fuentes en E:/DayZ-Baltic-Build/shape-repair-20261025/dry-bank-visual-water-plan-review-20261027/source-hashes.json.
Contexto NUEVO: tu revisión anterior dijo SOUND; consumidor dio OFFLINE_CANDIDATE_ONLY, pero postcheck independiente detectó4puntos que pierden piso. Se retiró candidato df0c5994, sin compilar. Mecanismo aislado: source.water Y redondeada1/512, source.level W sin redondear. oldbed-water=13ticks (.025390625) pero level algo mayor hace was_dry FALSE; solver baja esos4puntos hasta margen.001953125. Agua yCAPbyteexactos. Código actualusa level para was_dry yfloor; compartenbugautor/checker. Informe diagnóstico contiene4filas ydosreferencias.
Lee plan nuevo ev112-dry-bank-visual-water-fix-20261027.md. Cambio propuesto preciso: autor water=np.broadcast_to(arrays['water'][:,0,1,None],original.shape), checker water=np.broadcast_to(arrays['water'][:,0,1,None],original.shape); en ambos validar igualdad Y entre ambas columnaswater. q3/q4 stats usanwaterY. Level intacto pero deja de serreferenciadepiso. Mantener .025/.02/prior .002/500/ceilingoriginal/dominio/quant/CAP ybase9d8 original. No iniciar desde rechazado. Nuevo checker DEBE rechazar el candidato retirado porbounds, ymutanteuno de4puntos. ControlesCLI originales siguen, protegidoN/Azero real; hasta3hijosreadonly tests paralelos, directorios distintos. Validación adicionalfueraautorgenera y compara todospreviamentesecos contraagua guardada; novoP14certification. Candidatouna900s;sinbuild/NMG/DayZ. Nuevo presupuesto se abre porqueorquestadorretira anteriorporcausa concreta, no porquequieraunresultadofavorable.
Verifica mecanismo, sustituciones y contrato. Señala sólo errores con repro ocontradicción real. SiSound aceptar ejecutar esas dos sustituciones y cobertura. No hagasotraexploración amplia delcouncil. Valora si esto corrige los cuatro fallos sin relajar piso ysin tocar agua/extremos.'''
(O/'brief.md').write_text(brief,encoding='utf-8')
command=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
start=time.monotonic()
with (O/'response.json').open('wb') as out,(O/'stderr.log').open('wb') as err:
    child=subprocess.Popen(command,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
    try:child.communicate(brief.encode(),timeout=300)
    except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=30);raise
assert all(sha(Path(p))==h for p,h in before.items())
(O/'completion.json').write_text(json.dumps(dict(returncode=child.returncode,seconds=time.monotonic()-start,inputs_unchanged=True),indent=2)+'\n',encoding='utf-8')
print('FABLE_EXIT',child.returncode)
