# Desfase vertical en tesela del acceso este

PBO fd2c7023 / WRP e3fbb224 / NM68450401, sin cambiar datos entre sondas.
native-nav-v2 conserva FAIL:52 muestras direccionales del acceso este por
encima de0.8m, máximo7.278902m;750/751 referencias regionales pasan2m.
El punto regional fallido es Narva2466,6906: terreno4.092501m y error2.468797m.
Las rutas devuelven true y solo dos extremos; eso no demuestra superficie
ni locomoción correcta. Ambos controles locales encuentran camino.

run68462e65, misión BalticNavSeam:85 coordenadas ×4 consultas terminadas,
comparando WALK y ALL, Y solicitada de calzada/2/9m. Config efectiva conserva
la ruta propia de WRP/NM y filterIsolatedIslandsOnLoad=true. Al este el error
persiste con ALL: x2470,z6884 tiene terreno/carretera9m y navmesh1.827602m.
Cambiar únicamente el filtro de caminar no resuelve este punto. No se ha
aislado filterIsolatedIslands de generación ni su homónimo de carga.

Lector experimental de cabecera TESM6/tiles versión11 verificó60025 índices,
coordenadas únicas y sus límites horizontales. Entre NM antigua/nueva hay39
teselas con cambios en conteos o límites Y, concentradas en Narva. Los bytes
de casi todos los tiles difieren; pueden incluir referencias dependientes
del orden, por lo que no se equiparan con cambios geométricos. Ver comparaciónV2.
La tesela50,137 tiene límites Y1.25–9.0956 y muy pocos elementos de malla;
es compatible con simplificación vertical, sin demostrar mecanismo interno.

[Detour upstream](https://github.com/recastnavigation/recastnavigation/blob/main/Detour/Include/DetourNavMesh.h)
solo orienta el prefijo; DayZ usa otra versión. No se modifica ni reconstruye
el NM con este lector. La [guía oficial DayZ](https://community.bohemia.net/wiki/DayZ%3AGenerating_navigation_mesh)
recomienda conservar parámetros del generador. Antes de variarlos se prepara
un consumidor real: control local y cruce de infectado en ambos sentidos,
sin mover al actor por script. Mantener el FAIL geométrico independientemente
del resultado físico; no ampliar su tolerancia para producir PASS.
