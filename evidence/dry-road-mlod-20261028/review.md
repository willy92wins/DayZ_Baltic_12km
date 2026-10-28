**Veredicto: SOUND-with-fixes.** El autor y el consumidor implementan el plan con fidelidad; no encontré una vía de falso PASS sobre los datos reales. Hay tres correcciones que deberían entrar antes de aceptar MLOD_OFFLINE_VERIFIED, y ninguna requiere rediseño.

**Lo que verifiqué y coincide**

- **Layout de bytes.** El patcher asume cabecera de 28 bytes, puntos de 16 y normales de 12 seguidas. Coincide con `LOD.write` en py3d (`__init__.py:2885-2901`) y con `Point.read` (`:1799`). Los offsets del consumidor son los mismos pero calculados desde el LOD fuente y desde el tamaño del NPZ, no desde el informe del autor.
- **Anclas.** El SHA de fuente bbf4d5e4, el candidato 93168efe y el origen 8262/7/8934 coinciden con el descubrimiento. La clave del manifiesto para current-source-pins existe con sha f17273… y las claves de lineage son rutas Windows absolutas, que `str(Path)` reproduce si root se pasa como `E:/…`. Desajuste de forma falla cerrado por KeyError, no por falso PASS.
- **Mapa XYZ y prismas.** source_grid es `points.reshape(n,m,3)` con m=39; 819=21×39 y 2×20×38=1520 caras, igual que los 1520 componentes. El corte `grid[:len(old)]` del candidato queda anclado por la igualdad XZ exacta con la fuente, así que un corte erróneo falla cerrado.
- **Geometría.** Desplazar techo y suelo con el mismo ΔY por vértice conserva lados paralelogramos planos, convexidad, volumen y XZ. El consumidor lo reconfirma con cierre, volumen ≤1e-9, convexidad y correspondencia techo/suelo con el visible guardado por XZ.
- **Normales.** `normals()` reproduce `add_mesh` (normal geométrica descendente, Roadway negada); `face_normals()` reproduce `add_prism` con normal interior, por eso la selección de techo usa n_y<0. La reproducción float32 se exige en tiempo de ejecución sobre la fuente, no se asume.
- **Compare-self.** Copiar la fuente sin cambios falla en `bed_not_numeric_candidate` porque el candidato difiere en 82 Y. Bien.
- **Aritmética exacta.** Coordenadas float32 en rejilla 1/512 con |Y| pequeño: suma y resta de 180/512 son exactas en float64 y representables en float32; el autor además rechaza `nonrepresentable_height`.

**Correcciones (una ronda)**

1. **Independencia de anclas en el consumidor.** `verify_dry_road_mlod_ev112.py:81-82` toma la lista de pins de `inputs.json`, escrito por el autor. El consumidor no fija por sí mismo bbf4d5e4, 93168efe ni el sha del lineage. Un `inputs.json` reescrito apuntando a otro NPZ con su propio hash pasaría. Fijar esas tres constantes dentro del consumidor.
2. **Contrapruebas del plan aún no ejecutadas contra `check_saved`.** El plan §3 exige rechazo de aguaY, lechoX, UV/tag, normal girada, techo+5cm y media cubierta. Los tests sólo prueban `overlay` a nivel de API con triángulos sintéticos. Falta mutar bytes del archivo real de salida y ejecutar `check_saved` para cada caso, más el positivo real antes/después. Son ejecutables en segundos; sin ellos el VERDE no cumple el propio plan.
3. **Huecos en la allowlist de bytes.** En LOD 1 toda la región de normales está permitida; sólo se comprueban las referenciadas por caras, así que una normal no referenciada quedaría libre. En LOD 0/3 no se comprueba que ninguna cara no‑lecho (agua) referencie índices de normal <819. Añadir: conjunto de normales referenciadas == rango completo en LOD 1, y ninguna cara fuera del lecho usa normales <count en LOD 0/3.

**Backlog (no bloquean)**

- El consumidor no fija su propio código ni mesh_quality_v31; el autor sí se fija a sí mismo.
- El test file tiene 6 métodos, no 7 como indica el contexto.
- La junta se verifica contra la última fila de source_grid de extracción, no contra la primera fila del MLOD vecino; aceptable dado que los 200 restantes van por hash.
- Añadir aserción explícita de que el corte del candidato difiere de la fuente en exactamente 82 Y por LOD, para cerrar el compare-self por construcción.
- `Point.read` usa `"fff"` sin `<`; sólo relevante fuera de x86.

**Riesgos de ejecución real (no de diseño)**

Si alguna Y del candidato no está en la rejilla 1/512, el autor fallará con `nonrepresentable_height` o el consumidor con `geometry_not_saved_visual_prism`; ambos cierran, no aprueban. El presupuesto de 120 s incluye rehash de 201 modelos y py3d dos veces; debería bastar.

Compilación, centro ODOL, poses y motor siguen pendientes y no quedan cubiertos por nada de lo anterior.

FIN_REVISION
