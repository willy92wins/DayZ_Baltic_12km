# Corrección local de los brazos navegables del Neva

Estado: ejecución correctiva de P2/P9/P14 y del plan aprobado
`water-ground-rebuild-v1.md`, fase 2/5. BALTIC-013: dos brazos principales sin
el calado útil acordado; Pequeño Neva interrumpido antes del golfo.

## Evidencia y alcance

`evidence/v30-shore-pilot-2026-10-02/delta-audit/`: los ejes OSM de Gran/Pequeño
Neva fallan la comprobación continua sobre triángulos. No hay plataformas ni
reservas de carretera en sus vértices secos. Un experimento solo de fondo no
elimina el corte seco. Código causante de ambas dimensiones:
`tools/water/design_water_v3.py:124–126` (anchura media),
`tools/terrain/build_v30.py:430–431` (fondo decreciente hacia borde).

Se parte de NPZ `1117b4b1` (reparación Luga), nunca del piloto de orilla de Narva
`bb270ecc`, que sigue sin aceptación visual. Se conserva el diseño original.
La corrección será una capa separada, con salidas nuevas en E: y hashes.

## Método y límites fijados antes de construir

[DESIGN] Conservar los dos ejes OSM completos, sin recortar las bocas para
ocultar fallos. Perfil de fondo continuo según distancia al eje: calado mínimo
3,05 m con mar a 0,50 m. El fondo plano debe incluir todos los vértices de
soporte del corredor de 24 m: radio conservador 12 + diagonal de celda
sqrt(72) ≈20,486 m. Después asciende a 0,60 m/m hasta empalmar con el terreno
existente; solo se excava. Ancho de agua resultante alrededor de 52 m, dentro
del rango de diseño de navegables 30–60 m, con las ensenadas mayores conservadas.
No se aplicará a los brazos secundarios de 12–20 m.

El tramo OSM `way/34348577` une exactamente las cabeceras de ambos brazos
(21,7395 m) y `way/78518216` continúa 36,1517 m hacia el tronco del Neva.
Se incluyen esos dos segmentos fuente en la comprobación y la capa local;
no se inventa una recta que conecte dos puntos ni se recorta un fallo en la unión.

Límite espacial: 36 m alrededor de esos ejes; sin cambios fuera, ni en
plataformas fuera de reservas, Narva, cauces ajenos o núcleos de islas. Tierra convertida en
agua solo dentro de ese ámbito y con cota al menos 0,10 m bajo mar nominal.
La tierra restante conserva suelo ≥1,40 m y la máscara de playa original.
Antes de aceptar, medir que no desaparece ningún componente de isla seca
ni se altera su núcleo; el canal del Pequeño Neva debe separar la isla del
continente donde el trazado original fue rellenado.

## Puertas y parada

1. Fuente y axes por hash; máximo un candidato determinista inicial, una
   corrección solo si un fallo aislado explica el ajuste. Sin bucle de LP global.
2. Calado ≥2,99 m en todos los vértices de intersección corredor/triángulo,
   incluyendo extremos redondeados; controles afín, obstáculo y muestreo
   independiente. Comprobar enlace con mar y tronco del Neva por geometría
   real; no declarar conectividad por dos ejes separados.
3. Terreno y carreteras pasan; también los corredores retenidos anteriores.
   Congelar cobertura vial anterior para no ocultar estaciones al ampliar agua.
   Plataformas fuera de reservas/Narva y alturas fuera del ámbito idénticas. Piezas pond y
   puentes deben conservar poses; no se modifica la cota de agua.
4. Mapas comparables de línea de agua a marea mínima/nominal/máxima, islas,
   taludes y cambios. Candidato rechazado si sacrifica una isla o exige tocar
   una carretera fuera de la reserva acordada.
5. Reconstruir superficie y WRP en un mod aislado, inspeccionar PBO real y
   probar en motor. Navmesh nueva después de fijar la geometría; cualquier
   navmesh heredada de una compilación de previsualización queda marcada
   obsoleta, nunca presentada como navegación de este terreno.

El piloto de suavizado de Narva no se integra por tener buenas métricas:
su franja somera oscura necesita una resolución visual independiente.

## Revisión antes de guardar el candidato

La primera evaluación se detuvo en la protección de infraestructura, sin
escribir NPZ/ASC. El enlace adicional al tronco toca 52 vértices protegidos;
dos pertenecen a plataforma fuera de la reserva. Los dos brazos originales
no tenían ese conflicto. Recibo con coordenadas y cotas:
`delta-audit/first-candidate-protected-conflict.json` en la evidencia del piloto.

La prohibición inicial de tocar toda reserva era más restrictiva y contradictoria
con la fase 2 aprobada: los nuevos cruces fluviales quedan como reservas de puente
o vado hasta el mapeado. Corrección acotada del método: congelar plataformas fuera
de reserva y también todos los vértices secos que permanezcan secos dentro de
ella. Solo se permite excavar fondo existente o vértices convertidos a agua
dentro de esa reserva, para abrir el canal acordado. Registrar la cantidad y
extensión del futuro cruce; no presentarlo como carretera transitable ni puente
ya colocado. Comprobar las mismas estaciones viales anteriores, sin reducir
la cobertura con la nueva máscara. No se altera ningún objeto de puente.
