No encontré ningún fallo de geometría que invalide ninguna de las dos operaciones. Los problemas están en la trazabilidad de las puertas y en cómo se interpretan las métricas. Lo he comprobado solo leyendo los scripts y JSON de la lista; no he ejecutado nada.

## Hallazgos

**1. Media — el PASS de carreteras no está ligado al candidato.**
- **Dónde:** `review_small_watercourse_fix_v30.py:70-71` lee `road-gates.json` del directorio del candidato y solo mira `status`, `samples` y `chains`. Ese archivo no guarda ningún hash del terreno (`v30-watercourse-continuity/road-gates.json:1-43`).
- **Riesgo:** una copia antigua o de otra carpeta daría el mismo PASS. Por lectura, la geometría está protegida igualmente, porque plataforma y reserva están en `fixed` y `all_fixed_heights_exact` lo confirma. El hueco es de procedencia, no de geometría.
- **Corrección mínima:** que la puerta de carreteras escriba `terrain_sha256` y que la revisión exija que coincida con `sha(candidate)`. Lo mismo para `legacy-terrain-gates.json`.

**2. Media — el consumidor "independiente" mide justo lo que se optimizó, con un umbral más laxo.**
- **Dónde:** el constructor usa como núcleo el eje de `profiles.npz` ±0,5 m (`connect_small_watercourses_v30.py:36`). La auditoría muestrea exactamente ese eje (`audit_small_watercourses_v30.py:48-51`) y lo da por mojado con cualquier profundidad mayor que 0 (`:57-59`).
- **Riesgo:** pasar de 12,05 a 0,40 km de arroyo seco es casi automático, porque se midió la misma línea que se optimizó. No demuestra los 5 cm objetivo ni la franja de 1 m, y 1 mm de agua cuenta como continuidad.
- **Corrección mínima:** publicar también los km con profundidad < 0,05 m y muestrear dos líneas desplazadas ±0,5 m. Sería mejor llamarlo "autoconsistencia del eje", no "independiente".

**3. Baja — el halo de exclusión vial es más ancho que la reserva.**
- **Dónde:** `tri_sample(fixed)>0` (`audit_small_watercourses_v30.py:58`) excluye cualquier muestra cuyo triángulo toque un solo vértice de plataforma o reserva.
- **Riesgo:** eso deja fuera hasta unos 6 m más allá de la reserva en cada cruce. Así que "400 m fuera de plataformas/reservas" infravalora lo que queda seco.
- **Corrección mínima:** reportar aparte las muestras en las que el peso de la plataforma es menor que 1.

**4. Baja — la comparación antes/después solo se ata por el hash del terreno.**
- **Dónde:** `review_small_watercourse_fix_v30.py:49` no compara `sources` ni la versión del script de auditoría, que tampoco se guarda en su propio JSON.
- **Corrección mínima:** exigir `before['sources']==after['sources']` y añadir el hash del script.

**5. Baja-media — las entradas no incluyen las definiciones importadas.**
- **Dónde:** `restore_narva_ponds_v30.py:84` y `connect_small_watercourses_v30.py:123` hashean los datos y su propio archivo. No hashean `v30_common.py` (`cell_planes`), `audit_fairway_triangles_v30.py` (`records`) ni `finish_shores_v30.py`.
- **Riesgo:** según git status, `v30_common.py` está modificado sin commit. `cell_planes` decide los planos de las piezas, así que no se puede demostrar con qué versión se hicieron las piezas reutilizadas.
- **Corrección mínima:** hashear esos tres módulos en `inputs` y hacer commit de `v30_common.py`.

**6. Baja — la referencia del delta de piezas es preview6, no la fuente 73b.**
- **Dónde:** `v30-pond-recovery/water/local-delta.json:91` compara con `v30-preview6/water/pieces.json`.
- **Riesgo:** si preview6 no tiene las mismas `cls`/`level` que 73b, la cifra de "16 cambiadas y 17.621 sin cambios" no es respecto a la fuente real. Es probable que coincida, porque el acabado de orillas no cambió metadatos, pero no está demostrado.
- **Corrección mínima:** comprobar los hashes de `cls`/`level` de preview6 frente a 73b.

**7. Documentación — la continuidad sí cambia suelo seco fuera de la reserva natural.**
- **Dato:** `build.json` registra 10.156 vértices secos rebajados (como mucho 1,53 m, con suelo ≥ 1,4 m y margen ≥ 5 cm sobre las piezas). El código lo permite (`connect:60`).
- "Todo el suelo seco queda idéntico" solo es cierto dentro de la reserva natural (`nature_dry_land_exact`). Conviene precisarlo en el plan.

## Empaquetado: qué se puede reutilizar al bajar solo alturas

**Demostrado por lectura:**
- La continuidad deja `cls`, `level`, `water`, `platform`, `reserve`, `narva` y `beach` idénticos.
- Los planos dependen solo de `cls`/`level` (`v30_common.py:88-104`).
- Por tanto, si el generador de piezas solo usa `cell_planes`, las piezas de pond-recovery valen para el candidato 40d8. No localicé el script que genera las piezas. En `build_v30_water.py` y `prepare_v30_native_surface.py` no aparece ninguna lectura de alturas.

**Hay que regenerar sí o sí:**
- La importación nativa del `.asc`.
- La navmesh: cambian 22.468 vértices, de ellos 10.156 de tierra.

**Requiere prueba en DayZ / Terrain Builder:**
- Objetos colocados con altura absoluta, o con el desfase relativo que ya os dio problemas (`before-relative-offset-correction.tv4l`), sobre los 10.156 vértices rebajados: pueden quedar flotando.
- Objetos dentro de las 4 lagunas, que ahora quedan en agua.
- Si una franja mojada de 1 m bajo un plano de celda de 6 m se ve como cauce o como charcos.
- Si la colisión física coincide con la triangulación NW-SE del modelo.

## Revisado sin fallos

- **Lagunas:**
  - El alcance de clase/nivel coincide con la huella completa porque `ponds_do_not_intersect_fixed_vertices` es verdadero.
  - El cambio de plano en celdas vecinas está cubierto por las comprobaciones de esquinas mojadas y secas.
  - El FAIL legado de Narva (máx. 1,84 m, `legacy-terrain-gates.json:46-51`) se hereda sin ocultarse.
- **Proyección de la continuidad:**
  - Las restricciones son cotas superiores con pesos no negativos y solo se baja, así que la factibilidad por fila implica factibilidad conjunta.
  - La conversión a float32 queda dentro de la holgura de 1e-4.
  - Las 1.395 filas factibles que siguen fallando vienen de la reversión de 332 vértices por caras > 35°, y están reportadas.
  - Un `level` NaN en el vecino más cercano no puede entrar en filas usadas, porque su suma sale NaN y esas filas cuentan como inviables.
  - La comprobación de caras > 35° de la revisión cubre todas las caras, no solo las de tierra, así que es más estricta que la del constructor.
