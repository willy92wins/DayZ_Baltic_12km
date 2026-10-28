# Adjudicación de código del catálogo A

Fable5.1 nativo123.625s, SOUND-with-fixes, sin herramientas, fuentes intactas.
F1 reproducido con metadata bytes: antes escapaba emit y truncaba denominador;
ahora serializabilidad se verifica antes de READ_STRICT, error local conservado,
y continúa el segundo modelo. IO/fsync que falla permanece inconcluso global.
F3 se añade identidad de módulos cargados; también lzo/lzss transitivos fijados
por hash (sin editar archivos), y pin del medidor. Repro homónimo rechaza.
Guard de fila con error/measurement añadido; fixture falta error rechaza.

F2 no existe contra las fuentes fijadas: attach_navmesh:55 rechaza lowercase
duplicado y pbo_table:64 rechaza key normalizada repetida; test real pasa. No
duplicar defensa por un supuesto que contradice ambas definiciones leídas.
F4 refutado: ODOL.__init__:948 lod_errors={} y read_float devuelve float;
strict en ODOL:1174-1215 exige cursor/relaciones. No cambiar a truthiness de lista.
F5 refutado: sections:113-128 usa get_face_indices y error unassigned_face;
la suite17 previa y20final pasa con esos helpers reales. No interfaces inventadas.
F6: LOD vacío no equivale a carretera aceptada. Índice de cara con0vértices ya
rechaza; se añade empty_lod explícito sin inventar LODs ni rechazar vacío válido.

20tests finales PASS0.531s, postimágenes intactas. Código fb8ac897 y tests320dc473.
Ready para una lectura de catálogo120s/2GiB según plan; no poses/build/DayZ.
