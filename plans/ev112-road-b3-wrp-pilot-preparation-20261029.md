# Carreteras B3: preparar piloto WRP aislado

Estado: BORRADOR_PENDIENTE_DE_REVISION. No autoriza build ni DayZ.

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
