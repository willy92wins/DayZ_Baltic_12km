# B3G: el control rechazó la misión; no hubo mediciones físicas

Resultado: NATIVE_MISSION_COMPILE_FAIL. El motor rechazó init.c:220 con
`Formula too complex` y `Can't compile mission init script`. No apareció
baltic_contact_b3g.log. Los39tests offline y el lint de1archivo anteriores no
detectaron este error de compilación. El bridge sí quedó BOUND: eso no prueba
que la misión propia compile. No se lanzó el candidato y no hay comparación.

Run d4b28db9-f080-4a1c-85b4-c73faaee2e8e retirado por orderly_close; release
terminal_safe, self none, pending0, sin cleanup_degraded. El proceso permaneció
vivo hasta ese cierre; el nombre crash_*.log no demuestra muerte del proceso.
Se conserva identidad host del motor, misión, cuatro PBO y cinco vanilla.

Fallo operativo adicional: en la pausa de continuidad caducó el lease y se
agotó el plazo de recogida180s. Se readoptó sólo el run propio para cerrarlo.
El deadline de la primera observación no se persistió; no se reconstruye como
medida acreditada. Rechazo por plazo y rechazo nativo son hechos separados.

R0 fuente/código/tests/revisiones/recibos archivados; TODO CONSUMIDO. Source es
instrumentación histórica, no autorizada para relanzar. La preparación aislada
validó copias, no comportamiento. Los logs completos del motor son privados;
se publican hash y extracto pertinente sin volcados ni recursos vanilla.

Plan de recuperación B3G1 nuevo: dividir la expresión, mantener20campos exactos,
corregir falsa discrepancia JSON600/600.0 en copia, persistir relojes y vigilar
errores de misión antes de aceptar readiness. Heartbeat concurrente durante
propiedad, cierre en finally. Ningún nuevo run hasta revisar y probar el flujo.

Los47FAIL/21inciertos originales, RAM y aceptación visual/global siguen abiertos.
No se modificó agua/terreno/objetos ni se rebajaron tolerancias.
