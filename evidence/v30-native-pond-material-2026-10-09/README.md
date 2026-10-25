# EV33 — material de charca, sin supresion estable

La sonda cambia solo WetFloor de graphics/materials/water/pond_moss_1, mientras EV17 habia cambiado el material del oceano. Obtiene handle, indices validos y respuestastrue; baseline inicial intacta. Series0/1/2 de seis capturas cada una, mas controlNormalPower0 y reset. Camara y ventana2891x1648 estables durante las series. El parametro vuelve al valor por defecto mediante ResetParam; la API no permite leer el valor anterior.

La aparente limpieza en algunas capturas no supera con claridad las variaciones naturales. Centro seco: cambio mediano2.400RGB frente2.302 entre referencias. Conjunto de charcas3.062 frente2.930. Solo13pixeles de525673 superan todos los originales/restaurados por5niveles. No suprime espuma/halos de forma demostrada. NormalPower no ofrece control inequivoco con espuma del mar superpuesta; no afirmar que este handle sea el consumidor de los pixeles observados, ni descartar todos los shaders de charca. La ruta requiere comprobar el enlace del RVMAT CalmWater al recurso nativo antes de mas parametros.

No se altera produccion. Ajustes de render del perfil iguales; resumen conserva verdad del hash completo. Mapa y agua exactos. Cierre orderly cliente/servidor, lease liberado y banco libre. Sin cierre016/018 ni base1.0.

El hash completo del perfil cambia solo por uiTopLeftX (0.12500001 a 0.11997001) y uiBottomRightX (0.875 a 0.88002998), al ampliar la ventana antes de la referencia. No cambian los cuatro ajustes de render. Se conserva profile-changes.json; no se revierte el estado de ventana del usuario.
