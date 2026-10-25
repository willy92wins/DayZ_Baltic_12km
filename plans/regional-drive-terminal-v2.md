# Parada del coche: corregir la maniobra, mantener terreno y criterios

RegionalV1 terminó los seis casos: cuatro PASS y dos FAIL terminales, ambos
en colinas. Llegaron, conservaron salud1000, cuatro contactos y ningún salto.
`terminal-observation.json` registra9,67/9,10m/s junto al marcador de llegada.

[EXACT] `missions/BalticRegionalDriveV1.BalticTrial/init.c:121-149` mantiene
velocidad objetivo35km/h hasta entrar a5m del extremo, luego solicita freno.
La ruta tiene un límite cerrado y acaba activándose CORRIDOR_DEVIATION_STOP.
`tools/navigation/BalticDriveInput.c:25-30` ofrece BalticDriveStop: corta motor,
freno/handbrake y SetBrakesActivateWithoutDriver(true). No escribe pose/velocidad.

[DESIGN] Repetir solo ambos recorridos de colinas. Desacelerar desde50m
(objetivo4m/s), desde20m (2m/s) y desde8m (0,6m/s), con freno proporcional
al exceso y fuerza máxima1. Declarar llegada solo a<=1,5m y<=0,8m/s; después
usar BalticDriveStop y observar la parada5,5s. Mismo corredor3m, salud,
contactos y criterios del consumidor. No cambiar el PBO de entrada ni terreno.
Datos/mandos/registro solo servidor, sin RPC/UI. Una ejecución de dos casos;
si falla, preservar y discriminar, no ampliar umbrales.
