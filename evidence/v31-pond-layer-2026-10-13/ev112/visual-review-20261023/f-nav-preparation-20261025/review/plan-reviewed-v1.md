# EV112 — navegación propia de F y cobertura del parche
Continuación de la unidad de navegación de E, dentro de P10/P12 y la petición
viva de continuar autónomamente. Codex ejecuta e integra; Fable5.1 revisa este
plan. La visita personal sigue pendiente y no se inicia un cliente sin Guillermo.

[EXACT] F pasó4749 controles de servidor. Terreno merged
caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc;
mundo4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38.
Sus94 vértices nuevos están en X2892..2958/Z6804..6870. La navegación aceptada de E
pertenece a otro WRP y no se atribuye a F.
Config.bin extraído de E y F es idéntico (fe50a16944dc9c0dc64a05f53ba16de82af503e5a40d00e86ed5905ddc7170e3);
el texto decodificado también (cd4a781dafb1422385663b0a81490f2759cb9015c7518d0ab0fa15128a801601).
package-rectangle-f/config.cpp:64-67 conserva tileWidth12.5 y cellSize0.25/0.1/0.1.

[EXACT] Herramientas ya ejecutadas sobre E:
- tools/navigation/generate_navmesh_console.py:37-46 vincula run-id y PBO por SHA,
  salida nueva y límite <=7200s. Generador1.30 SHA66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7.
- tools/navigation/prepare_current_nav_probe_ev112.py:17 mantiene XZ/expectativas
  y recalcula únicamente Y nativa; conserva las cotas físicas de los puentes.
- tools/terrain/v30_common.py:19 usa la rejilla nativa z=12282-6r y diagonal NO-SE.
- missions/BalticV30ContinuityNavV1.BalticTrial/init.c:41-44 conserva SampleNavmeshPosition
  y FindPath con sus filtros. La fuente definitiva con temporales escalares ya
  pasó C37. No se añaden APIs del juego.
- tools/navigation/verify_continuity_nav_v30.py:16 y tools/terrain/verify_v30_acceptance.py:18
  conservan las expectativas positivas/negativas, posición y distancia a superficie.

[DESIGN] Preparación y presupuesto:
1. Terminar/publicar el A/B de servidor vacío de E. Congelar los tres PBO de F,
   comprobar contenido config.bin contra los bytes extraídos y guardar identidades
   de ejecutable real y de proceso MCP como esquemas distintos. No tocar parámetros.
2. Mantener las37 consultas existentes. Añadir4 recorridos locales, cada uno
   dividido en dos consultas por un punto intermedio:45 consultas totales.
   R=E:/DayZ-Baltic-Build/shape-repair-20261025. R/f-nav-route-discovery.json conserva
   las primeras líneas rechazadas por aproximarse al agua. R/f-nav-dry-corridors.json
   fija alternativas elegidas solo con terreno y agua E/F, antes de cualquier consulta:
   EW(2886,6828)->(2946,6828); NS(2934,6804)->(2934,6864);
   NE/SW(2910,6804)->(2958,6852); NO/SE(2898,6876)->(2958,6816).
   La criba exige todas las esquinas de las celdas recorridas secas en E y F,
   margen>=0.05m, y cruza celdas con delta>=0.1m. No demuestra ausencia de objetos3D.
3. Elegir el punto intermedio antes de ejecutar: muestreo<=1m de cada línea,
   distancia>=6m a sus extremos, dentro del parche y delta absoluto>=0.1m.
   Preferir el máximo delta. Comprobar además un disco2.1m alrededor del punto
   con muestras<=0.5m: seco en E/F y delta>=0.05m. Este disco cubre la tolerancia
   de ajuste de extremo del consumidor. Si no hay punto admisible, preparación
   INCONCLUSA; no reducir el margen ni elegir según resultados del motor.
   Congelar coordenadas, terreno, CSV, código y expectativas antes de ambos runs.
4. Medir la referencia E con su NM9 y las45 consultas. Conservar cualquier fallo.
   No retirar ni mover consultas después de ver resultados. Comparar luego F
   usando los mismos XZ/expectativas y Y propias. El agua permanece idéntica.
5. Generar F en servidor de datos propio, lease/heartbeat y una salida nueva,
   un intento<=7200s. Mantener hashes de mundo/piloto/agua y código durante todo
   el cálculo. Cierre orderly/release/status por MCP; nunca cerrar runs ajenos.
   Si falla, conservar diagnóstico, sin repetición ciega ni ampliar el presupuesto.
6. Inspeccionar TESM9/VAND12, todas las966289 teselas de12.5m y cuadrícula983x983.
   Reempaquetar sustituyendo solo el NM; exigir las otras6826 entradas exactas,
   WRP exacto y stack piloto/agua idéntico. No redistribuir recursos vanilla.
7. Servidor normal F sin startNavmeshDataServer: ejecutar45 consultas y el consumidor
   existente sin relajar umbrales. Puerta adicional de cobertura: para cada uno de
   los8 tramos nuevos, al menos un waypoint real debe mostrar diferencia E/F
   de terreno>=0.05m y el consumidor ya debe probar SurfaceY contra F.
   Esto acredita muestreo del parche; no acredita locomoción ni seguimiento entre waypoints.
   Tests de esa puerta contra puntos externos al parche, casos ausentes y delta insuficiente.

PASS de esta unidad requiere generación/estructura/paquete/identidades estables,
45 consultas válidas incluidas las negativas y cobertura local. Guardar E/F y
resultados completos; discrepancias son FAIL o INCONCLUSO explicado, nunca eliminar
el caso. El A/B previo sigue perteneciendo a E. No extrapolar FPS, IA, capacidad,
contacto cliente, revisión visual, bosque de borde ni cierre global de EV112.
