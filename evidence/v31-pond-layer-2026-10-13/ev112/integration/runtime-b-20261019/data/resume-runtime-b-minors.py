from pathlib import Path
import hashlib,json,runpy
O=Path(__file__).parent;B=O/'review-runtime-b-minor-backups'
names=['fix-runtime-b-review-minors.py','write-runtime-b-result.py','archive-runtime-b.py','close-runtime-b.py','close-review-runtime-b.py','prepare-runtime-b-followup.py']
for name in names:
 p=O/name;s=p.read_text(encoding='utf-8');s=s.replace('.read_text()',".read_text(encoding='utf-8')")
 # All JSON outputs are ASCII escaped; prose outputs need explicit UTF-8.
 for a,b in [(".write_text(note)",".write_text(note,encoding='utf-8')"),(".write_text(readme)",".write_text(readme,encoding='utf-8')"),(".write_text(s)",".write_text(s,encoding='utf-8')"),(".write_text('\\n'.join(lines))",".write_text('\\n'.join(lines),encoding='utf-8')")]:s=s.replace(a,b)
 p.write_text(s,encoding='utf-8')
s=(O/'fix-runtime-b-review-minors.py').read_text(encoding='utf-8')
s=s.replace("(O/'water-temporal-runtime-b/REFERENCE-NOTES.md').write_text('# Referencias de terreno\\n\\nEl campo `d_terrain_minus_water_m` es histórico de C; véase [la anotación de procedencia](../probe-runtime-b/REFERENCE-NOTES.md). `ground` corresponde a B.\\n')","(O/'water-temporal-runtime-b/REFERENCE-NOTES.md').write_text('# Referencias de terreno\\n\\nEl campo `d_terrain_minus_water_m` es histórico de C; véase [la anotación de procedencia](../probe-runtime-b/REFERENCE-NOTES.md). `ground` corresponde a B.\\n',encoding='utf-8')")
(O/'fix-runtime-b-review-minors.py').write_text(s,encoding='utf-8')
prefix=s[:s.index("p=O/'close-runtime-b.py'")].replace('B.mkdir(exist_ok=False);changes=[]','assert B.is_dir();changes=[]')
recover="\nfor name in ('close-runtime-b.py','write-runtime-b-result.py','update-runtime-b-handoff.py'):\n backup=B/f'{len(changes):02}-{name}';p=O/name\n changes.append(dict(path=str(p),backup=str(backup),before=hashlib.sha256(backup.read_bytes()).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest()))\n"
tail="note='''"+s.split("note='''",1)[1]
cont=O/'resume-runtime-b-minor-documents.py';assert not cont.exists();cont.write_text(prefix+recover+tail,encoding='utf-8');runpy.run_path(str(cont),run_name='__main__')
# Rebuild the human-facing preview README in UTF-8; no bound JSON/mission changes.
dep=json.loads((O/'deploy-runtime-b.json').read_text(encoding='utf-8'));installed=json.loads((O/'missions-installed-ae.json').read_text())
doc=(O/'personal-view-ae/README.md').read_text(encoding='utf-8').replace('preparada y vinculada al paquete; no lanzada ni aceptada visualmente.','instalada, preparada y vinculada al paquete corregido; no lanzada ni aceptada visualmente.').replace('Para instalar la copia en mpmissions y lanzar:','Para lanzar la copia ya instalada en mpmissions:').replace('@DayZ_Baltic_EV112_LatticeForestV1','@DayZ_Baltic_EV112_RuntimeMarginsV2').replace('bf2627eb7abe95652eb215b27694983252c11d019e147635795b8d4cf114246e',dep['world_sha256'])
doc+='\nMisión: '+installed['personal_mission']+'\n\nLos 16 archivos están instalados y verificados por hash. Ruta: `route.json`; solicitud pública: `launch-request.json`. Lanzar cuando Guillermo esté delante. Comprobar session_status, lanzar dayz_test_run sin lease previo, adoptar con session_acquire_wait y mantener heartbeat. Cierre ordenado al terminar. Cliente no lanzado.\n'
(O/'personal-view-runtime-b/README.md').write_text(doc,encoding='utf-8')
print('Minor documentation completed in UTF-8; original encoding failure retained.')
