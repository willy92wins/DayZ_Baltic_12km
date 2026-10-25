# [DESIGN] Cota inferior de energía en el dominio preparado

**Estado:** diseño, no ejecutado. No se llamó al solver, no se generó candidato y no se cambió el dominio.

## Alcance y anclas

La evidencia `coordinated-crossing-component.md` demuestra que el movimiento de dos nodos analizado queda fijado por las siete filas activas citadas y que el vecino de una ULP alternativo viola una cota inferior. Eso no demuestra que todo descenso de energía en el dominio sea imposible ni que ampliar el collar sea la única opción. No se debe atribuir al par de vecinos un límite global.

El siguiente discriminador puede trabajar solo con `prepared-runs/attempt-08/prepared.npz` (121 alturas absolutas, A/rhs, cotas inward float32 y C/d para D8 + cruces) y `solve-once/solution.npz` (referencia raw float32). Pins actuales: prepared `52409A8D074D15EC068BDDC6E9265BC3782E84E9D54582B8A6D7B0A6675A787F`; solución `1B7A23EBB3C203427F1C77CB8DE6BECFCA750746E47F5494BBA6723B0610EAB1`.

El coste es el ya preparado por `prepare_wet_bank_matrices.py`: `J(x)=0.5*||A x-rhs_A||²`, con stencils EV88 xx/zz/xz y fidelidad 0.25. La puerta de cierre real está en `global-operator-prototype/real-sector-preflight/order-closure/projection.py:evaluate_objective_gates`: `J(closed)-J(raw) <= 1e-7*max(1,J(raw))`, además de mejora estricta frente al baseline. Para el raw ya registrado, `J(raw)=155.94405102975674`, allowance `1.5594405102975674e-5`, umbral de cierre `155.94406662416184`; baseline `279.1855928129427`.

## Certificado propuesto

Sea `x_r` el raw float32 promovido a float64 y `g=A.T@(A@x_r-rhs_A)`. La convexidad de J da para cualquier x del dominio `J(x) >= J(x_r) + g.T@(x-x_r)`. Minimizar esa tangente sobre una relajación factible proporciona una cota inferior válida, aunque se omitan restricciones: el conjunto relajado es un superset del factible físico.

Primera relajación: todas las filas lineales preparadas `C x >= d` (D8 y cruces P/F) y cotas absolutas inward `lo <= x <= hi`; omitir los conos de cara SOC y la retícula float32. No quitar filas ni ampliar intervalos. Define `M=[C; I; -I]`, `b=[d; lo; -hi]`. La relajación es `min g.T x` s.a. `M x >= b`.

No se acepta el `success` del LP como certificado. Construir `g`, `J(x_r)`, `M` y `b` como racionales exactos de los floats binarios almacenados. HiGHS (`scipy.optimize.linprog(..., method="highs")` ya se usa en `robust-f32-design/analyze_robust_lp.py:280`) solo proporciona multiplicadores candidatos; un `success` o dual residual pequeño no es evidencia por sí mismo. De sus multiplicadores se conserva cualquier `y >= 0`, se calcula exactamente `r=g-M.T@y`, y se forma

`LB = J(x_r) - g.T@x_r + b.T@y + Σ_i min(r_i*lo_i, r_i*hi_i)`.

Para cada x que cumple `Mx>=b`, `g.T x = y.T Mx + r.T x >= y.T b + min_box(r.T x)`. Por tanto LB es una cota dual válida incluso si los multiplicadores no cierran estacionariedad. Se descartan NaN/Inf y cualquier componente negativo de y; si redondeos de un solver producen y<0, no se clampa silenciosamente: el certificado debe marcar fallo, o usar y=0 como cota box-only separada. La suma racional evita que un residual dual se convierta en falsa prueba. Además, la aceptación real calcula J con float64/CSR y una suma float; para comparar contra esa puerta, el certificado debe restar una cota superior conservadora del error de evaluación de J sobre todo el box (derivable por fila con γ_k y una cota de |Ax−b| en el box, más γ_m para la suma). Solo si `LB - eval_error_bound > threshold_float64` se puede declarar imposible. Si esa cota de evaluación no se implementa/valida, el resultado es inconcluso, no imposible. Se conserva readset/hash antes y después.

## Interpretación mecánica

- Si LB supera `J(raw)+allowance`, ningún candidato en el dominio original puede cumplir la puerta de energía; la retícula float32 y los conos solo estrechan el conjunto y no rescatan la imposibilidad.
- Si LB es menor o igual al umbral, el resultado es **inconcluso**: la relajación puede admitir soluciones no factibles por cono/float32, y una cota baja no demuestra que exista un vector que pase.
- Para la puerta de mejora estricta, `LB >= J(baseline)` demuestra que tampoco puede cumplirse esa puerta; un LB menor no demuestra mejora.

El discriminador inicial debe tener presupuesto ≤10 s sobre las matrices pequeñas ya preparadas, memoria ≤256 MiB y cero llamadas al optimizador de terreno. Si el dual LP no produce un multiplicador verificable dentro de ese presupuesto, reporta `INCONCLUSIVE_CERTIFICATE`; no cambia tolerancias ni prueba otra parametrización. Si la cota queda débil, el siguiente fortalecimiento permitido sería incluir la dualidad SOC con una prueba explícita; no lanzar otro solver del terreno ni ampliar dominio desde ese resultado.

## Fixtures antes de cualquier evaluación

1. Caso analítico 1D: `J(x)=0.5(x-2)^2`, caja `[0,1]`, sin filas adicionales. Un dual factible y la fórmula exacta deben certificar `min J=0.5`; verificar que comparar con un umbral menor prueba imposibilidad y con uno mayor solo deja el caso inconcluso.
2. Multiplicador dual con una entrada negativa: debe rechazarse como certificado, nunca producir PASS/IMPOSSIBLE.
3. Residual dual no nulo conocido en una caja pequeña: el término `Σ min(r_i lo_i,r_i hi_i)` debe mantener una cota conservadora; test negativo quitándolo debe fallar la fixture.
4. NaN/Inf en matriz, gradiente o multiplicadores: estado de error/inconcluso y sin salida de cota aceptada.

Fuentes revisadas: `prepare_wet_bank_matrices.py` construye A/rhs absolutos y C/d en el NPZ; `face-slope-cone-pilot/pilot.py:499-555` confirma la función objetivo y las restricciones C, G y caja usadas por el solve; `order-closure/projection.py:39-49` define la allowance. Sus SHA actuales son respectivamente los del recibo de preparación, `D743F5006E0AA6606024A3C3291A74CB52B78F76C1AA5C6DFD95CDD26CDC9D2A` y `A990DC2D33FCA4FD2A446B958F0412A2D752A5D3072A85D82058BB634CFAF44B`.

