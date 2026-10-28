Revisión de plan B3E. Veredicto: **SOUND-with-fixes**. El diseño es correcto en alcance, aislamiento y límite de 60 s, pero tal como está puede terminar en HASHES_MATCH rápido sin localizar nada, porque no reproduce la carga real del consumidor ni cubre todas las fases posteriores al log oficial.

**Riesgos concretos**

- **El log oficial no lleva marcas de tiempo.** Nada demuestra que las líneas 76-79 (importar módulo, `main`, `validate_p_mods`, `find_dayz_tools`) no consumieran la mayor parte de los 60 s. Si la lectura de los cinco archivos termina en pocos segundos, la hipótesis queda debilitada y el siguiente candidato es la fase oficial, no el hash. El plan no prevé esa lectura del resultado.
- **Multiplicidad de lecturas.** El consumidor hashea Binarize hasta tres veces (línea 83 si está en `tools_sha256`, y dos veces en línea 86 por el doble `sha(p)`), y config.cpp dos veces. Una lectura única subestima la carga en factor 2-3.
- **Patrón de lectura distinto.** `sha()` del consumidor no se ve en el ancla. Si lee el archivo entero en memoria (coherente con el pico de 86 MB frente a 24.8 MB de Binarize), el diagnóstico por bloques no reproduce el mismo coste ni el mismo pico.
- **Fase omitida.** Entre el log y los hashes están los cuatro `is_dir` sobre P: (línea 81). Son baratos en teoría, pero están dentro de la ventana sospechosa y no se cronometran.
- **Caché de página.** El intento anterior ya calentó los archivos. Una lectura rápida hoy no excluye un bloqueo de primera lectura o de escaneo en acceso en el intento previo. El plan lo insinúa, pero debe quedar como límite explícito del recibo.
- **Hashes esperados de los recibos.** El plan dice que los dos recibos van fijados por SHA256, pero no indica de dónde salen esos valores esperados. Si el propio script los calcula, la fijación es circular.

**Modificaciones mínimas**

1. Registrar por fase: inicio, primer bloque, fin, bytes y duración, y añadir una fase cronometrada de `stat`/`is_dir` sobre P:/DZ, P:/bin, P:/core y P:/scripts, sin recursión.
2. Leer cada archivo con la misma multiplicidad que el consumidor (Binarize ×3, config.cpp ×2, resto ×1) o, si se prefiere una sola lectura, anotar la multiplicidad en el informe y extrapolar explícitamente. Recomiendo lo primero: sigue siendo sólo lectura.
3. Fijar el modo de lectura al del `sha()` consumido (bloques o `read_bytes`), tomado del archivo fuente del preparador sin importarlo. Registrar el modo usado en el recibo.
4. Añadir estado de interpretación `HASHES_MATCH_FAST`: hashes coinciden y la suma de fases queda muy por debajo del presupuesto. Significa que esta fase no explica sola el agotamiento y que el siguiente diagnóstico debe cronometrar la fase oficial con un plan propio. No implica entorno válido.
5. Escribir los SHA256 esperados de los dos recibos en el plan o como argumentos del padre, nunca calculados por el hijo.
6. Vaciado de eventos con `flush` más `os.fsync` por evento, no sólo `flush`.
7. Timeout parametrizable sólo hacia abajo para tests (valor por defecto 60, sin opción de subirlo); el censo real usa el defecto.

**Estado exacto**

B3E sigue INCONCLUSIVE_RESOURCE, 41 tests PASS y revisión adjudicada. Este diagnóstico no lo reclasifica ni certifica el preflight. B3D permanece OFFLINE_CANDIDATE_ONLY. Sin build, sin lease, sin tocar P: ni skills.

**Tests necesarios, suite ≤30 s con archivos temporales**

- Positivo: cinco archivos con hash correcto, fases completas, duración registrada.
- Mismatch: un archivo alterado, salida con ruta/esperado/observado y bloqueo.
- Ruta ausente y ruta fuera de las cinco permitidas, rechazada antes de leer.
- Error de E/S o permiso, clasificado INCONCLUSIVE_IO con fases parciales.
- Timeout: hijo de prueba lento con timeout de 1-2 s, verificar que sólo muere ese hijo, que el último evento persistió y que no hay reintento.
- Recibo con esquema, formato o hash incorrecto, resultado inconcluso.
- Verificar que el hijo no crea procesos descendientes y que los recibos originales no cambian de bytes.

**Límites de esta revisión**

No se ha visto `sha()`, `meter` ni el contenido de `tools_sha256`, así que el conteo de lecturas es inferido del ancla. No se afirma causalidad del agotamiento. Resultado rápido o lento de la nueva lectura sólo informa sobre hoy, no sobre el intento de 60.047 s.

FIN_REVISION