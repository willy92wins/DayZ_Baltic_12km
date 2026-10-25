# Comparación estructural Q / Chernarus — 24-10-2026

**Inventario terminado; rendimiento INCONCLUSO.** Pedido de Guillermo: comprobar
la optimización del mapa frente a Chernarus. No se cambió ningún mapa ni PBO.
Plan y criterios: `../../../plans/ev112-performance-chernarus-20261024.md`.

| Medida estática | Baltic Q | Chernarus instalado |
|---|---:|---:|
| Objetos WRP | 2.578.822 | 2.971.218 |
| Vegetación (también arbustos/troncos/juncos) | 2.560.922 | 2.572.370 |
| Recursos de modelo distintos | 5.343 | 2.352 |
| WRP, bytes | 223.136.580 | 235.121.529 |
| Vegetación/celda de 256 m, p95 | 1.671 | 1.826 |
| Vegetación/celda de 256 m, máximo | 1.948 | 2.521 |

El mapa Q tiene casi el mismo número de elementos de vegetación en un cuadrado
de 12.288 m, frente a 15.360 m del referente; sus máximos locales son menores.
Los tamaños de mapa son los de los terrenos del proyecto y de la sonda vanilla
anterior, no una nueva medición runtime. Las celdas incluyen mar y áreas vacías;
no son una comparación de biomas emparejados ni prueban rendimiento.

5.220 modelos distintos / 10.264 instancias de `baltic_water_v30` merecen perfilarse;
además hay 35 modelos/instancias del piloto. Los grupos se clasifican por ruta:
`dz/water` incluye lechos y piedras, no solo láminas. Recursos distintos no equivale
a draw calls; cuenta de objetos no equivale a coste de malla, sombras, física o LOD.

Candidatos de estrés del bosque: Q (8832,4992), (8576,5760); Chernarus
(3968,10368), (128,7040), centros de celdas de 256 m. Confirmar contenido, acceso,
pose y visibilidad antes de congelarlos como escenas. No son parejas validadas.

## Identidad y verificación

`static-inventory.json` contiene hashes completos de los tres PBO Q desplegados,
del PBO instalado Chernarus, ambos WRP, grupos, top recursos y celdas 128/256/512 m.
Q se enlaza con la lectura completa anterior de 2.578.822 objetos de compilación.
WRP Q `ae1ad96db2ddb43a3df79bcb083cfbcffe339bb8ceabcf04129b756807799fba`;
Chernarus instalado `ea27d819e09af3f94b237ba103dbb0d6a01293bce842162dfad0fb3e4d36e21b`.

El archivo extraído en P:/DZ tiene hash
`dd885ead8e1e940b72228df3b15eea4a6701a335f3f04ed4f9ea3074ea42462d` y no se usa
como referente actual. El WRP del servidor instalado también difiere
(`b1571bcef151123cf37b856f9b36bdca2a52f66d45e3ec9077eb69238b2a5771`): futuro A/B
debe usar el mismo ejecutable/contenido gestionado para ambos mundos.

El lector es heurístico y comprueba tabla única, ancla única, registros finitos,
IDs únicos y frontera con map-info. No decodifica todo el WRP ni alturas/navmesh.
Tres pruebas automáticas pasan: formatos 29/32 y densidad calculada a mano;
rechazo de IDs duplicados; rechazo de map-info ausente o ajeno.

128 controles deterministas del censo filtrado antiguo cruzan la lectura con
evidencia del motor: 128 coinciden en XZ a <2 mm, pero **solo 123 en 3D**. Cinco
piedras tienen diferencias Y de 0,010–0,193 m. Se conserva FAIL de paridad 3D;
el mecanismo no está aislado. La comprobación XZ es distinta, no una relajación
de altura. No permite aceptar soporte/colisión ni prueba independientemente
la completitud de los casi tres millones de objetos.

## Lo que queda

El MCP 1.30 devolvió `daemon_unavailable` al consultar estado; no se adquirió
lease ni se lanzó juego. `host-and-blocker.json` guarda hardware y el bloqueo.
No hubo FPS, frametimes, VRAM, ensayo de servidor ni comparación multijugador.
Falta validar la instrumentación cliente y ejecutar las escenas emparejadas.
La visita conjunta Q permanece pendiente, igual que carreteras y expansión de ríos.

Origen del cálculo:
`E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/performance-chernarus-20261024-a`.
Sin commit/push: tarea y aceptación global abiertas. `MANIFEST.json` vincula
esta evidencia y las fuentes. Sin cambios en memoria Codex ni trabajo ajeno.
