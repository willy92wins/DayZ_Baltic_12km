# Q02B1 — núcleo de medición geométrica certificado

VERIFIED_NUMERIC_KERNEL_ONLY: 53 consultas de oráculos propios, productor0.250s
(18.57MB RSS) y consumidor independiente0.360s (41.64MB). 21tests privados8.218s
PASS sin skips. Incluye un control deliberado RESOURCE_INCONCLUSIVE; el recibo
lo identifica y NO afirma que todos los registros tengan resultado numérico.

Intervalos racionales p48, testigos enteros para ambos extremos de cada raíz,
prefijos por suma y estaciones con frontera/soporte inciertos explícitos. Se
verifica cada certificado y el conjunto de certificados requerido por el
consumidor que camina aristas; no exige igualdad del número de cálculos repetidos.
Caps4096bits/100000operaciones porconsulta, raíz precontada antes de ejecutarla.
Umbral binario estricto1e-8 conservado. Atan2/sumas de giro pendientes.

El autor inicial agotó240.172s: dos archivos completos salvados del stream y una
cola de tests recuperada47.891s; no se presenta como terminal completo. Fable
164.781s NEEDS-WORK detectó fallos, incluidos transcript sobrescrito y expectativa
literal no exigida. Corrección Muse149.766s y revisión de integración; Fable delta
82.890s SOUND-with-fixes adjudicada. R0/R1 de tests tienen0tests y errores
preservados, R2/R3 y final son corridas diferentes tras correcciones concretas.
Los tests usan los oráculos históricos literales porhash; se descartaron fórmulas
regeneradas erróneas. El campo controls es el entero4 del contrato real.

ContratoR0 se conserva; R1 cambia sólo una expectativa equivocada ANTES de recibir
código: longitud T exacta no es degenerada, pero su envolvente p48 no prueba soporte
para h=T, por lo que SUPPORT_UNCERTAIN es correcto. No se cambiaron entradas,
tolerancias, etiquetas humanas ni umbral. Dos espacios finales se normalizaron.

No censo completo del mapa, naturalidad, reparación, build, DayZ, lease ni
carretera terminada. Nueve humanos GEOMETRY_UNBOUND/0resueltos, C1 NOT_REVIEWED,
calibration_ready=false. Los datos publicados son herramientas y oráculos propios.
Siguiente Q02B2 tiene borrador de prefijos compartidos/piloto real pendiente de
revisión, no autorización de ejecución. RoadB4B/Q03/Q05 siguen pendientes.
