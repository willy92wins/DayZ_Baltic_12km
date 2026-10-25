# [DESIGN] Regla escalar para crestas de un eje

## Dictamen

Los rechazos observados no demuestran que el solver no pueda suavizar una cresta. Demuestran que la regla EV92 exige un pico local positivo en ambos ejes cardinales antes de calcular `alpha`; eso excluye los lomos con relieve solo EW o solo NS. En una muestra parcial de resultados ya terminados y verificados por SHA, pude construir intervalos materiales analíticos para la mayoría de esos rechazos sin cambiar la dirección del solver. Admitirlos exige una modificación explícita del contrato de forma y su consumidor; no basta con cambiar la fórmula de interpolación.

## Contrato vigente y motivo del rechazo

El plan EV93 fija reducción del 25 % en ambos ejes y el midpoint del intervalo material [EV93 `author-stage-plan.md:9-10`]. EV92 calcula energía a partir de los momentos cuadráticos de las curvaturas `xx/zz/xz` y exige sus condiciones antes de hallar la cota energética [EV92 `verify_ev92.py:83-99`]. Después calcula la prominencia de foco como centro menos el mayor vecino inmediato y lanza `ValueError` cuando no es positiva en cualquiera de los dos ejes [EV92 `verify_ev92.py:100-116`]. Su midpoint se elige en las líneas 115-117.

La misma política está codificada independientemente en `shape_contract.py`: `positive_prominences` trunca a cero los ejes sin pico positivo [líneas 23-30], pero `evaluate_shape` solo da por reducida la prominencia del foco si `focus_B > 0` y la H queda bajo el 75 % [líneas 48-60]; el gate combina los dos ejes [líneas 79-84]. Por tanto, sustituir solo EV92 no haría aceptable una cresta de un eje: el consumidor seguiría rechazándola.

## Propuesta de cambio de política

Para foco `f`, eje `a` y vecinos cardinales `n1,n2`, mantendría la definición actual:

`p_a(X) = max(0, X_f - max(X_n1, X_n2))`.

Definiría un eje como **activo** exactamente cuando `p_a(B)>0`, sin epsilon ni umbral en metros. En cada eje activo se mantiene el objetivo EV92 `p_a(Hα) <= 0.75 p_a(B)`. En un eje inactivo se exige `p_a(Hα)=0`: no se le pide reducir un pico que no existe, y tampoco se permite crear uno nuevo en el foco. Si ninguno de los dos ejes es activo, la regla no identifica un lomo cardinal para suavizar y conserva el rechazo. Los focos con dos ejes activos conservan el contrato original sin cambio.

Para cada vecino, sea `d_i(α) = (B_f-B_ni) + α[(H_f-B_f)-(H_ni-B_ni)]`. La condición por eje es exactamente `min_i d_i(α) <= T_a`, con `T_a=0.75 p_a(B)` si el eje está activo y `T_a=0` si está inactivo. Cada desigualdad es afín; se obtiene su intervalo resolviendo el cruce de la recta con `T_a`, y se toma la unión de los dos vecinos. La energía conserva su cuadrática EV92 y su cota `α_E`. Para mantener la regla del midpoint sin escoger islas favorables, solo se admite una cola factible que llegue a `α=1`; su inicio es el máximo de `α_E` y los inicios de cola de ambos ejes. El único `alpha` sería el punto medio de esa cola. Si una cola falta, se rechaza esa dirección sin segundo solve ni barrido.

Esto cambia el significado del gate del foco —de “pico bidimensional obligatorio” a “reducción en cada eje con pico preexistente, sin crear pico en el otro”— y requiere actualizar de forma coordinada el plan, `scalar_rule` y `shape_contract`. No relaja el 25 % de energía, el 25 % en ejes activos, las métricas fijas de máximo/suma de cuadrados, la prohibición de nuevos mínimos8/mesetas2×2, el gate angular, D8/guard, cotas float32, cruces y cobertura P/F, ni los gates globales. El resultado float32 final debe volver a pasar todos ellos; la derivación del intervalo no certifica esos gates.

## Discriminador en datos terminados

Snapshot del ledger `fairing-layer1/ledger.jsonl`: 378 eventos, SHA256 `FABFC6AB5F5A627D0043DBF53CCA4341F0C755B2BC2B7BC58A01EE3FF16B3B51`. El productor seguía activo y el ledger creció después; por eso no es un censo de 703 ventanas. Tomé solo resultados y archivos `.solution.npz` cuyo SHA coincidía exactamente con cada evento. Dentro de esa porción, 113 rechazos terminaban en `baseline focus is not prominent on both axes`; los 113 tenían un eje positivo y otro no positivo. Recalculé desde B float32, dirección H float32 y los stencils persistidos, sin modificar ni interpolar el terreno: 105/113 tenían cola analítica común no vacía hasta `α=1` al combinar energía y la condición activa/inactiva propuesta; 8 no la tenían bajo esa regla conservadora. No evalué la forma final, agua ni gates globales para esos intervalos.

| queue / foco | prominencia B EW / NS (m) | cota activa | cota energía | cola común calculada |
|---|---:|---:|---:|---:|
| 0 / (1073,1204) | +0.63759 / −1.71910 | 0.84688 EW | 0.80580 | [0.84688, 1] |
| 7 / (1885,189) | +0.59144 / −0.37916 | 0.13060 EW | 0.70038 | [0.70038, 1] |
| 10 / (1362,1197) | −0.81232 / +0.45253 | 0.13099 NS | 0.54521 | [0.54521, 1] |

Los tres rechazos y sus soluciones son verificables en `fairing-layer1/results/window-0000.json` / `attempts/window-0000.solution.npz` (SHA resultado `a80c1e158443420828997e045157b333cbd821820aa3ed385752adb32fd760da`, solución `068d8d6c88965f73352642cecaed9a0ffe93780d32e4768bfe7fd0b07e0df3b5`), ventana 0007 (resultado `6ab7131b993ba3774eba2b11cb250515a7dc6fdfe4e6ba7bc5768eee76e52806`, solución `d7ba68518b310d80b74e64c74bd2f29bae624e9badff8bb39ecd7ebd8086883f`) y ventana 0010 (resultado `f3d15fcdde34d5ac89f4d38487764afb592c7ea1ea947f89209e3b1139b183f7`, solución `79c14ac638681c01a5ebd10b9e1f6b3d4c61b6ddb44d5956eee0ccd139f491a9`). El B anclado por `prepared.json` es `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`.

**Límite:** estos intervalos prueban que el rechazo escalar de muchos lomos de un eje es evitable bajo la política propuesta; no prueban que el `alpha` escogido pase el cast float32, `shape_contract`, ángulos, agua/exposición, ni el consumidor global. Las 8/113 sin cola común, los resultados todavía no procesados y los focos sin prominencia positiva en ambos ejes siguen sin resolver. EV93 continúa en ejecución y la pasada no se modifica aquí.
