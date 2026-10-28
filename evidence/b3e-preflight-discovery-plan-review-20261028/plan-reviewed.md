# B3E: localizar el agotamiento de preflight

Estado: BORRADOR_PENDIENTE_DE_REVISION. Sólo lectura y nuevos recibos. No build.

## Hechos e hipótesis

B3E dispone de 41 tests PASS y code review Fable adjudicada. La única ejecución
se detuvo por INCONCLUSIVE_RESOURCE: 60.047 s, pico residente 86.49 MB. El log
oficial confirma P:, Tools, DayZDiag, vanilla y junction Mods. No report.json de
preflight, contrato B3E, carpeta control ni candidato: no hubo compilación.
No se atribuye causa a Steam, antivirus, OneDrive, corrupción ni caché.

[HIPÓTESIS] El bloqueo está en una lectura o hash posterior al log oficial.
El consumidor actual no guarda fases intermedias, así que no permite localizarlo.
La comprobación de cinco metadatos muestra cuatro ejecutables de 0.19–24.81 MB
y P:/bin/config.cpp de 201417 bytes. Tamaño pequeño no prueba lectura rápida.

## Unidad independiente propuesta

[DESIGN] Un script stdlib de diagnóstico, sin importar ni ejecutar el preparador
consumido, carga sólo los dos recibos anteriores fijados por SHA256 y obtiene las
cinco rutas exactas: AddonBuilder, FileBank, CfgConvert, Binarize y P:/bin/config.cpp.
No búsquedas recursivas ni seguimiento de junctions fuera de esas rutas. Verifica
cada SHA256 esperado y registra inicio, primer bloque, final, tamaño y duración.
Cada evento se vacía al disco para conservar el último paso si agota presupuesto.
Conserva también tiempo antes/después de leer los dos recibos. Los recibos se
copian por bytes al nuevo directorio, sin modificar originales.

Un padre propio lanza ese script sin ventana, identidad PID/nacimiento y timeout
total de 60 s desde Popen; el hijo no lanza descendientes. Al agotar, termina sólo
ese hijo, guarda timeout y bytes parciales; no reintenta. No aumentar este límite.
No invocar preflight oficial otra vez ni mover/montar P:, editar skills, compilar,
empaquetar, desplegar, solicitar lease o iniciar DayZ. Sin caché que sustituya hashes.

## Interpretación y presupuesto

HASHES_MATCH: los cinco hashes coinciden en esta lectura; no demuestra qué ocurrió
en el intento anterior ni certifica todo el preflight. HASH_MISMATCH: conservar
archivo/ruta/esperado/observado y bloquear continuación. INCONCLUSIVE_TIMEOUT o
INCONCLUSIVE_IO: preservar fases, no declarar válido el entorno. Un fallo de
formato, ruta, esquema o hash de los recibos también es inconcluso.

Una revisión independiente de plan de hasta 180 s, entrega breve. Tras adjudicar,
implementación stdlib pequeña revisada antes de una única lectura de hasta 60 s.
Positivo y negativos de hash/ruta/error/timeout en archivos temporales antes del
censo real, agrupados en una suite de hasta 30 s. Ninguna repetición de B3E ni
reclasificación de su INCONCLUSIVE_RESOURCE. Una futura continuación de binarización
requerirá plan y evidencia propios; B3D continúa sólo OFFLINE_CANDIDATE_ONLY.
