# EV35 — espuma del consumidor confirmado

Una secuencia intacto / FoamColor magenta / reset / FoamPower0 / reset. Mismo punto residual, hora y viento de EV34. Material pond_moss_1 confirmado por EV34, propiedades leidas en P:/Graphics/materials/water/pond_moss_1.emat. Solo dos propiedades visuales; nada en produccion ni preferencias. Se resuelve el handle al pedir el control, no al aparecer el jugador.

Presupuesto: un run, un control cromatico y una supresion; watchdog90s. No mas parametros en este bloque. PASS del arreglo requiere suprimir el residual en la serie con espuma0 y recuperarlo al restaurar, por encima de variacion temporal, sin desplazar agua/terreno. Si solo cambia espuma legitima y persiste halo, no es arreglo. La marca magenta constituye control positivo de consumo si aparece y desaparece; no inferirlo de SetParamtrue. Fuentes de API: proto.c267-294, ppeffects.c430-443, ya leidasEV34. Mantener hashes, fases, muestras, cierre orderly y estado libre.
