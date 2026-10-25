# Relieve selectivo para jugabilidad

## Decisión y alcance

Guillermo autoriza el 30-09-2026 exagerar alturas en zonas concretas, incluso por
encima de ×3 y sin fidelidad a la escala vertical, en favor de la jugabilidad.
Esto sustituye la elección binaria ×1/×3. La geometría XY aprobada, P2/P3/P9/P11,
las islas y conexiones siguen vigentes. Se incorpora como P12.

**Aprobado:** el criterio de relieve selectivo. **[DESIGN]:** las cotas y áreas
de esta propuesta son un punto de partida técnico, no alturas finales aprobadas
ni terreno importado. Guillermo acepta después esta propuesta como punto de
partida («Me gusta la propuesta») y exige conservar la reserva con sectores de
alta densidad de árboles para ofrecer varios biomas (P13). No se ha cambiado
el WRP, el PBO o la navmesh.

## Propuesta inicial por zonas

Las cotas son metros sobre el datum del mar del mapa, no metros que se sumen
al terreno. Los rangos describen categorías, no pisos uniformes ni recortes
bruscos de altura. Se priorizan elevaciones que ya aparecen en el DSM.

| Zona | Cotas de diseño iniciales | Función |
|---|---|---|
| Costa, delta de San Petersburgo e islas | Llanuras bajas; diseñar respecto al agua máxima, sin levantar una cordillera | Conservar siluetas, canales, horizonte costero y accesos |
| Valles fluviales y entorno de lagos | Cotas subordinadas a cada sistema de agua, aún por diseñar | Mantener navegación, orillas y conexiones; no multiplicar superficies de agua |
| Interior ondulado | Lomos de 30–70 m | Cobertura, aproximaciones alternativas y separación visual entre áreas |
| A: elevaciones interiores al oeste de Gatchina | Crestas seleccionadas de 80–140 m | Dar presencia al relieve existente y crear pasos, evitando una meseta plana |
| B: elevaciones del sur, entre Peipus y Luga | Crestas seleccionadas de 100–160 m | Sector más accidentado y boscoso; valles accesibles entre elevaciones |
| Hitos puntuales dentro de A/B | Hasta 180–200 m si los perfiles lo admiten | Orientación y miradores; evitar que un único punto domine todo el mapa |
| Mshinskoye y humedales | Relieve bajo conservado dentro del entorno húmedo | Mantener el carácter de la zona natural; no rellenar humedales para alcanzar una cuota de altura |

El plano de `evidence/navigation/selective-relief-v1/zonificacion.png` dibuja
envolventes de estudio sobre la fuente ×3. Las elipses no son límites finales
de edición. El entorno de Mshinskoye es una referencia aproximada tomada del
encuadre original, no el límite legal de la reserva. El closeup se conserva
íntegro; las elevaciones propuestas deben desvanecerse antes del delta y costa.

## Reserva natural y variedad de biomas — P13

La reserva es una pieza central del mapa. La envolvente verde del plano es una
**reserva de diseño conservadora**, no una delimitación geográfica verificada.
Antes de generar el candidato, contrastar su perímetro con los datos de agua,
cobertura y la referencia original. La máscara resultante tiene prioridad
sobre cualquier elevación A/B: ningún incremento Z puede rellenar sus zonas
húmedas ni desplazar sus lagos y cauces para alcanzar una cota propuesta.

Dentro de este sector se diseña un mosaico, evitando una densidad uniforme:

- Núcleos de bosque muy denso con visibilidad corta y sensación de aislamiento.
- Bosque de transición y claros que permitan orientarse y recorrer el sector.
- Humedales y orillas conservados, con vegetación adecuada y pasos legibles.

Fuera de la reserva: litoral/delta más abiertos, interior rural con alternancia
de bosque y claros, y colinas meridionales con bosque y laderas diferenciadas.
Son categorías de diseño; las especies y variantes vanilla se seleccionan
después de verificar su inventario. La clase forestal WorldCover indica cobertura,
no densidad real de troncos ni especies, y no determina por sí sola la colocación.

Ahora se fijan terreno, máscaras y corredores; los árboles se colocan después
según P10. Ensayo posterior en una parcela densa representativa: comparar cámara,
clima y distancias iguales, medir tiempos de frame cliente y memoria, recorridos
de IA y colisiones. No deducir coste de vegetación del ensayo previo con100
infectados ni prometer capacidad80–100 jugadores. El presupuesto de instancias
se fija con esa medición; se ajustan distancias/mezcla de assets y transición
antes de vaciar el núcleo denso que da identidad a la reserva.

## Ingeniería necesaria antes de importar

1. Congelar la base nativa 0.2 y separar máscaras de costa, agua, reserva natural, humedales,
   islas, cruces y rasantes. Fuente DSM inmutable; Z de diseño en capa derivada.
2. Diseñar niveles y enlaces de los sistemas Narva, Neva y Luga. La autorización
   vertical no autoriza rebajar todos los lagos al mar. No atribuir batimetría
   al DSM ni aceptar navegación por el color azul del satélite.
3. Construir colinas amplias con transiciones continuas, apoyadas en el relieve
   existente. Suavizar el ruido del DSM sin borrar barrancos/cauces de referencia;
   separar el relieve regional del detalle local. Medir elevaciones relativas
   a los valles, no solo la cota máxima.
4. Conservar las conexiones principales y reservar rasantes suaves. [DESIGN]
   Objetivo inicial de pendiente longitudinal: hasta 6% en vías principales y
   hasta 8% en secundarias, sujeto a perfiles y prueba con vehículo. Son objetivos
   del proyecto, no límites verificados del motor. Curvas verticales y juntas
   necesitan métricas propias conforme a P11.
5. Comprobar viabilidad: subir 120 m al 6% exige al menos 2 km de desarrollo
   horizontal, antes de añadir transiciones. Las carreteras deben aprovechar
   valles y pasos; no copiar sobre ellas las pendientes de todas las crestas.
   No mover ciudades ni romper conexiones para hacer encajar una altura objetivo.
6. Preparar un candidato aislado con mapa de deltas y perfiles. Preservar el
   paso hidráulico y el gálibo de Narva; no multiplicar tablero, pilas ni assets.
   Si es necesario tocar sus accesos, repetir sus gates en el nuevo candidato.
7. Importar, guardar, reabrir y exportar; verificar todas las alturas y objetos.
   Regenerar navmesh sobre ese WRP antes de repetir pruebas. Las pruebas de 0.2
   son del baseline y no se transfieren automáticamente al nuevo relieve.

## Revisión previa y aceptación

Plan trazado a P2/P3/P5/P9/P10/P11/P12/P13. No modifica escala XY ni añade mapeado.
Cambiar solo las alturas no demuestra ni conducción, ni hidrografía funcional,
ni mejora de rendimiento. No iniciar una serie de multiplicadores globales.

- **PASS offline de geometría:** deltas finitos, registro exacto de áreas tocadas,
  mismas dimensiones y orientación, identidad fuera de las máscaras autorizadas;
  costa/islas/agua protegidas y perfiles de transición sin escalones artificiales.
- **PASS de diseño jugable:** al menos un recorrido documentado por cada zona
  elevada, accesos alternativos y vistas desde jugador a 1,7 m sobre el terreno;
  comprobar exposición de riberas y que los pasos no sean embudos involuntarios.
- **PASS de reserva/biomas:** perímetro de conservación contrastado y máscaras
  trazables; agua/humedales conservados y núcleos densos reservados. En fase de
  mapeado: contraste visual entre biomas desde jugador, recorrido entre claros,
  colisiones/navmesh y coste medido en el sector de máxima densidad.
- **PASS de ingeniería:** profundidad y anchura continua de cauces, gálibos y
  rasantes medidos en los límites de agua; posteriormente barco y vehículo reales.
- **PASS en motor:** fuente exacta del WRP/PBO, carga cliente/servidor, orillas y
  render cercano/medio/lejano, navmesh regenerada y consumidores representativos.
- **INCONCLUSO:** sin cotas regionales del agua, sin candidato importado o sin
  consumidor probado. Una propuesta visual no cierra ninguna de esas puertas.
- **FAIL:** nueva barrera de agua, inundación, isla perdida, carretera discontinua,
  escalón, modificación de XY o resultado que solo pasa relajando un gate previo.

Presupuesto de esta fase de diseño: un plano y una propuesta. La siguiente
iteración es un candidato regional unido a la hidrografía; ante un conflicto,
aislar su causa y resolver ese sector, sin probar factores Z a ciegas.

## Evidencia y fuente

- `tools/prepare_prototype.py:90–105`: variantes existentes y escala Z del DSM.
- `tools/geo_common.py:34–43`: transformación XY única ya usada por el proyecto.
- `evidence/navigation/relief-decision/comparison.json`: máximos 10,8619/32,5857 m.
- `evidence/navigation/regional-hydrology-constraints.json`: estrechamientos y
  conflictos insulares previos; no son navegación regional aceptada.
- `evidence/navigation/selective-relief-v1/design.json`: encargo, áreas, cotas
  propuestas y hashes de las referencias utilizadas para el plano.
