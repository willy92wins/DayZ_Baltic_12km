# EV27 — remate poligonal omitido del Volkhov

La petición viva exige terminar superficie y fallos. EV16 descubrió extremos desde `profiles.npz`; el Volkhov es un polígono sin perfil y su corte no entró en aquellas 15 cajas. La feature `name=Volkhov,class=river,width_m=polygon` corta x=12222 entre z3240,845 y3275,040. Esta es cobertura que faltaba, no otra ronda del Msta rechazado.

Una caja alrededor del centro de ese corte, extensión 60 m como EV16, fuente actual EV25. Reutilizar sin cambios el solver/consumidor EV16: hasta80 iteraciones/30s; soportes mojados/secos conservados, fondo y calado conservados, 35 grados o exceso anterior, movimiento de contorno<=4,1m, p90/fracción>30/máximo no aumentan, topología local conservada. Ingeniería, corredores, mar/delta, Narva y exterior24m fijos. No cambio de plano/piezas/materiales. Una propuesta, sin barrido ni segunda caja ajustada al resultado.

Antes de integrar: validar fuente guardada con consumidor global y comprobar cobertura compilada, alturas nativas y vistas de este remate; si falla una puerta, mantener EV25 y registrar el límite. No aplicar automáticamente una propuesta porque el solver diga éxito.

También aclarar los dos `no_contour` de EV16: stream_0452/0456 tienen tier1500; `build_v30_water.py:69,118-120` incluye solo tier>=2500. Los perfiles almacenados no prueban agua construida. Confirmar ausencia en water_v3.geojson y en la caja física para retirar esos falsos pendientes, sin crear los arroyos fuera del alcance.
