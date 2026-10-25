from pathlib import Path
import json,shutil,hashlib
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-native-render-diagnostic-2026-10-09';E.mkdir(exist_ok=False)
for p in B.iterdir():
 if p.is_file() and p.suffix in ('.py','.md','.json'):shutil.copyfile(p,E/p.name)
for folder in ['baltic_render_probe_v1','mission','views']:
 for p in (B/folder).rglob('*'):
  if p.is_file() and p.suffix!='.bin':dest=E/p.relative_to(B);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for role,name in [('client','baltic_render_probe_v1.log'),('server','baltic_render_layer_v1.log')]:shutil.copyfile(Path('P:/DayZ_MCP_dev')/('_'+role)/'profiles'/name,E/name)
rows=(E/'baltic_render_probe_v1.log').read_text().splitlines();phases=[int(x.split(';')[1]) for x in rows if x.startswith('PHASE;')];assert phases==[0,1,3,9,2,3,9] and rows[-1].endswith(';render;0;water;0')
result=dict(status='NATIVE_RENDER_CONTROL_CONFIRMED_NOT_A_MAP_FIX',run_id='19cf732e-e6b7-4e01-b988-5c5d423fcfb3',phases=phases,engine_ids_verified_by_label_and_registry={'Render debug mode':131,'Water':276},baseline_untouched=True,positive_wireframe=True,positive_water_removed_and_restored=True,process_memory_access='READ_ONLY; API used for two menu mutations',final_values={'render':0,'water':0},normal_views=['R1 aerial','residual close','old rectangular boundary','R3 medium','reserve boundary'],inconclusive_views=['wide old boundary: visibility haze prevents whole outline verdict'],limits=['Water toggle covers all water materials; it does not isolate Ocean Shore alone.','Wireframe overlay is not by itself a physically flooded-area map.','Calibrated dry center was not stably reproduced as the strong original patch.','No world, terrain, water level or production material change.','No whole-map visual or performance acceptance.'])
(E/'result.json').write_text(json.dumps(result,indent=2)+'\n')
(E/'README.md').write_text('''# EV21 — control nativo del renderizador verificado

Una sesión con terreno EV16 intacto. La API DiagMenu.Get/SetEngineValue está definida en P:/scripts/1_core/proto/endebug.c:334–341. Los IDs se obtuvieron del registro del cliente diagnóstico mediante lectura de memoria: dirección del objeto, enlace del registro y etiqueta exacta coinciden. El ejecutable está fijado por SHA256. No se escriben direcciones ni se inyecta código.

La primera referencia queda intacta. Render debug mode=1 dibuja la malla; Water=1 elimina toda la familia de agua y devolverlo a0 la restaura. El mismo control funciona cerca de las charcas. Esto establece consumo real, pero no identifica por separado océano, charca y espuma, ni demuestra que todo triángulo de espuma visible en wireframe sea inundación física. El centro seco calibrado no reprodujo de forma estable el parche fuerte original. BALTIC-016 sigue abierto.

Tras restaurar ambos valores se revisaron el borde rectangular histórico, R3 a distancia media y la reserva. Las texturas cargaron sin intervención manual. No se aprecia un escalón rectangular en la primera vista; las panorámicas más lejanas tienen bruma y no permiten aceptar todo el contorno. R3 y el río de la reserva son continuos en estas vistas, sin extender esto a todas las distancias.

Cliente y servidor cierran normalmente, lease liberado, owner nulo y cero runs. El addon diagnóstico no pertenece a la base. Los scripts de inspección estática conservan varias salidas parciales; el contrato operativo usado es api-value-access.json y la prueba en vivo live-ids.json. No convertir las direcciones particulares de este ejecutable en API portable.

Documentación oficial del modo wire y la familia Water: https://community.bistudio.com/wiki/DayZ%3ADiag_Menu
''',encoding='utf-8')
print(str(E))
