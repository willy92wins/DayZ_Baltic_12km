from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-polygon-terminal-2026-10-09'
E.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['plan.md','discover_and_solve.py','verify_terminal_global.py','discovery.json','authoring.json','verification.json','constraints.npz','delta.npz','tiles.jsonl','global-contours.png','contour-samples.npz','sectors.json','preserve.py']
for name in names:
    shutil.copyfile(B/name,E/name);assert sha(B/name)==sha(E/name)
readme='''# EV27 — remate poligonal del Volkhov: propuesta descartada

EV16 no descubria este extremo porque el Volkhov es un poligono sin perfil. Se proceso una caja junto al corte oriental, con el mismo kernel y limites de EV16: una propuesta, 29 vertices, sin variacion de niveles ni agua.

El consumidor local mejora el p90 de61,8074 a60,0805 grados. El consumidor global independiente rechaza la propuesta: la proporcion de giros>30 pasa de0,1456496107 a0,1456690995 (cuatro muestras mas de205.246). Los demas gates pasan, incluidas830 masas, cero conexiones nuevas/perdidas, cero ganancia de agua en caras secas, cotas protegidas y calado. No se relaja el criterio, no se empaqueta y EV25 permanece vigente. El remate no queda resuelto.

Dos antiguos no_contour no son fallos de representacion: stream_0452 y stream_0456 tienen tier1500, fuera del minimo2500 de build_v30_water.py. No figuran en water_v3.geojson ni tienen celdas fisicas de agua en aquellas cajas. No se anaden cursos excluidos del alcance aprobado.

La fuente EV25 fb36ec4c y el candidato rechazado4bf072bd siguen en E:. El delta, las restricciones, el descubrimiento y todos los consumidores quedan preservados aqui. Sin prueba de motor para una geometria que ya falla en fuente. Sin subagentes, sin push.
'''
(E/'README.md').write_text(readme,encoding='utf-8')
(E/'preservation.json').write_text(json.dumps({p.name:sha(p) for p in E.iterdir() if p.is_file()},indent=2)+'\n')
print(json.dumps(dict(status='REJECTED_CANDIDATE_PRESERVED',files=len(list(E.iterdir())),evidence=str(E))))
