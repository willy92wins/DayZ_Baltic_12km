# Kit7 — alturas y apoyos nativos verificados

El paquete mundo `10e09e3f…` con piloto `46244e7f…` pasa dos sondas nuevas en DayZ 1.30, sin cliente. No se heredan resultados de F.

- Alturas: **11.052/11.052**, todos los **3.430 vértices modificados** y **7.622 centroides de triángulos incidentes**. Cero fallos; diferencia máxima **0,0001861622 m** (0,19 mm), umbral 0,01 m.
- Bosque de frontera: **3.727 objetos / 269.968 muestras**, cero fallos de raíz, apoyo o margen con agua. `SAMPLED_BOUNDARY_CLEAR` describe muestreo finito; no acepta el disco continuo ni todo el bosque.
- UUID, CSV, fuentes, paquetes, run, PID/creación y puente ligados a cada log. Las dos sesiones cerradas por MCP; lease liberado, sin comandos pendientes ni cleanup degradado.
- **19 tests** pasan. Fable 5.1 por CLI emitió SOUND-with-fixes; corregidos sus hallazgos, con negativo real de Python optimizado y del productor cambiado incluso actualizando su hash.

El preflight rechazó primero la ruta con separadores `/`; el contrato exige la forma Windows normalizada. Con esa forma, ambos preflights y lanzamientos pasan. No se modificó la política del launcher. Las sondas usaron DataServer como la referencia F, porque este paquete conserva NM6; **navegación sigue pendiente**.

Los RPT tienen avisos de recursos sin render, stack GetPlugin de diagnóstico y avisos de limpieza también observados en F. Se publican los diagnósticos y hashes; no se afirma log limpio. La misión completó todos los puntos y ambos cierres terminaron correctamente.

Siguiente: ligar los 2.050 puntos de agua/colisión nuevos al paquete combinado, verificar cobertura de las 139 piezas/138 juntas y todos los controles laterales frente al agua completa, añadir regresión de los 4.749 puntos F y calibración física nueva. El descubrimiento conserva las expectativas F (ninguno cae sobre geometría nueva), pero aún no autoriza el lanzamiento combinado.

La navegación propia, vista conjunta, conducción, FPS y comparación de rendimiento del candidato siguen pendientes. Los defectos visuales globales de ríos y terreno no se declaran cerrados.
