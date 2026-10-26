**Veredicto: SOUND-with-fixes.** El comparador no tiene falsos PASS en el alcance definido. Hay dos hallazgos menores, ninguno en la ruta de producción del empaquetado.

**Lo verificado en `compare_non_geometry_lods_v31.py`**

- NaN: `normalized` convierte cada float a bits float64 (línea 4), así que NaN con distinto payload difiere y NaN idéntico iguala. El test lo cubre en la línea 24.
- Nada decodificado se descarta salvo `declared_end`/`parsed_end` (offsets físicos) y, solo en Roadway, `face_lower`/`face_upper`/`texture_index`/`material_index`, que se sustituyen por cobertura verificada y etiquetas resueltas por contenido. Los bloques opacos (`st_raw`, `neighbour_raw`, `vertex_raw`, `vbr_raw`) quedan en `value` como hex y se comparan exactos.
- Orientación: `min` sobre las tres rotaciones del triángulo distingue (a,b,c) de (c,b,a) cuando los tres índices son distintos, y la línea 34 exige exactamente eso. Multiplicidad: `labelled` es lista ordenada, no conjunto.
- Cobertura: `sorted(assigned)==range(len(faces))` rechaza huecos y solapes; sección vacía rechazada.
- Vértices del Roadway se comparan exactos y en orden, por lo que canonizar caras por índice es válido. Una permutación de vértices daría FAIL, no PASS.
- Selecciones o proxies en Roadway provocan `ValueError`; en producción eso aborta el empaquetado, no pasa.
- Todas las clases del reader usan `__slots__` sin herencia o `__dict__` puro, así que `normalized` no pierde atributos por la rama equivocada. `Vector3P` tiene slots x,y,z.
- Resolución 3e15 identifica Roadway correctamente.

**Hallazgo 1, test (`test_kit7_non_geometry_comparator.py` línea 8).** `zip(a.lods,b.lods)` trunca en silencio si el modelo nuevo tiene menos LODs. Un ODOL al que le faltase el Roadway pasaría el control positivo del test. La ruta de producción no lo sufre: `package_kit7_contact_only_v2.py` líneas 33 y 37 exigen cuatro LODs y resoluciones iguales por pareja. Fix: añadir en el test `assert len(a.lods)==len(b.lods)` y `assert old.resolution==new.resolution`.

**Hallazgo 2, endurecimiento opcional (líneas 41).** Al sustituir `sections` por `labelled_faces`, se descarta el número y orden de secciones. Dos secciones con metadata idéntica (misma textura, material, `special`, `min_bone`, `bones_count`, `area_over_tex`) fusionadas en una pasarían. Contraejemplo: Roadway con secciones S0 y S1 iguales salvo rango de caras, recompilado como una sola sección. En la práctica `area_over_tex` por sección hace casi imposible que una fusión real conserve los floats, y para Roadway la partición en secciones es solo batching sin efecto de motor. Fix barato: conservar `value['section_count']=len(lod.sections)` o el multiconjunto ordenado de `attrs`.

**Fuera de alcance, anotado.** `model_info` solo se compara en `bounding_center` en el empaquetado; masa, bbox y centro de masa cambian legítimamente al editar Geometry. El uint32 desconocido y los once floats de `Section.read` no se almacenan en el reader y por tanto no se comparan; es un límite del parser, no del comparador.

**Recomendación.** Aplicar el fix 1 al test antes de arrancar; el fix 2 es opcional. El comparador en sí es correcto para el uso declarado.
