# Recuperación terminal de la sonda de coche

Traza: P11/P10, terreno V29 y seis rutas congeladas de DriveV3. No editar el
terreno, paquete, navmesh ni criterios físicos para resolver esta maniobra.

[EXACT] `missions/BalticRegionalDriveV3.BalticTrial/init.c:136-143` baja el
objetivo a 0,6 m/s en los últimos 8 m y calcula acelerador desde velocidad;
`:123-125` exige 1,5 m y <=0,8 m/s para llegar. `:175` limita cada caso a 300 s.
El regreso sur conserva salud 1000, cuatro contactos, inclinación ~2,76 grados
y motor ~1018 RPM, pero cerca del destino casi se detiene sin registrar llegada.
[HIPÓTESIS] La demanda terminal resulta insuficiente para arrancar en esa
pendiente. Estos registros no aíslan por sí solos transmisión, tracción o control.

[DESIGN] Un experimento V4 conserva las dos rutas sur con XY/Z exactos, todos
los umbrales, freno, marcha y duración. Único cambio de control: en los últimos
8 m y por debajo de 0,2 m/s, demandar acelerador 0,5 (máximo ya usado en V3).
Fuera de esa condición se mantiene la fórmula anterior. Nunca escribir pose
o velocidad durante la marcha. Identificadores locales 0/1 conservan original4/5.

Presupuesto: una ejecución acotada de ambos sentidos. PASS exige el verificador
físico original completo y sus 18 negativos, incluido destino y parada. Si falla,
conservar evidencia y aislar el caso antes de otro ajuste; no aumentar tolerancias.
V3 y su fallo permanecen. Un PASS V4 solo acepta esas maniobras sobre el paquete
exacto; no demuestra una causa universal de la conducción DayZ.
