# Certificado AC-3 para la conversión float32

**Resultado:** no existe asignación dentro de las tres opciones de cada variable (−1 ULP, raw, +1 ULP). No se ejecutó búsqueda ni conversión.

En el foco `(864, 1187)`, crossing 76 permite para el foco solo la opción `+1`; crossing 80 permite solo `−1/raw`. Las tablas directas del ejecutor y las fracciones exactas coinciden en los nueve pares de cada cruce. El conflicto no depende de qué opción vecina se elija dentro de ±1.

Crossing 76 tiene ancho t 0.02988000 (≈0.179280 m en una arista de 6 m); crossing 80, 0.08180639 (≈0.490838 m). La evidencia apunta a posiciones raw cercanas a límites de intervalo y direcciones ULP incompatibles, no a un intervalo de ancho cero.

Esto certifica la inviabilidad del dominio de tres valores, no la inviabilidad de un dominio representable más amplio. No se ensayó ni se recomienda un ±2 arbitrario; cualquier extensión exigiría derivar el vecindario mínimo de las desigualdades exactas y aprobación separada.

JSON reproducible: `E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\float32-component-conversion-v1\ac3-diagnosis\certificate.json`. Receipt de la ejecución preservada: `E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\float32-component-conversion-v1\real-conversion-01\receipt.json` (NO_FEASIBLE_AC3, readset igual).
