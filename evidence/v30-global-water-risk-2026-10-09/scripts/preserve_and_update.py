"""Preserve this task's bounded evidence and refresh its live pointers."""
from pathlib import Path
import json,hashlib,shutil
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');E=W/'evidence/v30-global-water-risk-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=[]
def copy(a,b):
    b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b);assert sha(a)==sha(b)
    manifest.append(dict(source=str(a),copy=str(b.relative_to(E)),sha256=sha(b)))
for a in sorted(B.glob('*.py')):copy(a,E/'scripts'/a.name)
for a in sorted(B.glob('*.ps1')):copy(a,E/'scripts'/a.name)
for root in ('missions','terrain-detail','native-census-c1r3p-v2'):
    for a in (B/root).rglob('*'):
        if a.is_file() and a.suffix in ('.c','.json','.log','.jpg','.png','.csv') and a.name not in ('grid.csv',):copy(a,E/root/a.relative_to(B/root))
for a in B.glob('Baltic*.c'):copy(a,E/'scripts'/a.name)
for name in ('compiled-domain-discrepancies-v2.json',):copy(B/name,E/name)
copy(Path(r'C:/Users/guill/AppData/Local/Temp/codex-clipboard-d7e17edb-54ef-4c30-ba0b-231f4f9b84aa.png'),E/'user-images/bridge-residual-confirmed.png')
(E/'preserved-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
handoff=W/'HANDOFF.md';text=handoff.read_text()
updates={
'global_detection:':'global_detection: Auditor offline completo y censo nativo completo 4.194.304 vértices. Error altura máximo 0,015 mm. 73 secos con agua y 38 húmedos con flags falsos clasificados; no 111 defectos. Inventario compilado 16.980 instancias/9.025 modelos, corte real 0,51; V2 sustituye el primer inventario con corte por defecto. Cinco pérdidas microscópicas de juntas reproducidas en ODOL; dos reglas de halos corregidas en generadores.',
'land_artifacts:':'land_artifacts: Usuario confirma residual x=2718,48525 z=6812,81287; suelo 1,520454 m. Temporal nativo 562x62: en ese punto agua con ondulación adicional máximo 0,882279 m, 0,638171 m bajo suelo. No explica el parche. Control detalle medio-maximo-medio INCONCLUSO; índice original 2 restaurado. No cerrar 016 por consultas físicas.',
'runtime_lock:':'runtime_lock: Censos V1/V2, proyección, detalle y temporal ff4399c0 cerrados orderly_close; leases liberados. Comprobar session_status fresco antes de lanzar. Ningún run propio abierto al guardar este bloque. Los dos fallos de compilación previos se retiraron por lifecycle exacto; no crash. Prueba ajena LFSkateboard intacta.',
'next:':'next: Preview de reparación halo-fix-v2 en construcción: 113 modelos nuevos, 49 tiras obsoletas retiradas, terreno y niveles exactos; cinco microjuntas cubiertas en compilado. No promocionar: comparar WRP/PBO, repetir censo global y consumidores físicos. Continuar agua visual residual, juntas visuales globales, smoothing/finales y demás bugs antes de TB/navmesh.'}
for key,value in updates.items():
    lines=text.splitlines();indices=[i for i,line in enumerate(lines) if line.startswith(key)];assert len(indices)==1,key
    lines[indices[0]]=value;text='\n'.join(lines)+'\n'
handoff.write_text(text)
state=W/'evidence/v30-water-visual-fix-2026-10-08/diagnostic-state.json';d=json.loads(state.read_text())
d['next_control']='Historical experiment sequence completed; current state is ../v30-global-water-risk-2026-10-09/README.md. Wave amplitude, subdivision and near-plane controls did not remove the artifact.'
d['current_status']='OPEN_VISUAL_RESIDUAL_C1R3P; global native and compiled detection completed; isolated halo correction under validation'
state.write_text(json.dumps(d,indent=2)+'\n')
old=W/'evidence/v30-valley-smoothing-2026-10-08/README.md';text=old.read_text()
prefix='Estado actualizado 09-10: C/C1 globales retirados. C1R3P conserva R3 y relieve general con validación offline y motor 28x62 PASS; vistas R3 mejoran taludes pero mantienen giros lejanos angulares. Guillermo confirma residual de agua junto al puente. LAND180 terminó por idle_timeout orderly, no sigue abierto ni sufrió crash. Todos los runs de este bloque están cerrados. Continúa en [censo global y reparación de halos](../v30-global-water-risk-2026-10-09/README.md). El contenido posterior es histórico.\n\n'
if not text.startswith(prefix):old.write_text(prefix+text)
print(json.dumps(dict(preserved_files=len(manifest),hashes_verified=True,live_state_updated=True)))
