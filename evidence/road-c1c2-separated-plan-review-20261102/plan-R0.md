# RoadC1C2: preparación verificable separada de la sonda

Estado: BORRADOR_PENDIENTE_DE_REVISION. Consumidor: futura sonda RoadC1C2B del
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
- `.../source-final/observe_road_compile_c1c1.py:144-157`: caminante separado
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
privada preflight-local.py. Metadatos fuera de esos subárboles. Debe definir
todos los directorios permitidos, incluidos vacíos; no permitir extras bajo
work/tools/fixed. No requerir sólo que los archivos esperados estén presentes.
El runner Python y dependencias se fijan para atribuir la suite/procesos; no
declarar procedencia upstream ni loaded-image attestation.

## 3. Preparador y consumidor [DESIGN]

Dos módulos nuevos compactos en carpeta exclusiva, sin importar CLIs consumidas.
Se permite extraer funciones revisadas a la nueva unidad, con delta explícito;
no reescritura de lectores WRP ni nueva biblioteca genérica. Producer y consumer
recorren por separado manifiestos/fuentes/destinos; bibliotecas estándar comunes.

Preparador crea marker exclusivo antes de operar. Una sola ejecución; marker
consumido incluso en fallo. Tres fases ordenadas, cada STARTED fsync antes de
operar y DONE sólo tras cierre de todas sus guardas:
1. SOURCE_CHECK120s: canónico/alias, recursos/herramientas fijados, consumidorC1B,
   inventario exacto y hash de ambos brazos fuente. Perfil actual guardado.
2. COPY150s: cada archivo se abre con guardas path/handle y read+write+rehash
   del destino, misma fuente/mismos bytes. Copia nueva, sin hardlinks/junctions
   ni carpetas C1C/C1C1 reutilizadas. No cambia objetos ni geometría.
3. FIXED_AND_VERIFY90s: copias exactas tools/fixed, loggeroriginal, verificación
   completa work, tools y fixed, fuentes de herramientas y anclas al cierre.
   Conserva identidad path/handle dev/ino/size/mtime, reparse y controles reales
   antes/después. Inventario completo y directorios exactos. No cache de hashes.

El sobre total del escritor es360s/512MiB; cada subfase aplica su propio techo
y el restante global. No prestar tiempo entre subfases ni extender al fallar.
Copias/rehashes/diarios están dentro de los sobres; timeout puede dejar sólo
STARTED/prefijo y no promete informe final. Disco2GiB, ficheroWRP128MiB,
otros inputs64MiB y JSON32MiB, según límites heredados; tablaC1B5.18MB permitida.

Un consumidor180s/256MiB relee su contrato externo por SHA y fuentes/destinos;
comprueba cuatro árboles, tools/fixed, anclas, report+journals y perfiles.
No usa como prueba un hash autodeclarado por productor. El SHA del report se
congela fuera del productor antes de consumidor. Su lectura no ejecuta preflight,
AddonBuilder ni Binarize. Salida máxima32MiB, hashes y listas de faltas completas
o rechazo por cap; no truncar silenciosamente.

VERIFIED_PREPARED_PAIR_BYTES_ONLY exige todas las fases cerradas en orden,
contrato exacto, inventarios exactos, bytes/identidades contrastados, ausencia de
mutación observada y límites de recibos. Si falta cualquier puerta: INCONCLUSIVE
o REJECTED con fase/path, sin autorización nativa. RSS de recibos es observado,
no medición propia del consumidor. No demostrar vigilancia continua.

## 4. Unión futura con sonda C1C2B [DESIGN, no ejecutable todavía]

La pareja C1C2A creada aquí será la ÚNICA carpeta sacrificable de una futura
sonda, expresamente designada por su contratoB, si A tiene consumidor válido.
Antes de mutarla, B debe comprobar nuevamente todas sus entradas por hash,
anclas actuales, perfil y diariosA; un resultado histórico A no reemplaza esta
validación fresca. B no hace otra copia ni muta C1B/C1C/C1C1. Registrar baseline
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
CLI a consumidor real con oráculos; no sólo funciones mockeadas. La copia final
pública corre la misma suite y exactamente los mismos bytes de código/fixtures.

Asientos propuestos para A: Codex executor local600s explícito para contrato,
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
