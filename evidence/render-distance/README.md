# Cuadros azules y discontinuidad a distancia

2026-09-29. **CORREGIDO EN LAS CUATRO VISTAS ENSAYADAS, SAT1M.**
Los cortes originales se reproducen con el baseline y desaparecen al regenerar
el satélite a1m/píxel con capa48m. Ver resultado al final y sat1m-fixed-0..3.jpg.
El arte sigue siendo provisional; la revisión regional es un gate separado.

## Evidencia actual

| Comprobación | Resultado y límite |
|---|---|
| Baseline de navegación propia | SHA256 `3c3a2f0e649b13e73d483e027f3f3e50db58005848c85beb75321c7a50aa078f`. Estado desplegado vivo en `runtime.json`. |
| Sonda real de misión contra ASC corregido | 612 muestras; G máximo 0,004899957 m; P 0,002518691 m; E 0. Ambos accesos y tablero a 2 m. No demuestra geometría visual de LOD distante. |
| Control negativo: ASC anterior al arreglo de agua | Rechazado: G 0,586599998 m. El FAIL de la comparación contra V3 antigua se explica por una referencia anterior; no acredita regresión actual. |
| Texturas compiladas | 50 PAA, 400 niveles mip decodificados; dimensiones esperadas, satélites opacos. No demuestra selección de tiles por el motor. |
| Asignación nativa de satélite | 1.048.576 celdas de 12 m; 367 materiales; cero discrepancias entre posición de celda, nombre de material y Stage0. No analiza el quadtree compilado ni el render. |
| Resolución/artwork | `tools/prepare_prototype.py:118–123`: colorización WorldCover de 2048², 6 m/píxel. Sigue siendo una maqueta, no imagen aérea final. |

La textura MCO usada es la misma ruta que usa Chernarus, decodifica como ruido
gris opaco. No se ha demostrado que cause los grandes cuadros azules. Las franjas
estiradas de los tiles exteriores también existen en el PNG fuente; corresponden
al padding exterior, no prueban un fallo dentro del mapa.

Captura lejana del usuario: cámara (2698.90, 643.67, 6180.53), dirección
(-0.387, -0.736, 0.555). El círculo rojo identifica el puente. Las capturas originales
y sus hashes se conservan en la entrega `outputs/baltic-render-distance`.

## Prueba magenta ejecutada

`tools/playtest/build_sat_water_diagnostic.py` produjo una copia que reemplaza el
azul de agua pintada por magenta. ImageToPAA convierte los 25 satélites, Binarize
regenera solo texHeaders y FileBank empaqueta. Se comprobó el contenido del PBO:
solo cambian 25 S_*.paa y texHeaders.bin; se conservan byte a byte los restantes
395 archivos, incluido WRP, navmesh, máscaras, materiales y config.

- Candidato SHA256: `cc99a661bed81c02df0705c3955b9a77cc60ba0b30874f8d7a471c3d09deb6ee`.
- Se han decodificado 1.378.491 píxeles magenta; satélites opacos.
- Se cargó en el run `07d46fa5-c6e3-4bda-8dc4-7ede923849d7`.
- El usuario colocó la cámara aérea. `magenta-aerial.jpg` muestra grandes áreas
  magenta y cortes rectangulares; el satélite participa en la discontinuidad.
- La captura no muestra coordenadas y no reproduce exactamente la cámara inicial:
  no es una comparación píxel a píxel ni prueba que toda el agua sea incorrecta.
- Cierre normal por MCP, ambas termination_line y exit_metrics_valid. Se restauró
  baseline por hash y se relanzó antes de preparar el siguiente discriminador.
- **No es una corrección para jugar**; ya retirado del despliegue.

La observación cercana previa mostraba agua con olas y magenta a distancia. La
vista aérea aporta el discriminador de satélite, pero el mecanismo preciso
de selección/UV/LOD sigue sin aislar.

## Segundo discriminador: Stage0 global

Plan: `plans/distant-satellite-ab.md`. `build_global_sat_diagnostic.py` descompila
los 367 materiales reales con CfgConvert, cambia solo Stage0/TexGen3 para usar
el satélite completo y verifica la recompilación con el consumidor. Conserva
53 entradas originales, añade un PAA, modifica 367 RVMAT y texHeaders. WRP,
config, navegación, máscaras y detalles intactos. Opacidad 255; error RGB medio
de conversión 1,449/255. Evidencia: `global-sat-package.json` y `global-sat-texture.json`.

Candidato `ed0eaf403dba99a68d59483d0b1ab535d09cb8db8bca6a4ee479fac80688db76`
desplegado para ensayo; run `0c7d3377-5ebb-41a2-9f42-a28ef18a8e65`.
**RECHAZADO VISUALMENTE.** Cámara (2023.47,525.28,7209.79): área blanca y
ausencia de superficie distante; el usuario confirma la regresión. Captura
`global-sat-fail-aerial.jpg`. La lluvia intensa introduce otra variable respecto
al run magenta: no atribuir aún toda la regresión exclusivamente a las UV.
No se editó el proyecto TB ni se modificaron alturas. Rollback baseline preservado.
La adopción para restaurar devolvió `run_protected`; el usuario cerró DayZ y
se restauró baseline3c3a por hash. La variante global está retirada. Después
se ejecutaron cuatro vistas baseline automáticas con clima fijo en run e04d3e75;
cierre normal ylease liberado. Los cuadros se reprodujeron sin lluvia.

## Fuentes y alcance

El autor de un [caso DayZ de tiles cambiantes](https://forums.dayz.com/topic/248690-satellite-tiles-are-randomly-repeatedorderedmessed-up/)
describe una familia de síntomas parecida. Sirve como pista, no como causa raíz
de Baltic. La [documentación de tiling de Pennyworth](https://github.com/pennyworth12345/A3_MMSI/wiki/Mapframe-Information)
explica recorte, solapes y estiramiento exterior en Terrain Builder; su alcance
original es Arma y no valida parámetros DayZ. Consultadas 29-09-2026.

El ensayo SAT1M posterior corrige los grandes rectángulos en las vistas comprobadas. Continúan pendientes cruce
a pie/vehículo, IA útil, CE, agua regional y rendimiento 80–100. El objetivo de
la siguiente prueba es aislar este fallo antes de avanzar con población del mapa.

## Ensayo nativo48m: rechazado

PBO520ef309 conserva config y navegación; geometría completa idéntica. En el
run d3a9ceb0-4154-4360-8af4-351efeebcdec los rectángulos persisten en las vistas
media, lejana e inversa. Evidencia tiles48-fixed-0..3.jpg y tiles48-camera-v2.log.
Clima fijo y cuatro SETTLED confirmados; cierre normal y baseline3c3a restaurado.
No repetir48m como supuesta solución.

## Ensayo SAT1M: preparación (completada)

Plan terrain-sat1m.md. Exportación a546e955 preserva todos los valores de altura
y ambos objetos; sat1m-native.json. Texturas512px, resolución1m/px, capa48m:
4775 RVMAT y2048 PNG. Se compacta la paleta por tile: L00_L02 significa
gravel+grass, no el prefijo gravel+conifer. El helper deriva y cruza la paleta
por todas las variantes hermanas antes de rellenar slots N; rechaza conflictos,
slots irresolubles y texturas distintas de las cuatro vanilla. 3754 materiales,
14192 slots completados; originales respaldados fuera del proyectoTB.
No se considera corrección hasta comparar el render real.

## SAT1M: resultado en motor

PBO5030cb7425621a4c54effdb674a970731377adfdc24feb196ab54da160aa2e2c,
138745891 bytes/6827 entradas. Los4775 RVMAT y2048 PAA reales coinciden con
la salida compilada; config/navmesh idénticos al baseline. Run d1047836-644e-433b-b4e8-b44cf59bf2ce.
Cuatro SETTLED con coordenadas/clima esperados. Vistas media/lejana/inversa
sin los grandes cortes rectangulares del baseline; cercana conserva puente y
orillas. Capturas sat1m-fixed-0..3.jpg y sat1m-camera-v2.log. PASS visual acotado.
El run se cerró por MCP después de las cuatro capturas, antes del temporizador
235s; no hay marcador COMPLETE_RESTORED y no se afirma ese final temporizado.
Cierre normal cliente/servidor, termination_line y exit_metrics_valid. Sonda
retirada por hash y lease liberado; paquete corregido permanece desplegado.

Es una corrección observada al regenerar el satélite1m/px y sus tiles nativos.
No se ha leído el mecanismo interno del renderer, ni se demuestra una regla
universal1m. La colorización WorldCover original sigue siendo provisional y
no se ha auditado visualmente todo el mapa. No se ha alterado la geografía.
