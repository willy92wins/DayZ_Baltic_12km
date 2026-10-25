# DayZ Baltic 12km — contexto operativo

La petición viva de Guillermo asignó a esta sesión preparar y ejecutar la fase 0. No perpetuar esa asignación sobre encargos futuros. Leer HANDOFF.md y el plan que indique la nueva petición.

1. No variar el recorte aprobado ni agrandar localmente San Petersburgo. Fuente: evidence/aprobacion.json + recorte-v0.kml, fijados por hash.
2. Agua, reserva natural, conexiones y Narva/frontera son requisitos de producto. Vanilla primero; edificios y anchuras humanas.
3. Datos GIS verificados no equivalen a terreno importado ni a agua/carreteras jugables. Mantener los gates separados.
4. Fuente original inmutable fuera de OneDrive; generated derived/source no versionados por Git. Guardar retoques en capas independientes antes de regenerar.
5. Antes de tocar DayZ Tools, refrescar dayz-preflight si cambió el entorno. Antes de gestionar DayZ MCP, lease y lifecycle guard del runbook. DZ es solo lectura.
6. Sin concurrencia con Exta. No existe una entrega de terreno suya incorporada a esta base.
7. Objetivo 80–100 jugadores. Hardware desconocido; no declarar rendimiento por densidad aritmética, tamaño de mapa o número de tests.
8. No usar el Python global ni instalar plugins GIS experimentales como dependencia de producción.

## Uso del escritorio compartido

Preferencia explícita de Guillermo, 30-09: Computer Use bloquea su escritorio.
Preparar rutas, archivos y comandos antes de activarlo; anunciar el objetivo del
bloque y agrupar las acciones de UI dependientes. Observar entre acciones sigue
siendo obligatorio. Al acabar el bloque, terminar el control disponible y avisar;
no mantenerlo durante cálculos, generación, empaquetado, lectura de logs o
redacción. Reabrir solo para la siguiente operación que realmente necesite UI.
Escape físico detiene ese bloque; no reanudar hasta nueva indicación del usuario.
No equiparar dejar de enviar clics con haber liberado el bloqueo del escritorio:
si la API no expone liberación, comunicar esa limitación sin inventar un método.

## Ritmo de ejecución

Petición explícita de Guillermo, 03-10: completar primero una unidad funcional
de trabajo y comprobarla al final. Agrupar implementación y después su validación;
no intercalar rondas de comprobaciones repetidas ni cierres documentales largos.
Repetir pruebas solo por cambios, fallos o una duda concreta que afecte al resultado.
Antes de una acción destructiva, conservar la comprobación de destino y respaldo.
