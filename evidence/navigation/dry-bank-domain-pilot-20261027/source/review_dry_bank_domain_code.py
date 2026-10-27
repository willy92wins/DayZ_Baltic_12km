from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'dry-bank-domain-code-review-20261027';O.mkdir(exist_ok=False)
context=R/'dry-bank-domain-setup-20261027/context.json'
data=json.loads(context.read_text(encoding='utf-8-sig'))
before=data['hashes']|{str(context):hashlib.sha256(context.read_bytes()).hexdigest()}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
brief='''Revisión independiente READ ONLY Fable5.1 por CLI nativo. Codex es executor/integrador autorizado. Una revisión antes del único candidato. Identidad de la ruta acreditada hoy por la revisión de plan anterior; verificar modelUsage de esta ejecución. Frontera: Read/Glob/Grep únicamente; no editar, Bash, MCP, Git, hijos ni escribir fuera. Máximo700palabras SOUND/SOUND-with-fixes/NEEDS-WORK con hallazgos concretos path:line y repro ejecutable; termina FIN_REVISION. Receptor: Codex verifica citas/repro.
Fuentes completas congeladas en E:/DayZ-Baltic-Build/shape-repair-20261025/dry-bank-domain-setup-20261027/context.json. Lee primero el plan nombrado allí y los cuatro NUEVOS scripts pilot_dry_bank_domain.py, verify_dry_bank_domain.py, run_dry_bank_domain.py, test_dry_bank_domain.py en esa raíz. No leer grandes npz/binarios. Revisión acotada de código frente a plan ya SOUND-with-fixes.
Contrato: única geometría original, orillaSECA2.25<|q|<18; lecho|q|<=2.25, CAP<=6 inclusivo entero, agua, XZ, bordes y protecciones intactos. Prior lineal2.25→18; .002/500; cuantización dirigida1/512; piso soporte+.02 y W+.025 si ya seco; infeasibles fijos. .025 experimental NO P14. Comprobar procedencia histórica sólo q>4. Checker recibe archivos guardados, no autor.free, reconstruye protecciones originales y derivacionesCAP/lecho. Identidad en bytes. Energía discreta estrictamente menor y pendientes físicas no mayores tras cuantización. Mutantes CLI +control idéntico que preserva pero REJECTEDsinmejora; timeout124. No build/NMG/DayZ. Probes viejosdescriptivosnuncaPASS. Revisor no aprueba mapa: sólo seguridad/validez del experimento. Inputs/plan intactos, una candidata900s, una corrección por repro máximo. No cambies toleranciasni pidas council previo. Distingue bugdemostrable de mejora opcional de instrumento. La suite de11controles se ejecuta paralelamente, sin solver todavía.'''
(O/'brief.md').write_text(brief,encoding='utf-8')
command=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
start=time.monotonic()
with (O/'response.json').open('wb') as out,(O/'stderr.log').open('wb') as err:
    child=subprocess.Popen(command,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
    try:child.communicate(brief.encode(),timeout=300)
    except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=30);raise
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
(O/'completion.json').write_text(json.dumps(dict(returncode=child.returncode,seconds=time.monotonic()-start,inputs_unchanged=True),indent=2)+'\n',encoding='utf-8')
print('FABLE_EXIT',child.returncode)
