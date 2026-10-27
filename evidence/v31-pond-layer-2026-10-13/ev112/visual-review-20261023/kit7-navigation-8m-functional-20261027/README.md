# Kit7: las cuatro alturas corregidas y 607 consultas nativas verificadas

El cambio funcional reduce GenParams.tileWidth de 12.5 a 8 m. La referencia,
coordenadas, filtros y tolerancias siguen idénticos: altura 0.801 m,
terreno 0.011 m y corredor 2.1 m. El resultado nativo es PASS_KIT7_NATIVE_GRAPH:
607 consultas, cero height_issues y cero local_failures. El FAIL anterior y
sus cuatro casos se conservan en kit7-navigation-runtime-20261026.

Generación propia `0db37e43-0bd0-4ac6-8b03-bc85daf9d5b2`, terminada `2026-10-27T05:39:12.980936+00:00`.
TESMv9/VAND12 inspeccionado: 2359296 teselas y
1338007300 bytes. La malla se empaqueta preservando6826 entradas
restantes, WRP, piloto y agua. La configuración de 8 m y su receta se archivan aquí;
los grandes binarios y los paquetes vanilla permanecen fuera de Git.

La generación recuperó un lease caducado sin reiniciar ni cancelar su proceso.
Se conservan el intento de cancelación no ejecutado, sus recibos de error y
la recaptura del mismo PID/creación/comando. El adaptador revisado clasifica
solo ese evento, conserva el registro original y exige finalización con código 0
y los controles originales de cierre, observador y RPT. Se mantuvieron el tiempo
y las tolerancias. Los registros de cola con sesiones ajenas se conservan localmente.

Esto valida el grafo y sus alturas en las 607 rutas, no locomoción de actores,
barcos, visual humana, FPS o aceptación global. La RAM de este paquete8m
todavía debe medirse frente a Chernarus con 6 pasadas nuevas ABBAAB, 30+120 s,
presupuesto 1.10 y dispersión 5 %. La preparación sellada y los controles sintéticos
incluidos no son mediciones nativas ni heredan el benchmark anterior.

Siguen pendientes los otros sectores y el censo global; el piloto híbrido de
14 vértices continúa sin integrar. Se conservan todas las protecciones aprobadas.
