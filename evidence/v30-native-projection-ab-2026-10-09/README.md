# EV48 — proyección nativa confirmada; comparación de charcas incompleta

La reconexión funciona. El paquete principal EV28, el diagnóstico EV41 y la sonda EV43 coinciden con sus SHA256 previstos antes de arrancar. No se modifica terreno, agua, material, perfil ni paquete desplegado.

## Resultado que sí queda comprobado

La sonda de solo lectura obtiene 257 muestras completas con la cámara exacta y pantalla 1920×1080. Se ajusta una única focal con seis puntos y se comprueban otros cinco independientes: focal nativa 559,4394637 px; error máximo reservado 0,0001608 px. Las posiciones nativas se saturan en los límites de pantalla; el punto saturado se excluye del ajuste y se verifica después. El máximo de todos los puntos proyectados y limitados es 0,0002674 px. La estimación visual anterior era 561,027931 px, próxima pero no exacta.

Primer arranque A: el modo `static` se rechaza sin aplicar cambios; se corrige a `lookat` y la matriz resultante coincide exactamente con EV34. La primera referencia presenta menú, cielo magenta y vegetación anómala. Quitar el menú no lo resuelve. `computer-use` consigue activar la ventana. La primera consulta posterior de estado falla por solicitar ambos contenidos false; se reobserva con screenshot, sin repetir entrada. La escena ya aparece normalmente cargada. Esto verifica recuperación por activación en este run, no identifica el mecanismo interno del streaming ni cierra el ticket de foco de dayz-mcp.

Seis capturas A válidas, entre 16:08:40.853 y 16:09:14.722, sin cielo magenta. El consumidor usa rayos sobre los triángulos nativos, terreno/F actuales y mar máximo 0,85 m; excluye 8 px alrededor del agua y 16 px alrededor de la mira. De 172.376 muestras secas, 4.495 presentan variación superior al control seco; 4.360 están en la zona de las seis charcas. Umbral RGB 11,002184 sobre 9.202 muestras control. La variación temporal no es por sí sola identificación de agua/material. Sí proporciona una referencia reproducible para la bisección pendiente.

## Lo que no queda comprobado

Se lanza B con las cuatro instancias omitidas, mismo terreno, sonda y cámara. Antes de medir B, Computer Use informa de parada por la tecla Escape física. No se emiten más entradas por ninguna vía para continuar el experimento. B queda **sin medir**; no hay A de retorno y no se atribuye el residual a las charcas ni al océano. Los logs de B son instrumentación de preparación, no una referencia gráfica válida.

Ambos runs se cierran mediante `dayz_test_close` con terminación ordenada cliente/servidor y logout comprobado. Se libera el lease; `session_status` final muestra banco libre y sesión sin lease. No crash.

## Continuación

Reanudar EV41 desde una referencia A estable, B omitido y A de retorno; la calibración nativa EV48 evita repetir el ajuste visual. Reobservar estado/lease/paquetes antes de cualquier prueba. No borrar las charcas como arreglo. Mantener abiertos 016/019 y la base completa: forma de orillas/remates, cruces, lagos reservados y TB/navmesh/IA siguen pendientes. No promover EV38/39/40/42/46/47 rechazados.

La recuperación por foco no equivale a corregir dayz-mcp. Ticket existente: fb-20261008-233507-8b1c. Sin subagentes ni push.
