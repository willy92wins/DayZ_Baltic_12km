# RoadC0 — gates previos a fuente real

Muse Wonder1.0 nativo: plan43.281s SOUND-with-fixes y código72.625s SOUND/CONVERGE. Cuatro precisiones del plan fijadas antes de código: matriz48bits, contratoB3original/saneado ligados, dos prefijos distintos y terminadorexacto. Catorce tests sintéticos R0PASS1.703s, sin skips. Codex autor/integrador con contexto compartido; I/O stdlib común, consumidores con recorridos propios. No corrección ni cambio de fuentes/oráculos.

El consumidor no rechaza el co-mutante sólo por recalcular un hash: compara el registro contra los literales externos y prefijo contra su propia lectura de fuente. Esa precisión no cambia el dictamen. La taxonomía OUTPUT_EXISTS/IO_ERROR después de un fallo parcial queda backlog: todo fallo consume intento, ninguno se promueve aPASS ni se relanza aquí. La review fue estática; no se le atribuyen tests ni compilación.

Se autoriza una fuente0/3 y una lectura independiente de60s cadauna,256MiB,64MiBsalida; sin Binarize/PBO/DayZ/P: ni cambios del mapa. El censo originalB3 se hereda porpin; no se repite. SourcePAIR no es build-ready ni aprobación de pivote o carretera.
