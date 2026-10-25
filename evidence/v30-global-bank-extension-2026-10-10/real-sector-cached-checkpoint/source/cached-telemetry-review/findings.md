# Revisión de telemetría cacheada del piloto

**Dictamen: SOUND para la enmienda acotada de instrumentación.** No ejecuté el solver ni preparé terreno; los archivos fuente inspeccionados permanecen fijados por sus SHA.

La comparación AST confirma que `Counters` del `solve.py` original es igual a la clase de nivel de módulo en el driver cacheado y que el cuerpo de `process_memory()` después de retirar esa clase es idéntico al cuerpo de `_cached_process_memory()`. El único cambio de comportamiento en el driver es que `_memory_snapshot()` delega al helper cacheado. El diff restante añade el pin y la entrada al readset de `AMENDMENT_CACHED_TELEMETRY.md`. El consumidor cambia exactamente dos líneas: ruta `SOLVE_DRIVER` y SHA fijado; no hay cambios de gates.

En un proceso GIS Python 3.12.14 x64 fresco, ejecuté el AST exacto de la clase/helper cacheados 10.000 veces, sin importar el driver ni invocar `main()`/`solve()`. Duró 0,1923 s; `_pointer_type_cache` pasó de 3 a 4. La API devolvió las cinco claves esperadas y su medición registró working set actual 25.051.136 B, pico 27.312.128 B y `PeakPagefileUsage` 19.099.648 B. No superó 30 s ni 256 MiB.

El ABI concuerda con el SDK Windows local: `Psapi.h:466–477` define `PROCESS_MEMORY_COUNTERS` como dos `DWORD` seguidos de ocho `SIZE_T`; la firma de `GetProcessMemoryInfo` en `Psapi.h:520–526` recibe `HANDLE`, `PPROCESS_MEMORY_COUNTERS` y `DWORD`. En el intérprete probado, `c_ulong=4 B`, `c_size_t=8 B`, `Counters=72 B`; offsets observados coinciden con la definición C. `ctypes/__init__.py:255` importa `_pointer_type_cache`; `:307–313` documenta en la implementación local cómo la caché retiene la clase y el tipo de puntero.

Pins verificados: solver congelado `7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149`; driver base `9f4fc8e5edc2ad7a8276264d4b6fea05ee8682b777d370cb75a283f0cb4d296e`; driver cacheado `5e75e0e1d3e3c6938679cd31e87f4f317353e64ff919c471d79d1a04d50f98f9`; consumidor `3e7a6996f5e4b637ba7d94ad20dd3add6643f52db31d7098c6baa32e238d4799`; enmienda `d64ad4441348bb2054800851cf7ef19f5f143143d62b93e0659de804b2565f7a`.

La verificación no confirma convergencia ni el presupuesto de memoria del solve real. Mide el helper en aislamiento. El campo existente `peak_commit_bytes` corresponde a `PeakPagefileUsage`; no es una medida de RSS.

Evidencia: `review.json` SHA-256 `b6eb9f3c20650059e00209dd675934a6b9a900b639111ee88d357efe11412048`; script de revisión/sonda `review_cached_telemetry.py` SHA-256 `7978b25681d0baf086f815524878424991ea107ac0ba0ef28b54048f2cfdd125`.
