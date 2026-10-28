# B1: captura nativa íntegra, diagnóstico inconcluso

Run propio 7de477e9-56cc-4b9c-ae6e-aa9d19db457b, 28-10-2026.
345 registros completos: tres rondas de los115puntos fijados antes de medir.
Identidad de misión, CSV, ejecutable y4PBO verificada antes/después; filePatching
desactivado, sin serverMods externos. Cierre oficial, run retirado, sin lease,
sin comandos pendientes ni limpieza degradada. No cliente ni revisión visual.

## Resultado

- Cero discrepancias de referencia Ground/Roadway decisiva.
- INCONCLUSIVE_DIAGNOSTIC:20Roadway ya inciertas (60filas) y109filas
  donde cambia el reloj durante las consultas. Oleaje global no cambia en
  ninguna fila; no hay deriva de estado/lista de objetos entre rondas.
- Profundidad frente a superficie con fake wave menos origen:1035valores,
  residuo máximo absoluto0.000009m. Sin fake wave: máximo0.160596m.
- Al variar la altura del origen, los contrastes lineales de profundidad
  tienen residuo máximo0.000010m. Superficie sin fake high/low idéntica en345filas.
- En los43fallos originales de agua, las129observaciones sin fake coinciden
  numéricamente con Wref. Eso no identifica un objeto ni demuestra agua accesible.
- Ejemplo723: origen6.092312 -> depth+0.749641; origen6.927969, encima del
  lecho de6.91797 -> depth-0.0860157. Pond=false en ambos, sin cambiar el mapa.
- Se conservan todas las rondas, signos y valores, incluidos109confusores.
  El subconjunto sin confusores registrados no prueba que no existan otros.

Las observaciones apoyan H1 (dependencia de Y) y H2 (fake wave) en estos puntos.
H3/identidad de superficie y referencia de producto siguen INCONCLUSIVE.
El resultado original2658 permanece FAIL:47puntos fallidos y21inciertos.
Esto NO repara el mapa, no convierte sus fallos a PASS ni valida el piloto entero.

## Validación del instrumental

Revisión Fable5.1 CLI nativo460.266s; fuentes revisadas archivadas.
Correcciones adjudicadas: serialización de hora de creación, close nulo y
comprobación explícita filePatching/serverMods.21tests de identidad y8mocks
de lifecycle pasan. El contrato puro anterior conserva26tests; su productor
compiló ahora en el motor y escribió la captura completa.
La banda1ms de identidad temporal concilia formato host100ns y MCP/psutil;
no cambia altura0.01, Roadway/RV0.03, agua0.05 ni Bullet0.01.
Las correcciones finales tienen revisión de Codex y tests; no se atribuye
una segunda revisión externa que no se ejecutó.

## Continuación

No repetir B1 ni la sonda2658. Resolver el referente de agua de producto desde
el diseño original, independientemente de H/B/W medidos; no sustituirlo por
flags+NoFake (la propuesta anterior ya falló).
B2 requiere demostrar espacio libre de orígenes/rayos y geometría de oclusores,
conservar los fallos700/723 y los3impactos en árboles, sin mover muestras ni podar.
RAM, C1 sin revisar, nueve regresiones humanas y calidad global siguen abiertos.
Piloto de orilla completa sigue sólo offline; los82Y experimentales del solape
de carretera no equivalen a integrarlo. Council ampliado continúa en cola.

Los hashes se refieren a archivos en disco y a los procesos propios registrados;
no se afirma un hash de memoria del motor. Los binarios vanilla/PBO y trazas
privadas de CLI no se publican. manifest.json verifica los archivos conservados.
