from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
def replace_lines(p,changes):
    with p.open(encoding='utf-8',newline='') as f:s=f.read()
    lines=s.splitlines(keepends=True)
    for i,line in enumerate(lines):
        key=line.split(':',1)[0]
        if key in changes:lines[i]=key+': '+changes[key]+('\r\n' if line.endswith('\r\n') else '\n')
    v=''.join(lines)
    with p.open('w',encoding='utf-8',newline='') as f:f.write(v)
    with p.open(encoding='utf-8',newline='') as f:assert f.read()==v
replace_lines(W/'HANDOFF.md',{
'runtime_lock':'EV76 run3b4a4a81 cerrado orderly y lease liberado. EV77 run16638541-9244-485c-81fe-67aa6fe4a143 ABIERTO RUNNING_IDLE esperando foco manual, cliente94292/servidor163944. Lease liberado; session_status ownernull/selfnone, boxoccupiedtrue/adopttrue. No mantener lease durante espera humana. Cámara [2417,65,6745], nativaFOV1.1/1920x1080. ProbeV2READY131/276/fase0; vista magenta, wire todavía NO ejecutado. Reacquire antes de acciones, no lanzar otro run.',
'next':'EV77 esperando foco manual para referencia normal válida. Reacquire/adopt el run16638541 y bridge_status.ready; luego wire1/wire-only2/restauración0 si no agotó auto-restauración1200s. Si ya agotada, registrar diagnóstico incompleto antes de otro ciclo. Un run, una pose; máximo10min de comparación tras referencia válida, espera humana sinlease. No atribuir causa por ausencia de líneas. MapaEV72 intacto; no promoverEV68.'})
# Correct waiting instructions in the actual diagnostic plan rather than append a conflicting rule.
p=B/'plan.md';s=p.read_text(encoding='utf-8').replace('máximo10min tras cámara estable','máximo10min de comparación tras referencia normal válida').replace('Restaurar antes de cierre orderly, liberar lease y comprobar ocupación.','Durante espera humana liberar lease conservando el run; readoptar antes de mutar. El probe se restaura solo a los1200s: no ejecutar fases fuera de ese plazo ni declarar comparación completa. Restaurar antes de cierre orderly, liberar lease y comprobar ocupación.')
p.write_text(s,encoding='utf-8')
readme='''# EV77 — comparación wire pendiente de referencia válida

Un único run16638541-9244-485c-81fe-67aa6fe4a143 con EV72 exacto y probeV2 diagnóstico. Source/deployed, labels/registro131/276 y cámara nativa pasan. Fase0normal y Water0 confirmados. Ningún wire1/2 ejecutado todavía.

Tres capturas de arranque tienen cielo magenta/materiales sin cargar: no sirven para el contraste. Se pidió foco manual una vez. Cliente94292 y servidor163944 se dejan abiertos para esa intervención; lease liberado durante espera humana, ownernull/selfnone y boxoccupied/adopttrue. No confundirlo con banco libre ni lanzar otro run.

Tras respuesta, adoptar con session_acquire_wait, comprobar bridge.ready y una referencia normal válida con mismo mapa/pose, luego fases1/2/restauración con readbacks. El probe limita su vida a1200s y fuera del plazo fuerza9: si se agota, no atribuir las capturas a fases no ejecutadas. Leer HANDOFF para estado actual.

Los resultados de Luna y EV75/76 se conservan en ../v30-water-cause-investigation-2026-10-10. Esta unidad está PENDIENTE, no demuestra causa ni reparación. Mapa, niveles y materiales intactos; sin push.
'''
(B/'README.md').write_text(readme,encoding='utf-8')
D=W/'evidence/v30-water-wire-classification-2026-10-10';D.mkdir(exist_ok=True)
rows=[]
for p in sorted(B.rglob('*')):
    if not p.is_file() or p.suffix.lower() not in {'.py','.md','.json','.c','.cpp','.jpg','.log'}:continue
    assert not p.is_symlink();rel=p.relative_to(B);dest=D/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,dest)
    h=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==h
    rows.append(dict(path=rel.as_posix(),sha256=h,bytes=p.stat().st_size))
(D/'preservation.json').write_text(json.dumps(dict(status='WAITING_USER_FOCUS_NO_WIRE_RESULT',files=rows),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(files=len(rows),bytes=sum(r['bytes'] for r in rows))))
