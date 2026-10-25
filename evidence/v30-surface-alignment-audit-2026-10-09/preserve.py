from pathlib import Path
import shutil
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-surface-alignment-audit-2026-10-09';E.mkdir(exist_ok=False)
for p in B.iterdir():
 if p.is_file() and p.suffix in ('.py','.md','.json'):shutil.copyfile(p,E/p.name)
(E/'README.md').write_text('''# EV22 — desalineación de máscaras confirmada

Las 1.024 máscaras se leen del PBO desplegado EV16 y se decodifican con ImageToPAA. Los 150.847.524 píxeles de un metro del dominio se comparan una sola vez, sin contar solapes, con el terreno triangular y el campo de planos validado contra el agua compilada. Los4.775 materiales contienen las cuatro superficies.

35.772.220 píxeles están bajo agua nominal. 59.717 tienen algún peso de superficie terrestre en la máscara compilada;19.613 tienen profundidad>=0,20m. La clasificación con PNG de procedencia confirma55.958 píxeles ya incorrectos antes de comprimir,5.707 de ellos con margen de dos píxeles respecto a tierra y profundidad>=0,20m. Otros4.239 se explican solo por compresión. El FAIL original se conserva; el margen es clasificación, no cambio retroactivo de gate.

Un negativo altera a rojo un píxel mojado real y el consumidor aumenta su cuenta de defectos. El control de un quad no plano distingue triangulación nativa de bilineal/diagonal opuesta. Estos controles complementan el negativo elemental inicial, que por sí solo no probaba el consumidor completo.

La regla nominal actual reconstruida desde cls/level NO coincide con el campo congelado del agua desplegada. Una reconstrucción de texturas debe usar los planos compilados, no inferirlos otra vez. No se han cambiado máscaras, satélite, terreno ni niveles en esta unidad.

Grava sobre tierra seca también puede ser camino u orilla legítima. La auditoría no juzga por sí sola el color del satélite, la carga de teselas ni todas las distancias. Las PAAs y PNGs decodificadas quedan en el build externo; el informe conserva sus hashes.
''',encoding='utf-8')
print(str(E))
