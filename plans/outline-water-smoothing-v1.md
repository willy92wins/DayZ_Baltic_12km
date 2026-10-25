# Suavizado general y agua en zonas bajas

Petición viva de Guillermo, 01-10-2026: suavizar el outline general y corregir
el agua que aparece intermitentemente en terreno bajo. Extiende P2/P10/P12;
no cambia el recorte XY, la reserva, el acercamiento de SPB ni P9/P11.

## Diagnóstico antes de editar

1. Identificar el paquete real: V10 `d1008dd6`, agua `f9a5cdf7`; conservarlos.
2. Separar geometría triangular, bordes de la textura WorldCover y agua dinámica.
   Medir todas las alturas nativas; muestrear también el interior de las celdas
   costeras. Las clasificaciones agua/tierra proceden de los vectores congelados.
3. Observar con cámara fija los puntos problemáticos, cerca y a media distancia.
   Registrar terreno, nivel sin/con oleaje visual, rango de mar y clima. No
   interpretar una superficie azul pintada como una inundación física.

[EXACT] `P:/scripts/3_game/global/game.c:1174-1187` declara rango de mar,
oleaje máximo/actual y consultas con/sin oleaje visual. Estas últimas ignoran
el terreno y pueden devolver objetos: registrar tipo y profundidad también.
El registro histórico `evidence/render-water/auto-observer/baltic_water_observer_auto_v1.log`
midió mar0.5..1m y wave_max0.25m; refrescarlo en V10. Sumar1+0.25 es una
envolvente conservadora de diagnóstico, no una fórmula del motor demostrada.

[EXACT] `waterway_common.py:41-52` interpola la diagonal NW-SE observada.
`prepare_lake_bathymetry.py:45-66` usa distancias al contorno y banco+0.35m.
El consumidor regional existente acepta tierra desde mar_máximo+0.25m;
no demuestra todos los triángulos de todas las orillas ni margen visual dinámico.

## Edición y puertas

[DESIGN] Crear una capa derivada del V10, sin sobrescribir el aceptado. Suavizar
los cambios bruscos de forma identificados, usando transición continua y
restricciones explícitas de costa/canales/islas, gálibo y carreteras. No bajar
el agua ni borrar humedales para ocultar el síntoma. La magnitud y soporte se
fijan con el diagnóstico; ningún ASC se importa antes del consumidor independiente.

PASS offline: referencias intactas; ámbito/delta trazables; terreno finito;
sin nuevas inundaciones secas; profundidad y anchura navegables conservadas;
reserva/islas protegidas; no nuevos taludes>35° ni regresión en el acceso Narva.
PASS nativo: importación, guardar/cerrar/reabrir, export completo y comparación
de todas las alturas/materiales/objetos; regenerar navmesh sobre ese WRP.
PASS visual/dinámico: mismos puntos y cámaras antes/después, agua observada
durante variación y margen documentado. FAIL o INCONCLUSO conserva el V10.

Computer Use agrupado: preparar antes los ficheros y cámaras. No mantenerlo
durante cálculos o empaquetado; respetar sesiones ajenas. El Escape anterior
terminó el bloque; el «continua» posterior autoriza reanudarlo.

## Candidato V24, fijado antes de resolver

Diagnóstico: 425970 muestras en47330celdas costeras;25647 muestras fuera del agua
vectorial bajo1.25m. Sonda localV10 observó agua sobre12muestras de borde y los
4controles interiores secos durante129s; registro parcial, no ensayo completo.
La marea real recorrió0.5..0.999984m. No atribuir inundación al interior por su
cota1.25m: esos cuatro controles no se inundaron en este intervalo.

[DESIGN] V24 suaviza el relieve seco con sigma12m, transición48m alrededor de
carreteras/agua y delta acotado6m. Perfil monótono lleva bajos1.25→1.40m; fuera
de orillas reduce pendientes, y el suelo protegido del puente se conserva.
El collar de30m a la costa se resuelve con planos nativos: toda intersección
seca alcanza1.4m o agua local+0.35m, la mayor; núcleos de lago a más de una
diagonal de celda conservan15cm mínimos de profundidad. Canales de navegación
conservan todos sus vértices exactos; el consumidor independiente vuelve a
medirlos. Taludes limitados35°,16direcciones conservadoras. Cota±6m en el collar.
LP acotado300s,1hilo; si no es factible no se produce ASC. El aspecto suavizado
es un candidato por contrastar visualmente, no una aceptación por fórmula.

## Discriminador V24 y excepción local V25

V24a inviable, ningún ASC. `individual-row-bounds.json` demuestra146filas de
tierra imposibles bajo±6m. Un islote de14.4969m² en[6360.28,10779.68,6365.44,10784.90]
no contiene vértices nativos y sus triángulos están a−12m: para alcanzar1.4m
se necesitan13.4m, no6. `conflict-geography.json` verifica la forma contra los
vectores; no figura entre los283 polígonos de tierra protegida anteriores.
La hipótesis inicial de conflicto en lake217 no se confirmó: el subconjunto
original, su variante sin margen y su variante sin núcleo son factibles.

[DESIGN] V25 conserva exactamente todas las restricciones de V24a. Amplía solo
la cota de subida a15m en vértices mojados a48m o menos de los vértices de esas
146filas. El resto conserva±6m; no cambia la profundidad protegida de los canales.
La región y los límites se congelan en pre-solve.json/local-exception.npz antes
de resolver. Esto recupera formas de tierra omitidas por discretización;
su extensión real y las pendientes deben pasar el consumidor independiente.

## V26: completar el margen seco declarado

El consumidorV25 encuentra531vértices secos bajo1.4m. Ocho son del acceso
protegido del puente (1.270..1.386m) y deben permanecer exactos según el plan;
el verificador inicial no distinguió esta excepción. Los demás son pequeños
déficits del objetivo suavizado, máximo1.6971mm. V26 eleva únicamente los
vértices secos no protegidos bajo1.4m, guarda el delta explícito y conserva
V25. Se repiten pendientes/ámbito; costa/lago/canales se comprueban sobre el ASC
o se reutilizan solo si se demuestra identidad exacta de todo su soporte.

## Rechazo V26 y discriminador V27

La auditoría adicional de los23lagos sin núcleo a8.485m detecta9sin una muestra
de15cm de profundidad; algunos completamente secos. V25/V26 no se importan.
V27 conserva las restricciones originales y añade15cm mínimos sobre un núcleo
a4.5m en esos23lagos (representante si tampoco existe ese núcleo). Esto prueba
primero si conservar el agua es compatible con el margen de orilla existente;
no se relajan márgenes ni se modifica el contorno vectorial. Solve acotado300s.
Si no es factible, aislar por lago antes de proponer una transición diferente.

## V28: transición representable y protección de islas

V27 inviable. El certificado geométrico muestra que en lake127 y172 el punto
mojado pedido está dentro de la envolvente convexa de la parte seca del mismo
triángulo. Un plano afín no puede estar0.5m por debajo de todos esos puntos.
El conflicto existe sin limitar pendiente ni delta vertical; no se arregla
aumentando la cota. Diagnóstico `small-lake-geometric-conflict.json`.

[DESIGN] Solo en los23lagos sin núcleo a8.485m se admite una transición de6m
desde el contorno original hasta el inicio del margen seco agua+0.35m. El
modelo de agua y los vectores fuente quedan intactos. Dentro de sus núcleos
a4.5m se exige15cm de agua; si tampoco tienen ese núcleo, se conserva un
representante mojado. El mar y los demás lagos conservan la orilla estricta.

La revisión V25 también detectó34islas protegidas que perdían margen al bajar
su interior con el suavizado. V28 prohíbe bajar todo el soporte nativo original
de esas islas; conserva las alturas que ya pasaron el consumidorV9. No es
aceptación por máscara: volver a comprobar las intersecciones y representantes.
Se reconstruye el sistema con estas protecciones; solver300s/1hilo. Ningún
candidato previo se importa. Copia editableV26 creada,8988archivos verificados,
todavía sin abrir/importar; puede recibir el siguiente ASC aceptado por la UI.

## V29: proteger las caras de las islas, no elevar su fondo adyacente

V28 se detuvo antes del solve:238restricciones de fondo chocan con la cota
conservadora de vértices de isla. No hay solape entre polígonos de agua e islas.
El soporte de construcción de islas incluye vértices mojados; congelar su
cota reproduce una meseta que invade el núcleo del lago. El comentario final
de `refine_foundation_lake_shore.py` ya distingue soporte diagnóstico de límite.

V29 conserva V28 y sustituye esa cota por el contrato geométrico ya aceptado:
intersección entera de isla≥nivel local, núcleo a6m y representante≥nivel+0.35m.
El exterior del collar conserva el suelo de isla como mínimo. Se agregan
planos explícitos, sin reducir profundidad ni margen del resto de orillas.

## V30: precisión de las restricciones de isla

El diagnóstico algebraico de V29 reduce su rechazo a una fila de coeficientes
nulos con RHS−8.58306888e−8m:85.8nanómetros de redondeo sobre cota fija. El
certificado no supera su propio umbral1e−7, y no prueba un conflicto físico.
V30 descarta términos nulos y recupera la holgura1e−6m que ya empleaba V9
(`refine_foundation_lake_shore.py`, generación de land_constraints). Mantiene
el consumidor independiente1e−5m y todos los márgenes físicos previos. No
aumenta tolerancias de pendiente, profundidad, ámbito ni calado.

V30 resuelto, ASC a8f83e7a. Primeras puertas PASS: ámbito/pendientes/margen seco,
reserva5.941332km² y7controles positivos/negativos. La comparación adicional
del acceso oeste es exacta; al este hay0.974mm máximo de diferencia fuera de
los693vértices protegidos. Se conserva ese FAIL de igualdad como diagnóstico;
la aceptación de conducción usa los mismos criterios V10 ya fijados (6.5%,
3cm transversal/cuerda6m,1cm unión), sin exigir igualdad donde el plan permite
suavizar. Verificar ambos terrenos con ese consumidor antes de importar.

## V31: conservar los puntos de agua ya aceptados en motor

V30 pasa el consumidor continuo de costa/núcleos/islas, pero la comprobación
adicional de los81212 puntos congelados V5 encuentra242 muestras de lago sin
los15cm previstos. Ejemplo lake033, [8310,3702], está1.929m dentro del polígono:
el terreno pasa de1.68 a3.28m, sobre agua2.93m. La banda de lago entre el borde
y el núcleo de8.485m no estaba cubierta por aquel consumidor. V30 queda
rechazado para despliegue; no se ha importado. Terrain Builder solo abrió y
guardó una copia del V10 con nombre outline_v30.tv4p; ya se solicitó su cierre.

[DESIGN] V31 añade al sistema V30 todos los puntos anteriores con coordenadas,
clases, profundidad y márgenes intactos. Conserva las restricciones continuas,
pendientes, límites de cambio e islas; no mueve muestras para obtener un PASS.
Resolver una vez con límite300s,1hilo. Si es inviable, conservar certificado y
localizar la incompatibilidad antes de modificar la transición. Si es viable,
repetir consumidor continuo y comprobar también los81212 puntos. La importación
requiere ambas puertas, además de reserva y accesos. Este chequeo previo debe
formar parte obligatoria del empaquetador; no basta el PASS de los núcleos.

## V32/V33: transición de lago compatible con la malla, mar protegido

V31 inviable. El certificado independiente utiliza3restricciones y demuestra
el conflicto sin filas de pendiente: en lake168 dos vértices mojados deben
quedar≤2.130001m, pero una punta seca casi entre ambos se exige≥2.63m. El tercer
vértice tiene peso0.006606; incluso elevándolo al máximo8.63m no basta. Margen
algebraico69.183249, certificado válido. No es ruido numérico. Fuente:
`tests/regional_outline_smoothing_v31/geometry-conflict/report.json`.

[DESIGN] El margen agua local+0.35m se alcanza a6m del contorno de todos los
lagos. La geometría original de tierra conserva adicionalmente≥1.4m en sus
planos costeros, para proteger frente al mar; el contorno marino no retrocede.
Esto separa el borde físico del agua del alto de la ribera en una malla6m.
No se modifica el polígono ni el modelo de agua, ni las clases/posiciones de
los81212 puntos V5. Núcleos de lago,15cm, canales, islas, reserva y accesos
conservan sus criterios. V32 construye matrices; V33 agrega las protecciones
exactas de isla y todos los puntos congelados y resuelve300s/1hilo. Si falla,
diagnosticar; no relajar profundidad, mar ni taludes para obtener PASS.

V32 construido:349661variables,13939901filas,0constantes imposibles. Matriz
1d1919e2,variablesb32684f8. V33 añade449457planos de isla y puntosV5; resuelve
en175.031s, residuo máximo4.58e-7m. ASC9d2954fc. Comprobación separada de los
81212puntos congelados PASS,0fallos,0cambios de coordenadas/clases/profundidad.
El consumidor continuo y la reserva/accesos deben terminar antes de importar.

## V33: importacion nativa y discriminador de objetos

El consumidor continuo termino PASS en sus13puertas, incluidos los81212puntos
congelados. Reserva/accesos y7controles PASS. Importado el ASC9d2954fc en copia
aislada, Rebuild terrain y guardado. Primera exportacion literal `3.wrp`,
ce647459: alturas nuevas correctas (max5.96e-8m), materiales exactos,10161IDs
preservados. FALLA poses:4947objetos de agua y5puentes cambian soloY, entre
-3.173147 y+3.325739m. No empaquetar ese archivo. La secuencia no aisla aun
que accion interna recalcula las cotas. Evidencia first-export.json y
first-export-object-diff.json en outline-v33-native.

[DESIGN] Discriminador acotado: cerrar guardando, respaldar el proyecto/capa,
restaurar solo `default.tv4l` desde el editableV10 verificado y reabrir sin
Rebuild. Exportar a nombre nuevo y comparar todas las alturas/materiales/poses.
Esto prueba si restaurar la capa opaca conserva las posiciones absolutas;
no se interpreta ni parchea el formato ALB1. Si falla, conservarlo y diagnosticar
el formato/importacion de objetos. Si pasa, guardar/cerrar/reabrir y exigir una
segunda exportacion identica por contenido canonico antes de compilar.

El discriminador de capa mantiene las4952diferencias (4.wrp c46b8568); alturas
y materiales siguen correctos. La lectura acotada de ALB1 localiza4952registros
univocos: dos doubles de posicion, tres floats de orientacion, escala, offset
vertical float y IDlocal. Ejemplo ID6217 tiene offset-0.350000024m; restaurar
el fichero original conserva ese offset al cambiar el suelo. Esto es una
hipotesis de formato que debe probar el editor, no un parser general publicado.

[DESIGN] Corregir solo esos floats de offset por la diferenciaY observada entre
WRPoriginal y WRPnuevo, en una copia respaldada y con el editor cerrado. Guardas:
hashes fijos, identidad/modelo/rotacion/XZ exactos, registros univocos, cotas
finitas, delta<=3.326m y ningun byte distinto fuera de esos4952campos. La siguiente
exportacion nativa debe confirmar todas las poses contra V10. No reducir el
gate ni parchear el WRP para presentarlo como exportacion nativa.

## V33: precision residual y derivado de empaquetado explicito

La exportacion5,21144e07, conserva exactamente los9puentes. Solo670piezas de
agua difieren enY de2.98e-8 a9.537e-7m. Terreno/materiales/identidades y las
otras11componentes exactos. El FAIL estricto sigue guardado. Compatible con
precision float, sin atribuir un mecanismo interno que no hemos aislado.

[DESIGN] Se conserva el requisito de poses finales exactas. Tras cerrar y
reabrir, exigir dos exportaciones literales identicas en contenido canonico.
Crear despues dos archivos derivados separados con restitucion de esos670Y
del referenteV10: solo objetos baltic_water, diferencia<=1micrometro, ningun
byte fuera de esos campos, identidad/modelo/rotacion/XZ exactos. No modificar
los literales ni llamarlos PASS de igualdad contraV10. El consumidor estricto
actual debera pasar en ambos derivados y estos coincidir exactamente entre
si. Guardas negativas rechazan cambio de puente, horizontal, rotacion, modelo,
ID, altura material, NaN, delta excesivo o export truncado. Guardar hashes,
restituciones y procedencia de cada input en el paquete. Este ajuste del flujo
mantiene la geometria final exacta sin un epsilon global ni encubrir el FAIL.
La representacion editable permanece a menos de1micrometro; la compilacion
usa exclusivamente el derivado declarado. No es una prueba de export nativo
exacto contraV10. La reapertura nativa y el consumidor de juego son separados.

[DESIGN] Agua dinamica local: probeV1 sin cambios,24coordenadas/clases/camara
congeladas. Actualizar solo expectedGround para ASCv33 y la identidad final.
Exigir 600epocas completas entre20..190s, extremos<=21 y>=189,gap<=1s,
COMPLETE entre198..205, sin datos posteriores. Tierra seca: no mar/no estanque
y margen>=0.10m frente a ambas superficies; controles mojados: bandera agua y
>=0.15m de profundidad real superficie-suelo. Precision suelo<=5mm. No afirma
maximo global del oleaje ni todo el mapa. Verificador: verify_outline_water_probe.py.
