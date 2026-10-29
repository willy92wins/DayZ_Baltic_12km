# B3G2 — lector de logs abiertos y diagnóstico explícito

Estado: REVISADO_PARA_IMPLEMENTAR. Fable5.1 nativo65.203s adjudicado.
Corrección de instrumentación; no cambia
modelo, puntos, etiquetas, tolerancias, mundo ni misión Enforce cbb4f4a3.
Traza B3G1/P9/P10. Original47FAIL21inciertos y RAM siguen abiertos.

## Hechos frescos

B3G1 run09fd0cce-0cc7-4cd3-9d05-1d59fae3db74 retirado orderly_close,
lease release terminal_safe/selfnone/pending0. Heartbeat10s funcionó. Candidato
no arrancó. ReadAllBytes del script abierto lanzó IOException sharing violation;
el observador no produjo captura ni resultado. No repetir esa unidad ni salvarla.

Después del cierre se conservaron bytes:31Q sin END270, sólo diagnóstico tardío.
La misión alcanzó CreateCustomMission y consultas; NO captura completa.
Hay un DumpStack SCRIPT(E) por PluginConfigDebugProfile ausente y avisos al cerrar.
No es evidencia de excepción ni causa física. Paquetes instalados fijados:
bridge7078c2e4 y scriptsff0ad7ee; tres entradas extraídas una vez a
b3g1-failure-discovery-20261029/report.json, sin cambiar paquetes.

[EXACT] PluginManager.c:327-348, SHA86751f97..., imprime mensaje y DumpStack
si GetPlugin devuelve null. PluginItemDiagnostic.c:92-105, SHA18b1abea..., consulta
ese plugin y protege el uso con if(m_ConfigDebugProfile). MCP_DiagPlugins.c:30,
SHAa37838f3..., llama super.PluginsInit. La pila archivada coincide con ese camino.
Esto explica el DumpStack acotado; NO certifica inocuidad de cualquier SCRIPT(E).

## Propuesta y presupuesto [DESIGN]

1. Antes de autoría, revisión180s. Repro offline con escritor que mantiene abierto
   un archivo: ReadAllBytes falla y FileStream Open/Read con FileShare.ReadWrite
   funciona. No usar handles privados ni cerrar escritor para leer.
2. Nuevo lector de snapshot acotado20MiB: tomar longitud, leer exactamente ese
   prefijo con compartir escritura; fallo/EOF/cambio de identidad -> INCONCLUSIVE.
   Para END270 exigir segundo snapshot de misma longitud/hash, nombre/ctime/mtime
   y PIDbirth propios. Archivo creciente sin END permanece PENDING, deadline180s.
   Mantener bytes originales, no recortar errores ni reescribir texto capturado.
3. Clasificador explícito de logs: compile init.c/Formula too complex y errores
   desconocidos bloquean. Únicamente la secuencia exacta del DumpStack anterior,
   con mensaje, pila completa, un mismo timestamp y archivos/líneas fijados por
   las fuentes instaladas, se registra como diagnóstico conocido sin ocultarlo.
   Un frame alterado/extra, plugin distinto, traceback truncado, excepción o
   segundo error permanece bloqueante. No whitelist por palabra PluginManager.
   Si se necesita esa clasificación, reportar su presencia como confusor residual;
   la pareja sólo es DIAGNOSTIC, no cierre de calidad ni prueba causal global.
4. Nuevos wrappers/recibos, misión/directorios/sellos B3G2 aunque bytes de Enforce
   permanezcan idénticos. No mutar B3G1 sellado ni usar sus preparadores. Consumidor
   vuelve a verificar bytes/gramática/fuentes y conserva cada diagnóstico.

Code review180s/suite120s2GiB antes de preparación120s. Una pareja nueva, control
primero y candidato sólo con identidad y270Q/1080R completos. Preflight fresco;
FIFO600, readiness300/captura180, heartbeat10s después de adopción exacta,
cierre/release/status oficiales. Sin reintentos internos ni cambiar protecciones.
Antes de run deben estar entregadas/adjudicadas ambas revisiones y tests verdes.
No editar DayZ_MCP ni skills gobernadas para resolver este diagnóstico.

Tests independientes: archivo realmente bloqueado por escritor Windows,
snapshot creciente/truncado/oversize, END cambiado durante copia, encabezado
viejo/PIDforeign, DumpStack real exacto, variante de cada frame, error adicional,
mensaje ausente/pila incompleta, log con sólo compilación fallida. Positivo de
captura completa en primera observación conserva clocks como B3G1.

## Adjudicación B3G2 — 65.203s

Se refuta la premisa de Fable de que script_*.log carece de timestamp: los bytes
99df8cd5... muestran01:20:46.268 en el mensaje y todos los frames. Se conserva
igualdad de timestamp, además de contigüidad estricta sin líneas intercaladas.
Golden derivado del archivo archivado, no creado a mano; normalización sólo de
timestamp y ruta de misión explícita, cuyos bytes y origen se verifican aparte.
Un único bloque conocido como máximo. Un log limpio con cero bloques no exige
inventar un diagnóstico: puede pasar esta guarda; dos bloques bloquean siempre.
No confundir esa guarda con compilación/captura270 completa.

Se aceptan: identidad estable FileIndexHigh/Low+VolumeSerialNumber obtenida del
mismo handle por GetFileInformationByHandle, comparar antes/después; mtime sólo
frescura, nunca igualdad durante append; creación y PIDbirth del proceso adoptado
comprobado vivo, no PID supuesto dentro del texto. Conservar SCRIPT(W) y listar,
SCRIPT(E) fuera del golden exacto siempre bloquea. Avisos de cierre posteriores
al captureEnd no se introducen retrospectivamente en captura.

Repro cubrir escritor FILE_SHARE_READ y escritor sin compartir: con exclusivo,
INCONCLUSIVE limpio, sin VSS/backups ni cierre del escritor. FileShare.Delete
permite abrir durante rotación pero FileID cambiado invalida, no continuidad
inventada. El plan no atribuye falta deEND a DumpStack: sólo31Q por cierre de
nuestro run tras fallo del lector; no mide duración completa ni acepta física.

Golden debe contener literal de mensaje y todos los frames ordenados con sus
líneas exactas. Cada entrada instalada y misión tiene pin; se valida la fuente
de los frames disponibles, sin fingir inspección de archivos no extraídos.
Si hace falta ampliar esas anclas, descubrimiento específico antes del código.
No aplicar el consumidor B3G1 a una captura B3G2 con diagnóstico permitido:
wrapper nuevo liga el clasificador y conserva confusores; no mutar el sellado.
