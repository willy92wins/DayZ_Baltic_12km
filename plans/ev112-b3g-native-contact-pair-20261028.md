# B3G â€” contraste nativo de los prismas, antes de ampliar la reparaciÃ³n

Estado: REVISADO_PARA_IMPLEMENTAR. Run condicionado a cÃ³digo/suite/identidad.
Codex ejecutor/integrador; Fable5.1 nativo84.422s adjudicado29-10. Traza P2/P8/P9/P11.

## HipÃ³tesis e intervenciÃ³n aislada

B3F produjo PBO362ef4c201a572087120cc987de14ad03dc650824c5a565a776fef74ce41ae4a;
proofe62ed4709f9e5815740479aa60f16a2f4d4e003e9a070b4dd4886d0d95101a95;
manifestd34b3ecd5c4cccc239a3b86bbfd763e181dc22731b0b7eb86a34375df84572df.
Conserva los200modelos restantes/config201/orden; target2581a99f cambia sÃ³lo
Geometry segÃºn proofB3E2. NingÃºn resultado nativo se hereda de esta identidad.

[HIPÃ“TESIS] El interior estricto de los prismas compilados puede cambiar el
contacto RV en los originales700 y723. La captura B2 es histÃ³rica, inconclusa;
no basta para atribuir una diferencia futura a la nueva geometrÃ­a. Se propone
un contraste fresco de dos brazos con intervenciÃ³n Ãºnica PBO de contacto:
control ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84
(target351424ab) y candidato362ef4c2(target2581a99f). Sin recompilar o empaquetar.
No relanzar productor/misiÃ³n/preparadores B2 ni2658: productorB3G, sello y
coordinador nuevos, con consulta de agua simultÃ¡nea y comparaciÃ³n entre brazos.

[EXACT] Contrato B3E2 conserva700=(8256.275390625,8941.8515625),
723=(8262.7578125,8938.232421875), origen de modelo(8262,7,8934).
700dry y723wet permanecen; no moverlos ni escoger nuevos puntos tras resultados.
Reutilizar como datos inmutables los diez centrales y80offsets fijadosB2A,
con3rondas por brazo. No reutilizar PASS histÃ³rico ni ejecutar CLI consumidos.
Antes de implementar hay que localizar/pinear points y low_y originales, WRP,
agua, motor y todos los PBOs efectivos; si drift no explicado, INCONCLUSIVE.

## Instrumento y evidencia

[EXACT] P:/scripts/3_Game/global/dayzphysics.c:199/211 define RaycastRV y
RayCastBullet. missions/BalticVisualProbeV1.BalticTrial/init.c:118-152 ejerce
rayos, agua, SurfaceRoadY3D y tres referencias de mar. Son precedentes leÃ­dos;
volver a fijar scripts del motor real y firmas antes del cÃ³digo nuevo.

[DESIGN] Servidor propio sin cliente. Capturar cuatro rayos alto/bajo RV/Bullet,
vectores reales enviados, hit/miss, objetos completos, poses y tiempos. AÃ±adir
agua/Sea/Pond/Roadway y referencias de mar por grupo, sin recalcular orÃ­genes
bajos para sortear obstÃ¡culos. Toda salida reiniciada; misses no son altura0.
La representaciÃ³n script BUILDING debe registrarse, no exigir ordinal2 ni
certificar semÃ¡ntica por ordinal8. No clasificar objeto vacÃ­o como terreno.

Consumidor nuevo:90Ã—3 grupos por brazo, IDs/offsets/etiquetas y EOF Ã­ntegros,
contratos/CSV/mission/engine/WRP/paquetes/run/cierre ligados; comparar todos los
resultados conservando confusores de vegetaciÃ³n, reloj y marcos. No seleccionar
sÃ³lo el rayo que mejor concuerda. No imputar contactos a caras por cercanÃ­a.
Las diferencias de agua siguen siendo fallos o desconocidos, no se silencian
porque este experimento priorice colisiÃ³n. Los lÃ­mites vigentes se mantienen:
SurfaceY0.01m,Roadway/RV0.03m,agua0.05m,Bullet corregido0.01m,XZ0.01m,
con condiciones y calibraciÃ³n originales; si no son aplicables, INCONCLUSIVE.

Separar integridad de captura, comportamiento por punto y causalidad. Captura
completa no es PASS del mapa. Sin ensayo que aÃ­sle confusores no afirmar causa.
Incluso si700/723mejoran, los47FAIL/21inciertos del original quedan histÃ³ricos;
aceptaciÃ³n de una reparaciÃ³n completa requerirÃ¡ puerta posterior de dominio
completo y regresiones, sin descartar puntos. No prueba actor/CCT ni conducciÃ³n.

## Presupuesto y lifecycle propuestos, por revisar

Una revisiÃ³n de plan180s, cÃ³digo300s; suite120s/2GiB y lint de la misiÃ³n nueva
con contador de archivos>0. PreparaciÃ³n/identidad120s/2GiB. Una pareja de runs
(control y candidato), cada admisiÃ³n FIFO hasta600s por activaciÃ³n, readiness
300s y captura180s desde readiness; sin retries internos. Si el primer brazo
no vincula identidad/captura, no lanzar el segundo. Si cambian archivos entre
brazos, no comparar ni repetir sin nueva hipÃ³tesis/plan.

Verificar primero contrato vivo DayZ MCP y runbook. No sondear ocupaciÃ³n ni
preadquirir lease; dayz_test_run directo en cola, takeoverfalse. Adoptar sÃ³lo
run devuelto, heartbeat<=20s en exclusividad; cierre/release oficiales enfinally
y estado terminal documentado. Sin camera_set ni sesiones ajenas.
Preflight fresco del entorno real antes de futuros runs; el preflight offline
B3F no certifica entorno nativo. La skill gobernada permanece sin modificar.

Salida: comparaciÃ³n condicional por punto y evidencia independiente de ambos
brazos, o INCONCLUSIVE_DIAGNOSTIC. No acepta rÃ­os/picos/puentes/carreteras/RAM.
CarreterasB0 continÃºa en paralelo offline; C1 SIN REVISAR. Council ampliado encola.

## Anclaje y contrato de implementaciÃ³n â€” 29-10, para revisiÃ³n

Consumidor: el integrador ejecuta la comparaciÃ³n de ambos brazos y decide si la
hipÃ³tesis merece extenderse; nunca promueve el resultado a aceptaciÃ³n global.
Descubrimiento `b3g-source-discovery-20261029`:23 archivos/3.550.791.327 bytes
identificados. Motor a500be80, mundo10e09e3f, agua97edcafe, control ef229,
candidato362ef4c2 y cinco paquetes vanilla coinciden con sus recibos. Scripts
instalados ff0ad7ee5297c75da74364569a830bc0223315c0131579a0c11a7875d64cb2e2;
DayZPhysics279ce05c y Game81adad30 coinciden byte a byte con P:/scripts.
El primer lector parÃ³ al exigir el consumidor B2 anterior a su replay; la
continuaciÃ³n sÃ³lo leyÃ³ APIs/puntos pendientes. Replay4255d6c1 documenta2f5db614;
no hay deriva fÃ­sica ni se cambia un recibo anterior. No es preflight nativo.

[EXACT] Definiciones instaladas: DayZPhysics.c:199/211; Game.c:1178,1196-1200.
Contratos de referencia: collision_native_b2_ev112.py:19-110 (90 puntos y wire),
dry_road_native_consumer_ev112.py:27-61 (criterios por canal). Sus CLI y evaluaciÃ³n
geomÃ©trica B2 NO se ejecutan: sus contactos offline pertenecen a otro candidato.
Pueden reutilizarse funciones puras de CSV/parser/sintaxis con hash ligado.
No se comparan nuevas superficies contra caras antiguas como si fueran actuales.

| Dato | Cliente | Servidor | Transporte |
|---|---|---|---|
| CSV90 fijo, rayos, agua, objetos y matrices | no | sÃ­ | archivo del perfil |
| Identidad, paquete, run/cierre | no | sÃ­/host | lifecycle oficial + recibos |
| Juicio y comparaciÃ³n | no | no | consumidor Python offline |

[DESIGN] MisiÃ³n nueva BalticContactB3G.BalticTrial con header BALTIC_CONTACT_B3G;
todos los Q/R/H/O existentes y un registro W despuÃ©s de cada Q, con clave de
round/id/slot. W lleva sea/pond/surface/depth/road, tres pares sea/pond y alturas
de referencia; ademÃ¡s reloj de agua (inicio/fin). No basta un booleano agregado
para aceptar las tres referencias. t0 <= t1 <= water_start <= water_end <= t2;
si cambia reloj, confusor explÃ­cito, no prueba de movimiento. Cada brazo recibe
el mismo CSV/mission; las identidades de arm quedan en manifiestos externos y
run distintos, no se deducen del nombre del archivo. Nuevo parser comprueba W
en posiciÃ³n exacta antes de delegar sÃ³lo Q/R/H/O al parser puro fijado B2.

Juicio: comparar todos los rayos y estados, incluidos MISS. Conservar datos raw
de misses sin usarlos como alturas. Centrales: ground/road/water y RV con los
lÃ­mites/condiciones originales; dos evaluaciones alto/bajo separadas, sin escoger
la favorable. Offsets: diferencias descriptivas; no heredar ground/road/water de
la central como verdad del offset. Ground del offset contra NPZ fijado, no WRP.
Bullet: guardar residuales brutos y normal, pero INCONCLUSIVE hasta calibraciÃ³n
independiente fresca del mismo motor/canal. No reutilizar margen histÃ³rico como
si se hubiera recalibrado; el umbral0.01 se conserva sin declarar aplicabilidad.
Agua sin referente independiente se identifica como comparaciÃ³n al contrato
histÃ³rico del producto; ningÃºn residual coincidente certifica diseÃ±o natural.
Conservar todos los confusores de poses/vegetaciÃ³n, no imputar identidad por
proximidad. Frame-layout de matrices y semÃ¡ntica BUILDING siguen no certificados.

Puertas del producto antes del run: fixture independiente de planos+agua con
270 grupos, corruptos (W ausente/duplicado/desordenado/NaN; CSV/low/label cambiado;
IDs repetidos/EOF extra; miss con payload; reloj invertido; paquetes cruzados;
misma run en dos brazos; cambio de fuente). Fallos de integridad rechazan;
fallos fÃ­sicos se registran, nunca se borran para permitir comparaciÃ³n. Un solo
ensayo de suite y revisiÃ³n por postimagen; fixes con repro pueden comprobarse
en suite final, sin nuevas rondas de opiniÃ³n sobre lo intacto (gates-ledger).

Preflight MCP nuevo despuÃ©s del cÃ³digo aprobado: modo server, build/clean false,
no_base_mods/no_file_patching/navmesh_data_server true, takeover false, misiÃ³n
nueva, paquete propio aislado. Pedir `preflight:true` para validar peticiÃ³n;
admisiÃ³n real posterior `on_busy:queue,wait_for_box_s:600`. Fijar config servidor,
motor/scripts, cuatro PBO mod y cinco vanilla antes/despuÃ©s de cada brazo,
inventario exacto Addons y copia propia con hash; mundo/agua/bridge invariables.
No sobrescribir paquetes compartidos. Inventario/control/candidato ligados a
B3F proof y contrato B3E2 externos; sÃ³lo uno de los dos mods se carga por brazo.
Si hay drift, parar la pareja, no repetir. Hashes de disco no prueban memoria.

## Adjudicación del plan

F1: fuente original2658 íntegra fijada por SHA; comprobar REQUIRED completos
antes de misión/CSV y retener original_expected central íntegro. F2: adaptación
determinista tras validar headerB3G y W exactas; conservar SHA de texto original
y adaptado, no mutar helperHEADER global. F3: agua fuera de t0..t1.
Control primero, candidato segundo; consumidor120s/2GiB por brazo y pareja.
Guardar lista efectiva -mod y RPT de cargas con identidad, sin secretos.
Preflight se usa sólo si su implementación confirma que no adquiere/encola.
RevisiónFable84.422s y adjudicación en b3g-plan-review-20261029.
