# Navegación del delta corregido — 02-10-2026

Ejecución dentro de P9/P10 y `v30-delta-fairways.md`, después del PASS de las
1.682 lecturas reales del run 45e5b57c. No cambia producto ni geometría.

## Alcance y puertas

1. Generar todo el mundo desde WRP compilado `daca4196`, servido por el paquete
   `8b2d404a`. La NM V29 del paquete es solo bootstrap. Generador reiniciado,
   conexión nueva y rango observado 0..982 en X/Z; total 966.289 teselas.
2. Guardar `E:/DayZ-Baltic-Build/navmesh-v30-delta/baltic_trial.nm`, inspeccionar
   estructura TESM6 a 12,5 m y adjuntar con FileBank. Las otras 6.826 entradas
   del PBO deben ser idénticas; no recompilar WRP/config/superficie.
3. Repetir los diez casos congelados de BalticV30AcceptanceV1 (nueve caminos y
   filtro NONE) sobre el paquete nuevo. Añadir dos caminos locales, uno dentro
   de la isla recuperada y otro en la orilla continental; ambos extremos secos
   y con margen respecto al agua, seleccionados antes de consultar la NM.
4. Añadir una consulta WALK entre esos dos componentes secos. Ambos extremos
   deben existir en la NM a <=2,1 m del punto pedido. El camino no debe alcanzar
   el otro extremo: se acepta ausencia de camino o una ruta parcial cuyo final
   quede a >2,1 m, con comienzo correcto. Un resultado que llegue al otro lado,
   aunque FindPath devuelva false, falla. No asumir comportamiento de rutas
   parciales no documentado por la API.
5. El PASS acredita carga y esas consultas del grafo, no desplazamiento de un
   infectado, navegación de lancha, cobertura de todos los interiores o carga
   multijugador. Fallo de conexión/carga = INCONCLUSO; log incompleto no pasa.

La isla se identificó en la malla seca `cls==0 && height>=1` con ocho vecinos:
núcleo (8364,10200), 1.273 vértices / 45.828 m². Esa clasificación selecciona
controles independientes; la aceptación del grafo se mide luego en el motor.
Los nueve objetos de puente existentes están en Narva, fuera de esta abertura.

## Implementación acotada

- `evidence/v30-delta-fairways-2026-10-02/navmesh/prepare_queries.py`: copia de
  la misión ya compilada, nuevo nombre/log y CSV/referencia propios, create-only.
- `missions/BalticV30DeltaNavV1.BalticTrial/`: lecturas una sola vez en servidor,
  sin actores, RPC ni controles de jugador. El cliente solo carga el mundo.
- `tools/terrain/verify_v30_acceptance.py`: expectativa opcional `disconnected`
  sin cambiar el contrato histórico de los otros diez casos; controles contra
  registro real anterior y registros sintéticos explícitos antes de usarlo.

## APIs reancladas [EXACT]

`P:/scripts/3_game/ai/aiworld.c:59-67`: PGFilter y SetFlags.
`:89-98`: FindPath, array de puntos con principio/final.
`:112-122`: SampleNavmeshPosition y radio máximo.
Código consumidor ya compilado:
`missions/BalticV30AcceptanceV1.BalticTrial/init.c` SHA `0fea34a5`.
No se introduce otra llamada a Enforce. Datos/cálculo/log solo servidor, sin
estado nuevo compartido ni persistencia de juego; salida en profiles local.

## Comprobación física posterior del cauce (P9)

Tras guardar y cargar la navmesh, reutilizar el consumidor de lancha ya probado
en `BalticRegionalBoatV3`, con cuatro casos: ambos brazos completos más sus
conectores al tronco, ida y vuelta desde spawns independientes. Cambiar únicamente
el CSV, número de casos y nombre del log. Ejes del GeoJSON auditado, muestras
cada <=4 m; no cambiar rutas ni criterios al ver el resultado.

Lancha vanilla Boat_01_Orange vacía; acelerador y dirección por el addon
`@BalticBoatInputProbe` existente SHA `c5414ffe`, sin editarlo ni escribir pose
después del spawn. Solo servidor, un barco a la vez. Criterios anteriores intactos:
desviación <=7 m, pasos <=3 m, intervalo <=0,8 s, pérdida de salud <=1,
todos los puntos intermedios a <=7 m, destino <=6 m, motor/propulsor y callbacks
reales. Timeout 450 s por caso no acredita defecto del mapa por sí solo.
El verificador contrasta terreno contra ASC final por triángulo nativo.

Definiciones reancladas: `P:/scripts/3_game/vehicles/boat.c:49,55,61,106`
(dirección, acelerador, embrague y marcha), `4_world/entities/vehicles/boatscript.c:342`
(OnInput); addon local `diagnostics/baltic_boat_input/scripts/4_World/BalticBoatInput.c`.
El ensayo precedente fue servidor solo (run 769e5935); no se presupone cliente.
Un PASS seguirá limitado a lancha vacía, cuatro recorridos, sin giro completo,
tripulación, barcos medianos ni aceptación de todos los ríos o puentes.
