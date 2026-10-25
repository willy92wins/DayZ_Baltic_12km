# EV112 — cinco contactos RV corregidos; candidato U2

**Resultado:** U2 supera los 2823 controles congelados y la rejilla de 300 rayos
repetidos/próximos. Los cinco fallos de T desaparecen sin mover muestras ni
cambiar el consumidor, sus tolerancias o la calibración vanilla. Candidato
preparado para revisión personal; EV112 y el mapa completo siguen abiertos.

| Artefacto | Sonda 2823 | Rejilla 300, RV/Bullet con modelo | Caras Geometry, 62 modelos |
|---|---:|---:|---:|
| T | 5 fallos RV | 250/300 RV; 300/300 Bullet | 317708 |
| U1, expansión de cinco modelos | 0 fallos | 300/300 ambos | 367014 (+15,52 %) |
| U2, expansión local | 0 fallos | 300/300 ambos | 318910 (+0,3783 %) |

Motor: DayZDiag 1.30.164200.56, servidor dedicado. Runs y hashes en los
`runtime-identity.json`. Cierre ordenado de todos los runs propios, lease
liberado, sin ticket/órdenes pendientes ni degradación de cleanup.

## Corrección y pruebas

La suma de Minkowski horizontal con un cuadrado de semilado 1/512 m se aplica
a 46 componentes de los cinco modelos afectados. Incluye sus contactos y
extremos X/Z para preservar el centro del bbox. No aumenta el número de
componentes. Coordenadas de componentes no elegidos exactas; sus normales
se regeneran. Otros 57 modelos y LOD visual/Memory/Roadway byte a byte iguales.
Masa de cada componente contrastada después de guardar.

El certificado independiente de la unión superior cubre todo el lecho, dentro
de ±2 cm verticales y 1 cm horizontales. Cierre, orientación, convexidad y
compilación de 62 ODOL pasan; sus 62 matrices coinciden en float32 con el WRP
T existente y las juntas de agua son exactas. Terreno, bosque, agua y carreteras
de T conservados. PBO piloto U2:
`c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87`.
Mundo `06aae98a7763c131d97a55774da01b9af9db575c37216ebc9d13aaf082579bdb`;
agua `97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43`.
Despliegue separado: `P:/Mods/@DayZ_Baltic_EV112_RVOverlapU2`.

**132 tests PASS**, sin errores ni skips. La primera ejecución ampliada falló
por ocho fixtures versionadas ausentes del checkout parcial. Se recuperaron
desde HEAD, sin modificar los tests antiguos, y la suite completa se repitió.
Tests nuevos: expansión/contención analítica, selección de contactos y extremos
independientes, contactos de interior/arista/vértice/exterior, holgura positiva
sub-ULP, separación entre superficie superior e inferior y cara casi vertical.

## Diagnóstico y revisión independiente

T fallaba repetidamente en la coordenada exacta de cinco vértices; las 48
posiciones próximas de cada uno pasaban. También coinciden con vértices 342
controles que pasan: coincidencia no es causa suficiente. El control vanilla
falla RV en 14/24 vértices; sus desplazamientos incluyen exterior de huella y
no demuestran por sí solos un efecto de precisión. Bullet detecta los vértices.

El diagnóstico nuevo opera sobre ODOL y poses float32. En U1/U2 un contacto
tiene holgura de al menos una ULP respecto a arista superior y **cuatro** quedan
por debajo, aunque los cinco pasan el motor. No se conoce el algoritmo interno
de RV ni se ha demostrado un agujero para el jugador. La segunda razón del
FAIL de T, margen Bullet distinto, resulta de comparar Bullet contra el suelo
nativo al faltar la forma RV; se conserva íntegra, sin ocultarla.

Tres revisiones por CLI nativo de Fable 5.1, identidad comprobada, en
`reviews.json`: SOUND-with-fixes. Aplicados: menor coste, diagnóstico de aristas,
comprobación de rotación identidad, guardia de caras casi verticales y nuevos
contraejemplos. El brief de U2 decía tres casos sub-ULP; la evidencia muestra
cuatro, corregido aquí y en el plan. Se conserva el brief original para trazabilidad.
Las guardias finales no alteran el candidato ya construido; el diagnóstico
final es byte a byte idéntico al anterior y las 62 rotaciones se contrastaron.
`source/overlap-u2-used.py` conserva la autoría exacta vinculada al informe.

## Evidencia y límites

`t/`, `u1/`, `u2/`: resultados, geometría guardada/compilada, recibos y logs
completos comprimidos sin pérdida. `probe/`: puntos congelados y misiones.
`source/`: autores y consumidor exactos. `MANIFEST.json`: hashes y tamaños.
Los binarios grandes permanecen fuera de Git, identificados por SHA256.
Para reevaluar, descomprimir `u2/runtime.log.gz` y `t/calibration-fresh.log.gz`
y ejecutar `tools/water/eval_visual_probe_v31.py` con `probe/points.json`, el
log completo y `--collision-reference` apuntando a esa calibración.

No se acepta CCT/caminado, conducción, vista humana, AI o rendimiento. RPT
conserva navmesh v6 incompatible con v9, `cfgenvironment.xml` ausente,
stack de GetPlugin/PluginItemDiagnostic y warnings de clases de modelos;
`rpt-observations.json` los registra. La sonda completa no los convierte en PASS.

Siguen abiertos los demás ríos, relieve protegido (327 grupos de picos,
1156 depresiones y 5 transiciones), 3727 discos de bosque, cruce 015-45/60 m,
navmesh, carreteras físicas y comparación real con Chernarus. Los controles
de P11 heredados de T cubren 77559 secciones/130534 intervalos, sin fallos;
no sustituyen conducción. No ampliar el piloto a todo el mapa sin medir su
coste/contacto. U1 y T se conservan para comparación y rollback.
