**Veredicto: SOUND-with-fixes.** La geometría D, la auditoría y la sonda son correctas; hay un fallo real en una herramienta publicada y dos defectos de procedencia que conviene cerrar antes de publicar la unidad parcial.

**Fallos concretos**

1. **La versión CLI del inventario no puede terminar.** `tools/terrain/inventory_guarded_shapes_ev112.py:13` reasigna `a` al diccionario de arrays, y `:47` hace `out=a.out` → AttributeError tras todo el cálculo. Confirmación de que nunca se ejecutó: `guarded-relief-discovery/report.json` carece de `author_sha256`, `records_sha256` y `road_inputs`, que la CLI escribe en `:49-50`; el discovery lo produjo el script archivado `inventory_guarded_relief.py`, que además toma `road` de `terrain-free-final/domains.npz` (`:15`) y no de `s3_road_guard()`. La equivalencia de contenido sí está probada (audit_guarded_all_d.py rederiva free/shore/road con s3_road_guard y da provenance True), pero la herramienta publicada está rota. Fix: capturar `out=a.out` junto a `B=a.build` en `:11`, o renombrar el dict a `arrays`.

2. **Metadatos heredados en stage-report.json.** `tools/terrain/stage_guarded_relief_ev112.py:89-91` parte de `meta` del stage padre y solo sobrescribe algunas claves. Resultado: `stage-guarded-d/stage-report.json:21` dice `terrain_vertices: 1648` (valor de stage-combined) mientras terrain-stage-verification dice 1347; `pilot_pbo_sha256`, `objects_digest`, `added_models`, `remaining_objects` y `limits` también son del padre. Fix: fijar `terrain_vertices=int((H!=H0).sum())` y eliminar o marcar como `inherited_from_parent` el resto.

3. **Hashes de autor sin copia archivada.** Batch C guardó author-used.py y solver-used.py; batch D no. `report.json:2146-2147` referencia archivos sin commit en el worktree; no puedo verificarlos en solo lectura. Fix: archivar copias en batch-d o hacer commit antes de cualquier edición y anotar el SHA del commit.

**Verificado correcto**

- Corona anti-sobrepaso extendida a todo extremo protegido con pk0/pt0>0,3 del slice (`repair_guarded_shapes_ev112.py:71-74`); el relleno de 4 cubre el radio de guarda. Auditoría externa: 130 extremos afectados, 0 violaciones, masks rederivadas iguales a las del discovery.
- Los 8 SOLVER_FAILED son todos `Positive directional derivative for linesearch` (SLSQP); el clúster 35 (1024,254) cae solo por energía pura. 56 clústeres aplicados = 66 grupos, 9 rechazados = 15; 58 picos / 8 pozos cuadran con 327→269 y 1156→1148.
- Aserción de pertenencia de todos los `target_vertices` al clúster (`:62`) añadida como pedí.
- `despike_v31.prominence` y `census_pyramids_v31.prominence` usan formas y anillos idénticos; verificador independiente del solver válido.
- Stage D y replay producen el mismo WRP `81560aa2…`; verificación independiente: 2577241 + 1484 = 2578725, error de consumidor ~1e‑6 m. Bosque: 0 fallos medidos, 3727 de borde INCONCLUSO, correctamente no aceptado.
- Sonda: `tri_sample` y `tri_h` comparten diagonal NW‑SE y volteo Z; el terreno fijado es el base U2 `ab96…`, lo correcto para la generación en curso; deck de puente conservado; contrato XZ/expect verificado (`prepare_current_nav_probe_ev112.py:47-48`).
- Wrapper: generador desconocido o entrada errónea nunca lanzan; TIMEOUT/LAUNCH_FAILED/POSTCHECK_FAILED mantienen recibo; cabecera v9 solo pasa si la aritmética v6 se cumple y aun así queda "pending structural"; de lo contrario HEADER_LAYOUT_UNVERIFIED con exit 1. El proceso en ejecución no se ve afectado por editar el archivo.

**Menores**

- `test_guarded_relief_caps_ev112.py` prueba solo `crown_bounds`; la rama INFEASIBLE_BOUNDS de `main` (`:75-76`) sigue sin test porque `main` es monolítico.
- Cada clúster resuelve contra `h0` aunque vecinos de clústeres previos ya estén modificados; `pure_energy_decreased` es local a h0. Las puertas globales cubren la geometría; solo documentarlo.
- `inventory_guarded_shapes_ev112.py:20,34` siguen con 2048 fijo.
- No he ejecutado los 148 tests; su PASS queda sin verificar por mí.

**Conclusión:** corregir el punto 1 antes de publicar la herramienta; los puntos 2 y 3 son de evidencia y deberían cerrarse en la misma publicación. No se requiere aceptación visual ni navegación global para publicar herramientas + evidencia parcial con estado PENDING.
