from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-wide-bank-fairing-2026-10-10';D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(R/'candidate-terrain.npz')=='cce4cd0c2f71355c6d8a110804b52570644e496055ada9ef17d07b4cb60c455c'
paths={R/x for x in ['plan.md','authoring.json','candidate-terrain.npz','plot_candidate.py','profiles-mesh.png','plot-diagnostic.json','root_nominal_margin.py','root-nominal-margin.json','next-method-plan.md','archive_checkpoint.py']}
for name in ['author','review-independent','line-feasibility']:
 paths.update(p for p in (R/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
manifest=[]
for p in sorted(paths):
 if not p.is_file():continue
 rel=p.relative_to(R);copied=None
 if p.stat().st_size<=400000 and p.suffix.lower() not in {'.npy','.npz'}:
  dest=D/'archive'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);copied=str(dest.relative_to(D))
 manifest.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'archived':copied})
(D/'manifest.json').write_text(json.dumps({'status':'OFFLINE_PILOT_REJECTED','artifacts':manifest},indent=2)+'\n',encoding='utf-8')
readme='''# EV88-Q — piloto ancho rechazado, sin despliegue

Una única resolución BVLS produjo96 alturas sobre EV82-B. El foco pasa de
3.7361 a1.8115m; energía de diferencias segundas−83.65%, máximo quiebro focal
30→6.91grados. Son medidas offline, no aceptación del mapa.

El consumidor completo rechazó Q: cotas/cruces excedidos por redondeo float32,
una nueva ventana casi plana, tres extremos pequeños sin pareja, condición
por fila/columna incumplida y limitaciones de representación física heredadas.
P/F/metadatos/protecciones se conservan y no se encontraron huecos nuevos de
cobertura nominal. Dos errores del oráculo (orientación del cruce y rampa
confundida con foso) fueron corregidos después, con fixtures; el FAIL original
se conserva y no es dictamen definitivo de esas dos puertas. No otro full.

La interpolación analítica B→Q no ofrece una variante aceptable bajo todas las
heurísticas: para mejorar el foco25% hace faltaalpha≥0.23117; la condición
de prominencia en cada fila solo permitealpha0. En el límite focal, la diferencia
que bloquea una fila es6.75mm. Esto justifica revisar el método, no aceptar Q.

El plan `archive/next-method-plan.md` propone EV90 con conservación física,
cotas float32 hacia dentro antes del solve y controles de forma sobre todo el
parche. Es propuesta previa a nueva autoría, pendiente de revisión y preflight;
no se extiende al mapa ni se construye candidato por este documento.

Q SHA cce4cd0c2f71355c6d8a110804b52570644e496055ada9ef17d07b4cb60c455c.
Referencia operativa EV82-B. EV87-S es otra preview aislada con margen dinámico
abierto. Base1.0 sigue NO ACEPTADA; imágenes `profiles-mesh.png` son malla offline.
Los archivos grandes quedan externos y fijados por el manifest.
'''
(D/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'artifacts':len(manifest),'copied':sum(x['archived'] is not None for x in manifest),'destination':str(D)}))
