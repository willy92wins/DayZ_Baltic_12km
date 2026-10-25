# Prueba acotada de FTT 1.0.5

Guillermo, 03-10: «pruebala, si funciona ganamos mucho». Complemento experimental
al plan de terreno; no cambia P10 ni adopta una dependencia nueva.

## Alcance y puertas

1. Descargar la release indicada y comparar bytes y SHA con GitHub. Ejecutar
   FTT sobre `P:/baltic_ftt_pilot` → `E:/DayZ-Baltic-Build/ftt-pilot-v1/project`.
   Las copias ASC/satélite/máscara conservan hashes de V30; raíz propia.
2. Comprobar dimensiones 2048², celda 6 m, origen 200000/0 y tamaño 12288 m.
   Seleccionar fuentes explícitamente si el programa escoge otras.
3. Generar un tramo corto de carretera con modelos vanilla. Primero exportar
   objetos, sin Write heightmap. Leer la lista exportada: valores finitos,
   coordenadas dentro del marco, plantillas/modelos resolubles, escala y alturas
   razonables. Comprobar que el ASC no cambió.
4. Si la UI y el formato funcionan, comparar el tramo y su transición en TB;
   sólo con ese consumidor puede aceptarse la importación. El lector/exportador
   de FTT no demuestra por sí solo conducción, colisiones ni navmesh.

Presupuesto: una apertura inicial y una exportación pequeña; un fallo permite
un discriminador distinto con evidencia. Sin bucle de parámetros ni generación
global. Las barreras de seguridad requieren intervención del usuario; no se
desactivan. CU agrupado y liberado al pasar a verificaciones de archivos.

Resultados separados: `PASS_LECTURA`, `PASS_EXPORT_OFFLINE`, `PASS_IMPORT_TB`,
`INCONCLUSO` o `FAIL` con motivo. Sólo se promociona una capacidad acreditada.

El piloto no incluye WRP/NM propios: sus avisos de archivo ausente son esperados.
La biblioteca inicial contiene puentes; usar la carga de bibliotecas vanilla
documentada de FTT si necesita modelos de carretera, en el proyecto aislado.
Las colisiones de nombres V29/V30 y los bordes de laguna por loseta siguen siendo
límites abiertos; no sustituir agua ni bosques globales en esta prueba.

Fuentes y capacidades documentadas:
`research/2026-10-03-ftt-1.0.5-review.md`. Preparación y hashes:
`E:/DayZ-Baltic-Build/ftt-pilot-v1/preparation.json`.

## Resultado del 03-10

`PASS_LECTURA` y `PASS_EXPORT_OFFLINE`: fuentes 2048²/6 m y satélite/máscara
12288² cargadas; recta de unos 417 m exportada como 17 piezas vanilla, sin editar
el ASC. `PASS_IMPORT_TB` no alcanzado: TB quedó «No responde» al solicitar un
proyecto nuevo, antes de importar. No se creó TV4P de piloto ni se empaquetó.
Resultado nativo `INCONCLUSO`; no inferir error de FTT de ese bloqueo.
El presupuesto de este ensayo está consumido. Retomar desde el consumidor
aislado cuando TB responda, sin repetir descarga ni generación.

Recibo: [evidence/ftt-pilot-2026-10-03](../evidence/ftt-pilot-2026-10-03/README.md).
