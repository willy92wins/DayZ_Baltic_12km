# Consumidor nativo de la NM del delta

Run `5c1e4734`, servidor solo; mundo `916948ec`, NM `eece8e5e`, WRP `daca4196`.
Los trece casos congelados pasan (`verification.json`): once caminos positivos,
filtro NONE rechazado y separación WALK isla/continente. No se movió un actor.

La separación devuelve FindPath=true con tres puntos, pero acaba en la ribera
(8362,5;0,85;10298,25), lejos del destino (8400;2,4;10386). Es una ruta parcial;
el criterio congelado admitía ese resultado sin inferir conexión al destino.
Los caminos locales de ambas tierras existen, y el puente de Narva conserva
los dos sentidos de la consulta completa (270 m cada uno).

El registro completo `END;13` prueba ejecución de la misión/consultas con esta
NM nueva. No resuelve la causa de los distintos contadores offmesh ni certifica
cada enlace del mapa. No equivale a locomoción de infectados o de lanchas.

El RPT conserva mensajes de XML opcionales ausentes y una traza del plugin
diagnóstico de items (GetPlugin/OnInit), además de avisos pond. No se presenta
como arranque sin avisos. La sonda completó sus consultas y lifecycle confirmó
terminación de servidor, orderly_close, métricas de salida y retirada del run.
Logs originales archivados en `E:/DayZ-Baltic-Build/navmesh-v30-delta/runtime-5c1e4734/`.
Lease liberado, ningún Computer Use utilizado en este ensayo.
