# Carreteras B0 — consumidor, pivotes y huella completa antes del piloto

Estado: BORRADOR_PENDIENTE_DE_REVISION. Preparación offline, sin colocación,
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
