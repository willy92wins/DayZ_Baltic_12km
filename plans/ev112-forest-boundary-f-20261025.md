# EV112 — medición pendiente del borde forestal sobre F

Continuación autorizada del council y de boundary-recheck-20261024: ejecutar la
sonda pendiente sobre el candidato actual, sin eliminar árboles ni presumir el
comportamiento del motor fuera de la rejilla. Codex ejecuta e integra; revisión
acotada independiente por Fable5.1 mediante delegar antes del motor.

[EXACT] prepare_forest_boundary_probe_v31.py ha leído el WRP F
6e649b72bf4ec6789a83050f21b7e5597de417e14f251f854728eb20d8b84bd8 y producido
3727 objetos /269968 puntos. CSV486839035e62ddf90a026604ef44df08523826255e60cc20e542985442a09020,
idéntico al preparado histórico de R. No basta por sí solo para afirmar igualdad
de raíces/radios/embebido: se compararán también los registros completos.
Terreno F caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc.
Preparación local: E:/DayZ-Baltic-Build/shape-repair-20261025/forest-boundary-full-f.

[EXACT] El lector esperaba 0/1 aunque el emisor concatena bool. La captura nativa
histórica boundary-probe.log contiene true/false, igual que E45 actual. La prueba
extrae altura, booleanos y reloj de dos filas originales y adapta únicamente la
envoltura al esquema forestal; no se presenta como una captura forestal nueva.
El lector corregido exige true/false exactos y rechaza alias, NaN, IDs duplicados,
ausentes, UUID ajeno o reloj decreciente. Tolerancias sin cambio: raíz0.005m,
apoyo0.01m, margen no-pond>=1.0m. El emisor Enforce no cambia.
Firmas SurfaceY/SurfaceIsSea/SurfaceIsPond: P:/scripts/3_Game/global/game.c:1176,
1196,1197, comprobadas y consumidas en las capturas existentes.

[DESIGN] Una ejecución, máximo900s de captura tras el lanzamiento:
1. Conservar preparación original y fijar PBO real antes del lanzamiento. Si se
   usa F con NM9 nuevo, solo actualizar esos hashes tras comprobar las6826 entradas
   restantes y WRP idénticos; CSV/objetos/puntos/UUID/fuente de misión inalterados.
2. Banco libre por session_status. Lanzador oficial, servidor sin cliente, sin
   startNavmeshDataServer. Lease/heartbeat, identidad PID+creation+hash de archivo,
   stack world/pilot/water/MCP, binding actual BOUND. Nunca tocar runs ajenos.
3. Captura BEGIN269968/END269968 y UUID84936372-1378-44a6-823e-df7829724b7b,
   mtime posterior a creación del proceso. Conservar el log previo si existe;
   nombre de misión y UUID impiden aceptar una ejecución ajena. Archivar RPT.
4. Cierre orderly, release y session_status. Recalcular hashes de paquetes,
   fuente/CSV/identity.txt y consumir con eval_forest_boundary_probe_v31.py.
5. Un contraejemplo de raíz/apoyo/agua es FAIL medido y se localiza por objeto;
   preparar su corrección separadamente antes de cambiar geometría. Una captura
   incompleta/ajena/malformada es FAIL de evidencia. Cero contraejemplos solo es
   SAMPLED_BOUNDARY_CLEAR: el disco continuo y el bosque completo siguen INCONCLUSOS.

No cambiar posiciones, alturas, escalas, radios, agua, reservas ni umbrales en
esta unidad. No repetir la sonda buscando otro resultado. No atribuir locomoción,
visual, densidad, FPS ni capacidad a medidas SurfaceY. Preservar fallos y fuentes.

## Ajuste de ejecución tras la interrupción de NM F, 25-10 22:20 UTC

La generación F quedó incompleta al63% y su servidor terminó. No se empaqueta ni
se acepta ese NM. Para desacoplar esta medición, se usa el F original4e5f909 con
startNavmeshDataServer, igual que su prueba física4749 ya completada. Se sustituye
solo el modo previsto en el punto2; no se lanza un generador durante esta sonda.
El consumidor mide SurfaceY/IsSea/IsPond, sin APIs de navegación. Se fijan los tres
PBO originales y el manifiesto de preparación sin modificar ningún campo. El
recibo y la comprobación de identidad exigen explícitamente ese flag activo.
Este resultado no permite afirmar carga normal de NM ni aceptación de IA.

## Resultado de esta unidad — 25-10-2026

Sonda nueva completa269.968puntos/3.727árboles: SAMPLED_BOUNDARY_CLEAR, cero fallos de raíz/apoyo/margen de agua. Error raíz máximo0,00005752m. Modo data-server sin cliente, sin aceptación de disco continuo, navegación ni bosque global. Evidencia: [quality-continuation](../evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/quality-continuation-20261025/README.md).
