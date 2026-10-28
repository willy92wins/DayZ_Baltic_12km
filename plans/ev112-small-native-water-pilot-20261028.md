# Piloto incremental para aguas nativas pequeñas
Estado: EJECUTADO_RECHAZADO_OFFLINE. Consumidor: ejecutor Codex; revisión Fable.
Fecha28-10-2026. Deriva de P2/P8/P12/P14 y RELIEF-EAST-VIS-01; el censo
publicado d71b3cf es entrada, no aceptación visual del mapa.

## Problema y descubrimiento
La charca oriental candidata769 tiene19 giros>=45° en el screen abierto y
queda fuera del censo de aguas anchas: fracciónwide0 con la fuente actual.
La L de Narva292 es un control protegido:18vértices incidentes narva.
El CLI shore_ramp_v31 rechaza terrenos con v31_shore_ramp; no se borra esa
marca ni se reutiliza el CLI. Capa incremental nueva, con inputs inmutables.
Se desconoce todavía qué capa histórica originó cada forma; el discriminador
prueba elegibilidad actual, no esa causalidad histórica.

## Hipótesis y alcance
[DESIGN] Una curva periódica ajustada al contorno completo de un cuerpo nativo
cerrado, seguida de una rampa local, puede quitar codos sin eliminar el agua
ni su islote. Se ensaya una vez sobre769; la selección futura parte del censo
global, nunca de parches por coordenadas. Si falla, no se extiende ni se integra.
No toca MLOD, carreteras, bosque ni ejecutables. Todo resultado es offline.

Entradas: terrain-buried.npz815ef8b7, footprint084171b0 y native-shore.npz
b6612009 en E:/DayZ-Baltic-Build/shape-repair-20261025, según inputs del censo.
El programa recibe cadena/artefactos como argumentos; valida hashes, cierre,
que el cuerpo no tenga charca superpuesta, identidad de contorno y vecindad.
Otras cadenas, islotes, platform/reserve/narva, v31_kit, puentes, presa,
lagoon, causeway, shore_ramp y reparaciones de carretera permanecen exactas.
Añadir sólo v31_small_water_pilot; todas las máscaras previas bitexactas.

## Algoritmo de un candidato
[EXACT] shore_ramp_v31.py:538 smooth_pinned(p,pinned,closed,sigma) resuelve
una spline regularizada; :279 arclen y :283 resample trabajan en metros.
Se reutiliza sólo ese ajuste explícito, no run_stretch ni su filtro narrow.
[DESIGN] Remuestrear contorno a1m, cerrado; sigma12m es el valor original del
CLI, no un barrido. Exigir polígono objetivo válido/simple. No círculo ideal,
ruido aleatorio ni cambio de XZ de objetos.
Sólo se admite cuerpo de mar: todos seg.pond=false/seg.lev=.75 y ninguna
charca superpuesta dentro del dominio. Otro nivel/campo = INCONCLUSO_DOMINIO;
no se aplica este autor a charcas elevadas. Calcular distancia firmada al
polígono, negativa dentro. La pendiente de rampa
se obtiene de la mediana |H-.75|/distancia a la orilla original en el anillo
0<distancia<=9m, limitada al intervalo existente S_MIN=.05/S_MAX=.35.
Generar Hobjetivo=.75+s*distancia; mezcla completa hasta9m y suave hasta15m
(B0/B1 existentes). Fuera del collar15m de la orilla OBJETIVO, H bitexacta.
Medir desplazamiento objetivo-original primero: si supera9m, INCONCLUSO_DOMINIO.
Congelar todos los vértices
incidentes a otras cadenas y sus vecinos nativos, y todas las protecciones,
incluidas las alturas v31_shore_ramp y v31_despike. Excluir además todo vértice
más cercano a cualquier otra orilla que al objetivo. Aplicar el lado B-estricto
del autor anterior a los vecinos libres de protegidos y comprobarlo en float32.
La mediana es un estimador nuevo, no el ajuste LS del autor; se registra como tal.
Cuantizar a float32 ANTES de medir. No ajustar pesos tras ver el resultado.

Descubrimiento de dominio completado: ningún modelo de agua intersecta el
collar; el rectángulo conservador contiene5celdas pond pero ninguna está a
15m o menos del polígono objetivo. La comprobación exacta usa distancia entre
el cuadrado completo de cada celda y el polígono relleno, sin aproximar buffers.
Una celda de envolvente potencial está a14.998894m: congelar TODAS las esquinas
de la envolvente, no sólo las del footprint visible. También se conservan las
alturas de continuous_pilot y shape_repair. Los60m de cruces se protegen con
todo el inventario (conservador); el piloto no modifica ni diseña cruces.
La referencia MLOD incorpora el bounding centre del compilador antes de usar
poses WRP; la igualdad de pose se comprueba exactamente en float32. Son pruebas
de dominio de fuente; no se convierten en aceptación de binarios ni del motor.

## Guardas y aceptación mecánica
Preparar antes de autoría el área exacta, todos los datos/modelos de agua
presentes y el mapa de protecciones. Si no puede aislarse una charca nativa,
INCONCLUSO; no asumir que un contorno cerrado significa agua aislada.
El polígono objetivo debe contener el islote, pero éste se conserva por altura
y topología de salida, no sólo por el dibujo del objetivo.

Para OFFLINE_CANDIDATE_PASS deben pasar TODAS:
- cambio no nulo y exactamente dentro del área permitida; máscaras/demás arrays
  y todo terreno externo bitexactos. Agua superpuesta y sus esquinas exactas.
- correspondencia biyectiva de componentes mojados Y secos en el grafo nativo
  E/S/NO-SE antes/después, sin creación, desaparición, unión o división;
  no basta igualdad de contadores. Islote772 y otras orillas exactas.
- pendiente: ninguna cara nueva supera35° ni empeora >.01° si ya los superaba
  (mismos SLOPE_MAX/SLOPE_EPS del autor actual); no nuevos extremos/pirámides
  frente a despike_v31.prominence(H): no nuevos picos/depresiones>.30m ni
  aumento de la prominencia donde ya supera.30m (POLICY.native_prominence_m).
  Conservar el relieve fuera de la zona y registrar cambios en cada anillo.
- ningún nuevo hallazgo geométrico fuera del contorno piloto. En el contorno
  final completo, incluidos giros de cierre: cero giros>=45° y rectas>=60m
  usando la simplificación.25m de POLICY; esos umbrales no cambian.
- wiggle p90 final <=max(.08m,.5*p90 inicial), mismos WIG_ABS/WIG_REL de
  shore_ramp_v31, con cobertura completa y sin contar NaN como cero.
- reconstrucción nativa final por el consumidor independiente de107641segmentos
  (número nuevo libre, universo completo obligatorio), no sólo la spline objetivo.

Negativos mínimos: máscara vulnerada, islote hundido, cuerpo añadido/borrado,
unión/división con número igual, candidato igual al original, giro malo justo
en el cierre y contorno vacío; todos deben fallar por su causa. Analítica
positiva y topología diagonal justifican la conectividad del consumidor.
Se conservan607PASS como resultado del build anterior; no se transfieren al
candidato. Aun con PASS offline quedan reproyección de objetos/bosque, fuente
WRP, compilación, sonda, RAM y vista antes de integración/aceptación.

## Presupuesto y parada
Una revisión de plan y una de código, una corrección por repro concreto. Una
generación de candidato (sigma12, sin barrido), hasta120s/1GiB; evaluación
completa hasta300s/2GiB. Validación de fixtures antes del mapa. Si FAIL, guardar
delta y razones, no integrar ni repetir con otros parámetros: siguiente paso
debe cambiar hipótesis apoyándose en el fallo. Si límite de recursos/dominio
no verificable, INCONCLUSO. No relajar protección ni tolerancias para lograr PASS.
La L de Narva no se edita: exige primero distinguir el apoyo real de la presa
del terreno residual mediante geometría y contrato independientes.

## Adjudicación de revisión
Fable5.1 nativo28-10,168.6s, SOUND-with-fixes; fuentes inmutables. Se incorporan
los cuatro fixes: verificar nivel mar, excluir influencia de orillas intactas,
collar referido al objetivo y alturas anteriores protegidas. Los pins de curva
son intersecciones de aristas con ambos extremos protegidos; se reporta fracción
y se conserva FIXED_FRAC_MAX=.20. La propuesta de repetir dos puntos para el
giro de cierre no hace DP independiente del punto de arranque: el consumidor
de este piloto examinará todas las rotaciones del anillo nativo, con tolerancia
.25m y giros cíclicos, para impedir que el inicio oculte el defecto. Un anillo
degenerado se rechaza. No se inventa un PASS para regularidad circular.

## Resultado del único candidato
Código revisado Fable SOUND-with-fixes; corregido orden de protección de otras
orillas antes de calcular pins.20fixtures PASS. La curva original de preflight
se reconstruye exactamente, con13pins; no hubo ajuste de parámetros.
108alturas cambiadas, máximo2.455744m. Topología81componentes húmedos/28secos
con biyección;107547segmentos de otras orillas exactos. Pendientes sin regresión.
RECHAZADO:3vértices con regresión de pico y6de depresión;10giros>=45° en la
orilla final, máximo133.950658°. Wiggle.328899m frente límite.191354m también
incumple. La conservación de alturas no impide empeorar prominencia de vecinos:
dos depresiones nuevas se detectaron en vértices cuyo Y no cambió.
El límite temporal se cumplió, pero la medición RAM del wrapper era del launcher
del venv, no del intérprete: INVALID_MEASUREMENT, no certificar el presupuesto
RAM de esa ejecución. Diagnóstico separado en el intérprete:642326528B de pico
residente,1638989824B de commit; no transferible al autor/consumidor anteriores.
Presupuesto1candidato/1corrección consumido; no relanzar ni barrer sigma.
Evidencia: evidence/small-native-water-pilot-20261028. Siguiente descubrimiento:
plans/ev112-water-constraint-feasibility-20261028.md. No integración ni build.
