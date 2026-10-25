from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).parent;W=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=O/'review-runtime-b-minor-backups';assert B.is_dir();changes=[]
def edit(p,changeset):
 raw=p.read_bytes();s=raw.decode('utf-8');new=s
 for a,b in changeset:
  assert a in new,(p,a);new=new.replace(a,b)
 q=B/f'{len(changes):02}-{p.name}';q.write_bytes(raw);assert p.read_bytes()==raw;p.write_text(new,encoding='utf-8')
 changes.append(dict(path=str(p),backup=str(q),before=hashlib.sha256(raw).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest()))

for name in ('close-runtime-b.py','write-runtime-b-result.py','update-runtime-b-handoff.py'):
 backup=B/f'{len(changes):02}-{name}';p=O/name
 changes.append(dict(path=str(p),backup=str(backup),before=hashlib.sha256(backup.read_bytes()).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest()))
note='''# Referencias históricas y alturas nuevas

En `probe-runtime-b/points.json`, `probe-runtime-b/shores-points.json` y `water-temporal-runtime-b/points.json`, `d_terrain_minus_water_m` conserva el valor derivado del terreno C al seleccionar los puntos. No representa la separación nueva del terreno B. En el punto global3836, el campo histórico es−0,1439m; el `ground` nuevo es0,446000003m y el nivel0,75m, de modo que su diferencia nueva sería−0,304m redondeada.

`ground` sí se recalculó sobre B. Los IDs, coordenadas y expectativas se conservaron. Los consumidores de aceptación no leen `d_terrain_minus_water_m`; esta anotación aclara la procedencia sin modificar datos fijados por hash, puntos, umbrales ni veredictos. R2 menor2, cerrado por anotación explícita.
'''
(O/'probe-runtime-b/REFERENCE-NOTES.md').write_text(note,encoding='utf-8')
(O/'water-temporal-runtime-b/REFERENCE-NOTES.md').write_text('# Referencias de terreno\n\nEl campo `d_terrain_minus_water_m` es histórico de C; véase [la anotación de procedencia](../probe-runtime-b/REFERENCE-NOTES.md). `ground` corresponde a B.\n',encoding='utf-8')
dep=json.loads((O/'deploy-runtime-b.json').read_text(encoding='utf-8'))
for p in (W/'HANDOFF.md',Path('P:/DayZ_Baltic_12km_dev/HANDOFF.md')):
 raw=p.read_bytes();s=raw.decode('utf-8');a=s.index('<!-- LIVE-STATE:START -->');b=s.index('<!-- LIVE-STATE:END -->',a);block=s[a:b];print('LIVE span',len(block));assert len(block)<20000
 lines=block.splitlines();repl={'updated':datetime.datetime.now().astimezone().isoformat(),'status':'EV112 runtime B desplegado; OT7 R2 SOUND-with-fixes, cero críticos/mayores. Fuente eb77548; menores de trazabilidad en cierre. Nueva sonda4114 y temporal30x8 aún no ejecutadas. Paquete anterior y FAIL original conservados.','blocker':'Sin bloqueo de banco observado. Cerrar menoresR2 y ejecutar las sondas autorizadas;015-45/60m y hormigón siguen pendientes.','deployed':dep['mod']+'; mundo '+dep['world_sha256']+'; agua '+dep['water_sha256']+'. Runtime B pendiente.'}
 newblock='\n'.join(k.split(':',1)[0]+': '+repl[k.split(':',1)[0]] if k.split(':',1)[0] in repl else k for k in lines)+'\n'
 new=s[:a]+newblock+s[b:];assert len(new)>=.9*len(s)
 edit(p,[(s,new)])
(B/'manifest.json').write_text(json.dumps(changes,indent=2)+'\n');print('Four minor responses prepared; no package or acceptance gate changed.')
