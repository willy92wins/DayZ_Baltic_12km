# Operaciones del sistema global: representación acotada, sin resolver todavía

Estado [DESIGN], unidad de implementación autorizada por el integrador dentro del suavizado de toda la superficie pedido por el usuario. No autoriza un nuevo candidato ni un solve global. Las reglas de forma, agua, infraestructura y presupuesto permanecen en sus fuentes; esta unidad solo implementa la representación numérica del operador ya probado.

## Problema y cambio concreto

El prototipo acumula listas Python para cada coeficiente y el solver CP convierte A, C y G más sus transpuestas a CSR. Ese almacenamiento es innecesario para la malla regular. Se implementarán `matvec` y `rmatvec` vectorizadas con un único vector de variables global: las divisiones en bloques, si se necesitan para memoria, solo particionan el recorrido de filas, nunca crean bordes fijos ni soluciones que se peguen.

Referencias leídas: `prototype.py:13–45` define colocación y pesos de xx/zz/xz y fidelidad; `face-slope-cone-pilot/pilot.py:125–200` fija C y G; `pilot.py:453–457` define el operador normal y su precondicionador diagonal. Sus hashes son respectivamente `5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4` y `d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a`.

## Contrato [EXACT] derivado de esas fuentes

- Alturas absolutas, variables en orden de filas; las contribuciones fijas pasan a rhs de A, d de C y k de G. En los stencils A, rhs=`-fixed`; en C, d=`-offset`; en G, k conserva el offset y se usa `G*x+k`.
- A: solo stencils que tocan una variable, orden xx/zz/xz y fila fidelidad por variable. Pesos xx y zz `[1,-2,1]`; xz `sqrt(2)*[-.25,.25,.25,-.25]` sobre las cuatro esquinas separadas dos celdas; fidelidad `.25*x`, rhs `.25*B`.
- C: un testigo D8 por centro no estrictamente mínimo, vecino mínimo con desempate lexicográfico, orden de centros por filas. Operación `H_centro-H_testigo`. Un mínimo estricto de B queda exento, igual que CP. Se conservan las filas constantes para comparar exactamente el orden y dimensiones existentes.
- G: dos triángulos NW–NE–SE y NW–SE–SW por celda, cada uno con componentes `(x,z)` de gradiente escalado 6 m. Triángulo0 `(NE-NW,NE-SE)`; triángulo1 `(SE-SW,NW-SW)`. Orden celda, triángulo, componente. Se conservan inicialmente todas las filas constantes; no se introduce otra reducción en esta unidad.
- Cada adjunto suma en los mismos vértices globales y devuelve solo variables. El signo de z se verifica por coordenadas físicas y contra CP.
- Diagonales exactas por columna: suma de coeficientes al cuadrado. El operador de CG es `A.T A + rho*(I+C.T C+G.T G)`; no se materializa A.T A ni KKT.

## Criterios antes de usar el mapa

Comprobar contra los CSR originales, en dominios sintéticos pequeños con bordes reales, islas fijas, mínimos estrictos, empates D8 y variables que cruzan la columna64: dimensiones/orden de filas, rhs/d/k, acciones y adjuntos sobre varios vectores deterministas, identidad de producto escalar, diagonales y operador normal. Deben detectarse negativos de signo de z y omisión de una contribución que cruza64. Error de acciones/adjuntos <=1e-11 absoluto en fixtures de magnitud acotada; las comparaciones físicas posteriores mantienen sus tolerancias propias.

No basta comparar una implementación con su transformación: CSR se construye con las funciones originales fijadas, y pendientes/ángulos del futuro candidato se medirán con el consumidor geométrico independiente. Probar también entrada inválida no finita, dominio vacío y forma incompatible, con comportamiento explícito.

## Medición de recursos, sin candidato

Tras PASS de fixtures y revisión independiente, una sola instancia sobre el dominio global preparado final, sin solver: medir construcción, acciones y adjuntos de A/C/G, pico real y tiempos. El recibo debe fijar los vectores deterministas de entrada y una repetición de cada acción/adjunto, sin calentamientos ocultos. Límite 120 s para esa medición, nunca iniciar si la estimación deja menos de6GiB físicos libres; vigilar memoria libre y pico durante la ejecución. No heredar el presupuesto1.5GiB sintético como presupuesto global. Una caída de memoria disponible obliga a abortar la medición y registrar estado, sin alterar datos.

La máscara global debe tener un recibo final con P/F originales float64 y las499ventanas+halo/foco protegidos. El cap local B+0.5m del sector anterior se registra solo como escenario conservador de dimensionamiento: no se convierte silenciosamente en presupuesto global. El presupuesto total sigue referenciado a EV79±2m, pendiente de congelar con el resto del contrato de dominio antes de cualquier solve de mapa.

Un PASS acredita equivalencia de operadores y recursos medidos, no convergencia global, aceptación del relieve, agua dinámica ni render. El solver global requerirá otro presupuesto explícito basado en esa medición y un consumidor final de toda la superficie.
