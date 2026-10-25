from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).parent;W=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=O/'review-runtime-b-r2.json';r=json.loads(raw.read_text(encoding='utf-8'));assert not r['is_error'] and 'SOUND-with-fixes' in r['result']
assert sha(W/'tools/terrain/apply_engine_water_margins_v31.py')=='e024c5edea15248c7fffcc3b7555e5107b0b0ac299c1f5f048aaddf784e20743'
response=dict(verdict='SOUND-with-fixes',critical_major_open=0,raw_review_sha256=sha(raw),responses={
 'F1_source_commit':'Already committed while R2 was reading: eb77548 (producer), f2620a3 (interim HANDOFF). Working producer SHA remains e024c5ed...; close-review verifies the actual committed blob. No package change.',
 'F2_old_derived_field':'Annotated as historical terrain-C metadata in probe-runtime-b/REFERENCE-NOTES.md and water-temporal-runtime-b/REFERENCE-NOTES.md. Fresh ground is B; historical d_terrain_minus_water_m is not consumed. Bound JSON remains unchanged.',
 'F3_derived_counts':'close-runtime-b now exports actual probe/temporal/dam/reference/bridge/shore counts and the EV110/current015-18 comparison. Result writer and live-state writer derive their figures from that closure. Python compilation passed; these outputs will be checked after the real probe.',
 'F4_live_checkpoint':'Both root and worktree LIVE-STATE now state runtimeB deployed, review complete, new probes not run. Backups in review-runtime-b-minor-backups; no historical deletion. Final close will replace only the live/current sections.'},
 limits=['Reviewer executed no tests or hashes; executor freshly verifies bound artifacts.','Four-point margins are measured only under the observed fixed-weather wave interval, not all weather.','The submerged one-vertex depression is roughly1.6m below neighbors within a6m radius, max23.14deg; no visual approval.','All inherited015-45, concrete-joint, central-OT4, forest statistical/domain and phase limits remain unchanged.'])
p=O/'review-runtime-b-r2-response.json';assert not p.exists();p.write_text(json.dumps(response,indent=2)+'\n',encoding='utf-8')
(O/'review-runtime-b-minor-resume.json').write_text(json.dumps(dict(initial_attempt='UnicodeEncodeError writing annotation with defaultcp1252 after three helper edits; no package or bound input was mutated',continuation='Explicit UTF-8 prose and read operations; continued from three preserved backups, checked syntax, wrote notes and live checkpoint',status='COMPLETE'),indent=2)+'\n',encoding='utf-8')
for p in (W/'HANDOFF.md',Path('P:/DayZ_Baltic_12km_dev/HANDOFF.md')):
 rawp=p.read_bytes();s=rawp.decode('utf-8');a=s.index('<!-- LIVE-STATE:START -->');b=s.index('<!-- LIVE-STATE:END -->',a);old=s[a:b]
 replacements={'cleanup':'Sonda original8ac2dd30 y temporalbc28e1e4 cerradas ordenadamente; sin run ni lease propios. Paquete B desplegado, ambas sondas nuevas pendientes. Misiones preparadas, cliente no lanzado.','next':'Cierre R2 sin críticos/mayores; lanzar sonda4114 y temporal30x8 del paquete B, capturar antes del cierre ordenado y evaluar con gates originales. Después cerrar documentación y dejar vista preparada.','worktree':'P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c — rama claude/handoff-astra-map-review-6d301c; capa eb77548, generador AE845295f. Checkout raíz no integrado.','git':'Capa correctora eb77548; HANDOFF interino f2620a3. Sin push. Evidencia y cierre en este worktree, cambios ajenos preservados.'}
 newblock='\n'.join(k.split(':',1)[0]+': '+replacements[k.split(':',1)[0]] if k.split(':',1)[0] in replacements else k for k in old.splitlines())+'\n';new=s[:a]+newblock+s[b:];assert len(new)>=.9*len(s)
 backup=O/'review-runtime-b-minor-backups'/('final-interim-root.md' if p.parent==Path('P:/DayZ_Baltic_12km_dev') else 'final-interim-worktree.md');backup.write_bytes(rawp);assert p.read_bytes()==rawp;p.write_text(new,encoding='utf-8')
score=Path('C:/Users/guill/ObsidianVault/AI/20_Knowledge/council-scorecard.md');raws=score.read_bytes();s=raws.decode('utf-8');assert 'EV112 runtime B R2 —20-10-2026' not in s
u=r['usage'];models=', '.join(r['modelUsage'])
entry=f'''\n\n## EV112 runtime B R2 —20-10-2026

Una revisión independiente CLI Claude ({models}), {r['num_turns']} turnos, coste reportado {r['total_cost_usd']}USD. Tokens: {u['input_tokens']} entrada, {u['cache_creation_input_tokens']} creación de caché, {u['cache_read_input_tokens']} lectura de caché, {u['output_tokens']} salida (thinking incluido). Una lane; sin solape entre proveedores medido. F1/F4 comparten familia de trazabilidad, no corroboración independiente. [Revisión y respuesta](<E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/review-runtime-b-r2-response.json>).

| Finding | Severidad | Arbitraje | Verificación |
|---|---|---|---|
| F1 productor sin commit al inicio de revisión | MEN | YA-CUBIERTO | ORQ: productor eb77548 y HANDOFF f2620a3 ya comprometidos durante R2; SHA e024c5ed confirmado. close-review-runtime-b.py verifica blob. |
| F2 d_terrain_minus_water_m histórico junto a ground nuevo | MEN | ACEPTADO | ORQ: prepare-runtime-b-probe.py:17 y points3836 releídos; anotación explícita como C, campo no consumido. |
| F3 cifras del cierre fijadas por texto | MEN | ACEPTADO | ORQ: write-runtime-b-result.py y update-runtime-b-handoff.py releídos; ahora derivan conteos de close-runtime-b.py y comparación real015-18. |
| F4 LIVE-STATE decía no desplegado | MEN | ACEPTADO | ORQ: HANDOFF.md:7 leído frente a deploy-runtime-b.json; checkpoint desplegado/R2/sondas pendientes escrito con backup, sin alterar historia. |
'''
(O/'review-runtime-b-minor-backups/council-scorecard-before.md').write_bytes(raws);assert score.read_bytes()==raws;score.write_text(s+entry,encoding='utf-8')
print('R2 responses and scorecard recorded; no new review round, thresholds or package changes.')
