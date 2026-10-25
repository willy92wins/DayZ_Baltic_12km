# Integración del parche de orillas d5dadae8 y agua en pendiente — 03-10-2026

Ejecutor: Claude. Plan: `plans/v30-shore-wave-integration.md`. Terreno sin Terrain Builder.

## Identidades

| Artefacto | Ruta | SHA-256 |
|---|---|---|
| Terreno | `E:/DayZ-Baltic-Build/v30-wave-margin-constrained/terrain_v30.npz` | d5dadae846bcc60ecb4e03afbdb8db2e833ca209a54a3228a376682a51482f65 |
| Superficie | `E:/DayZ-Baltic-Build/v30-shore-wave-surface` | PAA 1428a660… (`package-gate.json`) |
| Mundo sin NM | `E:/DayZ-Baltic-Build/v30-shore-wave-package/out/Addons/narva_trial.pbo` | 88c8eac7baaaee9678cbe468e3c379a0fc96ef378a8b8682a40994d5b1145b9f |
| WRP compilado | entrada `baltic_trial.wrp` | 8a8218129fdb046536a4d8eca0d8117cf8fb3046f79724f844ccff48b945ae75 |
| NM | `E:/DayZ-Baltic-Build/navmesh-v30-shore-wave-runbe0c063b-r2/baltic_trial.nm` | 94be04c1cbda909ba97e75ecef1ad438cd8f9041bbaad872521978488b16c627 |
| Mundo con NM | `E:/DayZ-Baltic-Build/v30-shore-wave-nav-package/Addons/narva_trial.pbo` | 7c3fd0fdf83123ab64864a906fb493082fe1472fc7efa51fe46cadccfbfb0c8e |
| Agua | sin cambios | 339fa17f26c9ec7a47fca59f621447ef44dbc1212b7c654cc4f88e51dca24b13 |

Mods: `@DayZ_Baltic_ShoreWaveV30` (88c8eac7 + agua) y `@DayZ_Baltic_ShoreWaveV30_Nav`
(7c3fd0fd + agua), copiados y comprobados por hash. Misión `BalticV30WaterTemporalV3.BalticTrial`
desplegada idéntica a la del repo.

## Resultados

| Paso | Fichero | Resultado |
|---|---|---|
| Superficie | `surface-diff.json` | PASS_SURFACE_CHANGE_LOCAL: 49 PNG de 25 teselas, todas junto a los 13 puntos |
| Paquete | `package-gate.json` | PASS_PACKAGE_LOCAL_DELTA: 51 entradas distintas (WRP, texHeaders.bin, 49 texturas) |
| NM, intento 1 | `navmesh/generation-attempt1-timeout.json` | TIMEOUT del wrapper a 1.800 s con el generador al 99 %; sin fichero |
| NM, intento 2 | `navmesh/generation-attempt2.json` | GENERATED: 966.289 teselas, código 0, 28 min 55 s |
| Teselas NM | `navmesh-tile-comparison.json` | PASS_STRUCTURE_AND_LOCAL_TILE_DELTA: 138 cambios estructurales a ≤14,1 m; bytes distintos en 966.286 (generador no determinista); ninguna ruta de IA afectada |
| Attach | `navmesh/attach-verification.json` | PASS_NAVMESH_PACKED_BYTE_PARITY, sin Binarize |
| Lectura V4 | `v4-readback-verification.json`, `v4-readback-fixture.json` | PASS_SHORE_ENGINE_READBACK: 1.332 puntos, error ≤0,000571 m, 0 fallos (run be0c063b, mundo 88c8eac7; referencia rebasada con `tools/terrain/rebase_shorefinish_reference_v30.py`) |
| Serie V3 | `temporal-v3-result.json` | 13 someros con pond y calado positivo en 302/302 muestras, mínimo 0,061 m; tormenta alcanzada (20 m/s, nubosidad 1). Gate INCONCLUSIVE_PHASE_WEATHER: viento en calma hasta 1,30 m/s frente al umbral previo 1,0 (run 05ee00b9) |
| IA física | `physical-partial/` | FAIL_OR_INCOMPLETE: casos 0–3 (laguna, colinas) PASS; 4–11 sin ejecutar porque el cliente se cerró a las 21:42:17 (run 40dbee77) |
| Rutas IA | `physical-route-distance.json` | rutas a ≥1.275,6 m de los vértices cambiados; misión reutilizada |
| Agua vanilla | `vanilla-water-survey.json` | Chernarus: ríos/arroyos inclinados con lámina que sigue la pendiente; estanques horizontales (run af204798; el run 6f6e06e1 no compiló: `Unknown operator` en una expresión con constantes estáticas, disparador exacto sin aislar) |
| Visual | `visual/stepped-water-discontinuity-guillermo.webp` | Discontinuidad del agua escalonada en pendiente: BALTIC-015 |

Ciclo de vida: todos los runs propios cerrados con `orderly_close`; lease liberado; caja libre.
El JSON completo de teselas (614 MB) está en `E:/DayZ-Baltic-Build/v30-shore-wave-fixtures/navmesh/`.

## Límites

Sin revisión visual del paquete nuevo ni barco. La IA física queda pendiente de repetir con el
paquete que arregle BALTIC-015. El rendimiento no se evaluó.
