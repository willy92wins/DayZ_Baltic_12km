# Kit7 — sonda completa: 19 fallos de contacto
La prueba nativa del 26 de octubre mide **6.801 puntos** y devuelve **FAIL**.
La calibración nueva mide0,039991446m de margen vanilla con5aciertos y289controles
vacíos. Las4.749muestras de regresión F pasan; los19fallos están en el kit7 nuevo.

No fallan agua,terreno ni Roadway. En18puntos RV atraviesa el lecho y alcanza
el terreno aunque Bullet detecta el modelo; en otro, RV alcanza una cara
11,7mm inferior a la superior detectada por Bullet. Todos19coinciden con
vértices exactos del ODOL a la pose usada. Es un candidato de precisión en
bordes compartidos, **no una causa interna del motor demostrada**.

Se conservan los logs completos, expectativas congeladas, calibración,
paquetes, identidad run/PID/creación, revisión Fable y fuentes ejecutadas.
El consumidor no relaja criterios para hacer pasar la prueba.

La reserva MCP caducó al pausar el coordinador durante el contexto; el productor
terminó6801puntos. Se re-adoptó el mismo run/PID, se verificó la identidad
y se cerró oficialmente sin relanzarlo. El primer cleanup fallido queda
preservado junto al recibo de recuperación. Estado final propio: lease libre,
cero comandos pendientes y ninguna limpieza degradada.

Siguiente: candidato aislado de solape local de1,95mm en Geometry de19modelos,
con revisión y gates de cobertura,coste,poses y motor. No cambiar muestras.
La navmesh del kit7 espera al gate físico. Ningún PASS visual,cliente,FPS
o global se deriva de esta sonda.
