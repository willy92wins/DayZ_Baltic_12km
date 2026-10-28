**Veredicto: SOUND-with-fixes.** El núcleo geométrico (clipping canónico, tangencias, fans ambiguos, caras verticales, exposición H-W con raíz, tablero sumergido distinto de ausente, precedencia de geometría ambigua sobre "sin tablero") es correcto y conforme al plan. Hay dos defectos que deben corregirse antes de ejecutar producción y varias omisiones menores. Hashes de inputs.json no verificables sin Bash; sí comprobé que el pin nativo 6853a78f y el script_sha256 de A b7a17598 coinciden con los pins de inputs.json, y que contacts.json del censo declara 770 aristas (coincide con la línea 216).

**Bugs que requieren fix**

1. **Métrica de preflight falsa** en `tools/quality/road_surface_overlay_ev112.py:247-248`. `candidates` es un `defaultdict(list)` y la comprensión de `counts` lo indexa para todas las aristas, creando claves vacías. Por eso `candidate_edges` vale siempre 36467. Repro mental: `d=defaultdict(list); [len(d[e]) for e in range(3)]; len(d)==3`. El plan exige preservar pares totales, máximo por arista y caras candidatas; los dos últimos son correctos, pero el conteo de aristas con candidatos es inútil para dimensionar partición. Fix: usar `candidates.get(e,[])` o contar antes del bucle.

2. **Marco condicional usado para certificar sequedad** en línea 295. Un agua de proxy (kind 2, PROXY_CONDITIONAL) cuya altura hipotética cae bajo el terreno recibe `BURIED_RELATIVE_TO_SOURCE_TERRAIN` con `uncertain=True` y se excluye de `waters`. No se genera ningún finding, así que el tramo queda como seco por omisión. Esto contradice el plan (líneas 51-52 y 69-70: "no usar falta de intersección bajo un marco condicional para certificar sequedad"). Repro: quad proxy y=2, terreno y=3, flag 1 → `exposure` devuelve BURIED, `uncertain` True, filtrado; `findings==[]`. La cara sí queda en `surfaces`, pero `finding_pieces` del report la oculta. Fix: si `uncertain`, pasar la pieza a `overlay` (saldrá INCONCLUSIVE_WATER) sea cual sea la exposición, o emitir un estado explícito CONDITIONAL_BURIED. Hay 65 caras así en A; el impacto es real.

**Omisiones respecto al plan (recomendado corregir en la misma ronda)**

3. **Huecos sin procedencia** (`union` línea 157 y `gaps` línea 311-312). El plan pide reportar tamaño/ULP y procedencia de microhuecos. Los huecos se calculan sobre la unión de spans por cadena, pero sin `ref` de las superficies a cada lado. Además, la garantía "vecinos comparten t bitexact" depende de que los vértices compartidos sean bit-idénticos tras `transform` y de que `hull` no elimine vértices colineales (línea 33, `<=0` descarta puntos en T-junction, cambiando la clave canónica del vecino). No se comprueba ni se mide. No produce falso PASS, pero un hueco de 1 ULP se reportará como separación geométrica sin identificar que es artefacto de clave.

4. **Mar nominal vs charca nominal no separados** (`native_water`, líneas 252-264). El plan (124-127) pide distinguirlos; contacts.json del censo no guarda si la altura provino del plano del footprint o del 0.75 por defecto, y el consumidor sólo etiqueta `nominal=True`. Debe documentarse como limitación o derivarse del footprint pineado (que tampoco se pinea aquí; plan línea 19 cita 084171b0).

5. **Diferencia nativa vs modelo no registrada**. El plan pide "registrar la diferencia"; sólo existe `height_spread_m` por nodo. Dentro de una arista, dos capas de agua con alturas distintas se guardan pero no se compara explícitamente.

6. **Duplicado en nodos**, línea 303: `hits+waters` contiene dos veces las piezas de agua de modelo (están en ambas listas). No altera `height_spread_m`, pero infla `observations`.

7. **Presupuesto**: `main` no exige `seconds<=120` y bytes ≤2 GiB al final como hace el censo nativo (`road_water_contacts_ev112.py:255`); el vigilante puede escribir `resource-stop.json` y salir después de que `report.json` ya exista (ventana entre línea 339 y `stop.set()`). El lector debe tratar `resource-stop.json` como prevalente. Añadir el require.

**Rutas de fallo que abortan, no engañan** (aceptables, documentar)

- Línea 60 `require(side!=0)` puede saltar con hulls astilla de coordenadas ~1e4 m.
- Línea 71 `require(n[1]!=0)` puede saltar si `hull` conserva 3 puntos por redondeo mientras `np.cross` da n[1]==0 exacto. Ambos terminan en `failure.json`, no en falso resultado.
- `roadway_role` sólo reconoce `/water_ext.paa` con directorio. En el snapshot sellado todas las secciones usan la ruta completa `dz/surfaces/data/roadway/water_ext.paa`, así que no afecta a esta ejecución.

**Test (`test_road_surface_overlay_ev112.py`)**

- El oráculo Shapely (línea 15-22) compara sólo longitud, no extremos; un desplazamiento del intervalo pasaría. Comparar `lo/hi` con las coordenadas de la intersección.
- `broad_phase` y `census` (líneas 234-328) no tienen ninguna fixture. Los 28 tests verdes no acreditan la orquestación: lookup de `sections[...]['lods'][lod]['sections'][section]['texture']`, filtro de línea 295, nodos y gaps se prueban por primera vez en producción. Una fixture sintética con dos instancias y tres aristas, construyendo `data` a mano, cubriría los bugs 1, 2 y 6.
- Falta caso: Roadway `water_ext` cubriendo agua debe dar WET_AXIS_WITHOUT_BRIDGE_ROADWAY (sólo se prueba `roadway_role`).

**Verificado como correcto**

Orientación del terreno coherente entre `h[::-1]` del WRP y `bary` (fila 0 en z=top). Rechazo bbox con desigualdad estricta conserva tangencias. `clip` devuelve `(t,t)` en vértice tangente y maneja paralelas/colineales. Fans de ambas diagonales sin elegir ganador. `split_sign` divide en la raíz H-W exacta. `overlay` inserta raíces tablero-agua y da prioridad a INCONCLUSIVE_BRIDGE_GEOMETRY sobre ausencia. Cobertura de 36467 aristas exigida. Pins de terreno, referencia, cadenas, contacts y chain-coverage coinciden con el plan; WRP editable comparado byte a byte en alturas y rehashado al final contra el pin de A. STRtree sólo en broadphase.

**Siguiente paso**: corregir 1, 2, 7 y añadir fixture de orquestación; luego preflight y una única ejecución.

Identidad confirmada: Claude Fable 5.1 (claude-fable-5-1), CLI nativo, sólo Read/Glob/Grep, sin escrituras.

FIN_REVISION
