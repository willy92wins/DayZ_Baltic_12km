from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).parent;W=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=O/'review-runtime-b-minor-backups';B.mkdir(exist_ok=False);changes=[]
def edit(p,changeset):
 raw=p.read_bytes();s=raw.decode('utf-8');new=s
 for a,b in changeset:
  assert a in new,(p,a);new=new.replace(a,b)
 q=B/f'{len(changes):02}-{p.name}';q.write_bytes(raw);assert p.read_bytes()==raw;p.write_text(new,encoding='utf-8')
 changes.append(dict(path=str(p),backup=str(q),before=hashlib.sha256(raw).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest()))
p=O/'close-runtime-b.py'
anchor="bridge_sites=len(bs['bridges']),shores=bs['shores']"
edit(p,[(anchor,"probe_rows=len(rows),temporal_rows=temporal['rows'],dam_points=dam['points'],dam_rows=dam['rows'],bridge_sites=len(bs['bridges']),bridge_passed=sum(v['pass'] for v in bs['bridges'].values()),bridge_01518=bridge['sites']['015-18'],shore_wet_total=sum(p['family']=='shores' and p['expect']=='wet' for p in points),shore_dry_total=sum(p['family']=='shores' and p['expect']=='dry' for p in points),shores=bs['shores']")])
edit(O/'write-runtime-b-result.py',[
 ("now=datetime.datetime.now().astimezone().isoformat()","now=datetime.datetime.now().astimezone().isoformat()\nbase18=C['bridge_01518']['baseline'];cur18=C['bridge_01518']['current']\nwet18=f\"{base18['wet']}/{base18['under']}→{cur18['wet']}/{cur18['under']}\""),
 ("'| Sonda completa | 4.114 filas válidas, capturadas antes de cerrar el servidor |'","f\"| Sonda completa | {C['probe_rows']} filas válidas, capturadas antes de cerrar el servidor |\""),
 ('PASS; 278 puntos adicionales','PASS; {C[\'kit_unclassified_reference_points\']} puntos adicionales'),
 ("'| Puentes | 10/10 PASS, sin regresión frente a EV110; 015-18 mejora 6/9→9/9 puntos mojados |'","f\"| Puentes | {C['bridge_passed']}/{C['bridge_sites']} PASS, sin regresión frente a EV110; 015-18 {wet18} puntos mojados |\""),
 ("{C['shores']['wet_ok']}/50 mojadas, {C['shores']['dry_ok']}/50 secas; {C['shores']['islet_pairs_ok']}/10","{C['shores']['wet_ok']}/{C['shore_wet_total']} mojadas, {C['shores']['dry_ok']}/{C['shore_dry_total']} secas; {C['shores']['islet_pairs_ok']}/{C['shores']['islet_points']}"),
 ("'| Presa | 178 puntos; consumidor independiente PASS |'","f\"| Presa | {C['dam_rows']}/{C['dam_points']} puntos; consumidor independiente PASS |\"")])
edit(O/'update-runtime-b-handoff.py',[
 ("summary=f\"", "br=f\"{C['bridge_passed']}/{C['bridge_sites']}\";sh=f\"{C['shores']['wet_ok']+C['shores']['dry_ok']}/{C['shores']['n']}\";kp=C['kit_required']['passed'];kt=C['kit_required']['total'];pc=C['concrete_pending_count'];refs=C['kit_unclassified_reference_points'];pr=C['probe_rows'];tr=C['temporal_rows']\nb18=C['bridge_01518']['baseline'];n18=C['bridge_01518']['current'];w18=f\"{b18['wet']}/{b18['under']}→{n18['wet']}/{n18['under']}\"\nsummary=f\""),
 ('completada (4.114 puntos). Puentes 10/10, orillas 100/100, presa y 2.450 controles','completada ({pr} puntos). Puentes {br}, orillas {sh}, presa y {kp} controles'),
 ("assert 'Correccion fisica aislada de4vertices en validacion' in old", "assert ('Correccion fisica aislada de4vertices en validacion' in old or 'EV112 runtime B desplegado; OT7 R2' in old)"),
 ("'Kit v9 en49/51sitios; 2.450 controles obligatorios del kit y100/100orillas PASS en servidor.271juntas/labios", "f'Kit v9 en49/51sitios; {kp}/{kt} controles obligatorios del kit y{sh}orillas PASS en servidor.{pc}juntas/labios"),
 ("'Puentes v6:10/10 PASS en servidor, sin regresión frente aEV110;015-18 mejora6/9→9/9mojados.", "f'Puentes v6:{br} PASS en servidor, sin regresión frente aEV110;015-18 {w18}mojados."),
 ('Sonda4114 y temporal240;10puentes/100orillas/presa/2450controleskit PASS. G8estricto conserva271juntas','Sonda{pr} y temporal{tr};{br}puentes/{sh}orillas/presa/{kp}controleskit PASS. G8estricto conserva{pc}juntas'),
 ('| Servidor |4114filas;10/10puentes,100/100orillas, presa y2450/2450controles','| Servidor |{pr}filas;{br}puentes,{sh}orillas, presa y{kp}/{kt}controles'),
 ('FAIL por271labios/juntas','FAIL por{pc}labios/juntas'),
 ('relajado.278puntos del kit','relajado.{refs}puntos del kit'),
 ('| Temporal |240filas;30muestras','| Temporal |{tr}filas;30muestras'),
 ('servidor4114 y temporal240 capturados.2450controleskit/100orillas/10puentes/presa PASS; G8estricto FAIL solo271juntas','servidor{pr} y temporal{tr} capturados.{kp}controleskit/{sh}orillas/{br}puentes/presa PASS; G8estricto FAIL solo{pc}juntas')])
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
