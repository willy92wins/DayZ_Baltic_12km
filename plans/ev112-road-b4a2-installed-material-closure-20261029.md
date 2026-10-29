# RoadB4A2 — recursos instalados para el piloto vial aislado

Estado: REVISADO_PARA_IMPLEMENTAR_DESCUBRIMIENTO_INICIAL. Fable5.1 nativo59.875s adjudicado; ver delimitación final. Q04/P10/P11. Sólo descubrimiento de referencias y extracción privada de recursos; sin build, WRP nuevo, despliegue, DayZ ni modificación de P:.

## Problema y alcance

B4A1 obtuvo STABLE_CAPTURE de siete rutas en 0.360s/39MB. Las dos texturas coinciden con R0 instalado; los tres modelos y dos RVMAT tienen bytes distintos. Esto no demuestra diferencia semántica ni explica los estados históricos SOURCE_UNSTABLE. No construir el experimento con modelos distintos de los que aportaron sus caras y centros. B4A/R0 y B4A1 conservan sus dictámenes; no repetirlos.

Falta resolver asphalt_ext.paa y las referencias transitivas de los dos materiales instalados. Esta unidad prepara un manifiesto privado de dependencias instaladas que un futuro stage podrá consumir. No declara resolución real del motor ni que un directorio parcial satisfaga los 5509 modelos de la escena. El piloto RoadB3 conserva tres objetos elevados, controles y todos los objetos originales; su futura compilación necesita además un plan de resolución del resto de la escena.

## Anclas verificadas [EXACT]

- tools/quality/deployed_surface_inventory_ev112.py:51-74: pbo_table(f,length) devuelve propiedades y entradas normalizadas con mime/size/offset; rechaza duplicados y rutas inseguras. Es una primitiva, no se llama run ni se recatalogan modelos.
- tools/quality/road_consumer_discovery_ev112.py:12 fija CfgConvert.exe; run:80 invoca -txt -dst sobre config.bin instalado. Su CLI está consumida; sirve sólo como evidencia de invocación. Decodificar RVMAT es una nueva hipótesis que debe contrastarse con la salida real.
- tools/terrain/compile_visual_pilot_ev112.ps1:18-25 enlaza DZ/bin/core a P: y usa -project. No reutilizar ese lanzador ni sustituir su DZ compartido. No demuestra precedencia de un overlay para un nuevo build.
- B4A/R0 contiene los siete hashes de structures_roads.pbo SHA34c1cabe608823dc09ec25dd62c3738a84075a7187484fc99dbdf4e1c2ed2f5f, prefix DZ\structures\roads y catálogo guardado. Reutilizar esos rangos y todosLOD; no reextraer caras ni inspeccionar otros modelos.
- Inventario de nombres observado 29-10: Addons/surfaces.pbo 159807224 bytes y surfaces_bliss.pbo 74984680 bytes. Nombres y tamaño NO prueban prefijo ni pertenencia de asphalt_ext. La referencia exacta es dz/surfaces/data/roadway/asphalt_ext.paa.

## Hipótesis, contrato y pasos [DESIGN]

H1: los recursos instalados fijados pueden resolverse en un conjunto finito con correspondencia exacta de prefijo+ruta. H2: CfgConvert decodifica los dos RVMAT sin pérdida de referencias. No inferir H2 sólo de exit0.

1. Preparar contrato externo con pins de R0 report/manifest/contrato, B4A1 report/approval, models.jsonl/entries.json, herramientas y lectores. Nueva observación de hashes de surfaces/surfaces_bliss, si se leen, se fija como descubrimiento actual; no identidad retrospectiva de B0/B1. Presupuesto antes de ejecución. Sin acceso recursivo a P:.
2. Abrir structures_roads sólo por streaming; verificar hash global fijado y reutilizar tabla/rangos guardados tras comprobar cabecera. Extraer exactamente tres modelos y cuatro recursos internos a directorio privado nuevo, verificando igualdad antes/después. MIME distinto de0: INCONCLUSIVE_UNSUPPORTED_COMPRESSION, sin inventar descompresión. Los modelos no se decodifican.
3. Para la referencia externa y las que surjan de materiales, inspeccionar tablas/prefijos de los dos PBO candidatos surfaces/surfaces_bliss, sin inventario de geometría ni lectura completa en RAM. Coincidencia debe ser literal normalizada de prefijo+ruta, no basename/cercanía. Más de un proveedor dentro del conjunto: AMBIGUOUS_PROVIDER; ninguno: UNRESOLVED_EXTERNAL. La búsqueda está acotada a este conjunto, no afirma ausencia global. PBO de roads también puede suministrar dependencias transitivas propias.
4. Guardar los dos RVMAT originales instalados. Si son texto, parsear ese texto; si son raP, intentar una conversión CfgConvert por fichero, salida nueva, sin sobrescribir. Fijar ejecutable/argv/PIDbirth/rc/salida. Validar sintaxis tokenizada de asignaciones de texture/material y clases anidadas, incluyendo escapes y comentarios; no regex de líneas como prueba de exhaustividad. Desconocidos, include/macros, sintaxis no soportada o salida vacía se conservan INCONCLUSIVE, no cerrar el conjunto. Texturas procedimentales #(...) se guardan como tales, no archivos. Definir gramática concreta y fixtures antes del código; no prometer parser universal de config.
5. Cerrar por punto fijo los nodos rvmat referidos, con visitados por identidad, máximo32nodos/64aristas y profundidad8. Ciclo queda registrado, no omitido silenciosamente; agotamiento de presupuesto incompleto. Todo recurso final requiere provider/path/hash y ruta local privada. El manifiesto conserva aristas, tokens/offsets, compresión/errores, prefijos y cobertura. Otro proveedor necesario sale como pendiente para una unidad posterior, no ampliar raíces ni instalar dependencias automáticamente.
6. Consumidor independiente: desde originales guardados y referencias tokenizadas, comprobar que cada arista tiene resolución o motivo explícito y cada archivo corresponde a su rango/hash fijado. Omitir una referencia o introducir un proveedor ambiguo debe impedir cierre. No basta comparar dos listas construidas por el mismo recorrido.

## Salidas y límites

DEPENDENCY_SET_CLOSED_CONDITIONAL sólo si todos los recursos requeridos dentro de esta receta están fijados, los materiales comprendidos íntegramente y no hay ambigüedad. Sigue no_build/no_native y no acredita universo de archivos del motor. En los demás casos INCONCLUSIVE_DEPENDENCIES, con motivos y nodos pendientes. No cambiar etiquetas de agua, controles, pivote, ancho útil ni accesos; los nueve rechazos siguen abiertos.

Este manifiesto no autoriza construir: RoadB4B necesitará contrato de roots/precedencia para la escena completa, preflight fresco, pareja control/candidato y lectura compilada. No usar sólo las ocho dependencias del piloto como si resolvieran las referencias de los 2578398 objetos existentes. Los binarios y geometría vanilla son privados y no se publican.

## Presupuesto y pruebas

Plan review90s, implementación240s, code review180s, suite120s. Una extracción/descubrimiento120s/512MiB que incluye como máximo dos conversiones de materiales, cada una acotada30s dentro del total; sin reintentos internos. Streaming de PBOs y topes de salida por recurso16MiB/total64MiB. Si transitorios exceden, RESOURCE_FAIL con parcial y recibo, no elevar límites.

Fixtures independientes: referencia en LOD no visual; nombre igual en proveedor distinto; prefijo incorrecto; entrada duplicada/traversal; MIME no soportado; raP y texto con comentarios/escapes; textura procedural; nodo anidado omitido; macro/gramática desconocida; ciclo y límite de profundidad; archivo cuyo hash cambia entre extracción y consumo; conversión exit0 vacía y fallo de proceso. Un negativo co-mutado debe fallar aun con manifiesto repinado. Reusar metadatos B0/A sin volver a generar sus censos.

# Adjudicación B4A2

Fable5.1 nativo59.875s CONDITIONALLY_EXECUTABLE. Se separa la unidad: **REVISADO_PARA_IMPLEMENTAR_DESCUBRIMIENTO_INICIAL**, aún sin código ni contrato. Primero muestras/prefijos, después gramática y plan de cierre; no se implementa el parser final contra formatos supuestos.

La primera ejecución autorizada por este plan sólo extraerá los siete recursos instalados fijados, observará tablas/prefijos de surfaces/surfaces_bliss y resolverá literalmente asphalt_ext si corresponde; conservará y decodificará como máximo dos RVMAT si la firma raP lo exige, sin cierre transitivo ni stage/build. Comparará SHA de los siete con R0. Missing prefix => UNRESOLVED_EXTERNAL; múltiples proveedores => AMBIGUOUS_PROVIDER. Si la firma no es reconocida, guardar bytes privados y UNKNOWN, no forzar CfgConvert. Todo dentro del presupuesto120s/512MiB y sin reintentos. Nuevo código/tests/review antes de ejecutar.

Adoptado para la fase posterior: consumidor recorre originales por vía independiente y exige correspondencia de cada literal con posible ruta (.paa/.rvmat, separador o #() con arista o motivo inconcluso. Mutante que elimina una clase en el parser, no sólo una lista, debe ser rechazado. Cobertura léxica de todos los bytes es necesaria pero NO prueba semántica suficiente; anotación unknown/ambigüedad impide cierre. La gramática exacta se elige después de observar muestras, no copiar el ejemplo de escapes del revisor como si describiese ya el formato instalado.

Corrección F3: entries.json fija tabla/rangos, pero las referencias de TODOSLOD proceden de models.jsonl. Fijar AMBOS y la procedencia allLOD, no atribuir al inventario de entradas las referencias de los modelos. No reextraer ODOL ni repetir censos.

Pins de contexto medidos: R0 report217d331658cc0af43b984f2bef7138a1320338e55b2d8abd06d425fb6efa1e5d; B4A1 report0bd8d67c9eb89d280ef2027c1beb632ec55a9b703cd0349de2deafb270cb39ff. Approval B4A1 y recibos se fijan por hash en contratoexterno antes del código real. Los PBO surfaces se observan como estado actual, sin retroactividad. La revisión no aprueba el futuro build ni el cierre completo.
