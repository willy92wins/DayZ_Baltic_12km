# Carreteras B3: preparar piloto WRP aislado

Estado: REVISADO_PARA_IMPLEMENTAR_FUENTE_OFFLINE. Fable5.1 nativo93.172s,
SOUND-with-fixes adjudicado abajo. No autoriza build ni DayZ.

RoadB2 unidad1 ha generado24huellas completas Visual/Roadway para3instancias
y4hipótesis. Menor discriminación conjunta10.770329614269007m; ULPmundial máximo
0.000030517578125m. No se ha escogido pivote ni colocado carretera. Ancho útil,
accesos, apoyo y conducción siguen sin observarse. Rectas300/225m² y curva
209.4229046319747m² proceden de B0, no de cajas. El contraste de área curva sólo
mide cuantización de predicciones; no cambia cross0.03/grade0.065/chord0.03.

## Propuesta [DESIGN]

1. Descubrimiento acotado60s/2GiB antes de autoría: leer las definiciones actuales
   source_arrays/compiled_arrays/object_record y los recibos de la referencia
   sourceWRPb108352f/compiled0da63d3f. El count<200000 del lector piloto limita
   tabla de modelos, no número de objetos: no confundir ambos dominios.
2. Preparar un autor nuevo de una copia aislada: conservar bytes de terreno,
   materiales y objetos anteriores; añadir exactamente3modelos/poses de la
   receta B2. Censo propio completo de IDs para max+1, uint32 y unicidad. Medir
   terreno en el banco propuesto para asegurar separación vertical; Y200 de
   la fixture es hipotética y no acredita altura libre real. Si obliga a otra
   receta, revisar nueva derivación y fixtures antes de escribir.
3. Presupuesto propuesto para autor+consumidor offline120s/2GiB cadauno; pruebas
   de duplicado/desbordamiento de ID, payload alterado, nombres/pivotes y
   orientación. Consumidor independiente de bytes guardados, no reutilizar el
   resultado en memoria del autor. Sólo CANDIDATE_SOURCE_OFFLINE.
4. Binarización futura necesita su propio plan y preflight; conservar distinguir
   las4hipótesis después del ODOL/WRP guardado. Nativo posterior: verificar APIs
   INSTALADAS ModelToWorld/ObjectModelToWorld/GetObjectsAtPosition3D y enlace de
   cada objeto sin escoger por cercanía. Registrar origen/bases/huellas/accesos.

No modifica producción, agua, extremos, reservas ni P10. No puentes por posición
del personaje. Pilotos posteriores49seco,49/301,Narva71,kit118/cadena76 requieren
huella completa y accesos, no sólo eje ni el corredor histórico8m. Pavimentado,
conducción y la conexión RoadNetwork/ALB1 siguen pendientes.

## Descubrimiento acotado29-10 y diseño concreto para revisión

La unidad queda ligada a Q04 del council. Se ejecutó sólo lectura de fuente
b108 en5.859s:2.578.398objetos, IDs únicos positivos, máximo19.394.563; siguientes
IDs19.394.564/565/566. Prefijo17.307.629bytes SHA d16b5139; flujo de registros
SHA5a3ad8a4; terminador56bytes SHA091ebd37. Fuente286.261.435bytes. Datos completos
en road-b3-input-discovery-20261029/report.json. No WRP escrito ni modelo colocado.
Receta y24huellas B2 se conservan: menor holgura respecto al máximo del terreno
en las ventanas conservadoras es196.42708110809326m. Esto NO demuestra espacio
libre frente a árboles/edificios ni relación del origen/centro en el motor.

Anclas verificadas: `prune_visual_forest_v31.prefix:14-23` y `objects:26-33`
leen prefijo/objetos por stream; `wrp0wzd.object_record:54-55` empaqueta12f32,
u32ID,u32longitud,nombre; `package_visual_forest_ev112.source_arrays:16-26` exige
IDs únicos, `compiled_arrays:29-71` es lector heurístico deOBJ, no terreno.
`road_consumer_discovery_ev112.check_prefix:23-25` fija prefijo instalado
`DZ\\structures\\roads`; SELECTED:15 identifica las3entradas porhash.
No llamar wrp0wzd.read sobre millones de diccionarios: usar streaming acotado.

Autor nuevo [DESIGN], únicamente fuente aislada:
- Contrato de entradas con pins EXTERNOS del WRP, receta, informeB2,24huellas,
 3fuenteslocales, recibo descubrimiento y helpers. Verificar antes de parsear.
- Releer TODOS losIDs para verificar conteo/max/duplicados/overflow. Conservar
 cada byte anterior al terminador. Añadir exactamente3registros, concatenando
 prefijo literalPBO y entrada exacta local medida, con slash normalizado aWRP;
 matriz filaaplanada tal como receta, posición literal yIDsmax+1. Esta escritura
 de12float no escoge hipótesis de interpretación nativa. Nombrar las3instancias
 en manifiesto. Mantener terminador exacto y no publicar el WRPvanilla.
- Destino exclusivo, escritura parcial con nombre distinto, consumo antes de
 promover a candidate.wrp; no modificar fuente ni paquete/build/DayZ.
- Consumidor independiente: desde archivo guardado, igualdad por streaming de
 todos los bytes fuente salvo56finales,3registros terminales decodificados con
 struct frente a literales del contrato, mismo terminador yEOF. Segundo censo
 de IDs en candidato; exactamentecount+3, únicos y positivos. No importar autor
 ni comparar objeto enmemoria generado por él. Fallar por registro previo
 alterado, IDduplicado, nombre/matriz cambiados, truncamiento y extra final.
- Tests: fixturemínima0WZD con material y terminador no trivial; positivo3poses,
 negativos de cada invariante, firma/modulo/version alterados y fuente que
 cambie entre hash ylectura; conteo vacío/saturado/u32. Datos de prueba propios.

Revisión plan180s; autoría420s, revisión código180s, suite120s; autor yconsumidor
120s/2GiB cadauno, unaejecución real. No nuevos PBO ni aprobación decolocación
enmapa. Binarización ysonda tienen planes propios; antes deellas inventario3D
independiente para excluir oclusores del banco y preflight fresco. No aplicar
filtros del lector antiguo como aceptación deWAter/terrain/consumerNative.

## Adjudicación y nombres observados

Nuevo descubrimiento sólo de nombres/terminador en2.562s (no repetircatálogo):
2.578.398nombres SIN NULterminal;28objetosdecarretera existentes usan prefijo
`dz\structures\roads\bridges\` en minúsculas. IDsmin16.777.216/max19.394.563
únicos; terminadorID27.258.688 fuera de los3nuevos. Matriz delterminador contiene
sentinelasNaN: se conserva opaca bitexacta, no se trata comoobjetoválido ni se
normaliza. Recibo road-b3-name-discovery-20261029/report.json.

Contrato fijará tabla explícita en orden:
straight_identity→Parts/asf1_25.p3d→d72224ed…→ID19394564;
straight_90→Parts/asf2_25.p3d→4ce4b0a7…→ID19394565;
curve_90→Parts/asf1_10 100.p3d→2d52f9e5…→ID19394566.
NombreWRP nuevo enbytesASCII minúsculas, separadorbackslash simple ysinNUL como
los28registros existentes; conservar elespacio en asf1_10 100. Casing original
delPBO queda en tabla deprocedencia, no se cambia el PBO. Pin raw_name_hex
completo para cada entrada; consumidor no normaliza nombres alcomparar.

Se aceptan hallazgos1–5: mapamodelo/ID/rawbytes explícito, terminadorID separado,
lector propio de56+longitud sin lower/decode para preservación, tamaño candidato
=fuente+3registros, IDsmin/únicos explícitos. Contrato y fuentes deben estar
ligados abytessnapshot deunalectura ohash después de cada lectura independiente;
un cambio externo falla antes de promover. No modificar helpers sellados.
