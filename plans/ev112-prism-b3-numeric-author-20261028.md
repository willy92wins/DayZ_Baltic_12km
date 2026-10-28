# B3D: materializar el testigo numérico y consumir el archivo guardado

Estado: REVISADO_PARA_EJECUTAR. 35 tests finales PASS; sólo autoría/consumidor MLOD offline.
No autoriza compilar, empaquetar201, desplegar ni iniciar DayZ. Una pareja
binaria posterior necesita plan/revisión/presupuesto propios y preflight fresco.

## Intención y evidencia

EV112 mantiene navegación, agua y extremos mientras corrige Geometry de orilla
seca. B3 amplió12 prismas para que los controles originales700dry y723wet queden
estrictamente dentro del contacto, conservando Visual/Memory/Roadway. B3B fue
REJECTED_BINARY por igualdad exacta mundial; no puede aceptarse por proximidad.
B3C no cambió modelos: censó1520 componentes, local raw exacto en todos, dos
discrepancias mundiales calculadas/8caras, y produjo un testigo de17 cambiosY.
Ver evidence/prism-b3-quantization-20261028/report.json (SHA256
6e3653bb35321a72eee1c583c9345e7c8e27cc1d63340f192da4c0a238ce7028).

[HIPÓTESIS] Escribir exactamente ese testigo float32 y normales coherentes puede
producir un MLOD guardado que preserve todas las invariantes y los marcos
calculados. No demuestra que una compilación nueva conserve centro o metadatos.
El resultado de esta unidad será OFFLINE_CANDIDATE_ONLY, nunca PASS del mapa.

Corrección de fundamento: el guard de grosor exacto antiguo era sobre entrada
d130. En c769 guardado20/36pares son exactos y16 tienen residuos<=1.491e-8m;
el consumidor anterior permitía1e-6. B3D exigirá36/36 EXACTOS como B3C, sin
editar los recibos anteriores ni presentar el candidato antiguo como exacto.

## Anclas verificadas y alcance

[EXACT] tools/quality/prism_contact_b3_ev112.py:73-96 codifica Geometry MLOD
con cabecera28bytes, puntos16bytes y normales12bytes tras los puntos; el índice
normal de cada cara es único y su dirección se deriva del producto vectorial.
tools/water/review_compact_collision_v31.py:load devuelve cabecera/lods/blobs
guardados. tools/quality/verify_prism_contact_b3_ev112.py:components comprueba
asignación, cierre, winding, convexidad y normales; sus tolerancias existentes
de plano/base/normales1e-6 NO sustituyen la nueva igualdad exacta de grosor.
tools/quality/prism_b3_binary_ev112.py:pose_check exige matriz identidad y
traslación float32(origen+centro). Primitivas geométricas reutilizables; no
relanzar autores ni consumidores CLI B3/B3B/B3C consumidos.

Entradas selladas: c769 MLOD candidato B3, d130 fuente antes de ampliación,
ODOLb2c8 sólo como centro/bbox de referencia bajo hipótesis, contratoR1 5df50091,
contratoB3 447d, reportB3C 6e3653bb y censo2d63837e. Fijar también código lector,
autor/consumidor/tests/plan en contrato nuevo antes de ejecutar. Conservar
700/723 coordenadas y etiquetas por original2658, pose19394363, origen[8262,7,8934].

## Autor propuesto

[DESIGN] Autor separado y determinista: no llama al solver ni inventa cambios.
Lee el testigo sellado, rechaza índices repetidos/fuera de dominio/NaN y valores
before diferentes de los bytes de c769. Aplica exactamente17 Y float32 y nada
de X/Z. Autoriza normales sólo en caras incidentes en esos índices; exige que
pertenezcan a los12componentes y no compartan normal con ninguna cara exterior.
Recalcula normales de esas caras desde los puntos resultantes. Escribe un
candidato nuevo en directorio exclusivo, conserva fuente. Todo otro byte de
Geometry, Visual, Memory, Roadway, flags, caras, selecciones y materiales exacto.

## Consumidor independiente

[DESIGN] Proceso separado que NO importa autor ni solver B3C. Lee el MLOD
guardado de nuevo con el lector fijado; no confía en el resumen del autor.
1. Binding completo del contrato/entradas, cabeceras yEOF; cuenta9120/12160/1520.
2. Reconstruye índiceY permitido desde las diferencias before/after selladas y
   comprueba cada valor serializado bit a bit. Máscara de bytes propia: sólo
   Y de esos17 puntos y normales de sus caras incidentes; todo lo demás exacto.
3. Reconstruye todos los componentes,36 pares seleccionados de grosor EXACTO
   en coordenadas float32 guardadas (resta racional o float64 exacta demostrada
   en este rango), plano/base<=1e-6 respecto a d130, radialXZ idéntico a c769,
   bbox Geometry/modelo igual, cierre/convexidad/normales con límites vigentes.
4. Calcula las caras mundiales por ambas rutas con centro/pose fijados y exige
   identidad EXACTA de valores y bits de todo Geometry, no sólo puntos tocados.
   No declara estos cálculos coordenadas observadas del motor o futuro ODOL.
5. Overlay completo sobre Visual intacto con±0.02/.01;700dry/723wet quedan dentro
   estrictamente con mismos márgenesXZ locales/mundiales del B3, sin moverlos.
6. No validar por autor==consumidor: comprobar invariantes geométricas y datos
   guardados. Testigo identifica el cambio permitido, no prueba su corrección.

## Puertas, fixtures y presupuesto

[DESIGN] Planreview300s, codereview300s, tests120s, autor60s/2GiB,
consumidor180s/2GiB, una ejecución de cada tras revisión. Una corrección de
instrumento por repro antes de ejecutar; fallo posterior se conserva y obliga
a revisar la hipótesis/plan antes de nueva unidad. No barrido de candidatos.

Tests positivos: fixture no trivial con cambio real, normales y serialización;
caso exacto válido y parámetros de700/723 conservados. Negativos: índiceY
duplicado/fuera de12componentes, before incorrecto, after no representablef32,
NaN, X/Z/flag/Visual/normal ajena alterados, grosor con residuo pequeño que
cumpliría1e-6 pero no EXACTO, normal invertida, caja/extremo cambiado, marco
mundial discrepante, overlay fuera de límites, control movido/reclasificado,
testigo de otro candidato/contrato. Tests contra archivo guardado, no sólo arrays.

PASS offline sólo si todas las puertas exactas y geométricas pasan; errores de
lectura/identidad/recurso INCONCLUSIVE, violación geométrica REJECTED_MLOD.
Guardar fuente del instrumento, contrato, recibos, pruebas y candidato fuera
del público. Publicar sólo código/evidencia autorizados desde public-repo.
Después redactar plan binario nuevo; no reutilizar la autorización de B3B.

47FAIL21inciertos, referencia independiente de agua, RAM, nueve regresiones
visuales yC1 siguen abiertos. El council ampliado continúa en cola tras lo previo.

## Adjudicación del plan — Fable5.1 nativo151.5s

SOUND-with-fixes, fuentes intactas. F1 aceptado tras medición propia: d130
4560/4560pares exactos por resta Fraction (el guard histórico seleccionado
no demostraba por sí solo los1508 componentes restantes). El consumidor nuevo
exigirá grosor exacto en TODOS los4560pares del candidato guardado. Fuera de
los12componentes, identidad de bytes con c769/d130, comprobada por consumidor.
F2 aceptado: validación independiente de before/after representables float32,
bit-diferenciaY no vacía, XZ idénticos, índices únicos/autorizados, antes igual
a c769. Rechazar entrada redundante, NaN y un testigo parcial/fuente distinta.
F3 RECHAZADO por evidencia:17/36pares del testigo tienen grosor local recentrado
NO exacto; todos tienen grosor MLOD exacto y ambos marcos mundiales bit-idénticos.
Ese filtro adicional ya fue refutado y eliminado en B3C (H1:30válidos vs17).
No era condición previa ni motivo del testigo. Se reportarán grosores local y
mundial; no imponer un requisito nuevo ni relajar el MLOD exacto aprobado.
F4 aceptado: márgenes local/mundial y witness_component700/723 exactamente
iguales al recibo B3 sellado6b29e213; computados de nuevo desde archivo guardado.
F5 aceptado: Inconclusive para binding/lectura/cabeceras/EOF/conteos/recursos;
Rejected para violaciones geométricas/de máscara/contrato del testigo.
El consumidor no importa autor ni solver. Máscara desde caras/índices leídos,
no lista del autor. Dominio descubierto propio:17Y,50caras/50normales incidentes
sin compartir con caras exteriores. Techos MLOD winding negativoY, como antes.
Fixture sintético guardado positivo no trivial; candidato real se escribe UNA
vez tras code review y tests. No ejecutar el autor real como test y repetirlo.
Controles alterados/TAGG/margen1ULP/grosorresiduo/no-op se añaden a los negativos.
Preflight oficial sigue SyntaxError línea213; comprobación directaP:montada,
DZ/scripts,AddonBuilder yjunctionMods presentes. No se modificó skill gobernada.
Diag de ruta común Exp no encontrado; no se acredita entorno de ejecución;
esta unidad sólo autoría MLOD offline, ningún build niDayZ.

## Revisión de código recuperada

Fable5.1 nativo135.25s,SOUND-with-fixes; cápsula íntegra de tres archivos y
anclas, sin herramientas. Inputs intactos. Adjudicación completa en
R/prism-b3d-review-capsule-20261028/adjudication.md. Correcciones de clasificación
de excepciones y escritura pendiente antes de promoción, mutante nextafter
explícito y postcondición50caras/50normales.27tests geométricos y8CLI deben pasar
antes de una autoría real y su consumidor. No revisorN+1. TimeoutR1 anterior
300s y NameErrorprelaunch preservados. Nueva entrega consumida.

Suite final corregida: 27 tests geométricos (69.75s) y 8 CLI (11.125s),
ambos procesos rc0, en R/prism-b3d-final-tests-r1-20261028/report.json.
Autor y consumidor reales todavía no ejecutados al sellar este plan.
