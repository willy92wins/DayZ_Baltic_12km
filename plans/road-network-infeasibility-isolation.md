# Aislar la incompatibilidad de la red antes de otra variante

V16 mantuvo los criterios de lisura y eliminó las224 contradicciones individuales
deV15. Su sistema completo sigue INFEASIBLE con±2.05m. Un minimax diagnóstico
agotó602s sin solución: no demuestra ni otra cota necesaria ni inviabilidad sin
cota. Ninguno produjo ASC. No aplicar V16 ni repetir parámetros a ciegas.

[DESIGN] Cambiar a localización del conflicto: cargar exactamente la matriz y
los límitesV16, con objetivo0 (misma factibilidad, sin auxiliaresL1). Pedir al
solver el subconjunto incompatible y sus coordenadas. Máximo300s para resolver;
si el certificado no llega, conservar resultado, sin aceptación ni nueva variante.
Una contradicción identificada permite tratar su mecanismo en el siguiente plan.

[EXACT] API instalada de SciPy/HiGHS: `_highs_wrapper.py:113-136` construye
HighsLp concol_cost/lower/upper,row_lower/upper y CSC; `:188-208` passModel/run.
`_core._Highs.getIis(HighsIis)` y getDualRay se comprobaron por docstrings del
módulo instalado. Se usa solo para diagnóstico de matrices propias; no GIS
fuente ni terreno desplegado. No se añade dependencia ni se toca Python global.
