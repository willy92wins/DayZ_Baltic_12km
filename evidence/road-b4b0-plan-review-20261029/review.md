**Veredicto: SOUND-with-fixes.** El diseño de B4B0 avanza una correspondencia fuente–índice guardado sin falso PASS: los únicos estados de salida son índice-only o mismatch, build_ready queda en false, no reabre PBO ni repite censos A/B0/B1, y no afirma cierre de LOD por los 8 PBOs ni resolución de escena por los 12 recursos de B4A3. Los fallos concretos son de anclaje, no de dirección.

**Lo que se sostiene**

- **Formato anclado correctamente.** Los dos lectores sellados coinciden en header 24 bytes, skips de alturas y materiales, registro fijo de 56 bytes con id y longitud en el offset 48, y terminador exacto al EOF. Ambos descartan el nombre, así que un extractor nuevo que cuente nombres es necesario y no duplica nada.
- **Referente independiente existe.** La prueba del consumidor contra un referente literal y no contra la salida del productor está declarada. Hay que mantenerla como fixture escrita a mano.
- **Catálogo real.** Report fija 5509 modelos y 2578398 instancias, catalogo ae1a5ff7 fija nombre por índice y cuenta, y la verificación histórica (línea 389 de collision_scene_b2a_ev112) ya compara por normalización, no por bytes crudos. El plan lo trata como relación de nombres y cuentas, no identidad geométrica. Correcto.
- **Aritmética del candidato plausible.** La diferencia de tamaño es 283 bytes, que cuadra con tres registros de 56 bytes más 115 bytes de nombres. Es una comprobación de sanidad, no verificación.
- **Límites.** Caps de 512 MiB, nombre 4096 y 10000 referencias antes de alloc o read, set de IDs acotado a 3M, memoria 1 GiB. Suficiente para 2.58M ids y 5509 claves.

**Fallos a corregir antes de implementar**

1. **Normalización del join no anclada.** El plan dice "distinguir alias por slash/case documentado" pero no fija qué función normaliza. La fuente 0WZD usará con toda probabilidad backslash y mayúsculas, mientras el catálogo usa slash y minúsculas. Fix mínimo: importar `norm` del módulo B2A sellado (importar no es llamar CLI) o copiarla con un test de equivalencia sobre casos literales. Regla explícita: sólo diferencias de slash y case se fusionan bajo una clave; cualquier otra diferencia entre formas crudas que caigan en la misma clave es UNRESOLVED.
2. **Consumidor sin verificación de pins de entrada.** Está descrito como lector del reporte contra catálogo, receta y modelos, pero no exige que el reporte lleve hash y tamaño de fuente y candidato, ni que el consumidor los coteje con los pins b108 y 46063f37 y con los hashes de models/report/catalog antes de comparar. Sin eso un reporte viejo o de otra fuente pasa el join. Fix: el reporte incluye hash antes y después, stat y tamaño; el consumidor rechaza si antes distinto de después o si cualquier pin no coincide con el literal de la receta.
3. **Delta del candidato ambiguo.** "Delta 3 exacto" mezcla instancias y nombres. Fix: delta de instancias +3 leído de los tres registros finales del candidato, nombres esperados tomados del reporte B3 literal, y cada uno con estado propio. Si el nombre no está en el catálogo B2A, el estado es "nuevo respecto a B2A, proveedor sólo por pin B4A3", nunca MATCH. Leer esos tres registros, no confiarlos de B3.
4. **Caps declarados sin prueba negativa.** La suite enumera truncados, traversal y duplicados, pero no nombre mayor de 4096, nombre no ASCII, más de 10000 referencias ni models.json con dos entradas que normalizan al mismo nombre con SHA distinto. Fix: cuatro fixtures negativos más.
5. **Rendimiento del extractor.** 2.58M lecturas de 56 bytes por syscall más dos hashes de 286 MiB caben en 120 segundos, pero sin margen si se lee por registro. Fix: lector chunked con buffer propio, sin cargar el archivo entero como hacen los lectores sellados.

**Lo que no cambia**

La unidad sigue siendo lectura. No prueba precedencia actual, correspondencia con P: instalada, ni cobertura de materiales o texturas, que quedan NOT_EVALUATED. Los dos paquetes bajo rutas P:\Mods y package-kit7 son rutas build históricas, categoría que el plan ya separa. Si la relación completa no se demuestra, el resultado es INCONCLUSIVE_REFERENCE_MISMATCH y plan separado, sin adjudicar causa.

Con los cinco fixes aplicados en el contrato, la unidad puede pasar a autoría acotada bajo el presupuesto propuesto.