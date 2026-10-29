## Veredicto: **SOUND-with-fixes**

La hipótesis y el límite `COMPILE_PROBE_OBSERVED_ONLY` son correctos. No debe exigirse un lector OPRW semántico para esta captura.

Exigirlo crearía circularidad: C1D debe construir el decoder a partir de muestras independientes. Si C1C ya dependiera de ese decoder para aceptar las muestras, el decoder se estaría validando contra sus propias suposiciones. Para C1C bastan: fichero nuevo y único, tamaño, hash, magic `OPRW` y los 4 bytes siguientes registrados como crudos. No deben interpretarse objetos, alturas, materiales ni siquiera una versión esperada sin una referencia externa independiente.

Las correcciones siguientes son previas a ejecutar, no opcionales.

### Hallazgos bloqueantes

1. **Literales PE no equivalen a API verificada.**  
   Los anchors prueban que existen las cadenas de sintaxis, `-toolsDirectory`, rutas de ejecutables, `Build Successful` y los mensajes de error. No prueban precedencia entre argv, `userSettings` y defaults, ni que `-binarize=`/`-cfgconvert=`/etc. sobrescriban los `Use*Default=True` de [AddonBuilder.exe.config], ni el formato exacto aceptado por el parser, ni códigos de salida.  
   **Corrección:** clasificar cada afirmación como `LITERAL_OBSERVED`, `HISTORICAL_INVOCATION` o `RUNTIME_TO_OBSERVE`. El helper histórico sí corrobora orden posicional fuente→destino, `-project=` ancestro de la fuente y búsqueda de `Build Successful`, pero también usaba junctions hacia `P:\` que el plan no reproduce. Debe declararse explícitamente qué contiene `work/<arm>/root` y qué referencias externas a `P:` se esperan observar; no reintroducir junctions en silencio ni atribuir un fallo por dependencias ausentes a Binarize.

2. **`-include=include.lst` relativo es incorrecto o, como mínimo, no probado.**  
   La ayuda anclada en offset 90257 habla de ruta absoluta al fichero de patrones y el helper histórico pasaba una ruta absoluta.  
   **Corrección:** usar `-include=<ruta absoluta privada a include.lst>`, con hash fijado del fichero y contenido literal `*.paa;*.emat;*.xml;*.nm;*.c;*.csv`. Fijar también el directorio de trabajo del proceso; si no, la resolución relativa queda dependiente del CWD.

3. **La fase `-help` puede fallar por Steam antes de probar la CLI.**  
   Los literales incluyen “Steam must be running or specify -toolsDirectory”, pero la fase 4 no pasa `-toolsDirectory`. Un fallo ahí bloquearía los builds por una causa ajena a la entrega de ayuda.  
   **Corrección:** invocar la copia privada con CWD = directorio privado del exe y argv mínimo `AddonBuilder.exe -help -toolsDirectory=<raíz instalada DayZ Tools>`. Definir éxito como rc=0 más texto `WELCOME TO ADDON BUILDER`/`SYNTAX` capturado en stdout/stderr y log privado dentro de la ventana. Registrar que incluso `-help` puede crear `user.config` de .NET o tocar estado de Steam: es un intento consumido y no es side-effect-free.

4. **La puerta de control, tal como está, puede hacer la sonda indecidible por diseño.**  
   Se exige al control rc=0, marcador, hijo Binarize observado y exactamente un WRP para poder lanzar el candidato, pero a la vez se admite que “C0 control vacío puede no compilar”. Si C0 es vacío a propósito, exigirle WRP garantiza que el candidato nunca se lance.  
   **Corrección:** separar dos puertas:
   - *Puerta de lanzamiento del candidato:* proceso íntegro y atribuible — ventana de logs privada válida, rc/marcador coherentes, sin `ERROR`/`FATAL`, sin mutación de C1B, sin hijo inesperado.  
   - *Puerta de resultado de cada brazo:* un WRP nuevo único ≤128 MiB con magic/versión cruda.  
   Si el control cumple la primera pero no produce WRP porque es vacío, el candidato puede lanzarse una vez y su propio resultado se juzga con la segunda puerta. Si el control falla de proceso, el candidato sigue bloqueado. Sin esta separación, el resultado predecible es `CONTROL_NO_ARTIFACT` y coste sin información sobre el candidato.

5. **El gate de hijo Binarize es demasiado estrecho frente al muestreo de 150 ms.**  
   Un Binarize legítimo más breve que el intervalo, o varios Binarize por fichero, producirían un falso bloqueo. El plan acierta al llamarlo `NOT_OBSERVED` y no inventar identidad, pero debe asumir la consecuencia.  
   **Corrección:** registrar *todos* los descendientes observados (PID, birth time, ruta de imagen, SHA del exe fijado antes, argv completo), exigir “≥1 Binarize coherente” en vez de un hijo singular, y tratar DSSignFile observado sin `-sign` como anomalía. Si Binarize no se observa, el veredicto del brazo es `PROBE_INCONCLUSIVE_NOT_OBSERVED`, no “build fallido”. Comparar el argv hijo antes de atribuir lectura del bin/config copiado resuelve la nota del placeholder `-binpath`: si el hijo no es el exe pineado o su argv apunta a otro sitio, es `UNEXPECTED_CHILD`, no éxito parcial.

6. **Portabilidad de la copia privada y aislamiento de logs están infraespecificados.**  
   Copiar exe/config/DLLs no garantiza resolución de ensamblados .NET, que el fichero se llame exactamente `AddonBuilder.exe.config` junto al exe, ni que `log4net.Config=logger.xml` se resuelva desde el directorio del exe y no desde el CWD. Además, .NET guarda `userSettings` por usuario y por ruta del exe fuera del directorio privado, y Steam puede escribir fuera.  
   **Corrección:** lanzar con CWD fijado al directorio privado; inventario cerrado de DLLs con nombre+ruta+SHA y parada si falta una dependencia en tiempo de carga; snapshot previo/posterior de las rutas `user.config` de AddonBuilder alcanzables y declaración expresa de que el aislamiento es de *logs y salidas*, no de perfil de usuario ni de Steam, salvo que se redirijan `LOCALAPPDATA`/`APPDATA` sólo en el entorno del hijo y se observe el resultado. Mantener la regla actual: sin log privado dentro de la ventana, `NOT_OBSERVED` y parada; nunca usar el RPT global como recibo.

7. **La fase 3 de `SyntaxError213` es contradictoria.**  
   Dice que si el error persiste se archiva una copia corregida con un único delta, pero también que “Exit no0 bloquea todo lo posterior”. Si el original siempre reproduce el error, nada puede avanzar nunca.  
   **Corrección:** declarar que el original es el oráculo negativo (debe reproducir `SyntaxError213`) y que la copia con delta único, diff y AST parseable archivados es el preflight operativo cuyo exit=0 abre la puerta. Sin esa distinción, la fase es un callejón sin salida. No hace falta tocar la skill instalada.

### Hallazgos de presupuesto y mutación

8. **Los presupuestos no suman.** Autoría 600 s + review 180 s + suite 120 s no puede contener copia 180 s + preflight 60 s + help 30 s + dos brazos de 300 s + observador 60 s = 930 s de ejecución.  
   **Corrección:** publicar dos sobres separados — autoría/revisión y ejecución — y un techo total de ejecución ≥930 s más drenaje de logs. El observador que re-hashea árboles de ~13.786 ficheros y las fuentes C1B en 60 s/256 MiB es optimista; darle un presupuesto derivado de bytes/ficheros medidos en la copia, no un número redondo.

9. **RSS y disco “observados” deben definirse sobre el árbol, no sobre el padre.**  
   2 GiB RSS debe ser la suma de working sets de todos los descendientes vivos en cada muestreo, reconociendo que entre muestreos puede excederse. Al matar: primero el AddonBuilder raíz propio para que no respawne, después sólo descendientes verificados por PID+birth; nunca por nombre de exe. Añadir una espera corta de estabilidad de tamaño/mtime antes de hashear logs, porque `ProcessRollingFile` tiene `bufferSize=512` y puede perder o retrasar la cola tras kill/timeout.

10. **Mutación de inputs: separar tres clases.**  
    C1B e instalación deben quedar bit-idénticos (duro, bloquea aceptación). La copia `work/<arm>` es sacrificable: si el build la muta, se reporta `WORK_INPUT_MUTATED` con diff de hashes, pero no debe confundirse con `SOURCE_CHANGED` de C1B ni invalidar automáticamente el artefacto ya capturado, porque cada brazo tiene su copia. Lo que sí invalida es mutación cruzada entre brazos o de las herramientas instaladas. El observador debe recomputar hashes desde los artefactos, no fiarse de los hashes que el propio wrapper escribió en su recibo — el plan ya lo insinúa con “reporte/hash co-mutados”; hacerlo explícito como regla.

### Lo que ya está bien y no debe tocarse

El orden control→candidato sin reintentos, no usar `-clear`/`-sign`/`-packonly`, temp/out frescos, no prometer cuota dura de disco/RAM frente a un hijo opaco, tablas separadas para “hash instalado” frente a “proceso realmente observado”, no fijar versión WRP 32 sin observarla, no ampliar el blanco de errores tras ver el resultado, y dejar C1D como plan propio de decoder. Q03C/Q05 en paralelo lógico sin depender de aceptación nativa es correcto.

## Final: **SOUND-with-fixes**

Aplicadas las correcciones 1–7 como condiciones previas y 8–10 como precisión de contrato, la cápsula es ejecutable como `COMPILE_PROBE_ONLY` sin convertirse en aceptación de mapa ni en decoder encubierto.