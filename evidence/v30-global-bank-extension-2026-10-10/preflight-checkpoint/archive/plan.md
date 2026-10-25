# EV93 — extensión de orillas: inventario compilado y cola verificable

Estado: plan de preparación aprobado por root, ejecutor/integrador según petición viva del usuario. No autoriza todavía una pasada global de terreno. El piloto EV92 pasó sus 27 puertas offline; B permanece referencia operativa y BASE1.0 no está aceptada.

## Alcance inmediato

1. Crear un índice inmutable de las caras físicas y visibles de las 18.024 instancias de agua de B. Cachear únicamente representación ya existente; no alterar terreno, P/F, objetos, modelos, materiales, paquete o juego.
2. Materializar la cola completa de 5.450 semillas EV87, su primera capa 17×17 disjunta y el motivo explícito de cada exclusión. Mantener crestas de 12/24 m como inventario separado, sin clasificarlas todas como defectos.
3. Preparar la generalización de WINDOW17/core13/guard de incidencia completa y dirección D8. No copiar el alpha ni los 85/43/42 nodos particulares de EV92 a otra ventana. La siguiente autoría requerirá preflight generalizado y revisión antes de ejecutarla.

## Índice [DESIGN]

Usar las definiciones reales de `verify_ev87.py:424-494` (instancias, LOD física float32(3e15), visible1, traslación, cara triangular y clipping en triángulos nativos NW-SE) y `next-method-preflight/ev90_preflight.py:127-150` (identidad de B, PBO desplegado y WRP fuente). Las transformaciones se leen del 0WZD staged; no presentar esa lectura como extracción de objetos del OPRW. La relación con OPRW/PBO es la misma cadena hash verificada por EV90.

Persistir arrays float64 de XYZ por cara, coeficiente afín Y(X,Z), kind, object-id, modelo/face-id y rangos conservadores de celdas, más manifest de hashes. Un índice de rangos/bloques basta: no se exige duplicar polígonos recortados ni calcular un mapa global de márgenes. Consultar las caras candidatas por celda/ventana y aplicar el clipping existente cuando sea necesario. Se conserva cada cara; las degeneradas se enumeran y clasifican con la misma regla de área existente, sin desaparición silenciosa. No inventar P/F en celdas desconocidas.

## Verificación y parada

- Antes/después: hashes B, P/F, WRP0WZD, PBOs y todos los modelos leídos; 18.024 IDs únicos esperados, matrices de solo traslación, exactamente un LOD de cada clase requerida, sin datos no finitos. Salida exclusiva nueva, no sobrescribir.
- Consumidor independiente: enumeración de identidad/cara y consulta de rangos contra un escaneo directo; casos analíticos incluyen cara grande cruzando celdas, frontera exacta, orientación NW-SE, vacío y cara degenerada. Negativos de pin alterado, cara omitida e índice que excluya una cara real.
- Comparar exposición geométrica con el consumidor EV87 congelado en el piloto y en muestras deterministas de familias/zonas, con las tolerancias geométricas existentes, sin relajarlas para aceptar el índice. Igualdad de candidatos de bbox no equivale a igualdad de exposición.
- Un build del índice tras revisar source; presupuesto 10 minutos y 2 GiB de salida, detener con resultado incompleto conservado si excede. Un consumidor completo; errores de lectura/oráculo se corrigen conservando el intento, pero no se ajustan geometría ni tolerancias.
- El índice demuestra representación/consulta, no agua dinámica, marea ni render. Las pruebas gráficas siguen pendientes del escritorio visible.

## Cola [DESIGN]

Reutilizar exactamente la selección EV87 verificada (elegible, bisagra >30.0001°, prominencia cardinal d1 >0.1 m), su orden y todas las protecciones. Registrar cada semilla y su población, con primera capa greedy de separación Chebyshev ≥17, referencias a centros bloqueantes y frontera completa. Las solapadas permanecen pendientes; ningún conteo de seleccionadas acredita resolución. El índice y la cola son preparación para cumplir el encargo completo del mapa, no su cierre.
