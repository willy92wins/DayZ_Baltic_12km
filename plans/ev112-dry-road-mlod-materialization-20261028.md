# Materialización MLOD del lecho seco sobre carretera

Estado: MLOD_OFFLINE_VERIFIED; Fable revisó código congelado
en262.687s, identidad5.1 válida y sin denegaciones. Una lane de plan: unidad acotada y fuente discriminada,
sin diseño alternativo ni API opaca. Codex ejecutor/integrador; Fable independiente.
Consumidor: archivo guardado y verificación separada de todas sus LOD.
Traza: ev112-dry-bed-road-repair-20261028 §4; candidato93168efe validado y publicado
42eebfea. No ejecutar el plan antiguo de kit7/1e85.

## 1. Descubrimiento y revisión de alcance
[EXACT] R/dry-road-mlod-discovery-20261028/report.json,2.938s, sin escribir modelo:
cs_kit_118_0000 es el único de201modelos que cambia. Fuente vigente SHA256
bbf4d5e40dfcb3bf5216981f10cbf21db681d403ea51c4e20676956289207c5a,
en R/pilot-kit7-fc-20261026/source/baltic_stream_pilot. Origen8262,7,8934.
No es uno de los19Geometryoverlays: sus1520componentes son prismas exactos de
6puntos/8caras, con techo igual al lecho y profundidad180/512m. Inventario completo
de9120puntos/12160caras/normales; masa9120. Todas las asignaciones únicas.
Visual y Roadway:819puntos de lecho+26de agua,1544caras.82Y cambian por LOD;
203componentes físicos afectados. Bounds antes/después exactos, Memory preservable.
Algoritmo de normales fuente reproduce float32 de todos los lechos y caras físicas.

[EXACT] review_compact_collision_v31.py:16 load devuelve header/LOD/blobs sin
serializar; :51 overlay compara techo y lecho en toda intersección.
py3d/__init__.py:1792 Point lee XYZfloat32+flagsuint32; :2885 LOD guarda cabecera
28bytes, puntos16bytes y normales12bytes. :3001 P3D recibe stream, NO ruta string.
continuous_stream_pilot_v31.py:92 add_mesh promedia normales unitarias por vértice;
:124 add_prism extruye verticalmente180/512 y asigna ComponentNNNN. Verificado.

Revisión Codex: no hace falta reparticionar/expandir Geometry ni alterar poses;
la transformación vertical de techo y suelo del mismo prisma conserva convexidad,
espesor, volumen, XZ y conexiones. Se probará en el archivo real, sin asumir
equivalencia por lectura. Centro compilado aún no certificado: sólo bounds fuente.

## 2. Autor y artefacto
[DESIGN] Congelar porhash201MLOD actuales, informe/config/prefijo, candidatoNPZ,
mapa source_grid y dependencias. Directorio nuevo, overlay de un archivo con
manifiesto de200identidades restantes; no copiar ni modificar árbol desplegado.
Revalidar dominio semántico descubierto; entrada desconocida falla cerrada.

Parchear bytes exclusivamente de Y del lecho Visual/Roadway, Y de puntos físicos
correspondientes (techo y suelo reciben igual descenso), y normales afectadas.
Normales por algoritmo fuente, sin invertir winding. No serialización general.
Los demás bytes quedan EXACTOS: XYZacuáticos/water_ext, UV/materiales/texturas,
caras, flags, componentes, masas, tags desconocidos, Memory y cabeceras.
Regenerar normales del lecho por todas sus caras; guardar sólo diferencias.
Geometry usa una normal independiente por cara; reconstruir desde sus puntos.
Conservar tamaño de archivo, todas las identidades y coste físico. Candidato
global=NPZ nuevo+origen exacto; coordenadas son rejilla1/512 y representablesfloat32.

## 3. Consumidor y VERDE
MLOD_OFFLINE_VERIFIED exige:
- Sólo1identidad de201cambia; inputs fijos y output reabierto por parser;
- Los819puntos Visual/Roadway coinciden con NPZ, agua intacta; todas las caras y
  atributos no autorizados byteexactos. Consumidor calcula su propia máscara de
  bytes permitidos desde LOD fuente, sin confiar en offsets del autor.
- Cada componente físico cerrado, convexo y orientado; techo corresponde al
  triángulo visible guardado, suelo a techo−180/512. Asignación única de todas
  las caras/puntos; normales unitarias/orientadas errorfloat32<=1e-6.
- Overlay completo1520triángulos con techo físico: límites heredados±0.02m y
  extensiónhorizontal0.01m, sin elevarlos. Bounds, masa, componentes, caras,
  puntos y longitudblob exactos; volumen por prisma errornumérico<=1e-9m³.
- Correspondencia de juntas: filas compartidas con vecinos inmutables exactas;
  no heredar aceptación del consumidor anterior de lecho antiguo.
- Contrapruebas: aguaY, lechoX, UV/tag, normal girada, techo+5cm y falta de media
  cubierta rechazados por consumidor semántico/geométrico; positivo del archivo
  real antes y después. No basta discrepancia de un hash.

Presupuesto previo: revisión código600s, una corrección por repro; autor120s/2GiB,
consumidor300s/2GiB,1hilo; controles300s. Sin bucles de pesos. Fallo geométrico
REJECTED_MLOD, falta/dato/timeoutINCONCLUSO. No compilar hasta VERDE.

## 4. Siguiente frontera
Compilar el overlay, verificar ODOL/centro/poses y las200piezas/config restantes;
preparar mundo que preserveagua/H/objetos y comprobar área del corredor sobre
el artefacto compilado. Después FIFO DayZ, servidor y pruebas de contacto.
Esto no cierra visual humano, RAM ni todas las orillas. C1 sin revisión.

## 5. Adjudicación de revisión Fable
SOUND-with-fixes; informe dry-road-mlod-code-review-20261028. Aceptados:
anclas independientes en consumidor para fuente/candidato/lineage/source_grid;
cobertura completa de normales y separación explícita agua/lecho; contrapruebas
del archivo real obligatorias antes de aceptar, todavía pendientes de ejecución.
El recuento de tests previo era7, no6 (siete métodos test_ leídos); se añaden dos
regresiones para los huecos de normales. No se exige82 fijo para decidir PASS:
la correspondencia con el candidato independiente completo es más fuerte.
No cambian algoritmo, tolerancias, agua, extremos ni protecciones.

Primer autor detenido en2.203s antes de escribir modelo: la fuente actual es
sólo modelos, no contiene config.cpp ni $PBOPREFIX$. Corrección de ancla:
config.bin57d0d0ae y prefijo leídos del PBO vigente3d9550bf, verificado por
read_pbo (attach_navmesh.py:20). No se omite la comprobación. Salida fallida
dry-road-mlod-candidate-20261028 consumida; siguiente salida -r2-20261028.

## 6. Resultado ejecutado
Autor r2:3.594s,d13069d5. Consumidor10.171s:1520prismas,cobertura total,
error0,bounds/agua/juntas exactos,200modelos sin cambios.9tests+6mutantes
reales rechazados en30.765s. Primer autor consumido2.203s sin modelo.
No compilado ni desplegado; no aceptación visual/global. Evidencia
evidence/dry-road-mlod-20261028. Todas las ejecuciones citadas consumidas.
