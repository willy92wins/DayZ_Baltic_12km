# Replay de la cadena desde el diseño (paso 0 del plan) — 06-10-2026

Plan: `plans/v30-cadena-desde-diseno.md`. Productos en `E:/DayZ-Baltic-Build/v30-replay`, cada paso sobre la salida
reproducida del anterior, comparados por sha256 con los archivados.

| pasos | herramienta | resultado |
|---|---|---|
| 1–3 | auditoría V29, `design_navigable.py`, `design_water_v3.py` | los cinco productos del diseño y sus dos informes, idénticos |
| 4–5 | `build_v30_water.py`, `build_v30.py` | water_v30 96d4a7de, terrain_v30 365c2a94, ASC 362550d1: idénticos |
| 6 | `audit_fairway_triangles_v30.py --max-lowering-m 1.55` | 1117b4b1 y corridors 28866a8c: idénticos |
| 7 | `repair_delta_fairways_v30.py` | a84dfff0 y axes-corridors 038470e9: idénticos |
| 8 | `finish_shores_v30.py` | 73b01bb4: idéntico |
| 9 | `restore_narva_ponds_v30.py` | 2f954ad5: idéntico |
| 11 | `connect_small_watercourses_v30.py` | 40d8cfd9: idéntico |
| 13 | `deepen_wave_margins_v30.py --constrained` | d5dadae8: idéntico |

- Las herramientas de los pasos 6–13 aceptan ya sus entradas por argumento (lanes P1 y P2 de GLM, revisadas; un
  parámetro nuevo de `retain_dry_and_face_constraints` pasó a opcional para no romper
  `diagnose_wave_constraints_v30.py:52`). Con los valores por defecto se comportan igual: este replay lo comprueba.
- `restore_narva_ponds_v30.py` y `connect_small_watercourses_v30.py` tienen un solo commit cuyo hash no es el de sus
  recibos, ni con CRLF; aun así dan el producto exacto.
- `source/vectors` del worktree es un enlace (junction) al checkout principal; `tests/water_v3` y `tests/terrain_v30`
  se pasan por argumento (no están en el worktree).

| 10 | `build_water_pieces_v30.py` | pieces.json e0da8b7d idéntico; el PBO y los modelos binarizados archivados se reutilizan (mismas fuentes) |
| 12 | `deduplicate_water_v30.py` | pieces.json a565e5c4 y sus 8.777 ficheros fuente: idénticos |
| 14 | `profile_river_mouths_v30.py` | cb532605: idéntico |
| 15, 17, 23 | `patch_water_tiles_v30.py` | 7399885f, 7619fdf5, 3f3b74f4: idénticos |
| 16 | `narva_moats_v30.py` | e9cb9d9c: idéntico |
| 18 | `narva_v29_outline_v30.py` | sd_v29 d756a5da: idéntico |
| 20 | `polish_luga_head_v30.py --channel-width 30 --bed-depth 3.05` (eje del informe) | 1c0a52fb y sd 11564fdb: idénticos |
| 21 | `relevel_bodies_v30.py --river Luga_0:4440:3.14 --with-river-box … --bodies bodies-v3b.json` | fdfe2ff8: idéntico |
| 22 | `smooth_shore_outline_v30.py` | 5f207001 y sd a234bd7e: idénticos |
| 24 | `fit_channel_pieces_v30.py --overlap-all --no-pad --sea-cut 0.51` | terreno 914f060f y piezas 481e1dda: idénticos |
| 25 | `fit_shore_crossings_v30.py` (flags de la v3b) | **v3b fac76aea: idéntica** |
| v5–v8 | costa, dique, lagos (v7d), ríos | 62b162cb, e07ee373, ee048e5a, **v8 54af9940: idénticos** |

**El paso 0 está completo:** toda la cadena, del diseño OSM al terreno de la v8, se reproduce byte a byte con las
herramientas del worktree (`replay_06_13.sh`, `replay_10_25.sh`, `replay_v5_v8.sh`). El «DIFF» del árbol fuente del
paso 10 en `replay_10_25.out` es de la comparación: la carpeta archivada lleva los enlaces bin/DZ/core a P:\ que crea
el empaquetado; el deduplicado, que lee esos modelos, sale idéntico.

## Diseño suavizado (paso 1 del plan)

`design_water_v3.py --course-sigma-m 18 --seed-per-course` (`water_common.smooth_course`; sin las opciones el diseño
sale idéntico byte a byte) da `E:/DayZ-Baltic-Build/v30-redesign/design`: giros de más de 45° por km de 17,64 a 1,2
y de más de 20° de 43,5 a 10,4; 175 → 143 km de cauce; mismos 44 ríos, 74 arroyos y 387 estanques, con los índices de
los estanques 98, 376, 408 y 409 en los mismos osm_id.
