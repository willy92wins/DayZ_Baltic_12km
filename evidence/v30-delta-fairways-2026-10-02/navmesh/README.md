# Navegación del delta corregido

Generada y guardada con NavMeshGenerator sobre el WRP `daca4196` del paquete
aislado `8b2d404a`. Run de servidor de datos `d115461b`, generación completa
966.289 teselas en 8 min 55 s. `saved.txt` confirma la ruta y Saving complete;
`structure.json` valida offsets/cabeceras/límites de todas las teselas (TESM6,
12,5 m), no la topología completa.

- NM: `eece8e5ea40c8a11856b44a90c4569c0026ca255cfef5e40db1d547e4c0eb2f7`,
  452.103.816 bytes, en `E:/DayZ-Baltic-Build/navmesh-v30-delta/baltic_trial.nm`.
- PBO nuevo: `916948ec6590e590edb91218082bf2b0bba8a6f9276c3977b003512f9cc6f525`,
  desplegado en `P:/Mods/@DayZ_Baltic_DeltaV30_Nav`.
- Agua sin cambios: `e9b52b8c`. FileBank sustituyó solo la NM; las otras 6.826
  entradas son idénticas a las de generación, sin Binarize (`package.json`).
- Servidor cerrado orderly_close, lease liberado y Computer Use reseteado.
  Se conservan dos caducidades de lease y la readopción del mismo run propio;
  no se afirma posesión continua (`generation-closure.json`).

## Diferencias que requieren consumidor

La generación anterior (`24baf069`, V30 sin arreglos Luga/delta) tenía 687
enlaces offmesh frente a 121 aquí. La comparación empírica localiza cambios de
ese campo en 252 teselas, distribuidas más allá del ámbito editado. Cambian
11.286 cabeceras estructurales y 955.430 payloads. Las configuraciones compiladas
son idénticas (`c83e722d`), comprobado en ambos PBO reales. No se ha aislado la
causa ni demostrado que sea un fallo de navegación: no atribuirlo solo al delta,
a un parámetro, a aleatoriedad o a corrupción. Evidencia `tile-comparison.json`
y `config-comparison.json`.

Misión `BalticV30DeltaNavV1`: diez consultas históricas inalteradas (nueve caminos
y NONE), dos caminos locales de isla/continente y un control WALK que no debe
conectar ambos componentes por encima del agua. Referencia congelada antes del
motor; controles de lector: positivo histórico, dos positivos sintéticos y 16
negativos rechazados. Resultado posterior: `runtime-5c1e4734/` registra END13 y PASS en las trece
consultas reales. Carga propia acreditada; controles locales y Narva pasan.
La diferencia global de contadores sigue sin causa aislada ni cobertura total.

Misión `BalticV30DeltaBoatV1`: cuatro recorridos físicos independientes, ida/vuelta
de Gran/Pequeño Neva más sus conectores. Reutiliza controlador/criterios de V3;
solo cambia datos, total y nombre del log. Lancha vanilla vacía, propulsión real,
sin escrituras de pose tras spawn. No prueba barcos medianos ni todos los ríos.
Resultado: los cuatro viajes PASS, 2.269 muestras y salud 600 constante,
run16fe4ad8 cerrado ordenadamente. Ver `boat-16fe4ad8/README.md`.

## Lección de UI

El diálogo nativo Save Navmesh no apareció en list_windows, pero sí como segunda
captura acotada del padre. Con su screenshotId funcionaron enfoque de Nombre,
escritura de ruta y clic Guardar. Los índices UIA estaban fuera de la caché y
focused_element señalaba el buscador, pese a la ruta visible en Nombre. El primer
tamaño observado (189 MB) era parcial; Saving complete y el archivo final son
pruebas distintas. Skill local actualizada con respaldo (`skill-update.json`).
El validador genérico de skills no pudo importar PyYAML en los entornos GIS/MCP;
no se instaló nada ni se etiqueta ese comando como PASS. La entrada SKILL.md
permanece intacta: se añadió solo la observación a su referencia ya enlazada.
