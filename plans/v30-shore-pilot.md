# Piloto de orilla de Narva sur — 02-10

Continúa P9/P10 y BALTIC-007 dentro del plan de agua/suelo aprobado. Guillermo
ha vuelto a habilitar Computer Use. El banco compartido sigue ocupado por otro
proyecto; preparar el piloto sin intervenir en ese run.

Descubrimiento: en la vista de jugador (1062,4836), hay vértices mojados a menos
de 3 m del contorno con más de 2,5 m de profundidad. `build_v30.py:419–440`
conserva el fondo más profundo al aplicar la forma de orilla. Es un mecanismo
candidato para el dentado, aún sin aislar visualmente en A/B.

Experimento acotado: un candidato separado sobre la copia del Luga `1117b4b1`.
Solo elevar vértices de clase navegable a menos de 6 m de la orilla, dentro de
150 m del punto observado, transición radial 100–150 m y rebaje hacia el fondo
entre 3–6 m de distancia al borde. Límite de elevación 4 m. Objetivo provisional
de talud: 0,12 m por metro desde el contorno, profundidad mínima 0,10 m.

Fijar todos los vértices de triángulos que intersectan los 19 corredores útiles
ya auditados, además de plataformas, reservas y Narva protegido (620 m).
No cambiar máscaras, agua, diseño XY, alturas secas ni la copia desplegada.

PASS offline: cambios solo en el conjunto permitido; corredores numéricamente
idénticos; puertas existentes de terreno/carreteras PASS; error de la línea de
agua respecto al diseño local menor y sin nuevos saltos/triángulos excesivos.
El gráfico es diagnóstico, no aceptación del render. Si no mejora o rompe una
puerta, conservarlo rechazado, sin ampliar límites ni hacer más candidatos.
Si pasa, preparar A/B en el mismo punto. No regenerar navmesh hasta decidir las
correcciones geométricas que se incorporan juntas.

Resultado del único piloto: 199 vértices elevados, máximo 4 m; error medio de
orilla 2,50→0,71 m; caras mixtas >35° 40→6. Terreno, carreteras y los 19 corredores
auditados PASS. Preparar una copia de texturas/WRP en una carpeta de preview,
reutilizando el agua idéntica. La navmesh heredada de la preview es provisional;
este A/B solo juzga la geometría y el render, sin afirmar navegación actualizada.

Comparación: misión temporal nueva BalticV30ShoreCompareV1, laguna y Narva sur,
90 s por sitio, clima/posiciones/sondas iguales en A y B. Addon temporal
baltic_visual_ui_probe para solicitar una vez Continue si aparece MENU_INGAME,
con guardas y verificación detalladas en tests/visual-ui-probe/README.md.
Capturar desde el jugador, sin camera_set. Conservar A intacto y retirar B de la
lista de carga si su vista empeora. No hay escrituras de posición durante una
prueba física: esta misión se clasifica explícitamente como inspección visual.
