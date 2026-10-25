**Veredicto: NO-GO.** El `contact-review.json` ya está en FAIL y el fallo es genuino según las cotas pactadas. El defecto bloqueante no es el FAIL en sí, sino que el revisor no dice dónde ocurre y ningún mecanismo del código explica su magnitud. Hasta localizarlo no hay candidatura válida.

## Hechos comprobados

Los recuentos del packing-report cuadran: la suma de los 27 modelos da 2245 componentes (no 273), partiendo de 25156. Sigue siendo 13 veces el kit de referencia.

| Métrica del overlay global | Valor | Cota |
|---|---|---|
| Error vertical máximo | +0,0142 m | 0,02 |
| Error vertical mínimo | **-0,2034 m** | -0,02 |
| Área sin cubrir / exceso lateral | 0 / 0 | ≤1e-6 |
| Cierre, convexidad, asignación de caras | 0 inválidos en 27 modelos | — |

El +0,0142 coincide exactamente con lo que predice el autor (cota 0,0299 menos desplazamiento 0,015625). El -0,2034 no lo predice nada.

**Lo que descarté con el código y los datos, no con suposiciones:**

- **Fondo o laterales confundidos con techo:** no. `add_component` fuerza normales hacia dentro y el revisor exige volumen firmado negativo (`review_compact_collision_v31.py:71`), así que el fondo plano tiene normal +y y queda excluido. Los laterales comparten XZ exacto con la base, con coordenadas múltiplos de 1/512 y productos exactos en double, por lo que la componente y del producto cruzado es exactamente 0 y el filtro `<-1e-10` (línea 78) los excluye sin margen de error.
- **Caras desaparecidas:** cubierto por la asignación única (línea 77), el cierre por componente y el área sin cubrir igual a 0.
- **Máximos de diferencias lineales:** sí están cubiertos. Cada intersección techo-fuente es un polígono convexo donde la diferencia es lineal, y `get_coordinates` incluye todos sus vértices. El test con esquinas idénticas lo demuestra.
- **Baricéntrica del revisor (líneas 25-30) y planos del autor (líneas 52-55):** ambas correctas e independientes; los índices de `STRtree.query` están bien asignados en ambos scripts.
- **Solapamiento entre chunks:** no existe. Los chunks comparten una fila y las 1520/836 componentes de los extremos se explican por las 8 filas de "cap" de `continuous_stream_pilot_v31.py:345-362`.
- **Pliegue del lecho en XZ:** descartado por los propios datos. Un pliegue produciría errores simétricos y el máximo positivo es solo 0,0142, lo que acota cualquier doble capa a 3 cm.
- **Delantal comprimido en curva cerrada:** descartado. El giro máximo del río 131 es 0,645°/m (radio ≈89 m), así que el límite de delantal no actúa y las columnas conservan su espaciado nominal.

## El problema central

Dentro de su propio dominio, el techo de cada componente es la envolvente cóncava de sus puntos y nunca queda por debajo de la fuente más que el desplazamiento (≤0,0156 m). Fuera del dominio, la extensión lateral está acotada a 1 cm (`compact_stream_collision_v31.py:36`), y el perfil del lecho tiene pendientes ≤0,5 con terreno suave. Ningún mecanismo derivable del código produce -0,20 m. Eso deja dos lecturas, y no puedo distinguirlas sin ejecutar:

- **Hipótesis A:** hay un defecto real en el MLOD guardado que no es visible desde el código (un techo 20 cm bajo el lecho visible, donde un jugador se hundiría). Sería grave y no se puede descartar.
- **Hipótesis B:** el par extremo es un techo extendido lateralmente sobre una fuente vecina en un punto concreto de los caps de los extremos (chunks 0000, 0300 y 0312 tienen las cotas locales más altas, 0,0299). La superficie física de colisión sería el máximo de todos los techos, no cada par por separado, y ahí podría estar dentro de tolerancia. El criterio por pares es más estricto que el físico. Esto es una decisión del usuario, no una razón para relajar el check.

## Defectos concretos

- **`review_compact_collision_v31.py:36-52`:** el overlay solo guarda mínimo y máximo globales. No registra modelo, componente, triángulo fuente ni coordenadas del extremo. Imposibilita el triaje. Añadir esa salida es diagnóstico, no suavizado.
- **`review_compact_collision_v31.py:44-45`:** la cobertura se evalúa sobre la unión de todos los techos, así que no distingue si cada componente cubre su propio dominio. No produce falso PASS aquí, pero no separa error propio de error cruzado.
- **`compact_stream_collision_v31.py:36`:** tolerancia lateral de 1 cm con tolerancia vertical de 2 cm solo es coherente si la pendiente vecina es ≤2. Inconsistencia de diseño, aunque no es la causa en este río.
- **`compact_stream_collision_v31.py:34,38,51,74`:** los `ValueError` de `fit_grid` y el `QhullError` del fallback por triángulo no se capturan en `split`, que solo captura `QhullError` de `fit_grid`. Un bloque degenerado aborta toda la ejecución en vez de subdividir.
- **`author_compact_collision.py:4-5`:** rutas absolutas y un `py3d` externo cuyo hash no se guarda en provenance. Las propiedades `class=house, damage=no` sí coinciden con el autor original (`continuous_stream_pilot_v31.py:376`), descartada esa sospecha.
- **`author_compact_collision.py:23-25`:** asume orden row-major de 39 columnas solo con `%39`. El revisor compensa usando las caras visuales reales, así que no hay falso PASS.
- **Tests:** ningún test ejercita el error cruzado entre componentes, el desplazamiento de centrado, el script autor ni un componente orientado hacia fuera. Las 5 pruebas pasan mientras el pipeline falla con datos reales.

## Siguiente paso necesario

Antes de cualquier decisión, una ejecución del revisor que vuelque para el mínimo: modelo, selección de componente, índice de triángulo fuente, xyz mundial y ambas alturas. Además un `overlay(source, source)` para certificar que el lecho es univaluado. Si el extremo cae dentro del dominio propio de un componente, es la hipótesis A y el empaquetador tiene un bug serio. Si cae en una franja de extensión lateral, es la hipótesis B y la decisión sobre el criterio por envolvente es del usuario. Compilado, motor y rendimiento siguen pendientes en cualquier caso.