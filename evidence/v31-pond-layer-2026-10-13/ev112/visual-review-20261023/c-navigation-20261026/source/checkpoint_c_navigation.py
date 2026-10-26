from pathlib import Path
import json,gzip,hashlib,datetime,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
rel='evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/c-navigation-20261026';E=W/rel
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
I=R/'nav-c-retry-human-close-20261026';G=R/'navmesh-c-retry-v9-20261026';Q=R/'patch-nav-c45'
gen=read(G/'generation.json');result=read(Q/'result.json');coverage=read(Q/'coverage.json');final=read(Q/'final-session-status.json');packed=read(R/'package-midpoint-c-nav-v9/verification.json')
assert gen['returncode']==0 and gen['inputs_unchanged'] and not gen['failure_reasons']
assert read(I/'completion.json')['status']=='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION'
assert packed['status']=='PASS_NAVMESH_PACKED_BYTE_PARITY' and packed['original_entries_unchanged']==6826
assert packed['navmesh_sha256']==gen['navmesh_sha256']==sha(G/'baltic_trial.nm')
assert result['status']=='PASS_LOCAL_CONTINUITY_NAV_PATHS' and len(result['cases'])==45 and all(c['status']=='PASS' for c in result['cases'])
assert coverage['status']=='PASS_F_PATCH_WAYPOINT_COVERAGE' and len(coverage['coverage'])==8 and all(c['covered'] for c in coverage['coverage'].values())
assert result['log_sha256']==coverage['log_sha256']==sha(Q/'runtime.log')
assert final['self']['state']=='none' and not final['box_occupied'] and not final['own_run_present'] and not final['pending_commands'] and not final['cleanup_degraded']
for folder in [I,Q]:
 close=read(folder/'cleanup.json')['close'];assert close['graceful'] and close['run_retired'] and close['stop_method']=='orderly_close'
 assert sha(folder/'server.RPT')==read(folder/'rpt-binding.json')['sha256']
for p,h in read(Q/'deployment.json')['inputs'].items():assert sha(p)==h,p
E.mkdir(parents=True,exist_ok=False)
def save(p,name,compress=False):
 raw=Path(p).read_bytes();out=E/(name+'.gz' if compress else name);out.parent.mkdir(parents=True,exist_ok=True);assert not out.exists();out.write_bytes(gzip.compress(raw,mtime=0) if compress else raw)
for folder,dest in [(I,'generation/run'),(I/'observer','generation/observer'),(G,'generation/output'),(R/'package-midpoint-c-nav-v9','package'),(Q,'native45'),(R/'kit7-forest-impact-20261026','next-kit7/forest-discovery')]:
 for p in sorted(folder.iterdir()):
  if p.is_file() and p.suffix in ['.json','.jsonl','.log'] and p.stat().st_size:
   if p.suffix=='.log' and p.name not in ['runtime.log','generator.stdout.log','generator.stderr.log','consumer.stdout.log','consumer.stderr.log','coverage.stdout.log','coverage.stderr.log']:continue
   save(p,dest+'/'+p.name,p.stat().st_size>250000 or p.name=='generator.stderr.log')
for name in ['init.c','queries.csv']:save(Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticPatchNavC45.BalticTrial')/name,'native45/mission/'+name)
for folder,dest in [(I,'generation'),(Q,'native45')]:
 lines=(folder/'server.RPT').read_text(errors='replace').splitlines();selected=[dict(line=i+1,text=line) for i,line in enumerate(lines) if '--- Termination successfully completed ---' in line]
 assert len(selected)==1
 (E/dest/'rpt-termination-extract.json').write_text(json.dumps(dict(full_rpt_sha256=sha(folder/'server.RPT'),lines=selected,scope='Only termination marker extracted; full RPT remains local. Not a general no-error claim.'),indent=2)+'\n')
for name in ['discover_kit7_forest_impact.py','checkpoint_c_navigation.py']:save(R/name,'source/'+name);save(R/name,'executed-source/'+name,True)
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
summary=dict(status='PASS_C_NAV9_LOCAL_NATIVE_QUERIES',generation_run=gen['run_id'],probe_run=read(Q/'host-identity.json')['run_id'],generation_seconds=(utc(gen['finished_utc'])-utc(gen['started_utc'])).total_seconds(),navmesh_sha256=gen['navmesh_sha256'],navmesh_bytes=gen['navmesh_bytes'],world_pbo_sha256=packed['pbo_sha256'],wrp_sha256=packed['wrp_sha256'],queries=45,F_patch_routes=8,unchanged_package_entries=6826,client_started=False,server_exit_code_observed=read(I/'observer/terminal.json')['exit_code'],final_session=final,limits=['Native graph queries at frozen references, not actor locomotion or whole-map connectivity.','The45routes do not cover traversal of25Coptimizedmodels.','Kit7 remains isolated and requires its own WRP/native/nav acceptance.'])
(E/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
body='''# Navegación C/F — 26-10-2026

**PASS local en servidor:45consultas y8rutas sobre el parche F.** La malla propia C se generó, inspeccionó, empaquetó y cargó en un proceso nuevo normal, sin DataServer ni cliente. No es prueba de movimiento de actores, de conectividad global ni de tránsito por las25piezas C optimizadas.

La generación duró4260,87s (71min), con el mismo motor, WRP F y piloto C fijados antes de iniciar. NMv9/TESM, tilesv12/VAND,983×983teselas de12,5m;704564848bytes, SHA256`6e35d527914407edfd1fd39eeff8e9ec3249af6646aa6faefddbecc04be56303`. El inspector comprueba invariantes empíricos de cabecera/cobertura; no decodifica la topología completa de polígonos.

El PBO mundo`d091f5e44f4c8c4b9a6f0084379107b2a379b688e72e2d2731e7e126ed22c175` sustituye solo la entrada NM6 por NM9. Otras6826entradas exactas, WRP`0139cd1a7ce360436e474fa6448470dfe93bf34a21229b6cf44f4e839af54126` intacto. Piloto C`c7dc430d809bcec2f29ff1fe86f266f0f9680b8ad676a8722b0b45d4494de02f` y agua`97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43` exactos. Despliegue aislado `P:/Mods/@DayZ_Baltic_EV112_MidpointCNavV9`; anteriores conservados.

Generación run`e02b1334-4098-4a95-b92d-4346ceff73e9`; sonda run`4fce4ae3-839e-4316-8a2f-2821b4dbcca7`. Registro nativo terminaEND;45, consumidor45/45PASS. Las8rutas F contienen waypoints sobre terreno modificado, según comparación E/F congelada. Identidad de motor/PBO/WRP/NM/mission y PID/fecha de creación comprobada; RPT ligado por hash.

Ambos procesos se cierran por `dayz_test_close`, graceful=true, con línea nueva de terminación y retiro confirmado. El observador de generación registra−1 después de la intención propia; es un cierre ordenado comprobado, no fallo inferido solo por el código. La política0/−1 se corrigió y revisó antes de acabar la generación. La corrida antigua interrumpida sigueFAIL; no se reinterpreta retroactivamente comoPASS.

Estado final: selfnone, banco libre, pendientes0 y cleanup[]. Sin cliente. No procesos propios ni lease activos.

Kit-7 sigue como candidato offline aceptado en el checkpoint anterior. Descubrimiento nuevo de bosque:2.560.872registros inspeccionados,292conflictos con margen de lecho,0con agua y1.623posibles ajustesY entre los conservados. No se ha editado el bosque. Plan siguiente: `plans/ev112-kit7-stage-integration-20261026.md`,174registros de kit antiguo a sustituir por139piezas, composición y revisión independientes antes del motor. Las pruebas C/F de este checkpoint no se heredan por ese futuro mundo.
'''
(E/'README.md').write_text(body,encoding='utf-8')
manifest={str(p.relative_to(E)).replace('\\','/'):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
p=W/'README.md';s=p.read_text(encoding='utf-8');old='propias en el motor. La nueva generación de navegación C/F está en curso.';assert old in s;s=s.replace(old,'propias en el motor. **C/F ya pasa 45 consultas de navegación en servidor**,\nincluidas 8 rutas sobre el terreno corregido; movimiento real de IA pendiente.\n[Prueba de navegación y límites]('+rel+'/README.md).');p.write_text(s,encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8')
updates={'updated':'2026-10-26 (CNav9 generada/empaquetada;45consultas+8rutasFPASS; kit7offlinePASS; banco libre)', 'plan':'Unidad c-navigation-20261026 completada. Próxima composición propuesta en plans/ev112-kit7-stage-integration-20261026.md; kit7 coste/contacto/charcas ya aceptadosoffline, sin WRP/motor.', 'blocker':'Kit7 requiere composición/soporte de bosque/WRP/motor/nav propios.292conflictos bosque identificados y1623posibles ajustesY; no edits.38/48/71/79 con conflictos de soporte;98/67 protegidos;01545/60m pendiente. Cnav anterior consistente con cierre humano declarado; Fnav antiguo63% sigue causa desconocida.', 'cleanup':'Generación e02b1334 y sonda4fce4ae3 cerradas ordenadamente por MCP; selfnone/boxfree/pending0/cleanup[]. Sin cliente, procesos propios ni lease activo. Recibos y estado externo ACTIVE-WORK.md.', 'next':'Integrar kit7 aceptadooffline sobreF/C según plans/ev112-kit7-stage-integration-20261026.md: retirar174kitviejos, añadir139piezas,292conflictos de bosque y1623posiblesajustesY; lector independiente, fullforest, WRPcompilado y motor propios. No heredar CNav9 ni rendimientoE. Vista conjunta pendiente.', 'deployed':'CNav9 aislado P:/Mods/@DayZ_Baltic_EV112_MidpointCNavV9: mundod091f5e44f4c8c4b9a6f0084379107b2a379b688e72e2d2731e7e126ed22c175; NM6e35d527914407edfd1fd39eeff8e9ec3249af6646aa6faefddbecc04be56303. WRP F/agua/pilotoC exactos. C previo conNM6 conservado; kit7 no desplegado.', 'visual_probe':'C conserva4749+300físicaPASS; NMpropia CNav9 y45consultas/8rutasF PASS en servidor normal. Ninguna cobertura de actor ni tránsito por25modelosC. Sincliente/vista/CCT/FPS/capacidad. E+Nav9 anterior conservado.', 'handoff':rel+'/README.md; sesión C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-26-dayz-baltic-c-navigation.md.'}
for key,value in updates.items():s,n=re.subn('^'+re.escape(key)+':.*$',key+': '+value,s,count=1,flags=re.M);assert n==1,key
p.write_text(s,encoding='utf-8')
p=W/'bugs.md';s=p.read_text(encoding='utf-8');needle='**26-10 kit7:**';assert needle in s;s=s.replace(needle,'**26-10 navegación C/F:**NM9 propia+45consultas/8rutas localesPASS; sin actores ni aceptación global. [Evidencia]('+rel+'/README.md). '+needle,1);p.write_text(s,encoding='utf-8')
note=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-26-dayz-baltic-c-navigation.md');assert not note.exists();note.write_text(body+'\nEvidence: '+str(E)+'\nPublication receipt: '+str(R/'publication-c-navigation-receipt.json')+'\n',encoding='utf-8')
print(json.dumps(dict(files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()),status=summary['status'])))
