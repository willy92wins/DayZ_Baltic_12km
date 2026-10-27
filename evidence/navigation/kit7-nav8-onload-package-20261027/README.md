# Nav8Load1: paquete experimental aislado

**PASS offline de empaquetado; motor y RAM pendientes.** Cambia solo
filterIsolatedIslandsOnLoad de texto"true" al literal1. El tipo nativo todavía
no se afirma: requiere ConfigGetType0 y texto/int/float1 en el motor.
GenParams y tileWidth8 permanecen. No se regenera navegación.

- Mundo candidatoSHA f0e0e6b99da08b48f62ee47fa72b8905a5c9843bee4a30cefa18f517ddb1f603.
- NM360a7348… y WRP0da63d3f… idénticos a Nav8;6826entradas preservadas bytea byte.
- Solo cambia config.bin. Propiedades PBO idénticas; config final reextraído
  y decodificado de nuevo, delta independiente de un único token en clase exacta.
- Control nulo por la misma escrituraPython+CfgConvert: binoriginal idéntico.
-14tests deconfig/fixture real y12contratos de contenedorPASS. Estos últimos
  usan herramientas externas simuladas; la paridad real se prueba en el build.
- Revisión independiente Fable5.1 integrada; preservados informe y código revisado.

Paquete local en E:/DayZ-Baltic-Build/shape-repair-20261025/package-kit7-nav8-onload-20261027.
No se publica el PBO ni se sustituye Nav8. Todavía no está desplegado.
Próximo paso: preparar despliegue nuevo con relectura de entradas desde destino
más sonda deconfig+607 y revisión operativa. Solo si pasa, seis mediciones RAM
NUEVAS contraChernarus. Ningún PASS offline concede aceptación de navegación,
memoria, actores ni cobertura global. Nav8 original conserva607PASS/RAMFAIL.
