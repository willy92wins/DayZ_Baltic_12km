# EV87: auditoría local de `aboveP`

**Resultado acotado:** los dos ejemplos reproducidos son una cara física heredada que cruza unos `0.0001173 m` el borde de una celda cuyo `P` es aproximadamente `0.025 m` menor que el plano de la celda vecina. El residuo aparece ya en B. En H la misma cara y el mismo salto de nivel siguen presentes; en el segundo foco H expone `0.00003823565 m²` adicionales al bajar un vértice del terreno. Esto explica el mecanismo en estos dos casos, pero no clasifica el inventario global ni demuestra que el producto deba aceptar esos cruces.

La reproducción usa los triángulos físicos de ODOL `3e15` y las matrices del WRP 0WZD de B; las áreas `aboveP` recalculadas coinciden con los registros del consumidor en B/H. También compara por serialización los LOD no visuales del MLOD viejo y el generado: en ambos objetos el LOD físico coincide. La autoría genera geometría visible y conserva el resto de los LOD (`author_global_visual.py:97,138-145`). El cálculo del gate local intersecta la cara con cada triángulo nativo y recorta la parte expuesta antes de medir la diferencia de altura (`verify_coverage_contract.py:224-273`).

| Objeto / celda / triángulo | Plano de cara ODOL | `P` de celda | `P` vecino que coincide con la cara | Área `aboveP` B → H |
|---|---:|---:|---:|---:|
| `16799644`, `(1359,300)`, tri 0, cara 6 | `1.45000003092 m` | `1.425 m` | norte y este `1.45000000000 m` | `0.00069417316 → 0.00069417316 m²` |
| `16800008`, `(1245,371)`, tri 1, cara 8 | `2.22499997355 m` | `2.200 m` | sur `2.22500000000 m` | `0.00053414620 → 0.00057238185 m²` |

En el primer caso el borde norte de la celda es `z=4128`; la cara ocupa `z=4127.999882698…` a `4128.009882927…`, así que solo una franja de `0.000117302 m` entra en la celda con `P=1.425`. En el segundo el borde sur es `z=4806`; la cara ocupa `z=4800.000117302…` a `4806.000117302…`, y la pequeña intersección con la celda de `P=2.2` queda en la franja de `0.000117302 m` del lado norte del borde. La cara está al nivel del vecino sur `P=2.225`. El exceso sobre `P` medido tras la banda física de `1e-5 m` es `0.02499003092 m` y `0.02498997355 m`, respectivamente, en B y H.

Identidades fijadas en [aboveP-boundary-audit.json](aboveP-boundary-audit.json): WRP 0WZD `3071395e…1eff1f6`, P `768e8e58…9551e0`, B `f9fb23de…061f0`, H `a7146c27…fcf020`; ODOL por modelo y MLOD de origen/generado también quedan hasheados. El script reproducible es [aboveP_boundary_audit.py](aboveP_boundary_audit.py).

**Límite y efecto para la decisión:** esta evidencia respalda un cruce del contorno de un plano vecino, no un nuevo plano alto creado por H. No prueba la semántica visual o física que el motor asigna al solape. Excluir los parches que cambian las alturas bajo esas caras podría congelar la diferencia H−B (caso 2), pero no elimina el fallo absoluto que ya presenta B ni prueba que el resto del residuo agregado tenga el mismo origen. Los sumatorios `physical_outside_design_growth` siguen siendo `0.00344908020 m²` en B y `0.00355769761 m²` en H frente al límite vigente `0.002 m²`; no se atribuyen esos totales a estas dos muestras. Sigue haciendo falta el inventario completo por cara/celda que prepara el integrador antes de decidir la exclusión conservadora.

La transformación es la del 0WZD de B, enlazada al paquete en los recibos, no un readback de DayZ. La comprobación fuente de MLOD tampoco demuestra el orden de evaluación del motor.
