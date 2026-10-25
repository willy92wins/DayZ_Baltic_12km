# EV112 — navegación propia de F y cobertura del parche
Continuación de la unidad de navegación de E, dentro de P10/P12 y la petición
viva de continuar autónomamente. Codex ejecuta e integra; Fable5.1 revisa este
plan. Revisión Fable: SOUND-with-fixes; esta revisión del diseño incorpora sus
correcciones. Aún falta la nueva criba de ambas bandas, congelar referencias y
probar el preparador/puerta auxiliar antes de ejecutar. La visita personal sigue
pendiente y no se inicia un cliente sin Guillermo.

[EXACT] F pasó4749 controles de servidor. Terreno merged
caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc;
mundo4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38.
Sus94 vértices nuevos están en X2892..2958/Z6804..6870. La navegación aceptada de E
pertenece a otro WRP y no se atribuye a F. E se fija como terreno
705196d69646f2528aa5796d26e90bab36aebd07a5a0ddb861b31b7160f4a33e.
WRP compilado F:0139cd1a7ce360436e474fa6448470dfe93bf34a21229b6cf44f4e839af54126.
Agua97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43
y piloto c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87
se fijan en la generación de F y deben coincidir con el stack real de su run.
Config.bin extraído de E y F es idéntico (fe50a16944dc9c0dc64a05f53ba16de82af503e5a40d00e86ed5905ddc7170e3);
el texto decodificado también (cd4a781dafb1422385663b0a81490f2759cb9015c7518d0ab0fa15128a801601).
package-rectangle-f/config.cpp:64-67 conserva tileWidth12.5 y cellSize0.25/0.1/0.1.
Esta igualdad compara los paquetes finales E3a285df/F4e5f909, después de inyectar
la clase Navmesh. No compara el config contra el PBO crudo1db792f de Binarize.
La sustitución siguiente solo cambia NM respecto al paquete final F4e5f909.

[EXACT] Herramientas ya ejecutadas sobre E:
- tools/navigation/generate_navmesh_console.py:48 exige salida nueva y límite<=7200s;
  :60 comprueba SHA de entradas. Pasar --timeout-s 7200 explícito (default1800). Generador1.30 SHA66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7.
- tools/navigation/prepare_current_nav_probe_ev112.py:17 mantiene XZ/expectativas
  y recalcula únicamente Y nativa; conserva las cotas físicas de los puentes.
- tools/terrain/v30_common.py:19 usa la rejilla nativa z=12282-6r y diagonal NO-SE.
- missions/BalticV30ContinuityNavV1.BalticTrial/init.c:41-44 conserva SampleNavmeshPosition
  y FindPath con sus filtros. La fuente definitiva con temporales escalares ya
  pasó C37. SHA de init.c: f737ed906069ba73207e3f19ce76dd993f4ba67f43ac21a19a0bb35bbdf5973b.
  No se añaden APIs del juego.
- tools/navigation/verify_continuity_nav_v30.py:16 y tools/terrain/verify_v30_acceptance.py:18
  conservan las expectativas positivas/negativas, posición y distancia a superficie.

[DESIGN] Preparación y presupuesto:
1. A/B de E ya completo e independiente de F. Congelar los tres PBO de F,
   comprobar contenido config.bin contra los bytes extraídos y guardar identidades
   de ejecutable real y de proceso MCP como esquemas distintos. No tocar parámetros.
2. Mantener las37 consultas existentes. Añadir4 recorridos locales, cada uno
   dividido en dos consultas por un punto intermedio:45 consultas totales.
   R=E:/DayZ-Baltic-Build/shape-repair-20261025. R/f-nav-route-discovery.json conserva
   las primeras líneas rechazadas por aproximarse al agua. R/f-nav-dry-corridors.json
   conserva alternativas iniciales elegidas solo con terreno y agua E/F:
   EW(2886,6828)->(2946,6828); NS(2934,6804)->(2934,6864);
   NE/SW(2910,6804)->(2958,6852); NO/SE(2898,6876)->(2958,6816).
   Fable detectó que floor solo comprobó un lado de las líneas sobre la rejilla.
   Son hipótesis, no referencias definitivas. Rehacer la criba ANTES del motor:
   banda de2.1m a ambos lados y extremos (un rectángulo con extremos cuadrados
   puede contenerla conservadoramente); incluir TODAS las celdas que la toquen,
   incluso las adyacentes a líneas de rejilla/diagonales. Exigir todas sus esquinas
   secas en E y F, margen>=0.05m y cruce de celdas con delta>=0.1m. Guardar criba
   original y nueva, política y coordenadas resultantes. No demuestra ausencia
   de objetos3D. Ninguna coordenada se escoge usando resultados del motor.
3. Elegir el punto intermedio antes de ejecutar: muestreo<=1m de cada línea,
   distancia>=6m a sus extremos, dentro del parche y delta absoluto>=0.1m.
   Preferir el máximo delta. Comprobar además un disco2.1m alrededor del punto
   con muestras<=0.5m: seco en E/F y delta>=0.05m. Este disco cubre la tolerancia
   de ajuste de extremo del consumidor. Si no hay punto admisible, preparación
   INCONCLUSA; no reducir el margen ni elegir según resultados del motor.
   El muestreo de delta del disco es una criba, no una garantía continua; la puerta
   comprobará los waypoints reales. Registrar además pendientes locales de E/F como
   diagnóstico (config conserva maxSlope60/maxStepHeight0.45, sin modificarlos).
   Un preparador explícito combinará exactamente37 casos heredados y8 nuevos
   expect=path de un JSON congelado; comprobar tamaño, nombres únicos y cada
   consulta heredada completa, sin confiar únicamente en zip. E y F usarán nombres
   de misión, log y referencias distintos. Congelar coordenadas, terreno, CSV,
   init.c y expectativas antes de ambos runs.
4. Medir la referencia E con su NM9 y las45 consultas. Conservar cualquier fallo.
   No retirar ni mover consultas después de ver resultados. Comparar luego F
   usando los mismos XZ/expectativas y Y propias. El agua permanece idéntica.
   Taxonomía previa: nueva consulta que falla en E y F=INCONCLUSO, unidad noPASS;
   pasa en E y falla en F=FAIL de regresión; falla en E y pasa en F=resultado nuevo
   documentado, sin atribuir causa interna. Falta de evidencia/identidad=FAIL de
   evidencia. La unidad soloPASA si F supera45 consultas y su cobertura.
5. Generar F en servidor de datos propio, lease/heartbeat y una salida nueva,
   un intento<=7200s. Mantener hashes de mundo/piloto/agua y código durante todo
   el cálculo. Cierre orderly/release/status por MCP; nunca cerrar runs ajenos.
   Si falla, conservar diagnóstico, sin repetición ciega ni ampliar el presupuesto.
6. Inspeccionar TESM9/VAND12, todas las966289 teselas de12.5m y cuadrícula983x983.
   Reempaquetar sustituyendo solo el NM; exigir las otras6826 entradas exactas,
   WRP exacto y stack piloto/agua idéntico. El PASS físico4749 corresponde al WRP
   0139cd1 y esos mismos contenidos, no al SHA del PBO nuevo; registrar la equivalencia
   y que no se repite la sonda física. No redistribuir recursos vanilla.
7. Servidor normal F sin startNavmeshDataServer: fijar al lanzamiento el SHA real
   del PBO nuevo que contiene WRP F y NM F y los otros paquetes. El delta de terreno
   no prueba por sí solo la identidad del NM. Ejecutar45 consultas y el consumidor
   existente sin relajar umbrales. Puerta adicional: recibir resultado PASS del
   consumidor, su log vinculado y ambos NPZ E/F fijados por SHA. Para cada uno de
   los8 nombres nuevos debe existir una fila P real cuyo XZ tenga
   abs(tri_sample(E)-tri_sample(F))>=0.05m; el consumidor previo ya comprueba SurfaceY
   contra F. Un resultado FAIL nunca podrá superar esta puerta, aunque haya deltas.
   Esto acredita muestreo del parche; no acredita locomoción ni seguimiento entre waypoints.
   Tests: puntos externos al parche, caso ausente, delta0.03, y consumidor FAIL
   con deltas válidos. Caso/identidad malformados=FAIL; cobertura insuficiente
   con sonda válida=INCONCLUSO y unidad noPASS.

PASS de esta unidad requiere generación/estructura/paquete/identidades estables,
45 consultas válidas incluidas las negativas y cobertura local. Guardar E/F y
resultados completos; discrepancias son FAIL o INCONCLUSO explicado, nunca eliminar
el caso. El A/B previo sigue perteneciendo a E. No extrapolar FPS, IA, capacidad,
contacto cliente, revisión visual, bosque de borde ni cierre global de EV112.
