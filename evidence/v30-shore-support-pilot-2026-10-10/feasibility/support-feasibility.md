# Libertad local con soporte de agua EV82-B

Diagnóstico local; no modifica terreno ni candidato. P y F están byte-idénticos entre EV79, EV80 y B.

Hashes: terrain EV79 `dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c`, EV80 `0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b`, B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`; P `768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0`; F `f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`; constraints `ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c`; valley masks `685b3b9a337bca849f9338a27385ef959ee938fd37ab492d044419d236c64af2`.

## Contrato usado

La celda nativa se divide en NW–NE–SE y NW–SW–SE. P aporta un plano físico por celda; el consumidor usa el nivel nominal `max(P,0.85)` y 0.85 si falta P. F aporta alturas visibles raw por esquina en orden NW, NE, SW, SE cuando P existe; cuando no, el consumidor sustituye mar 0.85. Ambos se intersectan por triángulo. Para una arista que cruza la superficie L, se calcula `t=-d_i/(d_j-d_i)`, `d=h-L`; congelar el punto de cruce requiere `(1-t)δ_i+tδ_j=0`. Los segmentos sin cruce conservan signos mediante desigualdades: eso conserva la topología mojado/seco en los extremos, no el lugar del contorno ni el área mojada.

En cada parche 7×7 se fija el anillo exterior y todas las protecciones EV79 salvo `wet_support`, que se relaja solo en el análisis. Las cotas usan el presupuesto total EV79 ±2m y su suelo implementado `max(h79-2, min(h79, max incident P/F/0.85 + 1e-4), min(h79,1.8))`; los puntos ya sumergidos no pueden elevar su fondo (`δ<=0`) como condición conservadora adicional del análisis. El 0.95m se informa contra la geometría vigente; no se atribuye al EV79 como regla universal. Los nodos class!=0 y demás `other_fixed` siguen inmóviles.

## pico_(1146,1002) · filas 1877–1883, columnas 188–194
Nodos bloqueados incluyendo borde: 28/49. wet_support-only interiores temporalmente variables: 8.
P/F locales: 11 celdas con P; 44 esquinas F válidas; diferencias F vs P nominal >1e-10: 0. P+F no añade aquí ecuaciones independientes a P.

### P: exact P crossings + P sign topology
Rango igualdad 36/49; nullidad antes de inecuaciones 13; desigualdades no-cruce 392.
Cruces/no-cruces por superficie: `{"P": {"crossing_edges": 24, "no_cross_edges": 172, "coincident_edges": 0}}`.

- (1146,1002) m, B=6.325840m, selector=False, fixed original=True, wet_support=True, other_fixed=False: δ admisible [-0.0,-0.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[4.325840,8.325840]m, delta bounds desde B=[-2.0, 2.0]m.
  Clearances incidentales de superficie=[-5.4758, -5.4758, -5.4758, -3.6758, -3.6758]m; rango [-5.4758,-3.6758]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).
  Ecuación P directa: arista [[1881, 192], [1880, 191]] en celda/tri [1880, 191]/0, t=0.071158; coeficiente del objetivo=0.071158, vecino [1881, 192] coef=0.928842, vecino locked=True (cls=6, water=True, other_fixed=True). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.

### P+F: exact P and F crossings + sign topology
Rango igualdad 36/49; nullidad antes de inecuaciones 13; desigualdades no-cruce 784.
Cruces/no-cruces por superficie: `{"P": {"crossing_edges": 24, "no_cross_edges": 172, "coincident_edges": 0}, "F": {"crossing_edges": 24, "no_cross_edges": 172, "coincident_edges": 0}}`.

- (1146,1002) m, B=6.325840m, selector=False, fixed original=True, wet_support=True, other_fixed=False: δ admisible [-0.0,-0.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[4.325840,8.325840]m, delta bounds desde B=[-2.0, 2.0]m.
  Clearances incidentales de superficie=[-5.4758, -5.4758, -5.4758, -3.6758, -3.6758]m; rango [-5.4758,-3.6758]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).
  Ecuación P directa: arista [[1881, 192], [1880, 191]] en celda/tri [1880, 191]/0, t=0.071158; coeficiente del objetivo=0.071158, vecino [1881, 192] coef=0.928842, vecino locked=True (cls=6, water=True, other_fixed=True). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.

### topology-only: sign topology only; crossing locations and area not fixed
Rango igualdad 28/49; nullidad antes de inecuaciones 21; desigualdades no-cruce 864.
Cruces/no-cruces por superficie: `{"P": {"crossing_edges": 44, "no_cross_edges": 172, "coincident_edges": 0}, "F": {"crossing_edges": 44, "no_cross_edges": 172, "coincident_edges": 0}}`.

- (1146,1002) m, B=6.325840m, selector=False, fixed original=True, wet_support=True, other_fixed=False: δ admisible [-2.0,2.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[4.325840,8.325840]m, delta bounds desde B=[-2.0, 2.0]m.
  Clearances incidentales de superficie=[-5.4758, -5.4758, -5.4758, -3.6758, -3.6758]m; rango [-5.4758,-3.6758]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).

## escalones_(2196,1566_y_1572) · filas 1782–1788, columnas 363–369
Nodos bloqueados incluyendo borde: 31/49. wet_support-only interiores temporalmente variables: 10.
P/F locales: 16 celdas con P; 64 esquinas F válidas; diferencias F vs P nominal >1e-10: 0. P+F no añade aquí ecuaciones independientes a P.

### P: exact P crossings + P sign topology
Rango igualdad 41/49; nullidad antes de inecuaciones 8; desigualdades no-cruce 372.
Cruces/no-cruces por superficie: `{"P": {"crossing_edges": 34, "no_cross_edges": 152, "coincident_edges": 0}}`.

- (2196,1566) m, B=2.372809m, selector=False, fixed original=True, wet_support=True, other_fixed=True: δ admisible [0.0,0.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[2.372809,4.372809]m, delta bounds desde B=[0.0, 0.0]m.
  Clearances incidentales de superficie=[0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772]m; rango [0.3772,0.3772]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).
  Ecuación P directa: arista [[1785, 366], [1786, 366]] en celda/tri [1785, 365]/0, t=0.900316; coeficiente del objetivo=0.900316, vecino [1785, 366] coef=0.099684, vecino locked=False (cls=0, water=False, other_fixed=False). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
  Ecuación P directa: arista [[1786, 366], [1785, 365]] en celda/tri [1785, 365]/0, t=0.114760; coeficiente del objetivo=0.885240, vecino [1785, 365] coef=0.114760, vecino locked=False (cls=0, water=False, other_fixed=False). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
  Ecuación P directa: arista [[1786, 366], [1787, 366]] en celda/tri [1786, 365]/0, t=0.490460; coeficiente del objetivo=0.509540, vecino [1787, 366] coef=0.490460, vecino locked=False (cls=0, water=False, other_fixed=False). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
  Ecuación P directa: arista [[1787, 367], [1786, 366]] en celda/tri [1786, 366]/0, t=0.639884; coeficiente del objetivo=0.639884, vecino [1787, 367] coef=0.360116, vecino locked=False (cls=0, water=False, other_fixed=False). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
- (2196,1572) m, B=6.156673m, selector=False, fixed original=True, wet_support=True, other_fixed=False: δ admisible [-0.0,-0.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[4.156673,8.156673]m, delta bounds desde B=[-2.0, 2.0]m.
  Clearances incidentales de superficie=[-5.3067, -5.3067, -3.4067, -3.4067, -3.4067, -3.4067]m; rango [-5.3067,-3.4067]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).
  Ecuación P directa: arista [[1785, 366], [1786, 366]] en celda/tri [1785, 365]/0, t=0.900316; coeficiente del objetivo=0.099684, vecino [1786, 366] coef=0.900316, vecino locked=True (cls=6, water=True, other_fixed=True). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
  Ecuación P directa: arista [[1786, 367], [1785, 366]] en celda/tri [1785, 366]/0, t=0.159137; coeficiente del objetivo=0.159137, vecino [1786, 367] coef=0.840863, vecino locked=True (cls=6, water=True, other_fixed=True). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.

### P+F: exact P and F crossings + sign topology
Rango igualdad 41/49; nullidad antes de inecuaciones 8; desigualdades no-cruce 744.
Cruces/no-cruces por superficie: `{"P": {"crossing_edges": 34, "no_cross_edges": 152, "coincident_edges": 0}, "F": {"crossing_edges": 34, "no_cross_edges": 152, "coincident_edges": 0}}`.

- (2196,1566) m, B=2.372809m, selector=False, fixed original=True, wet_support=True, other_fixed=True: δ admisible [0.0,0.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[2.372809,4.372809]m, delta bounds desde B=[0.0, 0.0]m.
  Clearances incidentales de superficie=[0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772]m; rango [0.3772,0.3772]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).
  Ecuación P directa: arista [[1785, 366], [1786, 366]] en celda/tri [1785, 365]/0, t=0.900316; coeficiente del objetivo=0.900316, vecino [1785, 366] coef=0.099684, vecino locked=False (cls=0, water=False, other_fixed=False). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
  Ecuación P directa: arista [[1786, 366], [1785, 365]] en celda/tri [1785, 365]/0, t=0.114760; coeficiente del objetivo=0.885240, vecino [1785, 365] coef=0.114760, vecino locked=False (cls=0, water=False, other_fixed=False). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
  Ecuación P directa: arista [[1786, 366], [1787, 366]] en celda/tri [1786, 365]/0, t=0.490460; coeficiente del objetivo=0.509540, vecino [1787, 366] coef=0.490460, vecino locked=False (cls=0, water=False, other_fixed=False). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
  Ecuación P directa: arista [[1787, 367], [1786, 366]] en celda/tri [1786, 366]/0, t=0.639884; coeficiente del objetivo=0.639884, vecino [1787, 367] coef=0.360116, vecino locked=False (cls=0, water=False, other_fixed=False). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
- (2196,1572) m, B=6.156673m, selector=False, fixed original=True, wet_support=True, other_fixed=False: δ admisible [-0.0,-0.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[4.156673,8.156673]m, delta bounds desde B=[-2.0, 2.0]m.
  Clearances incidentales de superficie=[-5.3067, -5.3067, -3.4067, -3.4067, -3.4067, -3.4067]m; rango [-5.3067,-3.4067]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).
  Ecuación P directa: arista [[1785, 366], [1786, 366]] en celda/tri [1785, 365]/0, t=0.900316; coeficiente del objetivo=0.099684, vecino [1786, 366] coef=0.900316, vecino locked=True (cls=6, water=True, other_fixed=True). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.
  Ecuación P directa: arista [[1786, 367], [1785, 366]] en celda/tri [1785, 366]/0, t=0.159137; coeficiente del objetivo=0.159137, vecino [1786, 367] coef=0.840863, vecino locked=True (cls=6, water=True, other_fixed=True). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.

### topology-only: sign topology only; crossing locations and area not fixed
Rango igualdad 31/49; nullidad antes de inecuaciones 18; desigualdades no-cruce 864.
Cruces/no-cruces por superficie: `{"P": {"crossing_edges": 64, "no_cross_edges": 152, "coincident_edges": 0}, "F": {"crossing_edges": 64, "no_cross_edges": 152, "coincident_edges": 0}}`.

- (2196,1566) m, B=2.372809m, selector=False, fixed original=True, wet_support=True, other_fixed=True: δ admisible [0.0,0.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[2.372809,4.372809]m, delta bounds desde B=[0.0, 0.0]m.
  Clearances incidentales de superficie=[0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772, 0.3772]m; rango [0.3772,0.3772]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).
- (2196,1572) m, B=6.156673m, selector=False, fixed original=True, wet_support=True, other_fixed=False: δ admisible [-2.0,2.0] m. Min LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`; max LP `Optimization terminated successfully. (HiGHS Status 7: Optimal)`. EV79 floor/cap=[4.156673,8.156673]m, delta bounds desde B=[-2.0, 2.0]m.
  Clearances incidentales de superficie=[-5.3067, -5.3067, -3.4067, -3.4067, -3.4067, -3.4067]m; rango [-5.3067,-3.4067]m; corredor navegable 24m=False; ≥0.95m en todas=False (aplica aquí=False).

## Fixtures algebraicos independientes

P-only: h=(0,4), P=1 da t=0.25 y una sola ecuación/rango 1; δ=(+0.1,−0.3) conserva P. Al agregar F=3, t=0.75 da una fila independiente, rango 2 y solo movimiento cero. Controles de aristas completamente secas y completamente mojadas permiten una pequeña traslación sin inventar ecuación de cruce; las aserciones están en el JSON.

El control negativo propone cruzar un extremo seco a mojado; la desigualdad `−δ<=h−L` lo rechaza. La topología por signos no equivale a conservar el parámetro del cruce ni el área mojada.

## Mecanismo local de inmovilidad

En los dos objetivos secos (1146,1002) y (2196,1572), una arista P cruza hacia un vecino fuente de agua/clase 6 que permanece `other_fixed`. El vecino tiene δ=0 y el coeficiente del objetivo en `(1−t)δ_i+tδ_j=0` es no nulo; por eso la igualdad exacta fuerza δobjetivo=0 directamente. En (2196,1566) el propio nodo es class!=0/source-water y `other_fixed`; además el floor EV82-B colapsa su intervalo inferior a la altura base y la condición conservadora de no hacer más somero limita el extremo superior a cero. La fuente `other_fixed` ya lo bloquea por sí sola. La profundidad geométrica allí es 0.3772m respecto a los planos incidentes, pero el source corridor 24m es false; por tanto el umbral de 0.95m para corredor navegable no aplica a ese punto y este diagnóstico no lo clasifica como incumplimiento. Los tres puntos tienen corridor=false.

## Lectura limitada

El resultado se restringe a tres puntos y dos ventanas. “Nullspace” es el del sistema de igualdades más bloqueos; los rangos LP incorporan después cotas, signos/topología y fondo sumergido. Igualdad exacta P+F no se debe confundir con conservar solo área/clasificación: esta última condición admite desplazar el cruce y variar el área. No se resolvió una optimización de área ni se produjo una superficie candidata.

Fuentes exactas: el contrato consumidor P/F está en `verify.py:40-76`; composición de protecciones en `verify.py:127-141`; floor en `verify.py:159-165`; presupuesto y water-floor en `author.py:372-401`; máscara del corredor navegable en `v30-valley-smoothing-20261008/candidate-a/masks.npz:corridor`; regla de plano físico en `v30_common.py:88-105`. La triangulación y F por triángulo están verificadas en `analyze_spatial.py:150-181`.

No se modificó P/F, terreno, constraints, máscaras, motor ni paquete; se escribieron solo estos dos informes y el script en la carpeta de diagnóstico.
