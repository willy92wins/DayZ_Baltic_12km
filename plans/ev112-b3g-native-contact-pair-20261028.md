# B3G — contraste nativo de los prismas, antes de ampliar la reparación

Estado: BORRADOR_PENDIENTE_DE_REVISION. No autoriza misión, despliegue o run.
Codex ejecutor/integrador; revisión independiente pendiente. Traza P2/P8/P9/P11.

## Hipótesis e intervención aislada

B3F produjo PBO362ef4c201a572087120cc987de14ad03dc650824c5a565a776fef74ce41ae4a;
proofe62ed4709f9e5815740479aa60f16a2f4d4e003e9a070b4dd4886d0d95101a95;
manifestd34b3ecd5c4cccc239a3b86bbfd763e181dc22731b0b7eb86a34375df84572df.
Conserva los200modelos restantes/config201/orden; target2581a99f cambia sólo
Geometry según proofB3E2. Ningún resultado nativo se hereda de esta identidad.

[HIPÓTESIS] El interior estricto de los prismas compilados puede cambiar el
contacto RV en los originales700 y723. La captura B2 es histórica, inconclusa;
no basta para atribuir una diferencia futura a la nueva geometría. Se propone
un contraste fresco de dos brazos con intervención única PBO de contacto:
control ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84
(target351424ab) y candidato362ef4c2(target2581a99f). Sin recompilar o empaquetar.
No relanzar productor/misión/preparadores B2 ni2658: productorB3G, sello y
coordinador nuevos, con consulta de agua simultánea y comparación entre brazos.

[EXACT] Contrato B3E2 conserva700=(8256.275390625,8941.8515625),
723=(8262.7578125,8938.232421875), origen de modelo(8262,7,8934).
700dry y723wet permanecen; no moverlos ni escoger nuevos puntos tras resultados.
Reutilizar como datos inmutables los diez centrales y80offsets fijadosB2A,
con3rondas por brazo. No reutilizar PASS histórico ni ejecutar CLI consumidos.
Antes de implementar hay que localizar/pinear points y low_y originales, WRP,
agua, motor y todos los PBOs efectivos; si drift no explicado, INCONCLUSIVE.

## Instrumento y evidencia

[EXACT] P:/scripts/3_Game/global/dayzphysics.c:199/211 define RaycastRV y
RayCastBullet. missions/BalticVisualProbeV1.BalticTrial/init.c:118-152 ejerce
rayos, agua, SurfaceRoadY3D y tres referencias de mar. Son precedentes leídos;
volver a fijar scripts del motor real y firmas antes del código nuevo.

[DESIGN] Servidor propio sin cliente. Capturar cuatro rayos alto/bajo RV/Bullet,
vectores reales enviados, hit/miss, objetos completos, poses y tiempos. Añadir
agua/Sea/Pond/Roadway y referencias de mar por grupo, sin recalcular orígenes
bajos para sortear obstáculos. Toda salida reiniciada; misses no son altura0.
La representación script BUILDING debe registrarse, no exigir ordinal2 ni
certificar semántica por ordinal8. No clasificar objeto vacío como terreno.

Consumidor nuevo:90×3 grupos por brazo, IDs/offsets/etiquetas y EOF íntegros,
contratos/CSV/mission/engine/WRP/paquetes/run/cierre ligados; comparar todos los
resultados conservando confusores de vegetación, reloj y marcos. No seleccionar
sólo el rayo que mejor concuerda. No imputar contactos a caras por cercanía.
Las diferencias de agua siguen siendo fallos o desconocidos, no se silencian
porque este experimento priorice colisión. Los límites vigentes se mantienen:
SurfaceY0.01m,Roadway/RV0.03m,agua0.05m,Bullet corregido0.01m,XZ0.01m,
con condiciones y calibración originales; si no son aplicables, INCONCLUSIVE.

Separar integridad de captura, comportamiento por punto y causalidad. Captura
completa no es PASS del mapa. Sin ensayo que aísle confusores no afirmar causa.
Incluso si700/723mejoran, los47FAIL/21inciertos del original quedan históricos;
aceptación de una reparación completa requerirá puerta posterior de dominio
completo y regresiones, sin descartar puntos. No prueba actor/CCT ni conducción.

## Presupuesto y lifecycle propuestos, por revisar

Una revisión de plan180s, código300s; suite120s/2GiB y lint de la misión nueva
con contador de archivos>0. Preparación/identidad120s/2GiB. Una pareja de runs
(control y candidato), cada admisión FIFO hasta600s por activación, readiness
300s y captura180s desde readiness; sin retries internos. Si el primer brazo
no vincula identidad/captura, no lanzar el segundo. Si cambian archivos entre
brazos, no comparar ni repetir sin nueva hipótesis/plan.

Verificar primero contrato vivo DayZ MCP y runbook. No sondear ocupación ni
preadquirir lease; dayz_test_run directo en cola, takeoverfalse. Adoptar sólo
run devuelto, heartbeat<=20s en exclusividad; cierre/release oficiales enfinally
y estado terminal documentado. Sin camera_set ni sesiones ajenas.
Preflight fresco del entorno real antes de futuros runs; el preflight offline
B3F no certifica entorno nativo. La skill gobernada permanece sin modificar.

Salida: comparación condicional por punto y evidencia independiente de ambos
brazos, o INCONCLUSIVE_DIAGNOSTIC. No acepta ríos/picos/puentes/carreteras/RAM.
CarreterasB0 continúa en paralelo offline; C1 SIN REVISAR. Council ampliado encola.
