# B3F — composición experimental de201 modelos

Estado: BORRADOR_PENDIENTE_DE_REVISION. Codex ejecutor/integrador.
No autoriza ejecución antes de revisión de plan/código y tests. No DayZ ni despliegue.

## Hipótesis, producto y entradas

P2/P8/P9/P11: trasladar el ODOL que ya preserva geometría y controles al mismo
universo de modelos usado por B2, sin rehacer modelos ni mover poses. Sólo
composición de un PBO experimental. B3E2 es COMPILED_B3E_CONDITIONAL, no nativo.

[EXACT] Contrato B3E2 c3709a1929214e1372fb2026b8d84c8ae83466aa83e033da968fa196a598f8e4;
proof9a541c82274a9cad75c337d734db2d3ab62120a5e8694c3502fc09f9dd841884;
candidato ODOL2581a99ff60f5a6242af55483cce6dd1aa3556cbc36e8a2f1c1488fa08c93545,
en R/prism-b3e2-pair-20261028/candidate/saved-odol.p3d.
Baseline R/dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo
ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84:
descubrimiento sólo lectura28-10 acredita202entradas/201P3D, target351424ab y
config.bin57d0d0ae31a33fa329598ce2c17df43fbb8451fd3acc0844467b87fec3a239ca.
Es config201, NO el config de la pareja B3E2 de un modelo. Prefijo
baltic_stream_pilot, product dayz ugc. Reporte R/b3f-package-input-discovery-20261028.

## Diseño acotado

[EXACT] tools/quality/compiled_dry_road_gate_ev112.py:164-171 package_identity
compara propiedades, orden/universo201, entradaúnica modificada y bytes exactos.
tools/playtest/attach_navmesh.py:read_pbo recibe Path. El CLI y compose del viejo
package_dry_road_compiled_ev112.py están consumidos y fijan candidato3514:
NO invocarlos ni cambiar constantes. Se pueden reutilizar primitivas verificadas.

[DESIGN] Preparador/consumidor/tests nuevos y aprobación específica con pins
externos de contrato, proof, ambos census, baseline, candidato y herramientas.
Reverificar código/recibos/transitivos antes de leer y tras escribir. Comprobar
ambos census EXACT_CENSUS1520 y proof completo, sin recalcular geometría antigua.
El candidato copiado debe ser exactamente2581; no lectura desde una ruta de
despliegue mutable. La lista ordenada/propiedades y200modelos restantes/config201
deben proceder de baseline ef229 y conservar bytes exactos.

Preparar carpeta exclusiva sin junctions ni escrituras P:/Mods. Sustituir
únicamente cs_kit_118_0000.p3d. FileBank.exe fijado
f89aaeb22421b9158fbbf173f75d52b6f3de69986cb462e58956c78da82c4caf,
con argumentos de propiedades leídas; no Binarize/AddonBuilder. Fresh preflight
de herramientas y disco para esta fase; no reusar éxito viejo como entorno vivo.
La copia local de preflight sólo se ejecutaría desde entrada nueva revisada,
sin relanzar CLI/carpeta B3E2 consumidos ni editar skill gobernada.

Releer el PBO escrito con lector fijado. Comparar entradas completas, orden,
propiedades, config y200modelos con baseline mediante consumidor independiente;
extraer target y hash comparado con el ODOL aprobado. Guardar recibos y árbol
de procesos observados; ningún proceso ajeno. Resultado permitido:
EXPERIMENTAL_B3F_PACKAGE_IDENTITY_PASS_CONDITIONAL, REJECTED_PACKAGE o
INCONCLUSIVE_PACKAGE. Ninguno cierra los47FAIL21inciertos ni certifica juego.

## Puertas y presupuesto antes de empezar

Revisión plan180s, código180s, suite120s. Una preparación/preflight60s/2GiB,
una composición120s/2GiB y un consumo120s/2GiB, sin reintentos internos.
Antes de empaquetar, fixtures PBO escritos independientemente positivos y
negativos: modelo omitido/extra/orden distinto, config de1modelo sustituido por
error, target/control intercambiado, propiedades mutadas, proof/census/contrato
ajenos, archivo modificado entre fases, rc0 tardío y fallo de lectura preservado.
También integridad transitoria del candidato/200restantes y salida ya existente.

Si no cumple, conservar reporte y parar; no recompilar ni cambiar representación.
Tras éxito, plan NATIVO separado: discriminadores basados en evidenciaB2 y
controles originales, geometría+poses+paquetes sellados, FIFO oficial y cierre.
No repetir2658/B1/B2 ni asumir que estos dos contactos resuelven causa global.
