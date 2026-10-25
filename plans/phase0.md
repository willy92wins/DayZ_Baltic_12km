# Fase 0 — ejecución y gates

**Alcance autorizado:** revisar la base heredada, cerrar el recorte con el usuario, preparar el entorno, generar una maqueta candidata a importar y un plan de validación. Avance autónomo autorizado; proveedores externos autorizados expresamente para revisar coordenadas y diseño público.

## Resultado actual

1. Encuadre v0 aprobado, referencias fijadas por hash (P1/P3/P4).
2. DayZ Tools, P:, Diag, vanilla y Mods comprobados; GIS operativo en entorno aislado (P8). Existencia no demuestra funcionamiento de Buldozer/TB.
3. Descarga y procesamiento de 15 DEM, 4 WorldCover y 2 PBF (P2/P5/P8).
4. Transformación única del marco Web Mercator a ingeniería local; dos salidas Z del mismo ráster para perfiles, sin duplicar mundos editados (P1/P3).
5. ASC, SHP, máscara y colores provisionales, 28 checks GIS y 13 casos del validador (P1/P8).
6. Auditoría de red mediante IDs de nodos OSM; revisión específica de Narva (P4/P5).
7. Paquete y repo dev. Probe y región física importados, guardados y exportados desde TB; región reabierta y render Buldozer observado con avisos. Registro preciso y sector funcional pendientes; evidencia en `evidence/tb-import/informe.md`.

## Límites de las comprobaciones

PASS GIS: forma, cabecera, norte, coordenadas de centros, datos finitos, cobertura fuente, hashes y controles directos del DSM. La comparación ASC/TIF prueba serialización; no prueba por sí sola geografía. Los controles del DSM usan una fórmula independiente de registro y lectura de ventanas del original; no constituyen una segunda medición física de elevación.

FAIL: dimensiones/orientación equivocadas, huecos terrestres sin fuente, desplazamiento no explicado o pérdida de un elemento acordado.

INCONCLUSO: semántica real de muestreo de TB, agua elevada, costa recorrible, puentes, WRP/PBO, navegación, economía y rendimiento. No se convierten en PASS mediante una imagen GIS.

## Siguiente secuencia

1. Prueba desechable de registro e importación del mapa completo. Medir centros/vértices antes de corregir nada.
2. Sector pequeño de Narva con orilla, cruce, carretera, edificios vanilla y agua; mantener un caso de lago elevado y de canal del Neva como discriminadores adicionales del agua.
3. Buldozer y build mínimo; después cliente/servidor, cruces, navegación y loot. Comprobar artefacto desplegado antes de diagnosticar runtime.
4. Decidir Z con los perfiles y el sector. Delimitar presupuesto de edificios/vegetación a partir de mediciones; escalar al resto solo después.

No se añade construcción regional masiva mientras el sector no demuestre agua y conexiones. No se fija un límite de objetos arbitrario para prometer 100 jugadores.

## Narva: excepción de fuente comprobada

La selección inicial de vías principales deja Narva en un componente separado. Al añadir las geometrías locales de otras categorías OSM, los ocho núcleos comprobados comparten red. El camino topológico de Narva a San Petersburgo atraviesa seis ways etiquetadas `highway=construction`: 4481065, 4585845, 85216990, 85217048, 172618601 y 1314298224. Se preservan en `source/vectors/narva_crossing_detail.*` junto con el contexto local. No se altera la clasificación original ni se infiere transitabilidad real o jugable. Evidencia: `evidence/road-topology.json`, `road-topology-with-narva-detail.json` y `narva-crossing-inspection.json`. El análisis ignora restricciones de circulación/acceso; no es un enrutador de vehículos.
