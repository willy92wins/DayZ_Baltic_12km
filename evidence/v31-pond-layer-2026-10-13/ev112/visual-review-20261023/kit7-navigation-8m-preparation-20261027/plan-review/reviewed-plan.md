# Kit7: corregir la aproximación vertical de navegación

Petición de Guillermo27-10: corregir los cuatro fallos, repetir checks sin
rebajar tolerancias y publicar lo validado. Codex ejecuta e integra; Fable
revisa de forma independiente. Alcance: navegación del kit7. P7/P13 y contrato
`ev112-kit7-navigation-consumer-20261026.md`; no cambia geografía ni tránsito.

## Evidencia y cambio propuesto

[EXACT] El runtime4bbd2dce devuelve607conectividad/562corredoresXZ correctos y
cuatro alturas fuera de0,801m. Visual, Geometry y Roadway coinciden a<0,008m en
ocho puntos. Los planos de tres teselas del archivo generado reproducen las
ocho alturas nativas a<4,82e-7m; evidencia publicada en
`../evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-navigation-runtime-20261026/`.

[EXACT] Config desplegado:GenParams.tileWidth=12.5; cellSize1=.25,2/3=.1.
Definición efectiva en checkpoint/diagnosis/deployed-config.cpp:64-67; los
límites12.5m también constan en los encabezados nativos. Generador66935ce8
admite CLIconsole/server_address/reconnect/save_path; no opciónCLI de detalle.

[DESIGN] Variante aislada `tileWidth=8`, conservando todos los demás parámetros.
8m es múltiplo de.25 y.1 y divide12288m. Esperamos1536×1536teselas; comprobarlo,
no aceptarlo por cálculo. No se parchea NM ni se añade un parámetro desconocido.
La estimación offline con dos diagonales por celda reduce el peor error de los
ocho puntos de1,165 a0,779m; no modela contornos ni cuantización y NO acredita
el generador. Archivo local:kit7-nav-tile-width-screen-20261027-v2/result.json.
Reducir a10m no cumplía esa estimación;8m evita inicialmente el mayor coste de6m.

## Ejecución y límites antes de editar

1. Copia aislada del mundo a2919a80. Decodificar config.bin, cambiar únicamente
   tileWidth12.5→8, compilar y decodificar otra vez. Config semánticamente idéntico
   salvo ese valor;6826otras entradas byteexactas, WRP0da63d3f, piloto3d9550bf,
   agua97edcafe. Conservar todos los paquetes anteriores. La física6801 se
   vincula por esas entradas idénticas; no por el hash del contenedor nuevo.
2. Extender el inspector con el valor explícito8m y el wrapper con presupuesto
   máximo14400s, manteniendo default1800s. Probar identidades, límite superior,
   dimensión falsa y corrupción de límites; no relajar comprobación alguna.
3. Reutilizar lifecycle revisado: FIFO directo sin preconsultar banco, servidor
   propio sin cliente, lease/heartbeat/observador de PID y creación, cierre
   oficial en finally. Generación única14400s máximo, observador14700s;
   arranque300s.2,44×más teselas frente a una generación anterior de97min22s:
   es un presupuesto, no una ETA. Banco ocupado no consume intento.
4. Inspector estrictoTESMv9/VAND12 con8m; empaquetar NM preservando el resto.
   Nueva misiónUUID y nuevos directorios de evidencia; mismas607consultas,
   mismas coordenadas, referencia, filtros y límites. CapturarEND607 y cerrar.
5. PASS exige resultadoPASS_KIT7_NATIVE_GRAPH, cero height_issues/local_failures,
   coberturaF completa, identidad de todos los paquetes y cierre limpio.
   El históricoFAIL permanece. No aceptación por cuatro puntos aislados ni por
   estimaciones. Ante fallo, localizar nuevos polígonos y decidir una corrección
   motivada; no repetir generación idéntica ni rebajar tolerancias.
6. Medir RAM del paquete8m con el protocolo vacío existente frente a Chernarus:
   tres pasadas/mapa, ordenA-B-B-A-A-B,30s+120s y presupuesto1,10×/dispersión5%.
   No heredar el resultadoE+Nav9. Un exceso impide promover la solución como
   optimizada; primero conservar el éxito funcional como evidencia separada.

## Contraejemplos y parada

SuitePython del venvGIS con-I:tests/test_navmesh_v9_prefixes_ev112.py y
tests/test_navmesh_generator_identity.py; positivos8m/14400s, negativos de
dimensión/offsets/bounds/identidad y14401s. Prueba del nuevo packer contra cambio
extra deconfig y paquete base equivocado. ControlesNode del coordinador adaptado:
sesión ajena, captura incompleta, error de generador, cancelación y cleanup.
Consumidor607 conserva sus19controles sintéticos y nunca acepta un runtime
incompleto comoPASS. Tests deben ejecutarse contra las fuentes que se sellen.

Presupuesto de esta implementación: una revisión de plan y hasta dos rondas de
código con reproducciones; una generación8m y una sonda607. Si una causa nueva
impide cumplir, conservar evidencia y replantear antes de otra variante. No
equivale a renunciar al encargo del usuario. Solo publicar corrección validada
o herramientas probadas con el estado pendiente explícito. Locomoción, barcos,
vista humana y aceptación globalEV112 quedan fuera de este resultado.
