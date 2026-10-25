# EV92 — amortiguación escalar del testigo EV91 (propuesta, no autorizada)

## Decisión propuesta

EV91 sigue rechazado: su full consumer encontró una nueva meseta exacta 2×2 en `(836,370)` (36 m²). Esta propuesta no altera EV91 ni lo rehabilita. Define una posible candidata EV92 desde la misma base B y la dirección congelada `D = H_EV91 − B`, con una única regla escalar, sin segundo solve ni búsqueda de parámetros:

1. Calcular el umbral material inferior `α_lo = max(α_energía25, α_foco25_EW, α_foco25_NS, 0)` sobre la recta **sin cast**, en float64.
2. Fijar la regla determinista `α* = (α_lo + 1)/2` —el punto medio entre ese umbral y el extremo de la dirección EV91—.
3. Solo si se aprueba este plan por separado, formar `H92 = float32(B + α*D)` una vez y ejecutar todos los gates independientes actuales. Si alguno falla, rechazar esa única salida; no probar otro alpha ni ajustar umbrales.

`[DESIGN]` Esta no es una ejecución aprobada ni una candidata. No se escribió H92, no se ejecutó solver ni full consumer. El cálculo y el código reproducible están en `alpha-interval.json` y `derive-alpha-interval.py`.

## Cálculo anclado

Fuentes congeladas: B `v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz` (SHA `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`); dirección H_EV91 `ev91-descent/candidate-terrain.npz` (SHA `865901ab24aa3736da57847f9112d3c73181085213f89b48ef2e3e7a9f6ee702`); `prepared.json` y consumidor independiente `review-independent/verify_ev88q.py` con sus SHA listados en el JSON.

La energía usa `stencil_records(variables=prepared.variables_rc)` del consumidor. Para cada stencil se calcularon `b_s` en B y `d_s` en D directamente desde los valores binarios float64, y se sumaron exactamente con fracciones racionales (pesos y coeficientes de stencils incluidos): `c0=Σw b_s²`, `c1=Σ2w b_s d_s`, `c2=Σw d_s²`. No se ajustó el polinomio con puntos interpolados ni float32. Resultado:

- `E(α)=221.2263916770154 − 186.20880690454646·α + 84.52271160360701·α²`.
- `E(B)=221.2263916770154`; `0.75·E(B)=165.91979375776157`.
- El único cruce en `[0,1]` es `α_energía25=0.35384751023735084`.

Para el foco `(840,370)`, la prominencia cardinal es `max(0, centro − max(vecinos))`, equivalente a `max(0, min(centro−vecino1, centro−vecino2))`. Las cuatro diferencias centro-vecino decrecen a lo largo de esta dirección. Los primeros cruces por eje son EW `0.22764028932113087` y NS `0.220644799203558`; por tanto energía, no foco, domina el límite: `α_lo=0.35384751023735084`. La ventana escalar usada por la regla es `[0.35384751023735084,1]`, y el midpoint propuesto es `α*=0.6769237551186754`.

Un diagnóstico **solo en memoria** del midpoint con un cast float32 indicó energía −39.4703%, prominencias del foco −74.3414% EW y −76.6984% NS, ángulo local `29.999999°→12.996529°`, y ninguna nueva mínima estricta ni meseta 2×2 en la ventana local examinada. Es evidencia de materialidad local, no del contrato total; las áreas físicas, compiled/ODOL, P9, collar, sectores y poblaciones globales deben recalcularse sobre una eventual H92.

## Contrato que no cambia

EV92 conserva la base B, P/F, geometría/objetos compilados, protecciones, restricciones y todos los criterios/gates independientes EV90 vigentes. Mantiene la puerta `no new exact-constant 2×2 quads`: la razón para proponer el midpoint es alejarse de la cuantización común cerca de α≈1, no quitar esa puerta. Mantiene también mínimos de ocho vecinos, prominencia/población, energía/collar, ángulo/sectores/p99/conteos, cobertura física compilada, corredor P9, fondo/calado y cotas exactas float32.

El intervalo `[α_lo,1]` solo expresa las dos condiciones escalares de materialidad (energía 25% y foco 25%) en la recta real. No es el conjunto de alpha factibles para todos los gates; el extremo 1 está incluido como referencia de dirección aunque H_EV91 ya falla por meseta. El midpoint da una única regla declarada antes de mirar cualquier full resultado. Si el consumidor EV92 devuelve cualquier FAIL/INCONCLUSO, no se vuelve a elegir alpha dentro de esta propuesta.

EV91 plan exige rechazo sin reparación (`ev91-descent/plan.md:38-48`, `author_ev91.py:155-177`); por eso esta amortiguación requiere un plan EV92 nuevo y aprobación explícita antes de materializar terreno. El resultado full comunicado para EV91 (run `consumer/runs/attempt02`, SHA de reporte `594b1985cd8b75c5e3b17c3ea5262a162c4e23ea50474051285713ef132df061`) informó fallo solo por la puerta de meseta y PASS de las otras 26 puertas para H_EV91; eso no anticipa el resultado de H92.

## Límite de esta revisión

La evaluación local del midpoint es un cribado informativo y no incluye la aceptación completa. No se autoriza paquete, despliegue ni motor. Para cerrar revisión de diseño, confirmar únicamente que el contrato existente se conserva y que una sola salida futura se rechaza si no pasa el consumidor; no ampliar el dominio ni reinterpretar los gates tras ver esa salida.

