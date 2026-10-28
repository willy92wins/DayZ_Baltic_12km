# Reparación procedural del lecho seco sobre carretera

Estado: CANDIDATO_OFFLINE_VERIFICADO. Codex ejecutor/integrador; Fable revisión.
Consumidor inmediato: candidato numérico reproducible y verificador independiente;
materialización MLOD/LOD físico posterior, sin afirmar integración ni aceptación visual.
Traza: ev112-visual-geometry-reassessment-20261028 §4, reporte humano kit118
lecho/carretera; petición vigente de reparar equivalentes conservando agua/extremos.

## 1. Hechos y mecanismo
[EXACT] pilot_visible_exposure_ev112.py censa todos los201modelos/185744caras.
Único solape expuesto con rectángulos del corredor: primer modelo kit118,
23.956666420529523m². No recapitular producción consumida. El corredor procede
del grafo independiente36467aristas, ancho±4m; no representa pavimento medido.
Discriminador R/road-bed-water-discovery-20261028/report.json: el mismo solape
23.95666642052773m² tiene0huella de agua del inventario A y0agua nativa nominal.
17818instancias examinadas,16817con agua,5candidatas,27caras próximas;0ambiguas
tocan el solape. Distancia4.825m sólo a las caras próximas recopiladas, no mínimo
global certificado. Ni ondas ni ocultación de cámara certificadas.

[EXACT] continuous_stream_pilot_v31.py:312-319 aplica piso H+.02 al lecho seco,
también sobre el corredor; :316 aplica techo H+.02 sobre plataformas protegidas,
NO igualdad de la malla a una plataforma. :403 conserva H protegido. El contrato
seco anterior congelaba además su máscara técnica propia y road_guard: impide
corregir esta superposición. No reutilizarlo como permiso o prohibición universal.

## 2. Cambio de diseño acotado
[DESIGN] Reparar exclusivamente alturas Y de la malla seca propia. Mantener H,
agua/footprint, todas las máscaras, objetos/puentes/carreteras y sus poses byteexact.
No borrar máscaras ni modificar sus fuentes. Los guards de carretera y plataforma
siguen conservando el soporte nativo: la malla espuria se entierra, no se excava H.
015-45/60m excluye cualquier modificación incluso en la malla propia.

Reunir filas compartidas de cada sitio desde los201source_grid sellados; no tratar
juntas como fronteras independientes. Semillas: caras con solape expuesto previo,
incluyendo aportes de discos y su banda incierta. Censar las201identidades, sin
hardcodear nombre kit118 para seleccionar cambios. Corredor objetivo conservador:
rectángulos±4m más discos exteriores64lados; no llamar disco exacto al polígono.

Dominio modificable: vértices a distancia geodésica de malla <12m de las semillas;
12m es el ancho de transición ya usado por el generador (:259), no tolerancia nueva.
Fijar franja |q|<=4,
primera/última fila del CAP completo (distancia8) y círculo015-45. El borde lateral
seco conserva XZ/conectividad y sólo puede descender; no congelar su altura antigua.
Congelar TODOS los vértices de cualquier
cara que toque huella de agua real (todas las capas del A, ambiguas incluidas),
o agua nativa H<=W (algún vértice del refinamiento; contacto incluido). Contacto
de agua A incluye área o borde, y banderas ambiguas. Examinar región local completa,
no sólo el solape original. Extremo conservado = toda lámina y apoyo mojado,
eje/XZ y cierre exterior; la fila seca s=0 no es una frontera fija adicional.
Agua de referencia trasladada a CAP no cuenta como huella real.

Descensos d>=0. Formar restricciones continuas en cada vértice del refinamiento
cara/nativo/corredor: sum(bary*d)>=B-H+0.03*sum(bary de vértices libres).
El margen0.03m procede del enterrado CAP existente (:349); se desvanece donde
todo queda fijo. Si una cara fija sobresale, INFEASIBLE sin mover el extremo/agua.
Acotar además cada descenso al suelo mínimo H del dominio local menos0.03m,
redondeado hacia abajo a1/512; un punto originalmente inferior no se mueve.
La capacidad ponderada de todos los vértices libres da un testigo directo si no
alcanza la restricción. Esto evita compensar un apoyo casi fijo con descensos
kilométricos; INFEASIBLE_DESCENT_ENVELOPE es relativo a esta envolvente, no global.
Una LP minimiza el máximo gradiente de d por arista para repartir la transición;
otra minimiza sum(d) con t<=nextafter(tóptimo,+inf), factibilidad del solver1e-9.
Si esa fase no converge, no declarar óptimo lexicográfico; no elevar su cota.
Esto NO prueba naturalidad. Preflight: conflictos totalmente fijos y vértices
con soporte fijo B>H se reportan INFEASIBLE antes de optimizar.
Redondear sólo descensos mayores de1e-9m hacia abajo a1/512m; los menores se dejan
en cero y el gate geométrico posterior sigue mandando. Retener puntos fijos exactos.
Rechazar si el chequeo posterior detecta B>H en corredor (residuo numérico<=1e-9m,
ya vigente), agua/extremo alterados, NaN, fuente cambiada o conflicto no cubierto.
No elevar, recortar XZ ni modificar conectividad. Candidato NPZ de filas completas,
incluidos CAP; el ensamblador posterior deberá trasladarlo a todos los LOD reales.

## 3. Puertas, controles y límites
VERDE de esta unidad = CANDIDATO_OFFLINE_VERIFICADO, no mapa final:
- Selección completa de201modelos desde censo previo sellado; semillas reales no vacías.
- Identidad de fuentes y unión exacta de filas; mismo número/topología/XZ/agua.
- Todos los puntos fuera del conjunto autorizado iguales; sólo descenso cuantizado.
- Todo triángulo modificado separado de agua real/nativa; fijados extremos y015.
- Caras semilla y modificadas dentro del corredor, incluidos CAP y discos:
  máximo B-H<=1e-9 tras cuantización. Censo previo conserva la cobertura restante.
- Consumidor GEOS independiente reconstruye cortes, bary y H desde fuente nativa,
  no importa refinador/solver productor; comprueba todas las caras modificadas y
  todos los conflictos previos. El descenso sólo no puede crear solapes nuevos.
- Controles analíticos: triángulo sobre plano retirado, valle nativo entre vértices,
  agua elevada/ambigua que bloquea, extremo fijo conflictivo INFEASIBLE, junta entre
  modelos. Mutantes: omitir conflicto, mover XZ, agua o punto fijo, residual elevado.
- Reportar gradientes de corrección, alturas y área/localización nueva B<H;
  no asignar umbral estético inventado.

Presupuesto antes de ronda1: una revisión de plan600s, una revisión de código600s;
un lote de correcciones por repro nombrado. Preflight120s; producción600s/2GiB/
1hilo; consumidor600s/2GiB. Cada LP límite120s. Si falla por presupuesto o datos,
INCONCLUSO; si restricciones incompatibles, INFEASIBLE con testigo, sin aflojarlas.
No repetir procesos consumidos; continuación nueva sólo con evidencia discriminante.
Fallo de esta vía no cierra las otras familias ni obliga a pedir autorización.

## 4. Integración posterior
Antes de desplegar: transferir alturas exactas a Visual/Roadway/Geometry usando
fuentes/poses selladas, conservar agua/materiales/UV/selecciones, validar esquinas
y geometría real compilada; prueba DayZ por FIFO cuando esté preparada/revisada.
Esto queda fuera del PASS numérico. RAM, nueve regresiones y council siguen abiertos.

## 5. Adjudicación de revisión
Fable nativo413.75s, identidad claude-fable-5-1, sin denegaciones ni cambios de
entradas. SOUND-with-fixes, una ronda consumida; reporte en evidencia de esta fase.
Aceptados: distinguir extremo mojado/fila seca, collar|q|<=4, preflight fijo,
contactos de borde de agua, entierro nuevo y objetivo numérico explícito.
Contraejemplo ejecutado R/check_road_endpoint_chords_20261028.py:12segmentos
de fila corporal fija dentro del corredor, máximo B-H0.03706236090875947m.
Dejar toda esa fila fija haría inviable el plan. Se conserva como regresión.
No es necesario subdividir para este testigo si pueden descender los vértices
secos de esa fila; se retira la inferencia preliminar de que fuera imprescindible.
Precisión: primera fila CAP del plan significaba distancia8, no distancia1.
Se rechaza inferencia del punto2 de la revisión:112.7859m² totales menos23.9567
expuestos NO significa89m² con B>H bajo agua. El censo expuesto no filtra por W;
esa diferencia contiene superficie B<=H. Acotar chequeo a semillas/modificadas
es cobertura verificable por monotonía y censo previo, no excepción por esa hipótesis.

Preflight consumido8.25s:104semillas,1102caras locales,306vértices libres,
143caras mojadas congeladas;2muestras duplicadas con soporte fijo en cara608.
Testigo: arista exterior312–351, bary(0.3930197268583471,0.606980273141653,0),
B-H0.044270951063846375m. Ambos vértices son secos y dominio permitido; únicamente
la regla técnica de columna externa los congelaba. Se retira esa igualdad Y,
conservando XZ y todas las protecciones humanas/agua/terreno. No es una relajación
del umbral: el mismo B-H<=1e-9 sigue siendo obligatorio. La fuente (:308) buscaba
enterrar el borde, no preservar una cresta por interpolación sobre H no plano.
Se revisa este ajuste junto al código antes de producción; si aparece otro apoyo
fijo incompatible no se cambia más la máscara en este bucle. Se guarda INFEASIBLE.

Revisión de código Fable407.297s SOUND-with-fixes consumida; fuentes intactas.
Aceptado soporte casi fijo y cuantización de d=0. Se rechaza la receta de eliminar
bary<1e-9: descartaría soporte real y ni siquiera arregla su repro con peso1e-8.
Se adopta la envolvente derivada de H descrita arriba, capacidad máxima por muestra
y estado INCONCLUSIVE_SOLVER para fallo de HiGHS sin certificado propio. No se
modifica un peso positivo. Repros1e-8/1e-10 y d=0 fuera de rejilla añadidos.
Se fijó1hilo de HiGHS con threads=1, verificado en HighsOptions y wrapper local;
SciPy avisa que pasa esa opción nativa sin reconocerla en su capa Python.
Índices negativos y nodos de carretera aislados ahora fallan explícitamente.
Consumidor GEOS implementado aparte, sin importar productor/refinador/solver.

Producción consumida8.047s; consumidor13.718s. Ambos LP óptimos;82vértices,
203caras, descenso máximo0.142578125m; cero área expuesta en corredor.
14tests+5controles+6mutantes. No modelo desplegado ni aceptación visual.
