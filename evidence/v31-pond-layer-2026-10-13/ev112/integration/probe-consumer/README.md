# Consumidor de la sonda EV112: control offline

Se corrigio la aceptacion de muestras fuera de BEGIN/END. La reproduccion
anterior conserva FAIL; el lector actual pasa el log real y cinco rechazos
de encuadre, ademas de los seis controles fisicos/numericos existentes.
Esto no acredita que EV112 haya pasado una sonda del motor.

Los scripts y recibos se archivan byte a byte. Los ejecutores de controles y
el evaluador integrado conservan sus rutas de trabajo originales, indicadas
en manifest.json; no se presentan como ejecutores portables desde esta carpeta.
El comparador eval_bridge_regression_ev112.py acepta rutas por CLI y puede
usarse directamente. La auto-comparacion de EV110 demuestra no-regresion,
no un PASS estricto de todos sus puentes: 015-18 tenia6/9puntos mojados.
