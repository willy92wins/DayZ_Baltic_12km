# RoadC1C2: preparación verificable separada de la sonda

Estado: REVISADO_PARA_CONTRATO_Y_AUTORIA_C1C2A. Consumidor: futura sonda RoadC1C2B del
laboratorio0/3 de Q04, previa al pivote/huella del producto Q05/Q07 y P10/P11.
Esta unidad inicial C1C2A prepara sus entradas completas; no lanza herramientas
nativas. C1C1 consumido no se reanuda, modifica ni reclasifica.

## 1. Evidencia y decisión

Anclas [EXACT], relativas al worktree salvo prefijo R:
- `evidence/road-c1c1-canonical-probe-20261101/probe/report.json`: BUDGET antes
  de preflight/help/brazos, source_checked70.299s y copy_complete173.549s desde
  consumed.started. Intervalo103.250s. No fixed_inputs. No suboperación causal.
- `.../real/observer.json`: cuatro árboles6893files MATCH; falta fixed/include.lst.
  Observador110.313s de proceso,85.094s interno. No son dos mediciones independientes
  del mismo reloj ni predicción del tiempo de una corrida futura.
- `.../source-final/probe_road_compile_c1c1.py:214-229`: la fuente se coteja,
  cada copia se lee y vuelve a leer, después herramientas/fijos y un recorrido
  completo del árbol work, todo bajo un único180. No eliminar esa segunda lectura.
- `.../source-final/observe_road_compile_c1c1.py:125-137`: caminante separado
  de los cuatro árboles e inputs. Es lectura de bytes; no decoder de terreno.
- R=`E:/DayZ-Baltic-Build/shape-repair-20261025`. ContratoC1B b7d33588,
  reciboconsumidor4c52ddae; contratoC1C1 3d7f5b6a/report80a60369, completos en
  evidencia. Fuente6892comunes+1WRP por brazo,480678967B la pareja.

Hipótesis verificable: separar la materialización y su consumo de la ejecución
nativa permite comprobar PREPARED_PAIR sin que una ayuda/build consuma o dependa
de una preparación inconclusa. No se afirma que separar acelere el disco.
Se descartan: relanzar C1C1 con más tiempo; reutilizar sus work; saltar hashes o
guardar sólo cuentas; atribuir el coste a OneDrive/cache/antivirus sin aislarlo.

Se propone un NUEVO presupuesto de preparación y nuevos outputs. Aumenta la
asignación frente al intento180, se declara explícitamente y se revisa antes de
autoría; nunca cambia el recibo consumido. Los tiempos guardados motivan separar
los trabajos, no demuestran una cota suficiente ni garantizan éxito.

## 2. Contrato externo antes del código [DESIGN]

Crear `road-c1c2a-preparation-inputs-20261101` y salida exclusiva
`road-c1c2a-prepared-20261101`. Contrato fija referencias completas con SHA/bytes,
no abre WRP/PBO/P3D semánticamente ni recensa modelos. Reutiliza manifiestoC1B,
sus0/3WRP,configc054 y los12archivos de distribución AddonBuilder enumerados en
C1C1; preserve PNG/PAA/RVMAT literalmente. No generar catálogo nuevo.

Fija contratoC1C1, su aprobación/código final y rechazo como evidencia inerte;
también observador/report, originales9f8786a5/rawfix812e68aa, logger1d24d7d4,
include/exclude, herramientas ya enumeradas, binconfig y OShelper. No rederivar
el rawfix ni su SyntaxError. Revalidar anclas actuales exactas al congelar el
nuevo contrato: diferencia bloquea, no repinar para que pase. Firma observada
AuthenticodeValid/chainBuiltfalse conserva época; no nueva afirmación de cadena.
Ancla canónica/alias/tag/target/devino y ancestros exactos; no atravesar alias
en el lector regular ni tocar skills/P:. Cada hash identifica bytes leídos.

El contrato enumera DESTINOS: work/control/root, work/candidate/root,
tools/AddonBuilder con12archivos, fixed/include.lst, fixed/exclude.lst y copia
privada fixed/preflight-local.py. Metadatos fuera de esos subárboles. Debe definir
todos los directorios permitidos, incluidos vacíos; no permitir extras bajo
work/tools/fixed. No requerir sólo que los archivos esperados estén presentes.
La raíz preparada contiene exactamente work, tools, fixed y meta. En meta:
marker.json; source.started.json/source.done.json;
copy.started.json/copy.done.json; fixed.started.json/fixed.done.json;
report.json. No output/logs/process/profile ni otro hermano, aunque esté vacío.
Los recibos externos del supervisor/consumidor viven FUERA de esa raíz.
Directorios necesarios derivados de archivos declarados; lista de directorios
vacíos permitidos = []. Todo directorio/archivo adicional rechaza con su path.
El runner Python y dependencias se fijan para atribuir la suite/procesos; no
declarar procedencia upstream ni loaded-image attestation.

## 3. Preparador y consumidor [DESIGN]

Dos módulos nuevos compactos en carpeta exclusiva, sin importar CLIs consumidas.
Se permite extraer funciones revisadas a la nueva unidad, con delta explícito;
no reescritura de lectores WRP ni nueva biblioteca genérica. Producer y consumer
recorren por separado manifiestos/fuentes/destinos; bibliotecas estándar comunes.

Preparador crea raíz con mkdir exclusivo y meta/marker.json con open(xb) antes de operar; no sobrescribir un marker previo. Una sola ejecución; marker
consumido incluso en fallo. Tres fases ordenadas, cada STARTED fsync antes de
operar y DONE sólo tras cierre de todas sus guardas:
1. SOURCE_CHECK120s: canónico/alias, recursos/herramientas fijados, consumidorC1B,
   inventario exacto y hash de ambos brazos fuente. Perfil actual guardado.
2. COPY150s: cada archivo se abre con guardas path/handle y read+write+rehash
   del destino, misma fuente/mismos bytes. Copia nueva, sin hardlinks/junctions
   ni carpetas C1C/C1C1 reutilizadas. No cambia objetos ni geometría.
3. FIXED_AND_VERIFY80s: copias exactas tools/fixed, loggeroriginal, verificación
   completa work, tools y fixed, fuentes de herramientas y anclas al cierre.
   Conserva identidad path/handle dev/ino/size/mtime, reparse y controles reales
   antes/después. Inventario completo y directorios exactos. No cache de hashes.

FINALIZE dispone de10s dentro del total: primero persiste fixed.done.json,
después genera report.json con SHA/bytes de los seis journals y marker. El
reporte final se escribe exclusivamente, sin sobrescribir un reporte anterior.
Los tres sobres120+150+80 suman350; los10restantes cubren el sellado final.
Cada registro tiene phase, event, sequence entero único creciente y elapsed_ns
monotónico desde el inicio del proceso; wall_time sólo informativo. Secuencias
1..6 para STARTED/DONE, tiempos monotónicos no decrecientes y duración contra
su sobre. DONE no demuestra que FINALIZE haya terminado.

El sobre total del escritor es360s/512MiB; cada subfase aplica su propio techo
y el restante global. No prestar tiempo entre subfases ni extender al fallar.
Un supervisor externo (nuevo driver local, no CLI consumida) monitoriza tiempo
de pared y RSS del árbol propio; identifica PID/birth, mata sólo identidades
propias observadas al superar el sobre. Bloqueos en open() no dependen de que
el productor vuelva a consultar reloj. Incluye lanzamiento/drenaje en el total
540s; sólo inicia consumidor si quedan sus180s completos. Si no, INCONCLUSIVE.
Los topes se aplican antes de cada operación propia y desde fuera; no prometen
detectar hijos nunca observados ni detener I/O del kernel instantáneamente.
Copias/rehashes/diarios están dentro de los sobres; timeout puede dejar sólo
STARTED/prefijo y no promete informe final. Disco2GiB es cap de bytes de SALIDA observados, no espacio libre. Precondición
separada: más de3GiB libres en la unidad de salida, conservando C1C1. Las
fixtures usan carpeta temporal exclusiva en E con esas mismas guardas, no
TEMP de C ni limpieza ajena. FicheroWRP128MiB,
otros inputs64MiB y JSON32MiB, según límites heredados; tablaC1B5.18MB permitida.

Un consumidor180s/256MiB relee su contrato externo por SHA y fuentes/destinos;
comprueba cuatro árboles, tools/fixed, anclas, report+journals y perfiles.
No usa como prueba un hash autodeclarado por productor. El SHA del report se
congela fuera del productor antes de consumidor: el driver de Codex, tras
terminar o retirar las identidades propias, hace lectura nueva y fija SHA/bytes
del report si existe, journals/marker presentes y completion externo. Ese
external-observation.json también se pina como entrada del consumidor. Si un
kill impide report final, se consume el prefijo observado y el recibo externo;
no se inventa un report ni se relanza el productor. Se define su esquema y
literales antes de código. Journals completos deben coincidir por SHA con el
report y por SHA/longitud con esa observación externa; report.contract_sha256
debe ser el contrato externo, nunca un SHA elegido desde el report. Su lectura no ejecuta preflight,
AddonBuilder ni Binarize. Salida máxima32MiB, hashes y listas de faltas completas
o rechazo por cap; no truncar silenciosamente.

VERIFIED_PREPARED_PAIR_BYTES_ONLY exige todas las fases cerradas en orden,
contrato exacto, inventarios exactos, bytes/identidades contrastados, ausencia de
mutación observada y límites de recibos. Si falta cualquier puerta: INCONCLUSIVE
o REJECTED con fase/path, sin autorización nativa. Tabla de estados del contrato:
- Productor: IN_PROGRESS mientras corre; PREPARED_PAIR_BYTES_ONLY únicamente
  después de las tres fases y cierre; PREPARATION_STOPPED para fallo capturado,
  con phase/reason. Un kill puede dejar sólo prefijo, sin estado final.
- VERIFIED sólo si report PREPARED, fases completas ligadas/ordenadas, recibo
  externo terminó normalmente sin exceder sobres y todas las lecturas coinciden.
- INCONCLUSIVE: stop preventivo BUDGET/CAP o kill externo con prefijo coherente,
  sin afirmación PREPARED. Faltan archivos todavía no escritos: no son aceptación
  ni evidencia de mutación por sí solos. Un cap que detiene ANTES de excederse
  no equivale a constatar que el límite fue vulnerado.
- REJECTED: bytes/identidad/inventario inesperado, contradicción de binding/orden,
  exceso de límite efectivamente observado, o report PREPARED sin las puertas
  completas. Un fallo de lectura no prueba contenido distinto: I/O_INCONCLUSIVE
  si no hay otra contradicción, con path/error literal. Ningún estado parcial
  autoriza B. Las variantes concretas y códigos quedan congelados en contrato. RSS de recibos es observado,
no medición propia del consumidor. No demostrar vigilancia continua.

## 4. Unión futura con sonda C1C2B [DESIGN, no ejecutable todavía]

La pareja C1C2A creada aquí será la ÚNICA carpeta sacrificable de una futura
sonda, expresamente designada por su contratoB, si A tiene consumidor válido.
Antes de mutarla, B debe comprobar nuevamente todas sus entradas por hash,
anclas actuales, perfil y diariosA; un resultado histórico A no reemplaza esta
validación fresca. Baseline de B liga explícitamente manifiestoC1B b7d33588,
contratoA, reportA, consumidorA y observación externaA por SHA/bytes. B ejecuta
fixed/preflight-local.py desde la pareja preparada, SHA812e68aa, nunca la ruta
de autoría. B no hace otra copia ni muta C1B/C1C/C1C1. Registrar baseline
A completo fuera del work sacrificable; sus bytes originales siguen enC1B.

Contrato/código/review propios de B después de medir A. MarkerB separado y
exclusivo; no reanudar un intentoB. Empezar con comprobación fresca y preflight,
ayuda aislada, control0 y candidato3 condicionado a TODOS los gates de control.
Preservar argv/OShelper/parentPIDbirth, STARTED/fsync antes de logger/Popen,
loggerfase exacto, errores/logs privados, Binarize observado, OPRWúnico y
verificación de fuentes/work antes de siguiente brazo. No reducir estas puertas
para aprovechar tiempo. PresupuestoB se fijará con datosA, no hereda360 ni180.
No asignar ahora techo ejecutableB ni prometer que Binarize acepte control0.

No paquete aceptado/DayZ ni decoderOPRW0/3/terreno/materiales. MáximoB futuro
COMPILE_PROBE_OBSERVED_ONLY; pivote/huella/oclusores/accesos requieren datos reales.

## 5. Oráculos, revisión y cierre

Antes de código fijar literales externos: miniárbol0/3 (bytes, no generación del
expected desde productor), directorio vacío permitido/prohibido, includevacío,
loggeroriginal y fases. Negativos cerrados N01-N12: inputcambiado; archivoextra;
directorioextra; reparse/aliascambiado; destinoexistente; fuente que cambia durante
lectura; copia truncada; fixed omitido; DONE sinSTARTED/fasefueraorden; journal o
report co-mutado; consumidorfalseverde ante hashdeclarado; timeout/cap sin READY.
N06 se desdobla: cambio durante lectura mediante fixture determinista de I/O
en test de función (sin hook habilitable en producción), y mutación real de un
destino/fuente después de DONE ante consumidor CLI. N11 mantiene report y todos
journals consistentes pero cambia un byte físico: el rehash propio debe rechazar.
N13 hermano output/ vacío en raíz debe rechazar; N14 PREPARED sin fixed.done
debe rechazar. N15 journals co-mutados/timestamps/sequence y report sin repinar
su observación externa deben rechazar. Las pruebas aún NO están ejecutadas.
CLI a consumidor real con oráculos; no sólo funciones mockeadas. La copia final
pública corre la misma suite y exactamente los mismos bytes de código/fixtures.

Asientos de A: Codex EXECUTOR local600s explícitamente asignado para contrato,
oráculos y delta; revisión externa Anthropic180s (incluye contrato); suite120s
256MiB; una corrección180s por repro cerrado y una recuperación180s sólo si falta
dictamen. No bajar a Qwen/OpenCode consumidos ni repetir council. Revisión de
este plan180s, una ronda según gates-ledger; NO CONVERGE lo retira. Codex integra
con contexto compartido declarado; revisor no se coordina para evitar solaparse.

Sólo después de contrato externo y código revisados/suite verde: UNA preparación
360s y UN consumo180s,540s total, sin retries internos. Esta revisión de plan no
autoriza por sí sola materializar ni lanzar B. Fallo nuevo exige evidencia y
decisión técnica, no permiso de producto ya concedido. C1C1 se conserva BUDGET.
Q03C/Q05 históricos, ángulos y referentes no dependen de este stage. Nueve casos
humanos siguen0resueltos, C1NOT_REVIEWED, mapa intacto.


## Adjudicación Fable129.562s — revisión única consumida

SOUND-with-fixes / CONVERGE, identidad nativa claude-fable-5-1 por mensaje,
init y modelUsage. Cinco cierres antes del contrato: inventario de raíz, tabla
terminal, binding/orden de journals, supervisor/reserva de finalización y
distinción outputcap/free-space/ruta del preflight. Se aceptan sus contraejemplos
como diseño de oráculos, no como tests ya corridos.

Precisiones del integrador: la tabla del revisor llamó «mismo trabajo» a fases
que cambian alcance; se rechaza extrapolar85/2 o atribuir warm-cache. Los tiempos
observados motivan el diseño, no cotas de rendimiento. FIXED80+FINALIZE10 no
garantiza cabida. N06 no requiere debilitar producción: fixture de I/O sólo de
test y mutante físico por CLI cubren dimensiones distintas. El root.mkdir del
código anterior ya era exclusivo; se refuerza marker(xb) sin afirmar que esa
expresión por sí sola demostrase una carrera explotable. Se corrige el ancla
del caminante a125-137. Perfil/fuente original y firma histórica no repinados.

Postimagen editorial integrada por Codex (planner/integrator mismo contexto),
sin otra revisión externa ni consenso. Aún no contrato, códigoA, materialización
ni sondaB. Esta revisión sólo permite preparar contrato/oráculos y autoríaA con
los gates anteriores; presupuestoB y su código siguen pendientes de A.
