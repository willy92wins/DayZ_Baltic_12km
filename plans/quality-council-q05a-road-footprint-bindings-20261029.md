# Q05A — fuentes y selectores para huellas viales y ambos accesos

Estado: REVISADO_PARA_INVESTIGACION_DE_BINDINGS_GUARDADOS. Investigación concreta sobre evidencia
guardada; sin nuevo censo, NPZ, extracción vanilla, colocación, build o DayZ.

## Propósito y criterio de producto

[EXACT] product-spec.md:11-17, P5/P6/P9/P10/P11: conexiones y piezas humanas,
pasos terrestres y navegables, reserva de terreno ahora y mapeado físico después,
rasante y empalmes suaves. La decisión P9 conserva 1m/.95m/24m y excepciones;
24m es corredor navegable, NO ancho vial. No nueva decisión de producto aquí.
Q05/Q06/Q07 del council exigen huella completa, ambos accesos y alineación;
ninguna caja local ni eje nominal basta como ancho útil o conducción.

[EXACT] Q03C2R1 acaba de medir 1520 caras kit118 contra terreno fuente/agua
seleccionada, nueve áreas por cara verificadas. Hay 202.8643504880163m² por cara
con multiplicidad por encima del terreno fuente y sin huella seleccionada de
agua; NO son superficie visible, unión mundial ni conflicto vial acreditado.
Fuente NW-SE asumida, oclusores/agua nativa/marco compilado pendientes. No
confundir esa cifra con el antiguo conflicto23.9566664m² del corredor8m.

## Anclas verificadas y hechos guardados

[EXACT] tools/quality/pilot_visible_exposure_ev112.py:24 fija ROAD_SHA94ecbca6;
:50-57 road_guard exige xy(36428,2), edges(36467,3), longitudes positivas;
:140-144 lee reference.npz/xy/edges. Su rect(...width=4) en:30-35 y discos de
radio4 son la antigua banda8m, NO la huella de piezas de12/9m. No ejecutar CLI.

[EXACT] evidence/road-water-census-20261028/README.md:3-8 conserva770aristas
de contacto en29cadenas sobre124/36467, no770puentes. Su dominio nativo omite
agua3D. evidence/road-surface-overlay-20261028/README.md:3-24 añade capas3D y
Roadway:2413contactos, kit118 intercepta6aristas de carretera76. Conserva
desalineación diagnóstica Narva y contacto49/301; no aceptación por proximidad.
El código tools/quality/road_surface_overlay_ev112.py:204-240 fija fuentes y
transformaciones históricas; :294-359 produce contactos/contextos. No relanzarlo.

[EXACT] RoadB0R1 guarda tres local-faces-*.json privados en
E:/DayZ-Baltic-Build/shape-repair-20261025/road-b0-discovery-r1-20261028,
ligados por report.json. Contienen caras completas Visual/Roadway locales;
bounding_center NO es pivote certificado. RoadB2 tiene cuatro hipótesis de
origen/centro y fila/columna; RoadB3 sólo tres objetos elevados de ensayo.
No escoger una hipótesis por conveniencia ni aplicar dos veces una transformación.

[EXACT] Q03B6 indexa capas seleccionadas históricas3d955:201pilotos ya mundiales,
539009caras y17818poses. No es toda la escena Visual ni la época B2Aef229.
RoadB4B1 sólo equivalencia de contenido guardado, método no ligado/precedencia
actual no probada. Doce recursos B4A3 no cierran5509modelos.

## Unidad de investigación [DESIGN]

Una entrega de investigación read-only120s, máximo16MiB por archivo/64MiB total,
1200palabras más tabla. Fuentes: JSON/Markdown/código guardados; no abrir NPZ,
PBO/P3D/WRP, terreno815ef8 o vistaheights; tampoco config/recursos instalados.
Antes de leer comprobar longitud; si excede presupuesto registrar LOCATED_NOT_OPENED.
No regenerar ni volver a recorrer censos anteriores. No modificar P: ni archivos
sellados; no ejecutar los antiguos preparadores, CLI, autores o consumidores.

1. Recuperar los pins y esquemas GUARDADOS del grafo vial, cadenas, contactos
   nominales y overlay, incluidos nombres reales de campos y su significado.
   Identificar los seis edge IDs de kit118/cadena76 y el enlace exacto49/301,
   Narva71 y tramo49 seco. Coordenadas humanas sólo contexto; si la fuente no
   permite un join literal, UNKNOWN, nunca nearest como vínculo certificado.
2. Por esos contextos, distinguir centro de eje/reserva, superficie construida
   seleccionada, plantilla vial local y eventual acceso. Señalar si existe un
   selector de extremos/tangentes y su dominio de estaciones; NO fijar una
   longitud de acceso sin criterio leído. Ambos lados deben permanecer en
   cobertura incluso si el contacto está en un nodo compartido o extremo.
3. Enlazar hashes/épocas de caras B0, hipótesis B2, poses B3 y superficies Q03B6,
   conservando model_index, instance_id, source_ids y ordinal en columnas
   distintas. No construir una huella mundial mezclando épocas/hipótesis.
   Marcar provider/pivot/frame/usable_width y oclusión como UNKNOWN donde falte.
4. Proponer el próximo contrato de medición con dos dominios separados:
   A) contactos/solapes de superficies históricas ya mundiales contra reserva
   vial fuente; B) cuatro predicciones de plantilla local, sin colocación y sin
   certificar pivote. Para cada dominio listar datos que faltan antes de cargar
   arrays y las medidas que realmente puede probar. Una falta de pivote bloquea
   aceptación mundial, no el análisis local ya autorizado.

Entregable: tabla por fuente/selector con path, SHA, época, campo/pointer o
línea, leído/no abierto, verified/assumed/unknown y dependencia siguiente.
Estados OBSERVED_SAVED, LOCATED_NOT_OPENED, UNKNOWN, CONTRADICTED.
measurement_ready=false y placement_ready=false SIEMPRE en esta investigación.
No publicar caras/recursos vanilla completos. Un informe previo no se vuelve
a llamar fuente física actual; la tabla de puentes no define el universo vial.

## Cierre y validación propuesta

Una revisión externa del plan120s antes de investigación; no código, extractor
o nuevo lector en esta unidad. Codex integrador adjudica con anclas. La entrega
puede concluir INCONCLUSIVE_SOURCE_BINDINGS; no inventar campos ni completar
joins por semejanza. Investigación consumida una vez, sin retries internos.
Contrato/extractor posterior tendrá oráculos y presupuesto propios antes de
arrays. Diseñar (sin afirmar ejecución) mutantes de puente omitido/girado/corto,
arcén fuera8m, acceso ausente, cambio de época, eje o material, aguaRoadway falsa,
nodo compartido y cadena recortada. Preservar controles naturales/diseñados y
los nueve casos Q01; ningún sintético los resuelve por sí mismo.

Q03C2R1 y censos previos quedan consumidos. Q02B ángulos/referentes Q08/Q17 y
reparaciones siguen pendientes; no otro council. Nueve humanos0resueltos,
C1NOT_REVIEWED; Nav8 histórico607PASS no es validación de carreteras nuevas.

## Precisiones adjudicadas de Muse36.407s [DESIGN]

1. Separar chain_index, edge_ordinal_in_chain, flattened_road_row_index,
   global_edge_index|UNKNOWN, node_a y node_b. census:296 enumera road_rows;
   ese contador NO demuestra el índice del array edges. contacts guarda
   chain/edge/nodes:347. Sólo un join explícito puede ligar el índice global.
2. Dominio A sin polígono de reserva guardado identificado se limita a fuente
   eje/grafo: localización por estación, longitud, distancia lateral/lado;
   NO área de cobertura ni ancho. Aquí sólo se diseñan medidas, no se calculan.
   La huella completa continúa pendiente; banda8m no se adopta como sustituto.
3. Separar sha_recomputed (sólo bytes leídos) y sha_declared_in_manifest
   (declarado/copied, sin verificación del archivo no abierto). Desconocido no
   se rellena con digest inventado. Límites se aplican antes de cada lectura.
4. Añadir derived_from/transform_source y dependencias comunes. Overlay y Q03B6
   comparten fuentes históricas: no contarlos como corroboración independiente
   del marco ni de la geometría sólo por ser dos informes.
5. Dominio B se restringe a los tres modelos B0 pinados y sus centros guardados;
   las cuatro hipótesis B2 no se transfieren a kit118 ni a otra plantilla.
6. Los cuatro contextos son MUESTRA_INTENCIONAL_NO_REPRESENTATIVA. No extrapolar
   tasas/cobertura al universo124/36467. Arcén fuera8m es sensibilidad diagnóstica,
   no criterio de aceptación inventado. Tramo49 seco conserva alcance local.

El revisor leyó cápsula acotada y no los JSON privados ni todo el índice.
Sus límites de cobertura se conservan. Integrador comprobó census:294-359 y
graph_guard:111-124; no hay un campo global_edge_index demostrado en contacts.
La postimagen editorial fue adjudicada con contexto compartido, no nueva
revisión externa. Investigación todavía no ejecutada; no repetir esta review.
