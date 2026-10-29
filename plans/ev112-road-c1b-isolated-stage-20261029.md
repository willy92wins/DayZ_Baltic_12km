# RoadC1B — materializar los dos stages de laboratorio

Estado: REVISADO_PARA_CONTRATO_Y_STAGE_LIMITADO. 29-10-2026.
Codex planner/integrator; executor local asignado explícitamente para este corte.

## Resultado concreto y alcance

P5/P6/P8/P11: producir dos árboles privados nuevos, control0/candidato3, que sólo
difieran en `baltic_trial.wrp`. Todas las demás rutas, configuraciones y bytes deben
coincidir con un manifiesto externo congelado antes del código. No se modifica el
mapa poblado, P:, RoadC0 ni recursos vanilla. No build, paquete ni DayZ en C1B.

Hipótesis: los recursos observados bastan para armar un stage reducido verificable
por bytes. No equivale a cerrar dependencias del compilador/runtime. Si existen
dependencias adicionales, la futura sonda las registra; no se declara listo ahora.
El resultado es VERIFIED_LAB_STAGE_BYTES_ONLY, `build_ready=false`,
`dependency_closure=NOT_EVALUATED`, `compiled_terrain_decoder=NOT_VERIFIED`.

## Anclas reutilizadas sin repetir sus censos

- C0: control f00c3f57.../17307685B y candidato2fb3686b.../17307968B; prefijo
  17307629B/d16b5139 y terminador56B ya comprobados. Copiar, no regenerar.
- C1A reporte f3eb0ab1...:4775RVMAT propios/10052971B y config histórica.
  C1A1 reporte y contrato22dae243:2048PNG literales/140323829B por metadata,
  ochoPAA/40711646B por metadata; hashes de payload PNG/PAA todavía no observados.
  C1A1 recuperó strings, no un parser semántico de RVMAT. No repetirlo.
- B4A3 reporte d5ce5307...:ocho assets guardados y cuatro hojas nuevas en `leaves/`,
  con path/virtual_path/hash/size. Tres modelos instalados históricos, no identidad
  de archivos instalados hoy. Reusar copias pinadas, no abrir PBO ni P3D parser.
- Binarize/bin/config.cpp instalado dcf19f27... es distinto de P:/bin/config.cpp
  42b4cf95...; este corte elige explícitamente el instalado como entrada de ensayo
  bajo `bin/config.cpp`. No afirma equivalencia ni cambia ninguno.
- Descubrimiento puntual de metadata29-10: P:/core,58entradas/41archivos/9717421B,
  sin reparse observado, sin config.cpp. `texheaders.bin` sí presente. Se conserva
  TODO ese conjunto pequeño como soporte opaco, no se proclama cierre semántico.
  No usar ausencia de config.cpp para omitir core ni explorar todoP:.
- Config histórica stage-kit7-fc/.../config.cpp:8-12 requiredAddonsagua/piloto;
  19CAWorld;37worldName;24-55Outside/midDetail/UsedTerrainMaterials;56-212Navmesh.
  `tools/terrain/compile_visual_pilot_ev112.ps1:18-29` no se ejecuta ni se copia.

## Configuración de laboratorio explícita

[DESIGN] Nuevo texto exacto antes del código: CfgPatches/BalticRoadPivotLab y
CfgWorlds/BalticRoadPivotLab:CAWorld; requiredAddons sólo DZ_Data/DZ_Surfaces.
worldName conserva `dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp` para no
reescribir las referencias internas del WRP. Description identifica laboratorio;
longitude/latitude/center/time/date/MaxTide/MaxWave y las referencias de24-55
del config histórico se conservan. No bloque Navmesh en este ensayo elevado, ni
dependencias Baltic_Water_V30/Baltic_Stream_Pilot, ni inclusión de su población.
Config original intacta. No afirmar arranque nativo ni CAWorld resuelto en stage;
la herencia y requiredAddons son deudas explícitas para la sonda de compilación.
No aceptar co-carga con el paquete productivo del mismo prefijo en un futuro run.

Preparar el literal comparando una vez con la fuente histórica pinada; guardar
diff legible y SHA externo. Ambas ramas usan exactamente el mismo literal.
La prueba no es una autorización para retirar navmesh/población del mapa real.

## Manifiesto externo antes de autoría

Lista cerrada de fuentes y destinos normalizadosASCII lower con slash `/`:
4775RVMAT,2048PNG,8PAA; doce recursos B4A3; dos texturas exteriores y cuatro
RVMAT de UsedTerrainMaterials desde las rutas explícitas C1A; los41archivoscore;
bin/config.cpp instalado y config propio nuevo. Duplicados de destino sólo se
fusionan si SHA/bytes y fuente física observada coinciden; si no, REJECTED_COLLISION.
No normalizar `.png` a `.paa`, no basename, no inventar aliases de prefijo.

Codex preparador autorizado a una lectura fresca de esos payloads para fijar SHA,
tamaño e identidad path/handle/dev/ino/mtime antes de código, incluida la nueva
observación de PNG/PAA/core. Copias B4A3/C0/RVMAT/bin conservan sus pins históricos;
si difieren, rechazo, no repinar. Los SHA nuevos no acreditan identidad retroactiva.
No leer ni copiar el WRP poblado ni navmesh439MB; eliminar sus dos entradas de
configC1A por selector explícito, no por patrón global. Core se enumera sólo una
vez al preparar manifiesto, contra el conjunto/números observados; no seguir enlaces.

Cotas:8192entradas comunes,32MiB por archivo,384MiB payload común,1GiB ambasramas,
8MiBmanifiesto/8MiBreporte. Preparación120s/256MiB; stream1MiB, reserva por tamaño
antes de leer/copiar, lectura real<=declarado y EOF. Raíces fuente cerradas en E:,
P:/core,P:/DZ y config instalado. No escritura en ellas. Reparse en cualquier
ancestro bloquea, salvo ninguno esperado; SUBST no se equipara a symlink.
Relativos: rechazar absolute/drive/dotsegment/backslash/control/noASCII/reservados
Windows/colisión casefold y rutas que escapen del stage. Destino absoluto nuevo enE:.

## Autor, consumidor y pruebas

Codexexecutor600s incluye contrato/oráculos/código; una revisión nativa externa180s
de contrato+código; suite120s/256MiB. Una corrección180s por contraejemplo cerrado,
una recuperación180s si no hay dictamen; no bucle abierto. C1B no lanza ninguna
herramienta DayZ: preflight fresco corresponderá antes de una sonda C1C.

Autor: CLI nuevo exige pin externo del contrato; crea sello exclusivo antes de
copiar. Cada archivo se copia a control/root y candidate/root al destino literal;
WRP0/3 bajo el mismo nombre. Compara hash de cada chunk leído/escrito, EOF y
identidad final de fuente. Conserva parciales consumidos en fallo. No sobrescribir.
Nuevo consumidor, sin importar autor: lee contrato por pin externo y recorre ambos
árboles, rechaza extra/faltante/reparse, comprueba hashes/bytes/destinos/configs y
reabre todas las fuentes por su propio flujo. No confiar en el informe del autor.
No writer/parserWRP nuevo: identidad de las fuentes C0 se hereda porSHA exacto.

Oráculo literal previo con dos archivos comunes (uno de nombre con espacio) y
control/candidato de bytes distintos, configliteral; expectedfiles por rama.
Negativos obligatorios:extra/falta/modificado en stage, source cambia, PNG redirigido
a PAA en co-mutante, colisión casefold, traversal/absolute/reservadoWindows, bool en
bytes, salida ya existente, source reparse simulado, hashcontrato erróneo, config
de una rama distinto y fuenteWRPequivocada. Consumidor se ejecuta sobre fixtures
materializados independientes, no únicamente sobre salida del autor.

Una materialización real120s/256MiB y un consumidor120s/256MiB sólo tras gates;
sin retries. FULL sólo todos los bytes verificados y únicos; timeout/fallo no
produce stage aceptado. Ni suite verde ni copia exacta prueban formatoPNG/PAA,
compilabilidad, recursos transitivos, precedencia nativa o pivote.

## Después

RoadC1C necesita plan propio COMPILE_PROBE_ONLY si sigue sin lectorOPRW completo:
preflight fresco, invocación local anclada, control primero y candidato condicionado
a artefacto/identidad del control, presupuesto de una pareja, ninguna aceptación
semántica ni despliegue. Un escáner de modelos no se convierte en lector de alturas.
NativeC2/Q05 sólo con gates propios. Nueve humanos0resueltos,C1NOT_REVIEWED.

## Adjudicación Muse 29.813s, ocho precisiones incorporadas

F1: reconciliar las cuatroPAA y cuatroRVMAT del config por rutas completas; las
dosPAA grass pueden coincidir con el conjunto8, pero no se supone sin tabla.
F2: config propio destino dayz_baltic_12km_dev/tb/narva_trial/config.cpp; WRP
dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp. bin/config.cpp es distinto.
F3: pins completos/tamaños/paths en contrato antes de código.
F4: conservar clases vacías Names/Sounds/Ambient; omitir exclusivamente Navmesh;
literal/diff guardados. Dos replacements de clase y descripción, requiredAddons
quitando sólo las dos dependencias Baltic. No reinterpretar el config histórico.
F5: conservar todos los alias-fuente observados de un destino; sólo fusionar si
comparten identidad física y SHA/bytes. Si identidades distintas, rechazo aun si
SHA coincide. Consumidor reabre todos los alias, no elimina fuentes silenciosamente.
F6: todas las cotas abortan antes del código si las entradas reales no caben.
F7: fuera del core acotado, abrir sólo las rutas individuales; reparse e identidad
revalidados en preparación/autor/consumidor, no enumerar E: o P:/DZ.
F8: consumidor separa STAGE_BYTES de SOURCE_PIN_MATCH; FULL necesita ambos;
source drift no se atribuye a corrupción del stage. Formatos y compilación abiertos.
Revisión externa de la cápsula preimagen, postimagen adjudicada por integrador;
no otra revisión externa ni consenso. No repetir el plan review consumido.
