# RoadC1C — sonda compilada del laboratorio

Estado BORRADOR_PENDIENTE_DE_REVISION. P5/P6/P8/P11, preparación del piloto de
pivote vial; ninguna modificación del mapa. Codex planner/integrator y executor
local asignado para el wrapper acotado, revisión entre familias antes de ejecución.

## Hipótesis y límite de aceptación

Observar si la pareja fuente C0, copiada y verificada en C1B, produce artefactos
OPRW con la herramienta instalada. C0 control vacío puede no compilar. Se conserva
el primer resultado sin reintento y sólo se intenta candidato si el control cumple
las puertas de proceso/artefacto. El resultado máximo COMPILE_PROBE_OBSERVED_ONLY:
no certifica objetos0/3 dentro de OPRW, alturas/materiales, pivote, dependencias
transitivas, precedencia nativa ni calidad. Ningún paquete aceptado ni DayZ.
Un PBO que AddonBuilder produzca es subproducto privado de la sonda, no entrega.

## Anclas y descubrimientos

C1B contrato b7d33588, bindingsb632818a, consumidor4c52ddae; dos árboles sellados
480678967B/13786files. No ejecutar de nuevo sus CLIs. Nuevas copias de trabajo
sin hardlinks/junctions preservan los originales. Configlab c054ff97: CAWorld y
DZ_Data/DZ_Surfaces, sin Navmesh/agua/piloto. La herencia no está certificada.

AddonBuilder instalado SHA c113de9cab5e91d27ca0630e360db0a3eca190ec797e1dcad9cdfa70466b45e1,
1479600B. Literales PE guardados en road-c1c-invocation-anchors-20261029:
offset86031 sintaxisCLI; 86651–87097 rutas explícitas binarize/cfgconvert/filebank/
dssignfile/toolsDirectory; 90257 include copia directa; 92575 PNG/TGA conversion;
96765 plantilla Binarize. Literales NO prueban flujo de control ni semántica.
Helper histórico compile_visual_pilot_ev112.ps1:25 es evidencia de invocación,
no entrypoint. Include histórico `*.paa;*.emat;*.xml;*.nm;*.c;*.csv` se conserva
literalmente para esta sonda; no copiar PNG sin convertir por una extensión nueva.
No `-clear`, no `-sign`, no `-packonly`; temp/out nuevos.

logger.xml instalado usa ..\Logs compartido y config permite log4net.Config.
Se copia únicamente el pequeño conjunto instalado AddonBuilder exe/config/DLLs/
steam_appid.txt y en-US/*.dll (excluye copia.pbo) a directorio privado nuevo.
EXE/DLL/config bytes exactos; sólo la copia de logger.xml reemplaza los tres
file.value por rutas absolutas privadas. Guardar original/diff/pins y comprobar
por XML que sólo cambian esos tres valores. No editar instalación ni gobernadas.
La portabilidad de la copia y side effects de Steam/userSettings no se presuponen.
Forzar toolsDirectory y rutas de herramientas instaladas por argv; observar hijos.
No tomar RPT global como recibo propio. Si logger privado no aparece, no atribuir
el global ni certificar aislamiento; reportar NOT_OBSERVED y detener antes de build.

## Fases con puertas

1. Congelar contrato/oráculos antes de wrapper. Inputs: manifiesto/recibos C1B,
   todos los exe/DLL/config copiados y herramientas Binarize/CfgConvert/FileBank/
   DSSignFile instaladas, include literal y nuevos destinos. Inventario reducido
   tools sólo nombres explícitos; cap64files/64MiB porfile/128MiB conjunto.
   No abrir PBO/P3D/WRP semánticamente ni ampliar catálogos.
2. Wrapper copia árbol fuente por manifiesto a work/control y work/candidate,
   comprueba SHA/tamaño/identidad/reparse; sólo 1GiB conjunto. Copia180s/256MiB,
   sin tocar C1B/P:. Verificador propio recorre las copias y sus fuentes porhash.
3. Preflight oficial fresco60s/256MiB, rutas C:\ canónicas. Si SyntaxError213
   persiste, archivar original y copia cuyo único delta es prefijo raw de ese
   literal subst. Compile original debe reproducir SyntaxError; diff y AST de
   copia parseable guardados. No editar skill. Exit no0 bloquea todo lo posterior;
   warnings conservados, no certificación de entorno nativo por exit0.
4. Una invocación privada `AddonBuilder.exe -help`30s/512MiB, sin argumentos fuente,
   para comprobar entregaCLI/noGUI y flags usados. Si rc/recibo/ayuda/log privado
   incompletos, detener sin build. La fuente no se pasa en esta fase. No reintentar.
5. Una pareja ordenada, control primero. [DESIGN] argv: exeprivado, fuente
   work/<arm>/root/dayz_baltic_12km_dev/tb/narva_trial, output/<arm>/out,
   -prefix=dayz_baltic_12km_dev\tb\narva_trial, -project=work/<arm>/root,
   -temp=output/<arm>/temp, -include=include.lst, -binarizeFullLogs,
   -toolsDirectory y los cuatro ejecutables con rutas instaladas observadas.
   No asumir recursos instalados realmente leídos por tener su SHA.
   300s/2GiB RSS por brazo, disco salida2GiB observado, controles cada150ms.
   No promesa de cuota dura de disco/RAM: el hijo opaco puede sobrepasar entre
   observaciones; registrar máximos y matar sólo descendientes PID+birth propios.
6. Gatecontrol: rc0/reasonnull y marcador Build Successful en recibo privado,
   log atado a ventana del proceso, hijo Binarize observado PID/birth/exeSHA/argv,
   exactamente un WRP nuevo en temp, <=128MiB, encabezado OPRW y versión u32
   observada, bytes/mtime/hash ligados. No fijar versión32 sin observarla.
   Rechazar ERROR/FATAL en logs del brazo; warnings conservados. No extender
   blanco de errores por resultado. Si falla, candidato NO lanzado.
7. Observador separado60s/256MiB verifica recibos/ventanas/artefactos por relectura,
   inventario y estado final de work y C1B contra contrato. No importa writer ni
   inventa lector de alturas. Si fuentes cambian, SOURCE_CHANGED y no aceptación.
   Los hashes instalados y los procesos realmente observados van en tablas distintas;
   un hijo demasiado breve para observarlo es NOT_OBSERVED, no identidad ficticia.

## Autoría, oráculos y presupuestos

Codex executor600s contrato/oráculos/wrapper/observador; code review180s, suite120s
256MiB. Una corrección180 por contraejemplo cerrado, una recuperación180 si falta
dictamen. Preparación/copia no ejecuta builds. No nueva ronda del mismo plan.

Oráculos externos literales: rawOPRW/version y bytes opaque vs0WZD, único/múltiple
WRP, controlrechazado bloquea candidato, timeout, rcno0, rc0 sinmarker, log ajeno/
mtime anterior, desconocidoBinarize exe, hijo no observado, fuente mutada, extra
en árbol, loggerXML cambio adicional, reporte/hash co-mutados. Tests usan hijos
sintéticos y artefactos literales, no simulan éxito real de DayZ ni decoder.
Nada de relajar identidad/tiempos ni materializar una copia de fuente después
de su gate para ocultar cambios. Salida metadata32MiB, logs32MiB/archivo.

## Resultado y siguiente

Siempre evidencia privada de herramientas/artefactos, publicación sólo código,
recibos/pins/resúmenes sin vanilla completa. Preparadores y runs consumidos al
primer intento. C1D requiere plan propio para decoder de las muestras obtenidas;
no desplegar ni lanzar juego con un magic/hash. Q03C/Q05 y referentes pueden
continuar en paralelo lógico sin depender de aceptación nativa. C1NOT_REVIEWED,
nueve humanos0resueltos; no confundir esta prueba de herramientas con reparación.
