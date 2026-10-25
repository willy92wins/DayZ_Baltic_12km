# Integración del parche de orillas d5dadae8 en un paquete propio, sin TB

Petición de Guillermo del 03-10, tras la revisión de Claude: Terrain Builder queda fuera del
bucle hasta congelar la base y el siguiente bloque empaqueta d5dadae8. Revisión y decisiones:
`C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-revision-claude-relevo-y-herramientas.md`.
Ejecutor e integrador: Claude. Sin concurrencia con Codex ni Exta.

## Entradas fijadas

| Entrada | Ruta | SHA-256 |
|---|---|---|
| Terreno candidato | `E:/DayZ-Baltic-Build/v30-wave-margin-constrained/terrain_v30.npz` | d5dadae846bcc60ecb4e03afbdb8db2e833ca209a54a3228a376682a51482f65 |
| ASC candidato | mismo directorio, `baltic_terrain_v30.asc` | ed3b12f27d2a45426f899632f45b7714e098c8152eea61bc03a80c82448a1fff |
| Agua deduplicada | `E:/DayZ-Baltic-Build/v30-water-deduplicated` | PBO 339fa17f…, `pieces.json` a565e5c4… |
| Mundo de referencia sin NM | `@DayZ_Baltic_ContinuityV30` | e556f576… |
| Superficie de 40d8 | `E:/DayZ-Baltic-Build/v30-watercourse-continuity/surface` | `surface.json` del directorio |

d5dadae8 cambia 126 vértices mojados y ningún metadato, pieza ni plano de agua
(`evidence/v30-wave-margin-2026-10-03/constrained-review.json`).

Mecánica: los scripts que leen entradas no versionadas (`packages/`, `tests/`, `derived/`) se
ejecutan desde su ruta en el checkout principal, sin modificarlos, y escriben solo en E:. El
código, las misiones y la evidencia nuevos se escriben y se commitean en el worktree de la
sesión; al cerrar, `v29-base` avanza por fast-forward.

## Pasos

1. **Superficie** [EXACT]: `tools/terrain/build_surface_v30.py <npz d5dadae8>
   E:/DayZ-Baltic-Build/v30-shore-wave-surface --workers 12` (~2 min). Comparar cada PNG con la
   superficie de 40d8. Gate: solo cambian teselas que tocan el radio de 24 m de los 13 puntos;
   si no cambia ninguna, se usa la de 40d8. Diferencias fuera de ese ámbito: parar.
2. **Paquete** [EXACT]: `tools/terrain/build_v30_package.ps1 -Build
   E:/DayZ-Baltic-Build/v30-shore-wave-package -Terrain <npz d5dadae8> -Pieces
   E:/DayZ-Baltic-Build/v30-water-deduplicated -Layers <superficie del paso 1>`. Gate: «Build
   Successful»; `STAGED_V30_WORLD_SOURCE` con alturas, materiales, cabecera, puentes e IDs
   exactos; agua = 339fa17f; frente a e556f576 solo cambian `baltic_trial.wrp` (alturas en los
   126 vértices) y, si aplica, las teselas del paso 1.
3. **Despliegue aislado** en `P:/Mods/@DayZ_Baltic_ShoreWaveV30/Addons`, con hash tras copiar.
   No se tocan mods anteriores.
4. **Navmesh** [EXACT, receta de `plans/v30-continuity-native-runtime-resume.md` §Lecturas]:
   `dayz_test_run` (servidor, `navmesh_data_server`, misión V4Headless por ruta absoluta,
   `extra_mods` = el mod del paso 3), lease, `tools/navigation/generate_navmesh_console.py`
   hacia `E:/DayZ-Baltic-Build/navmesh-v30-shore-wave`, inspección TESM6, cierre del run propio
   y release. Después `tools/playtest/attach_navmesh.py` con el mismo PBO que alimentó el
   generador, `--replace-existing-sha256` de la NM V29 provisional y FileBank sin rebinarizar;
   despliegue en `@DayZ_Baltic_ShoreWaveV30_Nav`. Gate: generador con código 0, inspección
   PASS y PBO final idéntico salvo la entrada `.nm`.
5. **Consumidores**: una ejecución válida cada uno; una segunda solo por un fallo de
   compilación o de instrumentación identificado.
   - a. **Lectura V4 headless** con la misión ya desplegada y una referencia rebasada [DESIGN]:
     mismas XZ y clases que la de 40d8 (`v30-continuity-dedup-package/runtime-fixture-headless`),
     suelo esperado recalculado con d5dadae8 y lista de puntos afectados. Gate: 1.332 alturas
     dentro de la tolerancia de V4; 463 secos PASS; los 13 someros con profundidad positiva.
   - b. **Serie temporal V3** [DESIGN, `prepare_water_temporal_v30.py --revision 3`]: mismos 17
     puntos y cadencia (151 × 2 s), dos tramos en el mismo run: calma (nubosidad 0,1, viento 0)
     y tormenta (nubosidad 1, viento máximo que acepte el motor), registrando viento y ola en
     cada muestra; firmas de `P:/scripts/3_Game/weather.c` comprobadas antes de escribir la
     misión; lector ampliado sin cambiar los criterios V2. Gate: serie completa y, en ambos
     tramos, los 13 someros con pond y profundidad positiva en todas las muestras. Si la
     tormenta los expone: FAIL documentado y propuesta de margen, sin relajar el criterio.
   - c. **IA física** [DESIGN]: medir antes la distancia de las 12 rutas a los 126 vértices
     cambiados; si ninguna queda a menos de 50 m, se reutiliza `BalticV30ContinuityPhysicalV1`
     tal cual sobre el mod nuevo. Gate: 12 recorridos PASS con `verify_regional_chase.py`.
     Esta prueba abre un cliente de DayZ en el escritorio: se avisa antes de lanzarla.
6. **Cierre**: evidencia en `evidence/v30-shore-wave-<fecha>/`, `bugs.md` (BALTIC-009/014),
   HANDOFF y commit; fast-forward de `v29-base`.

## Fuera de alcance

Terrain Builder (sincronización, Generate Layers), comparador WRP v2, los 22 cortes, la revisión
visual (BALTIC-001/007/009/010/011) y el rendimiento de 80–100 jugadores.

## Coste y riesgos

Preparación ~1 h; superficie y paquete ~20 min; NM ~15 min con servidor; consumidores ~1 h de
juego. Total estimado 2,5–3 h.

- Más teselas cambiadas de lo esperado: parar y revisar el determinismo del ruido.
- Tormenta: confirmar en `weather.c` el rango del viento antes de fijarlo.
- La lectura V4 compara contra el suelo esperado; un punto afectado por d5dadae8 que siga
  dando el valor de 40d8 en el motor indicaría un paquete equivocado, no una tolerancia que ajustar.

## Resultado — 03-10, noche

- Pasos 1–4 PASS: 25 teselas de superficie, paquete con 51 entradas distintas, despliegue
  comprobado, NM 94be04c1 y attach sin Binarize. El primer intento de NM agotó el límite de
  1.800 s del wrapper al 99 %; el segundo, con 3.600 s, tardó 28 min 55 s.
- 5a PASS: la misión V4 completó su lectura durante el run del servidor de datos (mundo
  88c8eac7, el mismo que fija la referencia rebasada).
- 5b serie completa: 13 someros mojados en 302/302 muestras. Gate formal INCONCLUSO por viento
  en calma 1,30 m/s frente al umbral previo 1,0; la tormenta se alcanzó y no expone el lecho.
  El lector V3 necesitó corregir la cabecera del log de orden; la relectura V2 sigue idéntica.
- 5c 4/12 PASS e interrumpida por el cierre del cliente; se repite con el paquete siguiente.
- Hallazgo fuera del plan: BALTIC-015. Chernarus usa piezas de cauce inclinadas.
