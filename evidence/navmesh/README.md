# BalticTrial: navegación propia cargada

29-09-2026. Resuelto el aviso «Unable to load navmesh for BalticTrial».
Se generó y guardó navegación propia, se empaquetó conservando las 420 entradas
previas y el WRP byte a byte, y se arrancó cliente/servidor sin addons temporales.
La misión de BalticTrial ejecutó su sonda completa y MCP confirmó un jugador.

La generación completó 60025/60025 tiles en 1m57s, con 2694 full tiles. El archivo
ocupa 34717364 bytes. Paquete final: 421 entradas, 59460475 bytes.
PBO SHA256: `3c3a2f0e649b13e73d483e027f3f3e50db58005848c85beb75321c7a50aa078f`.
WRP compilado SHA256: `45b82cf01b48119032cdb104beab4b2a32f077f141a16bd4400dd94de762272d`.
Navmesh SHA256: `2bb43e22225c14c6c9a500e83d53d91805fe7da346b3b3944ec107a859ee2cb1`.

El bloqueo original era la navegación configurada aún inexistente. El primer
bootstrap no se aplicaba: su PBO contenía config.cpp vacío además de config.bin.
Una sonda temprana confirmó CfgPatches ausente y ruta antigua; reconstruir el addon
sin ese archivo, con el mismo config.bin, permitió cargar la misión y generar
la navegación. Después se retiró ese addon: la prueba final usa el .nm propio.
FileExist dio false para la ruta vanilla con barra inicial aun cuando el motor
la cargó: no usar esa consulta aislada como detector de archivos ausentes del VFS.

MCP: opción tipada navmesh_data_server implementada, revisión Grok SOUND,
commit integrado b024257, bundle reproducible y registro CAS verificados;
preflight, argumento real y conexión al generador comprobados. Sin argumentos
libres ni cambios de políticas. La infraestructura del daemon avisa módulos
antiguos en memoria; worker/registro frescos y ejecución nueva probada, no matar
el daemon para quitar el aviso.

El usuario detuvo Computer Use con Escape. No hubo más interacción con ventanas.
Lease liberado sin cleanup degradado; el run 5c56b92e-3aff-4df5-af0a-74a3121d1b28
permanece RUNNING_IDLE para el usuario, con actividad humana detectada. No iniciar
otro ni cerrarlo sin comprobar primero la sesión viva. NavMeshGenerator conserva
su ventana; archivo guardado y servidor de generación anterior cerrado oficialmente.

Pendiente: entrada visual/recorrido a pie y vehículo, navegación útil de IA,
agua regional y CE. La comparación contra la sonda V3 antigua detectó 0.5852m
en G; esa referencia precede a la corrección del agua. **Actualización:**
`../render-distance/mission-current-asc.json` confirma las612 muestras contra
el ASC corregido (error máximo4.9mm); el ASC viejo falla como control negativo.
El usuario confirma entrada y puente/río visibles, pero denuncia cuadros azules
a distancia. Ver `../render-distance/README.md`: render distante abierto.
La sonda actual reconoce el puente y sus tres puntos de tablero a cota 2m.
Esto aún no es la versión básica jugable ni la versión 1.0.

Nueva skill local: dayz-terrain-workflow, con referencia de navmesh/bootstrap,
validada por quick_validate.py. No se modificaron targets gobernados ni cambios
ajenos en DayZ-Modding-Knowledge-Pack. Copia de la skill en esta entrega.
