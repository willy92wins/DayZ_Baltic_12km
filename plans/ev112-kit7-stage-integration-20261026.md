# EV112 — composición de kit-7 sobre F/C

Continuación de la integración autorizada de los ríos. Descubrimiento de solo lectura sobre el WRP F `6e649b72bf4ec6789a83050f21b7e5597de417e14f251f854728eb20d8b84bd8`:2.578.725objetos,62piezas continuas existentes y2.560.872objetos de bosque. Kit-7 original tiene174registros en `water-fix-b/kit/kit-records.json`. Su candidato aceptado offline contiene139piezas y su terreno/charcas están fijados en `river-kit7-merged-byteexact-20261026`.

`kit7-forest-impact-20261026/result.json` identifica292conflictos con el margen de lecho,0con agua y1.623candidatos a ajuste Y entre los conservados. Es descubrimiento, no aprobación del bosque. No cambia XY, escala ni inclinación. Fuente, referencia Livonia, modelos MLOD y terreno están fijados en su manifiesto.

## Composición propuesta y revisión previa

[DESIGN] Reutilizar el mecanismo de `stage_combined_candidate.py`, adaptado una sola vez y revisado antes de ejecutarlo. Congelar los174registros antiguos por modelo y los12float32 de su matriz; retirarlos con multiplicidad exacta y exigir que todos se encuentren. Retirar solo los292ID de bosque identificados, ligados a sus bytes/modelo/matriz originales. Ajustar Y de los demás objetos de bosque por la diferencia de terreno triangular; registrar por separado deltas calculados y cambios float32 efectivos. Todo objeto restante, incluida cada pose de las62piezas C, conserva los demás bytes. Añadir139poses derivadas del ODOL validado con IDs nuevos únicos.

[EXACT] `tools/terrain/wrp0wzd.py:54` serializa un registro con `object_record(matrix, ident, raw_name)`. `prune_visual_forest_v31.prefix/objects` leen el layout0WZD y comprueban terminador. No editar esas funciones compartidas.

[DESIGN] Componer un PBO aislado de201modelos: las62entradas del PBO C exactas y139entradas kit-7 exactas. Extender solo config con las139clases de terreno necesarias, conservar dependencias y prefijo, compilar y releer. Para el manifiesto fuente, U2 contiene62instancias; sustituir las27 por las fuentes C (incluidas las2restauradasU2), conservar35 y añadir139kit-7. Releer todos los hashes/poses; ninguna recompilación silenciosa de los62modelos anteriores.

## Puertas y presupuesto

Una composición aislada, salida nueva, máximo900s de ejecución. Lector independiente del WRP fuente: exactamente2.578.398objetos si se retiran174+292 y se añaden139;201modelos piloto,62poses anteriores exactas,174retiradas antiguas exactas,292retiradas exclusivamente de bosque, alturas nativas exactas al candidato y materiales/config del mundo conservados. No aceptar solo el digest calculado por el escritor: confrontar fuente y salida con una lectura independiente.

Después ejecutar el consumidor completo de soporte/agua/transformación del bosque sobre el piloto combinado y terreno nuevo; límite1800s. Los puntos exteriores no se convierten en PASS por ausencia de cobertura. Carreteras y protecciones deben conservarse. No ampliar tolerancias ni repetir automáticamente ante un fallo: localizar el contraejemplo.

Solo después: compilación WRP, readback de todas las poses/alturas, paquete nuevo, sonda propia de agua y física incluyendo extremos/juntas, navegación del nuevo mundo y vista con Guillermo. El PASS de navegación C/F no se hereda. La comparación de rendimiento E/Chernarus tampoco se traslada a este candidato.

Este plan prepara la unidad siguiente. No modifica por sí mismo WRP, PBO, bosque ni despliegues; las piezas y recibos rechazados permanecen conservados.
