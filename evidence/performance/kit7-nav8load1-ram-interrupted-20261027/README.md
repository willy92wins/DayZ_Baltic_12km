# Nav8Load1: bloque RAM interrumpido, sin aceptación

**INCONCLUSIVE_INTERRUPTED_RAM_BLOCK.** Dos mediciones válidas y cerradas,
de las seis planificadas. La tercera no arrancó: MCP informó port_in_use_foreign,
run_id nulo. No se interrumpió ninguna sesión ajena. Después, session_status
confirmó lease propio ausente, cero comandos pendientes y ningún run propio.

Medianas descriptivas, sin comparador de aceptación:
- Baltic: residente4254,57MiB, privada4649,21MiB.
- Chernarus: residente3349,37MiB, privada3733,76MiB.

No se calcula un PASS/FAIL agregado con una sola muestra por mundo. Se conserva
el fallo de admisión y los dos resultados completos. No se ejecutaron pasadas4-6,
no hay repeticiones ni sustitución de una medida. El bloque original queda
cerrado como incompleto; no puede rellenarse posteriormente. Reanudar requiere
un plan revisado y un bloque íntegramente nuevo, conservando estos datos.

Los 80 controles de admisión verifican identidad conjunta, cobertura de fuentes,
hashes de revisión y reservas exclusivas. RAM1,10, dispersión5%, calentamiento30s
y medida120s permanecen. El PASS nativo de configuración y607 no cambia.
Las fuentes exactas usadas se conservan en frozen-inputs y frozen-input-map.json.
No se incluyen nombres de aplicaciones ajenas ni sus snapshots privados.
