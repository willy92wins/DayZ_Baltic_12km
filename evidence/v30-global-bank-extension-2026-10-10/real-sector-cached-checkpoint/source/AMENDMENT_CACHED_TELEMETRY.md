# Enmienda de instrumentación del piloto real

Decisión del integrador, 2026-10-10: corregir el mecanismo de medición de memoria antes de una sola ejecución adicional del mismo sistema. Es una corrección de instrumentación dentro del trabajo autónomo solicitado; no cambia el diseño del terreno ni los criterios de aceptación.

El intento original `solve-run-01` terminó RESOURCE_LIMIT tras 265.0815597 s, con pico de working set de 1,614,667,776 B y sin estado numérico ni candidato. Su resultado SHA-256 es `eedb911f07a4feb3c8ff0e9936dd9c6ad547cd7d92e057ac90de72bc1ae16d5f`. Se conserva completo; no se sobreescribe ni se declara inválido retrospectivamente.

El aislamiento `telemetry-pointer-cache/findings.md` SHA `9a04dc37c1957c2747dc3240dae72467425be405123473b0b9d9759e2dfd85c7` y `attempt-03/summary.json` SHA `e426fd1644d68a1d390a4c04a3d78947c36df32f88c8f350de347036690fa199` prueban que la clase Counters anidada crea 10,000 tipos retenidos y unos 54 MB de memoria privada en 10,000 llamadas. Elevar la misma clase a módulo reduce el crecimiento a una entrada y cero bytes privados observados. No se atribuye a esta fuga la totalidad del pico del solver.

Cambio permitido: copiar el driver original 9f4fc8e5edc2ad7a8276264d4b6fea05ee8682b777d370cb75a283f0cb4d296e a `solve_real_sector_cached.py`; usar el mismo helper GetProcessMemoryInfo con Counters definido una vez a nivel de módulo. Su ABI y semántica permanecen idénticos. Conservar el solver numérico 7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149 sin modificación. Incluir esta enmienda en el readset del nuevo driver.

Se conserva íntegramente PLAN_REAL_SECTOR.md 14f02179312bc25caf76a087cc873122caed30f6092464f1c01ac7572d519749: ventana, 40,512 variables, matrices y restricciones, fuentes y selección de seed, tolerancias, máximo 10,000 iteraciones, 600 s, 1.5 GiB de working set y mínimo 3 GiB libres. No hay cambio de alpha, dominio, protecciones, función objetivo o presupuesto. El tope de una ejecución del plan original se sustituye únicamente por una ejecución corregida adicional tras revisión; no se crea un bucle de variantes.

Antes del cálculo: preflight nuevo, demostrar que todos los arrays preparados son idénticos al primer intento, revisar el diff limitado y reconstruir el sistema con consumidor independiente. El consumidor nuevo deriva del 703f29380b0359df61a3d699573d68c6abdbe7a9688806e5c09867fd787a343e y cambia solo ruta/hash del driver. La reproducción de KKT existente conserva su significado numérico.

Una sola llamada adicional en `solve-run-02`. Si no converge, falla forma/agua o rebasa un límite, conservar diagnóstico y no relajar parámetros ni repetir automáticamente. Convergencia no es aceptación: candidato pendiente del consumidor, forma, agua, civil y D8. Ningún resultado equivale a aceptación global ni a validación gráfica de DayZ.
