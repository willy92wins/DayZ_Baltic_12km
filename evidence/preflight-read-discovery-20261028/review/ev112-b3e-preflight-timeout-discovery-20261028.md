# B3E: localizar el agotamiento de preflight

Estado: REVISADO_PARA_IMPLEMENTAR. Fable 5.1 nativo 66.25 s, SOUND-with-fixes
adjudicado abajo. Sólo lectura y nuevos recibos. No build.

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

## Adjudicación — 28-10-2026

Revisión y entrega en R/b3e-preflight-discovery-plan-review-20261028. Una entrega
completa, identidad claude-fable-5-1, fuentes intactas. Código aún no implementado.

- Se acepta cronometrar también is_dir de P:/DZ, P:/bin, P:/core y P:/scripts,
  la lectura del contrato y los dos hashes de fuentes preflight posteriores al
  log oficial. Sin importar ni ejecutar preflight ni tocar P:. El alcance de
  lectura se amplía sólo a esas dos fuentes y cuatro metadatos conocidos.
- La multiplicidad se toma del código y de los recibos reales, no del ejemplo
  del dictamen: tres herramientas se leen una vez; Binarize y config.cpp DOS
  veces cada uno. tools_sha256 contiene AddonBuilder, FileBank y CfgConvert,
  no Binarize. Las dos fuentes de preflight se leen una vez en esta fase.
- El helper consumido usa hashlib.sha256 con bloques de 4 MiB; se reproduce
  ese patrón. Se refuta la hipótesis de read_bytes para el hash de binarios.
- Un resultado rápido sólo mide esta lectura. No permite deducir retrospectivamente
  caché, fase oficial lenta ni causa global. Se conserva HASHES_MATCH y duraciones
  numéricas; no se crea HASHES_MATCH_FAST con un umbral arbitrario sin contrato.
  Si no aparece el retraso, otra fase necesitará una propuesta separada.
- Eventos con flush y os.fsync; el coste de la instrumentación se incluye y se
  declara. Timeout del padre 60 s total desde Popen, sólo reducción para tests.
- Valores esperados fijados ahora en el plan, no calculados por el hijo:
  dry-road-build-preflight-20261028/report.json:
  354fbb2e5edea80e88521f02cd135ac2f6a7608a14085af5cc088395a542e68e;
  prism-b3-binary-replay-20261028/contract-r1.json:
  5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244.
  El primero es un recibo de entorno histórico; el segundo es además la ancla
  de procedencia ya preservada en B3D/B3E. Ninguno demuestra entorno actual.
- Tests previos: positivo completo, mismatch, ruta ausente/ajena, error E/S,
  formato/esquema/hash de recibos inválido y timeout con hijo propio lento.
  Preservar último evento y originales; ningún reintento. Suite de hasta 30 s.

Se mantiene la revisión de código antes de una única ejecución diagnóstica.
No amplía los 60 s ni autoriza compilación. B3E sigue inconcluso y consumido.

## Ejecución asignada — petición viva posterior

Guillermo pide continuar pruebas y preparar carreteras. Codex implementa esta
unidad separable mientras descubre el siguiente trabajo vial. Code review
independiente de hasta180s antes de producción; una corrección agrupada, suite30s,
una lectura real60s. No autoriza relanzar B3E. El padre usa el handle propio de
Popen y GetProcessTimes para PID/nacimiento; kill se dirige al handle, no busca
procesos por nombre. Firma verificada en documentación Microsoft de GetProcessTimes.
La medición registra también la relectura de integridad de ambos recibos;
no se suma esa relectura como lectura de herramientas ni se oculta su coste.

Descubrimiento del ejecutor: sys.executable de GIS es un launcher Windows y su
imagen real es el CPython empaquetado de Codex detrás de ese entorno. Para el
hijo stdlib se resuelve GetModuleFileNameW(NULL) del proceso GIS vivo y se usa
esa MISMA imagen con -I -S, sin paquetes ni Python global resuelto por PATH.
Así el handle de Popen corresponde al intérprete que lee y se puede terminar
sin dejar al hijo del launcher. Se exige igualdad de PID reportado y handle,
y el negativo de timeout comprueba el PID escrito por el hijo antes de pararlo.
Firma GetModuleFileNameW verificada en documentación Microsoft. No es evidencia
retroactiva de causalidad del preflight anterior ni un cambio de runtime GIS.
