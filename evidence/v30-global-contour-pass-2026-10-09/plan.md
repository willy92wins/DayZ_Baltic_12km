# Extensión del contorno nativo a toda la superficie — EV14

Consumidor: preview de terreno y verificación global de sus triángulos. Unidad del suavizado completo autorizado por Guillermo, P14 y pasos 4/7 del rumbo 1.0. No congela la base por una métrica.

## 1. Fuente y descubrimiento

EV13 pasa en R1/R2 minimizando giros del contorno triangular real. El barrido completo enumera 1.001 cadenas, 427 km de contorno y 45.036 observaciones mayores de 30 grados. No convierte cada esquina en un fallo. Fuente `candidate-feasible/terrain.npz` cff6d175; agua visible 7a5d0900 y planos d59dcdb9 exactos. Los taludes/relieve general C1R3P ya integrados se conservan en esta unidad, salvo soportes estrictos del borde del agua. Costa marina, ingeniería y niveles conservan su política; no se amplía la resolución.

## 2. Extensión [DESIGN]

Una pasada de bloques de 96 m sobre todos los soportes de las orillas de estanques/ríos. Cada bloque tiene perímetro fijo y 18 m de contexto; dos bloques no editan una misma cara. R1/R2 EV13 y todos los controles nativos actuales quedan fijos. Se conservan los pesos y la función de giros cada 6 m de EV13; se calcula su derivada analítica para recorrer el mapa dentro de un presupuesto finito. La derivada debe concordar con diferencias centrales antes de authoring.

Límites originales: desplazamiento vertical <=2 m, pendiente <=max(original,35 grados), signos visibles y físicos conservados, fondo >=1 m o excepción exacta, ningún punto originalmente mojado se eleva, suelo seco >=min(original,max(1,8 m,plano+0,0501 m)). No se tocan metadatos, carreteras, plataformas, puentes, corredores ni cumbres protegidas. Una proyección analítica hacia la fuente impone las pendientes y el desplazamiento correspondiente del contorno <=4,1 m antes de serializar. No es otra ronda del solver.

Solo se integra un bloque si el consumidor geométrico de su contorno no empeora p90, máximo ni proporción de giros >30 grados, y mejora el objetivo sin perder área/cuerpos. Los demás quedan exactos y se inventarían con su motivo. La decisión no cambia los umbrales después de ver resultados.

## 3. Puertas y negativos cerrados

- PLAN §2: invariantes físicos, controles, metadatos y regiones fijas exactos sobre todo el NPZ final.
- EV13/PLAN §2: derivada analítica frente a diferencia central (tolerancia relativa 1e-4; error numérico del cálculo, no tolerancia geométrica). Casos recta, codo, cadena curvada; no usar el valor del autor como prueba de mejora final.
- P14/EV13: consumidor independiente reconstruye polígonos triangulares; compara giros a distancia métrica real. P90 global baja >=10%, proporción >30 y máximo no empeoran; R1/R2 exactos. Reporte por sector además del agregado; sectores sin mejora no se declaran resueltos.
- P2/EV13: 830 masas significativas, componentes, islas y contactos conservados en agua física y visible; intersección por cuerpo >=90%; sin nuevas caras secas inundadas. Desplazamiento de contorno <=4,1 m. Reutilizar los controles negativos físicos/de topología de EV13.
- Consumidor compilado: cobertura completa de todas las partes mojadas, objetos y alturas WRP identificados; cualquier junta nueva se corrige únicamente con la construcción exacta ya validada en EV12/13.
- Motor: censo completo, controles temporales actuales, navegación y vistas válidas. La última vista EV13 contiene todavía un residual gráfico; la forma global no lo cierra por asociación.

## 4. Presupuesto / parada

Un candidato global, una pasada, máximo 80 iteraciones o 30 s por bloque y 90 minutos globales. No variantes de pesos, tamaños, sigma o cotas. Una corrección de implementación solo con repro concreto. Bloques no viables se conservan; si falla el criterio global no se promueve ni se cambia el criterio. El trabajo restante del mapa continúa por sus unidades independientes.

APIs leídas: scipy/optimize/_minimize.py:113-115 y 651 (`jac=True` devuelve `(f,g)`); EV13/optimize_native_turns.py (objetivo y restricciones); EV13/verify_native_turns.py (consumidor independiente); EV13/project_feasible_candidate.py (proyección factible). Python GIS y worktree propios del HANDOFF.
