# RoadB4A: resolver entradas reales del futuro compilado vial

Estado: REVISADO_PARA_IMPLEMENTAR_DESCUBRIMIENTO. Fable5.1 nativo78.047s, SOUND-with-fixes adjudicado abajo. Siguiente unidad de Q04 del council
y P10/P11; no autoriza construir, empaquetar, desplegar ni arrancar DayZ.

RoadB3 ya produjo fuente aislada46063f37 con tres objetos adicionales y preservó
los2578398 anteriores. Falta demostrar cómo se resuelven sus modelos en el build:
el catálogo instalado y P: diferían en asf1_25. Las poses/pivotes nativos y ancho
útil siguen UNKNOWN. Antes de diseñar otro compilado hay que fijar esa diferencia.

## Fuentes verificadas [EXACT]

- tools/terrain/compile_visual_pilot_ev112.ps1:9-14 fija AddonBuilder,
  agua, piloto, include.lst y P:/DZ/bin/core;18-22 crea junctions;25 invoca
  AddonBuilder con project y temp. Es antecedente, NO entrypoint a repetir.
- tools/terrain/package_visual_forest_ev112.py:16-26 lee fuente,29-71
  localiza heurísticamente objetos OPRW. No decodifica altura ni certifica
  materiales. compare:74-95 incluye excepción forest-Y histórica que NO se
  traslada automáticamente al piloto nuevo.
- tools/quality/road_consumer_discovery_ev112.py:15-17 fija tres modelos
  instalados y config;23-25 prefijo DZ\\structures\\roads,72-90 muestra lectura
  de PBO y comprobación de entradas. R0/R1 consumidos; no ejecutar run.
- road-b0-discovery-r1-20261028/report.json y local-faces-0/1/2.json conservan
  nombres de materiales/texturas y centros ODOL. Reusar sus bytes por los pins
  externos del contrato RoadB3, sin reextraer caras ni recatalogar501entradas.
- stage-kit7-fc-20261026/root tiene enlaces DZ→P:/DZ, bin/core→P:, agua/piloto
  propios. Su carpeta narva_trial contiene config.cpp y WRPb108. Config:10-11
  requiere Water/StreamPilot;37 worldName. Una existencia no prueba identidad. README del catálogo instalado:13 documenta la diferencia histórica d72224ed/7eb9f894; no se presupone que P: siga igual hoy.
- package-kit7-fc-world-20261026/verification.json registra modelo5509,
  objetos2578398, versión32/stride64, forestY de un árbol con delta1.5258789e-5.
  Es evidencia histórica, no aceptación del build futuro.

## Descubrimiento propuesto [DESIGN]

Un extractor nuevo, sólo lectura de entradas, escribe únicamente un informe
y manifiesto en directorio nuevo de E:. Contrato externo de rutas/pins revisado.
No modifica P:, no sigue enlaces recursivamente ni cambia binarios o config.

1. Verificar recibos RoadB3/B0 y los tres local-faces por hashes externos
   existentes. Leer los metadatos de enlaces del stage y resolver rutas
   canónicas de las tres piezas WRP. Guardar original/resuelta y comparación
   SHA con el catálogo INSTALADO. Faltante/drift se conserva como tal.
2. Desde models.jsonl del catálogo instalado, de TODOS los LOD, listar referencias únicas de material/textura de las
   tres piezas. Comprobar esos archivos en la ruta de build y su identidad
   contra entradas instaladas cuando estén en structures_roads.pbo.
   Referencia externa a ese archivo: UNRESOLVED_EXTERNAL, nunca ausente ni
   satisfecha por cercanía/nombre. No afirmar cierre transitivo de RVMAT.
3. Leer el PBO por streaming con pbo_table y rangos referidos (sin read_pbo completo):
   verificar SHA34c1cabe completo, propiedad de prefijo real, exactitud de
   nombres y hashes de las tres piezas. Sólo extraer hashes/metadatos de las
   entradas referidas; no ODOL, caras, CfgConvert ni catálogo completo nuevo.
   Comparar la ruta de build sin sobrescribirla. Los binarios quedan privados.
4. Fijar config.cpp, include.lst, compile helper y ejecutable instalado porhash
   y existencia canónica; registrar ausencia sin bootstrap. Esto NO es
   preflight ni certifica qué hijos ejecutaría AddonBuilder.
5. Informe: INPUTS_MATCH / INPUTS_DIFFER / INCONCLUSIVE_DISCOVERY, cada entrada
   con fuente/hash/ruta/estado. Cero interpretación de pivote/ancho útil, cero
   aceptación de agua, terreno, memoria o carreteras.

Con resultado se redactará RoadB4B: nueva pareja control/candidato compilada
con resolución de assets explícita y gates propios. Si difiere P: de instalado,
proponer stage privado con referencias exactas; no «arreglar» datos compartidos
ni reutilizar buffers/modelos antiguos por su nombre. No se autoriza aquí esa
composición. Sonda nativa posterior requiere además inventario de oclusores:
la holgura196.427m sólo es relativa al terreno.

## Puertas, presupuesto y parada

Plan Fable180s; implementación240s, code review180s, suite120s. Una ejecución
nueva60s/1GiB. No reintento interno, no lectura masiva de todos5509modelos.
El PBO tiene318217469bytes;675405824 fue RSS del censo, no tamaño del archivo.
Conservar1GiB y usar streaming; si se rebasa, conservar RESOURCE_FAIL sin ampliar.

Fixtures independientes de rutas/entradas: modelo con mismo nombre yhash distinto,
ausente, prefijo distinto, referencia externa, path traversal yescape porenlace,
duplicado/cambio de entrada/recibo repinado sin autorización. Un manifest de
coincidencias debe fallar si se cambian bytes de una entrada guardada; no basta
comparar dos nombres. Leer bytes usados y hash de los mismos, fuente inmutable
antes/después. Informe inconcluso válido no se transforma en build listo.

No censo A/B0/B1/B2/B3 repetido; no modifica los nueve rechazos, C1 ni RAM.
Las tres piezas siguen experimento fuente, no pavimentado del mapa. Cualquier
compilado futuro necesita preflight fresco y presupuesto de fase propio.



## Adjudicación y requisitos concretos

1. F1 parcialmente refutado: PBO observado318217469bytes, no675MB; el censo
   anterior midió675405824 de RSS y no demuestra que1GiB sea imposible.
   Se adopta streaming para evitar doble copia sin elevar presupuesto.
   pbo_table(f,length), deployed_surface_inventory_ev112.py:51-74, devuelve
   propiedades y tabla con name normalizado/mime/size/offset. No importar run
   ni volver a generar modelos. MIME!=0 → inconcluso no soportado, sin
   descompresión inventada. Hash global por bloques y rangos concretos;
   comprobar archivo estable y hashes externos antes/después.
2. INPUTS_MATCH sólo si TODAS las comparaciones requeridas son MATCH y los
   prerrequisitos fijados existen/concuerdan. Drift comparable demostrado →
   INPUTS_DIFFER, conservando además la lista de cobertura incompleta.
   Sin drift pero con missing/unreadable/external/format incierto →
   INCONCLUSIVE_DISCOVERY. Nunca declarar build listo con estos estados.
3. FORMAT_DIFFERS sólo cuando firma/extensión medida acredita representación
   distinta; firma no reconocida → UNDETERMINED_FORMAT. No confundir bytes
   diferentes con contenido semántico diferente. No convertir ni normalizar.
   Un PNG vecino no sustituye una referencia exacta .paa que falta.
4. models.jsonl del catálogo, pin externo antes de lectura, aporta TODAS las
   referencias de LOD de esos3modelos. local-faces sólo Visual/Roadway como
   enlace de procedencia. No escanear otras familias ni reextraer ODOL.
5. Premisa histórica anclada a evidence/road-catalog-installed-20261028/README.md:13.
   En futurobuild se resolverá P:/DZ; los junctions del stage son evidencia
   histórica, no contrato actual. El helper compilador se pina como antecedente,
   jamás como entrypoint autorizado.
6. Registrar metadatos de reparse sin recorrido recursivo. La raíz P: es SUBST;
   resolver primero su destino autorizado, conservar cada enlace conocido y
   comprobar destino dentro de raíces explícitas del contrato. Cadena nueva
   no contemplada → UNRESOLVED_LINK, no seguir silenciosamente Path.resolve.
   Descubrimiento no necesita crear junctions ni permisos sobre rutas ajenas.

Revisión consumida. Código/extractor/contrato aún ausentes. La implementación
tendrá negativos de precedencia de estados, formato distinto, referencia en un
LOD no Visual, enlace no autorizado y PBO comprimido. Un éxito documental no
resuelve pivotes ni coloca pavimento.


## Ejecucion consumida 29-10

RoadB4A completado INCONCLUSIVE_DISCOVERY;39testscoleccionados38PASS/1SKIP. Fuentes/PBO fijados; siete rutas build SOURCE_UNSTABLE sin metadata suficiente para causa. No buildlisto. Ver evidence/road-b4a-build-discovery-20261029. Continuacion nueva instrumentada B4A1 revisada; no repetir este extractor.
