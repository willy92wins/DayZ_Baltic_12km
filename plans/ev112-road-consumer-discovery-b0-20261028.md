# Carreteras B0 — consumidor, pivotes y huella completa antes del piloto

Estado: REVISADO_PARA_IMPLEMENTAR. Preparación offline, sin colocación,
compilación, despliegue o DayZ. Continúa A; no repite catálogo501/265.

P5/P6/P9/P10/P11: reservar vías lisas y pasos navegables ahora, respetando P10
antes de mapeado global. La petición de preparar carreteras no modifica el agua,
extremos, islas ni la protección015-45. No asumir aceptación de conducción.

## Referentes recuperados

[EXACT] evidence/road-preparation-receipts-20261028/recovery.json liga decisionP9
d510af67cc4016a0ba7192aa01c070d314b9bc7e49b6256ca6ffaf64fc05b843 al blob
histórico público; fondo1m/calado0.95m/corredor24m, excepciones bajos/Narva y
sin envolvente máxima de oleaje. No es ancho de carretera.
Bed-report23.95666642052773m²: cobertura histórica de8m, no de12/9m. No repetir
el discriminador ni convertir ese dato en superficie reparada por B3E2.
Catálogo instalado34c1cabe: asf1/asf2 con extensión12/9m; ancho útil UNDETERMINED.

## Descubrimiento antes de diseñar poses

[DESIGN] Una unidad de lectura con fuentes instaladas/compiladas fijadas:
1. Localizar y leer configuración de roads y consumidor real del terreno:
   objetos WRP, red vial y/o importador TerrainBuilder. No decidir objetos sueltos
   por el TXT FTT histórico. Registrar definiciones verificadas path:line/hash y
   ejemplos vanilla comparables; si sólo hay evidencia nominal, INCONCLUSIVE.
2. Sobre asf1_25/asf2_25 y variantes candidatas documentadas, extraer de ODOL
   guardado Visual y Roadway: caras completas, materiales/texturas, selecciones,
   límites de superficie de apoyo y puntos de empalme. Espacio local/centro de
   bounding box/pivote real distintos. Comparar transformaciones con poses WRP
   conocidas y soporte nativo leído; no declarar convención por bbox solamente.
3. Separar pavimento visible, arcén y superficie útil inferida del material.
   Material no prueba adherencia ni ancho transitable. Si falta regla de ancho,
   presentar dos alternativas concretas con huella y conflictos; no asignarla
   al azar ni pedir aprobación sin evidencia.
4. Preparar cuatro corredores de revisión: seco49(5296,6000), cruce49/301 cerca
   de(4789.51465,5516.52197), Narva71 y kit118/cadena76. Coordenadas del personaje
   sólo seleccionan contexto; posición real de cruce viene de intersecciones
   exactas. La tabla de puentes no participa como oráculo de cruces ausentes.

Entregable: inventario de fuentes consumidoras, incertidumbres, máscaras de
Visual/Roadway en espacio local y propuestas de corredor con cobertura completa
de ancho y accesos; todo borrador sin poses autorizadas. Ríos/mar/lagunas por
superficies geométricas independientes; conservar extremos/nodos/contactos de
área pequeña y casos positivos diseñados. No buffer8m como prueba de huella12m.
Si agua/material/pivote no tienen referente suficiente, marcar ámbito desconocido
y seguir con fuentes independientes; ningún PASS global por ausencia de datos.

## Validación y límites

Planreview180s, codereview180s/suite120s si se necesita extractor nuevo; una
extracción offline120s/2GiB. Geometría/arrays vanilla sólo locales, no Git público.
Fixtures independientes: tira con arcén de material distinto, curva con bbox
mayor que ancho útil, pivot desplazado, Roadway ausente, intersección marginal,
cruce en nodo y hueco de puente. Campos faltantes conservados, no defaultsPASS.
Cierre permitido DISCOVERY_COMPLETE_NOT_PLACEMENT o INCONCLUSIVE_DISCOVERY.

Después: plan B de piloto seco con tolerancias justificadas por consumidor;
mantener cross0.03m/grade0.065/chord0.03m existentes. Las exclusiones antiguas
48m agua/470m Narva/18m extremos quedan NO EVALUADAS y necesitan puertas propias.
C: prueba de tablero/apoyos/accesos/agua y tránsito real en plan nativo separado,
después de hipótesis y revisión. Ni puente por cercanía ni pavimentado global.

## Adjudicación de Fable5.1 — 77.828s

SOUND-with-fixes, entradas intactas, en evidence/road-b0-plan-review-20261028.
Codex verifica y adjudica antes de implementación:

- Se conserva UNA extracción120s/2GiB; no se acepta multiplicar presupuestos
  por WRP/ODOL/corredores. La primera extracción se acota a asf1_25, asf2_25
  y una curva identificada en el catálogo A, configuración instalada y metadatos
  disponibles. No decodificar un WRP entero como efecto lateral. Si no cabe o
  falta referente, guardar alcance parcial y campos UNKNOWN. Las ampliaciones
  requieren hipótesis y plan propios; no reiniciar el catálogo A.
- Fuente de piezas: PBO instalado structures_roads.pbo34c1cabe y sus entradas
  fijadas por A. P:/DZ/structures/roads/config.cpp es sólo fuente nominal;
  FTT TXT y verify_ftt_pilot.py NO prueban consumidor del motor. Config binaria
  instalada exige lectura/decodificación con identidad trazada antes de afirmar
  sus clases. Vanilla worlds_chernarusplus.pbo instalado existe; su identidad y
  entradas deben descubrirse antes de usarlo, sin asumir equivalencia con P:.
- consumer_observed = WRP_OBJECT / WRP_ROADNET / AMBOS / UNKNOWN. Debe citar
  path:offset o path:line, hash y alcance de observación. Clases en config
  solamente no prueban instancia WRP ni consumidor efectivo del mapa.
- Registrar bounding_center, centro de cada LOD, offset realmente aplicado por
  lector/consumidor, resolución Roadway, selecciones, caras y materiales.
  No inventar offset si el lector sólo expone vértices. pivot_convention UNKNOWN
  hasta referente independiente; tres instancias coherentes, propuestas por el
  revisor, tampoco demostrarían por sí solas convención o altura del motor.
- Fuente vial candidata: tests/regional_foundation_roads_v6/reference.npz en
  checkout principal, ligada por ROAD_SHA de pilot_visible_exposure_ev112.py.
  Fuente de superficies candidatas: surface-prototypes.npz/instances.npz y
  manifiesto de evidence/deployed-surface-prototypes-20261028; es inventario
  geométrico, NO referente independiente de intención/clases/anchuras de agua.
  No derivar cruces del listado de puentes. Intersección debe ser línea contra
  superficie/área completa, conservar contactos puntuales y casos marginales.
  Se rechaza prescribir segmento-segmento/tolerancia0 sin definir representación;
  el método y error numérico se fijan contra fuentes antes de implementar cruces.
- Campos obligatorios: consumer_observed, pivot_convention, usable_width,
  shoulder_material, roadway_present, crossings_exact, sources, coverage,
  elapsed_s y peak_bytes. Desconocido explícito; Roadway ausente=false y ancho
  UNKNOWN, nunca0. Cualquier UNKNOWN necesario impide DISCOVERY_COMPLETE.
  Las alternativas de anchura futuras mostrarán huellas/conflictos medidos.
- cross0.03/grade0.065/chord0.03 son restricciones preservadas para piloto B,
  no prueban B0. RAM, nueve regresiones y C1 SIN REVISAR siguen abiertos.
