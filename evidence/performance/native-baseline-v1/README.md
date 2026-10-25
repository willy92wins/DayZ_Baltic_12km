# Primera base de coste fijo del terreno nativo

30-09-2026, DayZDiag1.29.163709; run15985eaf; candidato fd2c7023,
WRP compilado e3fbb224 y navegación68450401. Ver run.json y hardware.json.
Servidor sin jugadores, CE ni IA, con puente MCP; cliente no iniciado.

El motor completó30s de calentamiento y120 muestras de1s. El validador
aceptó el registro y rechazó diez corrupciones de control. Mayor timeslice
de actualización19ms, ninguna superior a50ms. No son tiempos de ejecución
CPU ni percentiles de render; ~8412 llamadas OnUpdate/s tampoco son FPS.

El host conservó170 muestras del mismo PID/fecha de creación durante187.86s:
memoria residente1273.22–1276.22MiB y privada1589.82–1595.52MiB.
CPU media4.82% de un núcleo lógico en toda la serie. En el intervalo
posterior al cierre del editor (78.44s),1.85% de un núcleo y memoria
residente1276.15–1276.22MiB. Es un intervalo del mismo ensayo, no un A/B.

La API nativa GetMin/Max/AvgFPS64 devolvió14.2857 de forma constante mientras
OnUpdate avanzaba miles de veces/s. Se conserva como resultado bruto; no
se ha validado qué representa en este modo headless. No declarar14FPS de
capacidad, ni declarar miles de FPS usando OnUpdate.

NMG cerrado antes de arrancar. TB se cerró durante los primeros20 intervalos;
Codex y otras aplicaciones de escritorio estaban presentes. No afirmar
benchmark de servidor dedicado limpio, ausencia de fugas, render cliente,
coste con población, red/persistencia ni80–100 jugadores. La base no muestra
un coste fijo de CPU que justifique reducir terreno o resolución SAT1M.

Cierre por lifecycle MCP: forced_kill; exit_metrics_valid=false; cleanup
sin degradación. Los contadores anteriores al cierre sí están guardados.
El RPT conserva avisos de recursos/diagnóstico y XML del entorno; no se
declara un arranque sin avisos. El archivo engine.log prueba la misión nueva.
