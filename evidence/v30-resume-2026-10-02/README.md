# Reanudación V30 — 02-10-2026

Estado: navmesh generado, guardado, inspeccionado y desplegado. **La nueva
navegación aún no tiene prueba de carga ni de caminos en el motor.** El arranque
de Baltic fue rechazado porque otra sesión usa LFPowerGrid; no se interrumpió.

## Cadena de artefactos

| Artefacto | SHA-256 |
|---|---|
| Mundo previo, conservado en `E:/DayZ-Baltic-Build/v30-preview6/out/Addons/narva_trial.pbo` | `93c505930de817abc00bf2b38bd7564c18602bf1175e2ae62f5a42fa0faa33c7` |
| WRP compilado, idéntico antes/después | `471dc77bfdc9fe6644dd63e816c42f893adad359cc75bc717ffea8e4f03e6dbd` |
| NM nuevo, `E:/DayZ-Baltic-Build/navmesh-v30/baltic_trial.nm` | `24baf0692f47fdc67b6ee02abe5363e10c426b1d9e67b29560494724023898a1` |
| Mundo nuevo desplegado, `P:/Mods/@DayZ_Baltic_V30/Addons/narva_trial.pbo` | `69140d41ef4841078a5c159222814490a85832e319977b8b22c18be940e24811` |
| Agua sin cambios | `e9b52b8c4fc07df8bc4854dcd9e144e16875af8006221f16efaa6ab95de56681` |

`tools/playtest/attach_navmesh.py` usó FileBank sobre el árbol compilado: 6.826
entradas permanecieron exactamente iguales y solo se sustituyó el NM. No se
volvió a pasar Binarize. Recibos: `deployed-before-navmesh.json`,
`navmesh-packaging.json`, `deployment.json`.

## Verificación realizada

- Relectura del handoff y de las correcciones de Claude; puertas de terreno y
  carreteras repetidas sobre V30: PASS, 76.536 estaciones viales sin fallos.
  El gate genérico de profundidad >=0,10 m **no certifica** el canal de una lancha.
- Generación completa: 966.289 teselas, 7m03s, 1.127.559 polígonos y 4.079.169
  vértices. Conexión, `World params received` y final en `generator-complete.txt`.
- Guardado manual confirmado por Guillermo. Archivo de 452.021.176 bytes;
  estructura TESM6 y límites de todas las teselas comprobados por el lector local.
  `navmesh-structure.json` es una comprobación empírica de formato, no de topología.
- Servidor de datos propio `00b10da3-5293-4c0e-a8b4-fdee60a3968a` cerrado mediante
  lifecycle: `orderly_close`, retirado. Identidad en `generation-run.json`;
  RPT/script privados archivados en
  `E:/DayZ-Baltic-Build/navmesh-v30/generation-runtime/`.
- Antes de copiar el PBO nuevo se verificó que ninguno de los dos procesos
  ajenos cargaba `@DayZ_Baltic_V30`. No se mutó la sesión ni los mods ajenos.

## Prueba preparada, pendiente

Misión `missions/BalticV30AcceptanceV1.BalticTrial`, también instalada en
`DayZServer/mpmissions/`. Linter: 1 archivo, cero errores/avisos. No implica
compilación en el motor. Nueve rutas positivas y un filtro NONE negativo, con
posiciones congeladas antes del primer intento. `verify_v30_acceptance.py`
exige cobertura completa, terminal END, flags y extremos útiles; no acepta
FindPath=true como prueba suficiente. Todavía no se ha ejecutado con una salida
real de esta misión.

`acceptance-reference.json` fija código, coordenadas y CSV. Se corrigió antes de
ejecutar el hash del CSV para describir los bytes CRLF realmente escritos; se
conserva además el hash LF. Las coordenadas no cambiaron con esa corrección.
Las elecciones iniciales descartadas antes de ejecutar están identificadas como
`initial-unused`; nunca produjeron una prueba en juego.

El arranque esperó 45 s y devolvió `takeover_required`, sin run propio creado,
ante `f1afd2c3-b68b-4c32-ad06-09533cc98525` de LFPowerGrid. Ese rechazo es
coordinación del banco compartido, no un FAIL del mapa.

## Diagnósticos de calado, sin aceptación de lancha

`fairway-diagnostic.json` incluye ejes históricos del delta sustituidos
deliberadamente por V3; su descripción inicial de referencia sin cambios no es
válida para esos brazos. **No usar su total como regresión de V30.**
`current-fairways-diagnostic.json` comprueba únicamente los ejes conservados.
En las estaciones centrales muestreadas no apareció un corte seco. En Luga,
23 muestras laterales del corredor de 24 m quedaron por debajo de 2,99 m, con
mínimo 2,744 m. Esto no demuestra encallamiento ni cumple por sí solo un mínimo
de 3 m en toda la anchura. Se excluyeron extremos, tramos demasiado cortos,
Narva preservado y el delta nuevo; todos figuran en el resultado.

Las sondas de caminos están en tierra cercana a los sitios visuales: sus offsets
constan en la referencia. El punto (1062,4812), llamado Neva en el handoff de
entrada, corresponde al sector Narva sur. No presentar las rutas de tierra como
prueba de agua ni las consultas como locomoción física.

## Siguiente paso

Cuando `session_status` muestre el banco libre: lanzar la misión preparada con
V30, adquirir lease, esperar el log nuevo `baltic_v30_acceptance_v1.log`, archivar
la identidad exacta y validarlo. Después, inspección visual desde jugador sin
`camera_set`. Mantener abiertos BALTIC-007/009/010/011 hasta su evidencia propia;
BALTIC-008 sigue pospuesto a un sector mapeado. No regenerar el NM ni reconstruir
el terreno solo porque faltara el banco para validar.

La skill `dayz-terrain-workflow/references/navmesh-bootstrap.md` ya contiene el
contrato aplicado de WRP idéntico, archivo guardado y caminos útiles; no se ha
creado una skill duplicada. La ruta ejecutable directa de NavMeshGenerator es
compatible con Sky; no hace falta un acceso directo al menú Inicio. Los menús
de entrada fallaron en esta sesión y Guillermo inició/guardó manualmente.
