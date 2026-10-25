# Diagnóstico temporal acotado del agua V30

Continuación del encargo vigente, 03-10. No cambia el diseño ni los criterios V4.

Problema: trece muestras mojadas dieron GetWaterDepth <= 0, aunque SurfaceIsPond
era true y la superficie sin ola correspondía al plano esperado. El terreno
coincidió con la referencia. Falta separar oscilación, semántica de la consulta
y ausencia efectiva de agua.

[EXACT] API declarada en P:/scripts/3_Game/global/game.c:1162,1174-1187,1510.
La implementación nativa es opaca. No atribuir causa antes de ejecutar.

[DESIGN] Una misión de servidor sin jugadores mide los trece puntos congelados
y cuatro controles (estanque profundo, estanque profundo alto, mar y orilla seca).
151 muestras separadas al menos 2s por punto; unos cinco minutos útiles. Registra
suelo, presencia de agua, superficies con/sin fake wave, profundidad consultada a
tres cotas, nivel de mar y ola. Todo es estado de servidor; no RPC, ninguna edición
del terreno ni movimiento de jugadores. Las cotas distintas ayudan a discriminar
si GetWaterDepth depende de la Y de entrada. No simular continuidad rellenando
muestras ausentes ni repetir hasta encontrar una fase favorable.

Consumidor: rechazar series incompletas, IDs duplicados/desconocidos, valores no
finitos o tiempo no creciente. Exigir los17 puntos en151 rondas y al menos300s.
Informar rangos, cambios de signo y residuos entre consultas, sin promocionar el
FAIL previo a PASS. Si los valores no se explican, resultado INCONCLUSO. Si existe
falta persistente de cobertura o agua por debajo del suelo en un punto que debe
ser permanentemente mojado, proponer/corregir la geometría local conservando los
corredores navegables y carreteras. La serie aislada no cierra la revisión visual.

Presupuesto: una ejecución válida; segundo intento solo por fallo de compilación,
serie incompleta o instrumentación incorrecta identificada. No cambia la NM.
Despliegue bajo lease, paquete @DayZ_Baltic_ContinuityV30_Nav fijado por hashes.
Cerrar solo nuestro run mediante lifecycle y liberar lease al terminar.

## Corrección de instrumentación del primer run

Run d304c54b: END151/17 presente, pero el lector rechaza correctamente la
serie: duración298,87s e intervalos mínimos1,977s. La misión programaba con
timeslice acumulado y registraba GetTime; ambos relojes no coincidieron en esta
ejecución. Se preservan misión, log y fallo V1. No se reduce el umbral temporal.

La revisión2 programa la siguiente ronda2000ms después de terminar la anterior,
usando GetTime tanto para programar como para registrar. Conserva los17 puntos,
151 rondas, el paquete y los criterios del lector. Además registra por separado
la consulta de superficie antes/después de SurfaceIsSea/SurfaceIsPond y después
de GetWaterDepth: V1 devolvió nivel marino en puntos cuyo plano de estanque V4
sí encontraba. El efecto del orden es HIPÓTESIS hasta comparar las tres consultas
en el mismo punto/instante. Es el segundo intento acotado por instrumentación,
no una repetición para conseguir fases de ola favorables.
