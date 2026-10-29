# RoadC0 — aislar la calibración de las tres piezas de carretera

Estado: REVISADO_PARA_AUTORIA_DE_FUENTES_DE_LABORATORIO. Consumidor de esta unidad: futuro build
RoadC1 del laboratorio vial; no es una reparación ni candidato de producción.
Trazabilidad: Q04 del council, P5/P10/P11 y petición humana de preparar carreteras.
Codex planner/orchestrator/integrator; si pasa review, Codex EXECUTOR local
explícitamente asignado para el corte acotado. Review externa nativa; no council.

## Decisión técnica [DESIGN]

Separar un laboratorio de calibración de la recompilación de la escena completa.
Crear dos archivos 0WZD nuevos en una carpeta exclusiva: control sin objetos y
candidato con sólo los tres registros literales de RoadB3. Ambos copian exactamente
el prefijo terreno/materiales y el terminador de la fuente histórica b108.
Los 2.578.398 objetos originales se omiten deliberadamente EN ESTAS COPIAS DE
LABORATORIO; fuente, candidato RoadB3, mapa y paquetes publicados no se modifican.
La ausencia de objetos en el laboratorio no repara ni oculta fallos del mapa.

La compilación posterior resolverá tres modelos y materiales de terreno, no
simulará que doce recursos B4A3 cierran 5.509 modelos. No transfiere el resultado
de laboratorio a precedencia/oclusores/colocación del mapa completo. Las cuatro
hipótesis raw/origin × fila/columna siguen abiertas. Los originales B2/B3 se
reutilizan por hash y no se vuelven a ejecutar.

Alternativa considerada y descartada aquí: insertar objetos directamente en
OPRW compilado. package_visual_forest_ev112.py:29–64 tiene un lector HEURÍSTICO,
ancla baltic_water_v30 y tablas auxiliares no decodificadas; no autoriza un writer
OPRW ni saltar Binarize. El lector tampoco sirve automáticamente al control0.

## Anclas [EXACT, leídas el 29-10]

- evidence/road-b2-recipe-20261029/manifest.json enlaza receta R1 af3ee395 y
  world-faces-private48666b12 a través del contratoB3. No había un contract.json
  en la raíz B2 consultada porQ05A; el contrato NO se declara inexistente.
- B2: tres poses (100,200,300), (200,200,300), (300,200,300); primera identidad,
  otras90grados; 24huellas ya guardadas, no recalcularlas. 0.03m/10ULP y
  separación10.7703296m pertenecen a esa receta, no son aceptación nativa.
- evidence/road-b3-source-pilot-20261029/contract.json (copia pública saneada)
  tiene objetos19394564–566, nombres exactos asf1_25/asf2_25/asf1_10 100.p3d y
  matrix12. Contrato original7454f8b7 debe fijarse desde ruta de export-manifest.
- road-b3-input-discovery/report.json: prefijo terreno/materiales17307629B,
  SHA d16b513978ba9b98c222d0dee4b80e8f519713140394406517c99da3fa0287a5.
  Fuente b108352fc648ba36dbbf1fd5e7def8cb26fd1b226cd22d19a3e6d08c364678ee,
  286261435B. No confundir con prefix_bytes286261379 del contratoB3.
- tools/quality/author_road_object_pilot_ev112.py:159–196 describe prefijo0WZD;
  :199–228 recorre registros de48B matriz+IDu32+longitudu32+nombreASCII, y
  terminador56B con longitud0 alEOF. verify_road_object_pilot_ev112.py:159–225
  lo recorre por cursor. Se leen definiciones, no ejecutar esos CLIs/suites.
- El terminador opaco exacto sigue siendo dato heredado; no se supone que la
  aceptación sintáctica de una escena vacía demuestre que Binarize la acepte.
  Holgura196.427m guardada sólo frente a terreno fuente, no espacio libre motor.

## Corte ejecutable después de review [DESIGN]

Primero congelar contrato y oráculos externos antes de código: pins de recetaB2,
contratoB3 original/export, descubrimiento de prefijo, source_sha/size/prefix y
terminador; lista de tres IDs/nombres y 48bytesfloat32 literales. El contrato
nuevo describe dominio LAB_ONLY,0/3objetos y negaciones de aceptación, y fija
outputs/marker exclusivos. No abrir NPZ/PBO/P3D ni extraer caras.

Autor nuevo pequeño: abrir fuente sólo lectura, comprobar reparse/identidad
path/handle dev/ino/size/mtime, SHA completo por chunks<=1MiB, longitud exacta,
prefijoSHA y terminador heredado; parseo acotado del prefijo para que offset no
sea una cifra arbitraria. No recenso del stream de2.5Mobjetos: su identidad y
censo se heredan explícitamente deB3 pinado. Verificar bits de tres matrices,
nombres/IDs/longitudes antes de escribir. Copiar el mismo prefijo a ambas salidas
y después terminador o tresregistros+terminador. Reserva de salida antes de
escribir, carpeta/marker exclusivos incluso en fallo, archivos incompletos
jamás marcados aceptados. Fuente inmutable comprobada al finalizar; no afirmar
vigilancia continua de cambios revertidos. Preservar cualquier parcial.

Consumidor nuevo separado: no importa autor ni parser del autor. Carga contrato
porSHAexterno y fuente propia; recorre prefijo con cursor, compara cada rango de
ambas salidas contra fuente mediante chunks; decodifica registros con lectura
exacta secuencial. Exige control0, candidato3, nombresraw/IDs/matriz48B exactos,
terminador56B idéntico alEOF, ninguna cola/objeto adicional y conservación del
prefijo completo. Verifica reporte completo y hashes/longitudes, no sólo claims
del productor. El consumidor no prueba otra vez unicidad de los2.5Mobjetos que
no están en estas copias; herencia declarada. Errores I/O, identidad, contrato,
estructura y bug interno separados; no catch general convertido enPASS.

Límites: fuente<=512MiB, prefijo<=32MiB, salida conjunta<=64MiB,3registros,
nombres<=4096BASCII sin traversal, dimensiones/productos dentro del archivo
antes de avanzar, materiales/strings acotados por bytes restantes. Memoria
256MiB por proceso; no cargar286MiB fuente completa. JSON<=1MiB/reporte<=1MiB.
No nuevos helpers genéricos, ni modificar módulos sellados.

## Validación y parada [DESIGN]

Oráculos literales previos: prefijo0WZD pequeño con alturas/materiales, fuentes
con objetos y terminadoropaco, expected control/candidato hex completo; signed
zero en matriz, nombre con espacio. Expectativas no generadas por el autor.
Positivo end-to-end autorCLI→consumerCLI con contratoSHAexterno.
Negativos cerrados: fuenteSHAincorrecto; offsetprefijoincorrecto; alturas/material
truncados; prefijo mutado enuna salida; ID/nombre/matriz/orden mutados; objeto
extra/control no vacío; cola tras terminador; terminador cambiado; duplicadoID;
nombretraversal/noASCII; límite512MiB/64MiB/4096B antes de lectura/asignación;
reparse/identidad cambiada simulados; outputexistente; reporte+hash co-mutados
sin poder engañar comparación contra fuente. No contar skips como pruebas.

Presupuesto antes de ronda1: autor local600s para contrato/oráculos/código;
review180s incluye contrato; suite120s/256MiB; única corrección180s por repro
del conjunto cerrado y una recuperación180s de dictamen no entregado. Una
autoría real60s/256MiB y consumidor60s/256MiB sólo tras gates; sin retries.
Plan una revisión120s, no bucle genérico. Si hipótesis de prefijo/código falla,
preservar y retirar esta unidad; no ampliar caps ni llamarla build listo.
Fuente única de parada: gates-ledger §Cuándo para un bucle.

Resultado: VERIFIED_ISOLATED_SOURCE_PAIR_ONLY o rechazo/inconcluso concreto.
Cero build, PBO, deployment, DayZ, lease, conducción o selección de pivote.
No emitir resultado si ambas salidas y consumidor no están íntegros.

## Después: RoadC1/RoadC2, aún no autorizados por este plan [DESIGN]

RoadC1 necesita preflight fresco, stage privado de recursos de3modelos y
terreno/materiales/bin/core con identidad/precedencia y destino exactos; nada
de enlaces globales DZ incidentales ni tocarP:. Revisar contrato de compilación
control/candidato y consumidor OPRW capaz de0/3objetos antes de ejecutar pareja.
RoadC2 liga modelos/paquetes instalados y transformaciones a testigos separados
de las4hipótesis; sondeo físico con identidad propia y controles de oclusión,
sin cámara_set. Ni un raycast ni ordinalBUILDING demuestran semántica global.
FIFO600s, lease/adopción exacta, heartbeat10s y cierres oficiales en plan propio.

La calibración permite después Q05/Q06/Q07 sobre huella completa y dosaccesos.
El mapa completo seguirá necesitando recursos/oclusores/agua y P9/P11; no
suprimir esos gates por el éxito de laboratorio. Humanos0resueltos,C1NOT_REVIEWED.

## Adjudicación Muse43.281s, previa a código

SOUND-with-fixes/CONVERGE. F1: fijar matrix48_hex y record_bytes, conservando bits;
el contratoB3 real usa números representablesf32 y su evidencia se hereda, no
se inventa un pin de lectura binaria nueva. F2: original localizado mediante
export-manifest en road-b3-source-inputs-20261029/contract.json; fijar ambosSHA
original7454 y saneadofdee más enlace. F3: nombres distintos para prefijo
terreno/materiales y preterminador. F4: igualdad de56bytes exacta en ambos
caminantes, nunca sólo longitudcero. Se integran sin cambiar tolerancias.
La supresión de objetos sólo define laboratorio: no cierra5509recursos ni
aceptación del mapa. Futuro rechazo del control no aislaría causa deBinarize.
Revisión de cápsula; postimagen editorial Codex, sin otra revisión externa.
