from pathlib import Path
import hashlib,gzip,json,datetime,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
rel='evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-cost-contact-20261026';E=W/rel
assert not E.exists();E.mkdir(parents=True)
def save(p,name,compress=False):
 p=Path(p);raw=p.read_bytes();out=E/(name+'.gz' if compress else name);out.parent.mkdir(parents=True,exist_ok=True);assert not out.exists();out.write_bytes(gzip.compress(raw,mtime=0) if compress else raw)
folders=[('kit7-collision-baseline-20261026','kit7/baseline'),('kit7-midpoint-review','reviews/kit7-author'),('kit7-midpoint-author-run-20261026','kit7/author-run'),('kit7-midpoint-saved-review-20261026','kit7/saved'),('kit7-midpoint-build-20261026','kit7/build'),('kit7-compiled-contact-20261026','kit7/packed-contact'),('kit7-compiled-review-20261026','reviews/kit7-packed'),('river-kit7-merged-20261026','kit7/water-original-output'),('river-kit7-merged-byteexact-20261026','kit7/water-byteexact'),('nav-c-retry-review','reviews/nav-retry'),('nav-c-retry-postprocess-review','reviews/nav-postprocess'),('nav-c-retry-postprocess-review/after-fixes','reviews/nav-postprocess/after-fixes')]
for folder,dest in folders:
 for p in sorted((R/folder).iterdir()):
  if p.is_file() and p.suffix in ['.json','.md','.js'] and p.stat().st_size:
   save(p,dest+'/'+p.name,p.stat().st_size>500000)
for name in ['author-report.json','packing-report.json','binary-review.json','records.json','compiled-contact-review.json']:
 save(R/'river-kit7-midpoint-a-20261026'/name,'kit7/candidate/'+name,name in ['author-report.json','packing-report.json'])
save(R/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint-report.json','kit7/water-byteexact/footprint-report.json')
for name in ['human-confirmation.json','launch-inputs.json','host-identity.json']:
 save(R/'nav-c-retry-human-close-20261026'/name,'navigation-active/'+name)
sources=['measure_kit7_collision_baseline.py','author_kit7_midpoint_collision.py','test_kit7_author_guards.py','accept_kit7_midpoint_review.py','run_kit7_midpoint_author.py','review_kit7_midpoint_saved.py','run_kit7_midpoint_build.py','verify_kit7_compiled_contact.py','run_kit7_compiled_contact.py','close_kit7_compiled_review.py','validate_kit7_pond_footprint.py','diagnose_kit7_terrain_container.py','preserve_kit7_merge_bytes.py','orchestrate_nav_c_retry_v3.js','test_nav_c_retry_command.cjs','test_nav_c_retry_coordinator.cjs','package_and_deploy_c_nav9_retry.py','orchestrate_c45_retry.js','finish_c45_retry_probe.py','verify_c_orderly_close.py','test_c_orderly_close.py','test_c45_retry_flow.cjs','test_c45_retry_command_final.cjs','accept_c_retry_postprocess.py','parse_mcp_safe_c_retry.js','checkpoint_kit7_cost_contact.py']
for name in sources:save(R/name,'source/'+name);save(R/name,'executed-source/'+name,True)
progress=(R/'navmesh-c-retry-v9-20261026/generator.stderr.log').read_text(errors='replace').splitlines()[-2:]
snapshot=dict(status='GENERATION_ACTIVE_NOT_ACCEPTED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),run_id='e02b1334-4098-4a95-b92d-4346ceff73e9',server_pid=34564,progress=progress,client_started=False,limits='Point-in-time snapshot. This checkpoint does not contain a complete C navmesh or runtime C45 result.')
(E/'navigation-active/snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
body='''# Kit-7: coste, contacto y charcas — 26-10-2026

**Candidato aislado aceptado offline; integración en WRP, bosque y motor pendientes.** La generación C/F está activa en el instante del snapshot; no se declara navegación PASS.

Los139modelos del cauce continuo de1,66km pasan lectura MLOD, compilación ODOL y contacto global sobre el PBO. Se conservan los otros3LOD byteexactos en fuente y se derivan las poses desde el centro realmente compilado. Ninguna pose heredada de otro río.

| Medida releída | Original | Candidato |
|---|---:|---:|
| Componentes |127528|8623|
| Caras |1020224|263552|
| Vértices |765168|149022|
| Máximo individual vértices/caras |6/8|70/136|
| Bytes P3D fuente |1826042263|114200506|

Los máximos individuales aumentan y permanecen dentro de72/140, techo fijado desde C antes de autoría. Los totales y cada modelo reducen/no aumentan coste. No equivalencia de rendimiento ni FPS.

Overlay completo de127528triángulos de lecho y115055de cubierta; cero área perdida/excesiva, certificado inferior cubierto y error superior máximo0,014370m dentro de±0,02m. Cierre/convexidad y selección completa de8623componentes. Los negativos sobre las dos primeras piezas consecutivas rechazan elevar5cm y retirar media superficie. La mínima diferencia entre pares solapados no es la envolvente de contacto: se conserva el certificado de unión inferior.

PBO aislado1f27e9d3ed05036fd359b49c9fa30a5665c8056cc1f85585b63ff278852d7a8e. Fuente/entradas/manifiestos/informe final fijados por hash tras revisión Fable y cierre de sus hallazgos. La clasificación del LOD respeta precisiónfloat32; no compara con el decimal1e13 exacto.

La nueva huella de charcas conserva plane,field,visible exactos aF;36celdas inactivas retiradas de envolvente, cover intacto. Bury no modifica vértices ni expone bordes nuevos. Su primera salida falló byteparidad porque np.savez guardó sin compresión: todos los NPY eran idénticos. Se conserva esa salida FAIL y se prepara otra carpeta con el NPZ original exacto, sin recalcular ni cambiar el terreno.

Navegación: el usuario confirmó cerrar una ventana en la interrupción C anterior. Es consistente con la evidencia; no prueba al iniciador nativo ni explica la antigua salida F. Un nuevo intento C, mismos PBO/WRP/motor, está activo con observador y lease. Se corrigieron comandos largos y el lease inicial C45.23controles de cierre,5flujos,8casos de comandos y fallo real demorado pasan; Fable SOUND.0/-1solo se admiten con todas las pruebas independientes de cierre ordenado; la salida anterior sigue rechazada por prematura. C45 preparado conserva45consultas/8rutasF, sin cobertura de25piezasC ni actores.

No se ejecutó el cliente ni se cambiaron paquetes desplegados. Los230tests del checkpoint anterior siguen siendo evidencia de esas fuentes sin cambios, no una nueva corrida. EV112 global continúa abierto:268picos,1144depresiones,4transiciones censadas, otros ríos y01545/60m pendiente. Próximo: completar navegación C; integrar kit7/árboles y probar su propio WRP, agua, física, navegación y vista.
'''
(E/'README.md').write_text(body,encoding='utf-8')
manifest={str(p.relative_to(E)).replace('\\','/'):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
p=W/'README.md';s=p.read_text(encoding='utf-8');start=s.index('Nuevo candidato **kit-7:');end=s.index('\nEl mapeado urbano',start)
s=s[:start]+'''El candidato **kit-7: 1,66 km de cauce continuo** pasa coste y contacto completo
en fuente y PBO: **127.528 → 8.623 componentes**, con la geometría de charcas
anterior intacta. Sigue aislado; faltan integración de bosque/WRP y pruebas
propias en el motor. La nueva generación de navegación C/F está en curso.
[Pruebas, costes y límites](evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-cost-contact-20261026/README.md).
''' +s[end:];p.write_text(s,encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8')
updates={'updated':'2026-10-26 (kit7 coste/contactoPBO/charcasPASSoffline; navegaciónC activa, sincliente)', 'plan':'Unidad kit7-cost-contact-20261026; plans/ev112-kit7-collision-budget-20261026.md y ev112-kit7-water-integration-20261026.md. Navegación por ev112-c-navmesh-human-close-retry-20261026.md.', 'blocker':'Kit7 ya reduce127528→8623componentes y pasa contacto completoPBO; falta bosque/WRP/motor. Cnav previo cerrado por usuario según declaración consistente; nuevo run e02b1334 activo. Fnav antiguo63% sigue causa desconocida.38/48/71/79 con conflictos de soporte;98/67 protegidos;01545/60m pendiente.', 'validation':'Kit7:139MLOD+ODOL,otros3LOD fuenteexactos,contactoglobal±.02m/extension.01mPASS,negativos5cm/mediazonaPASS,8623componentes cerradosconvexos,caps70/136≤72/140. Pond plane/field/visibleexactosF,0burycambios. Fuente y PBO aislados; no integración.230tests anteriores sin cambio de core; nuevos23cierre+5flujos+8comandos y negativo real demoradoPASS.', 'cleanup':'Nueva generaciónC e02b1334-4098-4a95-b92d-4346ceff73e9 ACTIVA con servidorPID34564, lease coordinado y sincliente. Función116 supervisa generador86786 y observador12082. No lanzarotraDayZ ni cambiarPBO durante generación. Estado vivo externo ACTIVE-WORK.md.', 'next':'Completar generaciónC actual y validar NM/paquete/C45(45consultas,8rutasF). Kit7 aceptadooffline: river-kit7-midpoint-a-20261026 y river-kit7-merged-byteexact-20261026; integrar bosque/registros/WRP y comprobar enmotor. No afirmar kit7jugable ni rendimientoF/C. Conservar T±.75/radio24m solo relieve.', 'handoff':rel+'/README.md; sesión C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-26-dayz-baltic-kit7-cost-contact.md.'}
for key,value in updates.items():s,n=re.subn('^'+re.escape(key)+':.*$',key+': '+value,s,count=1,flags=re.M);assert n==1,key
p.write_text(s,encoding='utf-8')
p=W/'bugs.md';s=p.read_text(encoding='utf-8');start=s.index('**26-10 kit7:**');end=s.index('**25-10 C:**',start)
s=s[:start]+'**26-10 kit7:**139modelos/1,66km continuos pasan MLOD+ODOL/contactoglobal±.02m;127528→8623componentes,caps70/136. CharcasexactasF,0burycambios. Sin integraciónbosque/WRP/motor ni vista; no cerrado. [Evidencia]('+rel+'/README.md). '+s[end:];p.write_text(s,encoding='utf-8')
note=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-26-dayz-baltic-kit7-cost-contact.md');assert not note.exists();note.write_text(body+'\nWorkspace: '+str(W)+'\nEvidence: '+str(E)+'\nLive work: '+str(R/'ACTIVE-WORK.md')+'\nCommit/publication receipt follows in R/kit7-cost-contact-local-commit.json and publication-kit7-cost-contact-receipt.json.\n',encoding='utf-8')
print(json.dumps(dict(files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()),evidence=str(E))))
