# EV112 — Baltic E frente a Chernarus: servidor vacío
**PASS del presupuesto local de RAM**, seis pasadas completas A-B-B-A-A-B,
tres por mapa,30s de calentamiento y120 ventanas por pasada. Baltic E utiliza
su navegación9 propia. Ejecutable, misión normalizada, configuración y paquetes
quedan vinculados por hash antes/después; el agregado vuelve a leer todas las
capturas y los archivos vinculados.

| Mediana entre tres pasadas | Baltic E | Chernarus | Baltic/Chernarus |
|---|---:|---:|---:|
| Memoria residente, MiB | 2786.98 | 3349.35 | 0.8321 |
| Memoria privada, MiB | 3150.33 | 3733.39 | 0.8438 |

La residente es un16.8% menor y la privada un15.6% menor.
Dispersión residente: Baltic0.081%, Chernarus0.129%.
Dispersión privada: Baltic0.078%, Chernarus0.093%.
Se mantiene el margen previamente fijado de1,10 y dispersión máxima5%.

CPU descriptiva: medianas6.272% y4.733% de un núcleo lógico;
rangos4.260..6.535% y4.227..14.328%.
La variación es elevada: no se adjudica una ventaja ni un presupuesto de CPU.
No hay cliente, CE, IA ni jugadores. No son FPS, VRAM, conducción, capacidad
multijugador ni un veredicto global de optimización. La prueba pertenece a E, no F.

La captura5 produjo un falso FAIL del lector antiguo:51.068-20.068 en float
resulta30.999999999999996. El lector nuevo calcula con Decimal sobre el texto
el calentamiento real registrado: primer tick menos duración de primera ventana
menos INIT, y exige>=30 sin epsilon. También rechaza el falso positivo de una
primera ventana larga que antes ocultaba calentamiento insuficiente.
Se conservan result.json y el log original; result-revalidated.json de cada
pasada y comparison.json son los resultados finales. No se repitió ni descartó
ninguna medición para obtener un resultado favorable.

188 tests PASS, cuatro nuevos casos de regresión y diez controles negativos
legacy ejecutados aparte. Fable5.1 revisó el cambio: SOUND.
La exactitud es sobre el texto del motor, con resolución aproximada de1ms
en estos logs; no se declara una precisión temporal física mayor.
El host es interactivo: background-activity-summary.json registra actividad
de otros procesos sin publicar sus nombres. No acredita aislamiento de carga.
Ninguna compilación, generador ni revisión externa propia corrió en las ventanas medidas.

Los seis runs se cerraron de forma ordenada y liberaron el banco. Se corrigió
el archivado del RPT para vincular misión y creación, porque su nombre puede
redondearse al segundo siguiente al nacimiento del proceso. No altera datos
de medición. Se distingue hash del archivo ejecutable del hash de ruta MCP.
RPT conservados incluyen avisos/errores heredados del entorno MCP/DayZ;
un PASS de RAM no significa ejecución sin errores.

Los .gz conservan bytes originales, incluidas terminaciones de línea;
ORIGINS.json guarda hashes descomprimidos. No se publican configuración con
credenciales, inventario de aplicaciones privadas, PBO, NM ni otros binarios.
Reevaluar en otra máquina requiere disponer de los archivos locales vinculados;
no se pueden afirmar esos hashes usando únicamente esta exportación pública.

verified-sources/ conserva las fuentes exactas usadas por la validación, incluidas
las terminaciones de línea del host Windows; Git puede normalizar la copia de
trabajo del código. Los hashes de ejecución se contrastan con estos bytes.
