# B2 nativa — discriminar oclusión y sensibilidad del rayo

Estado: REVISADO_SOUND_WITH_FIXES, adjudicado 28-10-2026. Codex ejecutor/integrador; Fable crítico
independiente mediante delegar. Consumidor: diagnóstico geométrico y próxima
corrección de validadores EV112, P2/P8/P10/P11/P14. No es aceptación del mapa.
R = E:/DayZ-Baltic-Build/shape-repair-20261025.

## Pregunta, alcance y conservación

B2A publicada712ad0a reconstruye5509modelos/2578398instancias y90orígenes
condicionales. Tres RV altos nombran un haya; otros dos devuelven contactos
sin objeto cerca de SurfaceY en vértices donde Geometry tiene caras.
Eso no identifica terreno ni aísla la causa nativa.
Original2658 conserva47FAIL/21inciertos; ni etiquetas ni tolerancias cambian.
No repetir2658/B1/B2A ni podar, mover árboles, editar modelos/terreno/agua.
No tocar dinámicos, cámara ni jugador. Sólo misión en servidor Diag propio.

Conservar los diez centrales349/348,350/311,700/701,723/725,1425/1426 y
sus80desplazamientos float32 ya fijados por B2A. No escoger offsets tras ver
qué pasa. Origen bajo fijo por grupo = low_y de B2A; no recalcularlo con una
altura del terreno que lo aparte de un obstáculo.

Comparar cuatro rayos por punto: RV alto/bajo y Bullet alto/bajo.
Alto = SurfaceY actual+100 y final = SurfaceY actual−10, igual al productor
original. Bajo = B2A.low_y fijo; mismo final. Registrar los vectores realmente
enviados y todos los resultados, incluso misses, null y componentes−1.
Tres rondas completas,270puntos/1080rayos; orden fijo, tiempos por grupo.
Los rayos son sondas, no reparaciones.

La prueba de separación B2A sigue CONDICIONAL. La nueva captura no convierte
dos hipótesis de marco en prueba de exhaustividad. La coincidencia de pose
y contactos tampoco demuestra causalidad ni identidad histórica de vanilla.

## APIs verificadas y mapa servidor/cliente

[EXACT] missions/BalticVisualProbeV1.BalticTrial/init.c:118-139 ejecuta
SurfaceY, RaycastRV alto y RayCastBullet/BUILDING.
[EXACT] P:/scripts/3_Game/global/dayzphysics.c:199 declara RaycastRV con
contactComponent y set<Object>, ObjIntersectGeom, radius0, NEARESTCONTACT.
:211 declara RayCastBullet con hitObject, hitPosition/Normal y hitFraction.
[EXACT] P:/scripts/1_core/proto/enentity.c:274-288 documenta GetTransform
con vector[4], orden aside/up/dir/position; proto external con out vector[].
La declaración no acredita el enlace nativo: marcador BEGIN/OK en su primera
llamada y captura incompleta si no enlaza. No atribuir un error de enlace al mapa.
[EXACT] Object.c:305/503 GetOrientation/GetShapeName; GetPosition y
GetObjectsAtPosition ya ejercitados por B1. Sólo GetTransform es nuevo aquí.
[EXACT] water_query_diag_b1_ev112.py:122-139 documenta formatos numéricos:
vectores seis decimales, escalares seis cifras significativas. Reusar parser
finito/formatos como dependencia, no modificar su consumidor B1.

| Dato | Servidor | Cliente | Transporte |
|---|---|---|---|
| Puntos, rayos, objetos, matrices, tiempos | Sí | No | CSV local → log local |
| Identidad proceso/run/paquetes/cierre | Host y MCP | No | Recibos seleccionados |
No RPC, SyncVars, sesiones humanas ni persistencia de mundo.

## Productor y consumidor

[DESIGN] Misión BalticCollisionB2.BalticTrial, init.c y points.csv nuevos.
CSV canónico regenerable desde B2A.points.json y original2658.90filas únicas,
id/slot/XZ/low_y; comparar cada central y estados originales antes de desplegar.
Esperar10s iniciales y100ms tras precarga de objetos en cada punto.
GetObjectsAtPosition40m sirve para precarga/snapshot, nunca para redefinir
el universo independiente de objetos del censo B2A.

Registrar Q por ronda/id/slot con t0 antes de RH, t1 después de BL y t2
después de matrices; posición, suelo, high/low/end, máscara BUILDING=2,
cantidad de objetos/proxies; cuatro R con identificador fijo RH/RL/BH/BL,
hit/contact/normal/componente/fracción, lista completa de objetos devueltos.
Registrar O por objeto válido/null, shape, GetPosition y cuatro vectores
GetTransform. Dos sets RH/RL y dos Object BH/BL separados, salidas reiniciadas
antes de cada llamada. Arrays reutilizados, llamadas en líneas individuales.
Capturar los cuatro rayos antes de construir texto; O se puede formar dentro
del bucle posterior. H conserva todos los objetos de cada R. BEGIN90;3 / END270.
Fallo de apertura, esquema, contador o enlace => log incompleto/FAIL explícito.

[DESIGN] Consumidor puro collision_native_b2_ev112.py:
- Orden/esquema exactos,90×3,cuatroR porQ,cantidadesO/hits declaradas y EOF.
- Rechazar NaN/Inf, IDs/slots ausentes/duplicados/extra, reloj invertido,
  vectores enviados distintos de CSV y bajo distinto del B2A fijado.
- Validar alto/final contra SurfaceY medido con sólo incertidumbre de formato
  y aritmética float32; no añadir margen físico a tolerancias previas.
- Conservar estados y medidas originales. Informar diferencias de suelo
  contra NPZ (.01m anterior) y todas las comparaciones con Geometry B2A,
  por marco/cara/instancia; no escoger el contacto más cercano al esperado.
- Comparar poses nativas con candidatos WRP por shape y posición/matriz,
  reteniendo ambigüedades y residuales del redondeo a seis decimales. No
  cambiar la geometría ni declarar objetos ausentes por no estar en40m.
- Si falta un candidato esperado, hay objetos/proxies no vinculables,
  cambio de matriz o t1!=t0, marcar confusor; t2 sólo mide la captura O.
  Comparar rondas por identidad/pose, no por índice O (orden no garantizado).
  Mantener
  cualquier resultado bajo como condicional aunque la captura sea íntegra.
- Emitir tabla de los270estímulos, diferencias alto/bajo y central/offset,
  por consumidor y ronda. Etiquetas descriptivas, no veredicto causal.
  No PASS físico por mayoría ni un miss convertido en altura0.
  Un miss conserva salidas crudas, nunca son contacto válido. Set RV vacío
  produce NO_OBJECT_NEAR_SURFACE/OFF_SURFACE respecto a SurfaceY del XZ
  emitido y error de formato; nunca identidad TERRAIN. Conservar delta XZ
  del contacto. Diferencia RV/Bullet tiene confusor de capa/consumidor.
- Resultado físico INCONCLUSIVE_DIAGNOSTIC incluso con contrato completo.
  El binder separado acredita identidad; mocks nunca cuentan como motor.

## Vinculación y lifecycle

[DESIGN] Reutilizar patrón B1 sin modificar archivos B1 consumidos:
binder nuevo, misión/mod/directorio únicos y coordinador nuevo. Vincular
accepted SHA externo, CSV, init, B2A, original, engine y paquetes antes/después.
Los ocho PBOs estáticos B2A son5vanilla instalados +3propios. En -mod hay
los3propios copiados por hash a mod B2 +bridge (4); declarar ambas listas,
sus relaciones y9identidades únicas, sin copiar vanilla a un mod.
Host captura los5vanilla bajo Addons del ejecutable real, con hashes
pre/post iguales exactamente a B2A.report.packages; los3propios también
iguales a B2A y deployment. Falta/extra/cambio => PACKAGE_DRIFT, no diagnóstico.
Archivo en disco no prueba hash de las páginas del proceso.

Identidad de run/PID/creación/mission/config/engine/bridge, ausencia de cliente,
mtime y contenido del log, cierre y release: mismas exigencias verificadas
en water_query_native_b1_ev112.py:59-96, adaptadas al nombre y270filas.
Ninguna credencial/commandline cruda a disco. No ejecutar helper B1 consumido.
Preflight oficial dayz_test_run(preflight=true) fresco, sin lease/reserva ni
sondeo de ocupación; source server.py:5391-5402 confirma ruta sin admisión.
Si preflight.py de la skill sigue con error de parseo, no editarlo por esta tarea.

Después de revisión de misión/consumidor/binder/despliegue: FIFO oficial,
on_busy=queue,takeover=false,server,no_file_patching,no_base_mods,
navmesh_data_server,build=false. Adopción exacta del run devuelto; heartbeat
cada<=20s, readiness<=300s, captura<=180s desde readiness.
finally cierre oficial; fallback stop sólo si close lo pide, release y
session_status terminal. Conservar fallo propio sin tocar procesos ajenos.

## Criterios y presupuesto antes de la ronda1

Plan: una revisión600s. Una implementación; pruebas<=120s/2GiB, lint de
exactamente1misión con0errores. Preparación/identidad de archivos<=120s.
Revisión de código600s; una corrección por contraejemplo ejecutable.
Una captura nativa completa; FIFO<=600s por activación. No repetir un
experimento inconcluso sin discriminador y plan nuevo. Siguen las paradas
de gates-ledger; ante falta de observabilidad, retirar esa afirmación.

Fixtures cerrados: CSV alterado/central movido, fuente incompleta, NaN,
falta/duplicación/extraQ/R/O, hit falso con vector obsoleto, componente−1,
dos hits conservados, RL origen cambiado, RH/final cambiado, reloj invertido,
offsets sin central, originalPASS sustituido, shape/pose no vinculable,
redondeo válido de matriz vs deriva real, diferencias high/low sin causa
automática, rayos de suelo sin objeto, API_GETTRANSFORM incompleta,
otro run/PID/misión/paquete, falta/extraPBOvanilla, sello cambiado,
captura vieja, cierre incompleto y log bajo otro perfil.
Positivo analítico:270grupos íntegros con10centrales y80offsets sin tocar
los FAIL históricos; variaciones altas por árbol no deciden producto.

PASS de integridad sólo con identidad completa y cierre oficial; no equivale
a mapPASS. Link GetTransform sólo confirmado por log nativo completo.
Nueve regresiones, agua independiente, RAM y C1 siguen abiertos.

## Adjudicación de revisión independiente

Fable5.1 CLI,188.828s,entradas intactas,FIN_REVISION; informe privado
R/collision-native-b2-plan-review-20261028/review.md. H1/H2/H4 aceptados.
H3 aceptado con identidad geométrica para deriva, no índice O: el orden de
enumeración no tiene contrato estable. t0/t1 sigue siendo conservador;
cruzar un milisegundo no demuestra movimiento y no anula datos crudos.
Precisiones aceptadas: registrar máscara2; O posterior a rayos; low float32
fijo; ausencia de log por compilación/enlace es infraestructura incompleta.
GetTransform también se invoca en vanilla Object.c:1395/1405/1447; se mantiene
el marcador propio para confirmar su ejecución en este experimento.
No cambia presupuesto, hipótesis ni autorización de producto.
