# Zigzags de RIVER_80 en la v9 — diagnóstico (06-10-2026)

Guillermo, sobre la vista RIVER_80 de la v9: «aún tiene ríos que hacen zig-zag y otros patrones angulados, falta
smoothing». Diagnóstico sobre el terreno y la textura que recibe el motor, sin pasar por las métricas de las
herramientas que dan forma a las orillas.

## Qué es cada zigzag (`river80-located.json`, `scripts/locate_v9.py`)

Píxeles de la captura proyectados sobre el terreno de la v9: el río principal es river_057 (el **Msta**, clase 5,
nivel 1,0 m), el estanque dentado es un estanque OSM (way/26698284), la «W» es river_075, la red de la derecha
river_074 (acaba en un corte cuadrado a 60 m del borde) y el canal recto de la marca A es lake_135, el **canal de
Sivers** (OSM way/22328675, canal real del siglo XVIII).

## Causas

1. **La pasada única de orillas usa un contorno de malla.** `tools/terrain/profile_inland_v30.py:151-164` calcula el
   contorno de cada componente desde la malla de clases de 6 m (distancia, gaussiana, tope de 4 m). Una fila recta
   de la malla sigue recta tras suavizar: la orilla visible de los ríos va por filas de la malla. En la v6 (paso 25,
   que ajusta los cruces al contorno vectorial `sd_shape`) la orilla seguía el diseño en diagonal; la pasada la
   empeoró (`river80-waterline-v6-v9-proto.png`). Su métrica medía contra su propio contorno y no lo vio.
2. **Lagos y estanques ya son angulosos en el diseño.** Los lagos del contorno v2 heredan la escalera del ráster V29;
   los estanques OSM son polígonos toscos (`polygon-smoothing-sigma12.png`).
3. **El agua muy baja tiene la orilla clavada.** Con el agua a 1,0 m, el fondo a 0,70 m (nivel − 0,30) y la tierra en
   su suelo de 1,40 m, el cruce solo cabe a 2,6 m o menos del vértice mojado (`msta-low-water-pinned.png`). Son el
   1,1 % de las aristas de orilla del mapa (1.404 de 131.782, niveles 0,98–1,10 m) y el 33 % en la ventana de RIVER_80
   (`scripts/pinned_edges.py`).
4. **La textura.** Los bordes de bosque y pradera salen del vértice más cercano de la malla de 6 m: dientes vistos
   desde el aire (`landcover-nearest-vs-smooth.png`; con campos de clase difuminados un vértice cambia el 6,7 % de
   los píxeles). La franja parda de orilla sigue la línea de agua (`satellite-v8-v9.png`).

## Métrica independiente (`visible-waterline-metric.json`, `scripts/waterline_metric.py`)

Para cada punto del contorno de diseño, cada 2 m, se busca a lo largo de la normal dónde acaba el agua visible (el
terreno sobre los triángulos nativos por debajo del plano de la celda, como lo dibujan el motor y la superficie) y se
mide la distancia al diseño y el giro de la línea visible en cuerdas de 6 m. Fuera quedan la franja de 66 m del borde,
Narva y los navegables y el delta.

| clase | giros > 45° del diseño | v6 visible | v9 visible | prototipo (contorno vectorial) |
|---|---|---|---|---|
| lagos | 21,6 % | 22,9 % | 21,4 % | 23,4 % |
| estanques | 26,7 % | 33,3 % | 32,7 % | 33,8 % |
| ríos | 6,9 % | 10,5 % | 16,7 % | 10,8 % |
| arroyos | 0,7 % | 18,8 % | 10,5 % | 19,4 % |

Distancia de la orilla visible al diseño (p50/p90) en ríos: v6 0,62/2,38 m, v9 1,62/4,12 m, prototipo 0,88/2,62 m.
Los arroyos (3–6 m) son más estrechos de lo que la malla puede dibujar: el contorno de malla les da menos quiebros.

## Decisiones de Guillermo (06-10) y siguiente candidato (v10)

- Suavizar lagos, estanques y cuerpos de río a lo largo de su contorno: σ 12 m, cada punto como mucho 4 m, área
  conservada (`polygon-smoothing-12-4.json`: giros > 45° en lagos 20,4 → 8,6 %, estanques 25,8 → 16,9 %, ríos
  9,0 → 4,3 %).
- Bajar solo el vértice de orilla del agua muy baja hasta el nivel + 0,05 m (mínimo 1,0 m); vigilar en RIVER_8 el
  parpadeo de BALTIC-016.
- Bordes de bosque y pradera suavizados en la textura.
- El canal de Sivers sigue recto; solo se redondean sus uniones.
- La pasada de orillas sigue el contorno vectorial en lagos, estanques y ríos; los arroyos conservan el de malla.
- Puerta: la métrica de arriba, por clase, mejor que la v9 (arroyos, como mucho medio punto peor) y sin empeorar la
  distancia p90; puertas del terreno sin fallos nuevos; dos rondas de arreglos como máximo.
