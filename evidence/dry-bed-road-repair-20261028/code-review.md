**Veredicto: SOUND-with-fixes.** El mecanismo (LP sobre descensos, restricciones en vértices del refinamiento, cuantización monótona, preflight de soporte fijo) es correcto y coincide con el plan. Dos correcciones antes de producción, ambas con repro ejecutable sobre el solver; el resto va a backlog. No apruebo resultado: el consumidor GEOS sigue pendiente y producción no se ha ejecutado.

**Verificado contra fuente y evidencia**

- Unión de filas: `kit-118-geometry.json` muestra 26 modelos, 0000 con 21 filas (8 CAP + 13 cuerpo) y los siguientes solapando una fila. `attach_grid` exige igualdad en filas compartidas; `covered==1` y `face_mapping` exigen propiedad única y topología idéntica; `seen.all()` falla si falta cualquier fila. Las filas 0 y última fijadas son CAP distancia 8 (`continuous_stream_pilot_v31.py:347-362`). Todo fail-closed.
- Collar: `abs(qs)<=4` con el mismo `qs` que `dry_contract`; las columnas ±2.25 incluidas.
- Columna exterior: `:307-308` pone |q|=18 en `ground-.03` por vértice y `:313` la excluye del fairing. El testigo (cara 608 = fila 8 col 0, arista estaciones 0–1 en q=−18) es B interpolado sobre H no plano, no una decisión de diseño de cresta. Descender esos vértices es coherente con el enterrado fuente, no abre borde nuevo (es frontera de malla, XZ intacto) y sólo oculta más bajo H. Acepto el ajuste tal como lo documenta §5; `dry_contract` sigue congelando `border`, pero ese contrato no se reutiliza aquí y el plan lo dice explícitamente.
- Agua A: `local_water` incluye kinds 1 y 2, no filtra flags (ambiguas incluidas), usa envolvente convexa (conservadora) y `predicate='intersects'` (borde incluido). Nativa: mínimo de H−W en todos los vértices del refinamiento, cortes incluidos. Congela todos los vértices de la cara. Correcto.
- Corredor: filtro por AABB de arista +4/cos(π/64) es exacto para rectángulos; todo nodo cuyo disco toque la caja tiene todas sus aristas incluidas. Discos exteriores de 64 lados, como el plan.
- Muestras: vértices de `polygon ∩ corredor`. B−H es lineal por polígono de refinamiento; el máximo de una función lineal sobre un polígono cualquiera se alcanza en un vértice exterior, así que basta con `exterior.coords` aunque el corte no sea convexo o tenga agujeros.
- Cuantización: `floor` sólo aumenta descensos; las restricciones son monótonas; el residuo se recalcula sobre Y cuantizado con umbral 1e-9. Los Y fuente están en rejilla 1/512 (`:329,:363`), así que el `floor` sobre d=0 exacto es identidad.
- Gramática SciPy/Shapely: `linprog(method='highs', options={time_limit, primal_feasibility_tolerance, dual_feasibility_tolerance})`, `dijkstra(min_only=True, limit=)`, `STRtree.query(predicate=)`, `shapely.union_all/get_parts/to_geojson` son válidas.
- Presupuestos: 120 s por LP, watchdog 600 s / 2 GiB (`MAX_BYTES = 2*1024**3`), 1 hilo. Pins de todas las entradas y de los scripts, rechequeados al final.
- 015: `Point(10397.4,9421.9)` radio 60 coincide con los otros 14 productores (orden x,z correcto).

**FIX 1 (bloqueante, repro): soporte libre casi nulo produce candidato absurdo o INFEASIBLE mal etiquetado.**

`fixed_conflict=(effective==0)` trata como soporte libre un peso de 1e-8. La restricción exige entonces d ≥ c/1e-8.

```python
p=np.array([[0.,1.,0.],[1.,1.,0.],[0.,1.,1.]]);t=np.array([[0,1,2]])
out,r=g.solve(p,t,[False,True,True],[0],[[1-1e-8,1e-8,0]],[.1])
# r['status']=='NUMERIC_CANDIDATE_PENDING_CONSUMER', r['maximum_descent']≈1e7
```

Con peso 1e-10 HiGHS descarta el coeficiente (`small_matrix_value` 1e-9 por defecto), la fila queda 0 ≥ 0.1 y devuelve status 2 → `'INFEASIBLE'`, ocultando que la causa es soporte fijo. Tras pasar el preflight el LP es estructuralmente factible (d sin cota superior), así que status 2 nunca es infeasibilidad real: debe mapearse a INCONCLUSIVE_SOLVER. Corrección: en `barycentric` anular pesos < 1e-9 antes de renormalizar; en solver y en `wholly_fixed` del candidato usar `effective<=1e-9` como soporte fijo; relabelar status 2 de fase 1. El plan prohíbe umbrales estéticos, pero este es el mismo 1e-9 ya vigente.

**FIX 2 (repro): se cuantizan todos los vértices libres, no sólo los cambiados** (plan §2 línea 61).

```python
p=np.array([[0.,1.001,0.],[1.,1.001,0.],[0.,1.001,1.]])
out,r=g.solve(p,t,np.ones(3,bool),[0]*3,np.eye(3),[-1,-1,-1])
# d=0 en todos; out[:,1]==1.0, r['changed_vertices']==3
```

En producción los Y están en rejilla, pero HiGHS devuelve ruido d≈1e-12 en vértices que deberían ser 0, y `floor` los baja 1/512: infla `changed_vertices`, `modified` y el área enterrada nueva, y el consumidor revisará caras que no debían moverse. Corrección: aplicar `floor` sólo donde `two.x[:count]>1e-9`; el chequeo de residuo posterior sigue garantizando el gate.

**Backlog (no bloquea)**

- Tests exigidos en §3 ausentes: mutantes (omitir conflicto, mover XZ, mover punto fijo/agua, residuo elevado), agua elevada/ambigua bloqueante, y junta real 0000/0012 (el dominio de 12 m sí cruza la fila 20; el test de junta es sintético). Nada del candidato (`local_water`, `local_corridor`, filas fijas) tiene test.
- `bed_source_face` puede ser −1; lo garantiza transitivamente el censo de exposición pinned, pero el candidato debería requerirlo explícitamente.
- Nodos de grado 0 del grafo no reciben disco en `local_corridor` aunque el censo los contó; afirmar grado ≥1 o añadir discos por bbox de nodo.
- `empty_free_set` lanza excepción cuando no hay conflicto alguno; debería ser estado reportado, no fallo.
- La columna exterior ya no está fijada, pero `dry_contract` en `pilot_bank_profiles_ev112.py:116` sigue congelando `border`; documentar que el consumidor no debe reutilizar ese contrato para esta reparación.

**Lo que no afirma esta revisión**: ni naturalidad ni aceptación visual; ni colisión/LOD; ni que el candidato de producción vaya a ser factible tras liberar la columna exterior. Si aparece otro apoyo fijo incompatible, INFEASIBLE con testigo, sin tocar máscaras, como fija §5.

FIN_REVISION
