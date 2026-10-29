CRITICA_DEL_ENCUADRE

El sistema actual exhibe una asimetría estructural: audita con precisión submilimétrica la identidad de entradas, poses y biyecciones internas (`pose_tolerance_m=.001` en `tools/quality/screen_shapes_ev112.py:78`; residuo baricéntrico `1,93e-12 m` en `evidence/native-shore-census-20261028/README.md:11`), pero evalúa capas aisladas o proyecciones 1D omitiendo la interacción tridimensional que ven el jugador y el motor físico. En concreto: `placed_water` descarta todos los objetos del WRP salvo dos prefijos de agua (`tools/quality/screen_shapes_ev112.py:64`); `pilot_axis` colapsa láminas 3D a un eje medio (`tools/quality/screen_shapes_ev112.py:100`); `road_water_contacts_ev112.py:78-108` intersecta solo el eje nominal con agua nativa omitiendo anchuras de calzada, agua 3D y `Roadway` de puentes; y `verify_roads_v30.py:4-5,78-79` excluía 48 m del agua y 470 m de Narva (`evidence/native-shore-census-20261028/README.md:51`).

Tampoco debe equipararse todo rechazo humano a ceguera del detector: el censo nativo ya señala candidatos en 793 de 1.030 cadenas (`evidence/native-shore-census-20261028/README.md:21-23`) y la parada oriental registraba un `native_spike` previo (`evidence/visual-tour-20261027/README.md:66-68`), pero faltaba adjudicar, desbloquear submáscaras no estructurales (`shore_ramp_v31.base_protection` congela el contorno 292 en Narva, `evidence/native-shore-census-20261028/README.md:33-38`) y reparar por clase generativa. Inversamente, ni toda recta o arco es artificial (canales de San Petersburgo en `product-spec.md:9` o estribos de presa frente a meandros naturales), ni añadir ruido o redondear codos corrige ejes escalonados (`evidence/visual-tour-20261027/README.md:24,50`). Finalmente, buscar cadenas por distancia euclídea al avatar (`tools/quality/native_shore_census_ev112.py:134-151`) confunde observador con defecto.

---

## Propuestas priorizadas de mejora

**COB-01** | **Dominio:** Generación, deltas y atribución visual | **Tipo:** `TECNICA` | **Coste relativo:** Bajo | **Riesgo:** Bajo
- **Problema observable:** Las observaciones humanas quedan como `UNCONFIRMED_CONTEXT_ONLY` porque la posición del personaje no localiza el defecto (`ROAD49-RIVER-VIS-01`, `RELIEF-EAST-VIS-01`, `CROSSING-VIS-01`) y no separa «no detectado» de «detectado sin reparar» o «bloqueado por máscara».
- **Evidencia:** `evidence/visual-tour-20261027/README.md:17,52,56-58,68-70`; `tools/quality/native_shore_census_ev112.py:134-151`.
- **Cambio (generador/validador/colocación):** Sustituir la búsqueda radial en `contexts` por un validador de frustum desde pose/orientación archivadas de cámara (excluyendo el volumen del avatar) contra terreno, agua nativa y todos los modelos `0WZD`, cruzando impactos con censos y máscaras para etiquetar `NO_DETECTADO`, `HALLAZGO_SIN_REPARAR` o `BLOQUEADO_MASCARA`.
- **Consumidor independiente:** Proyector de siluetas en plano de imagen contrastado contra las capturas/metadatos locales de visita sin reutilizar `contexts`.
- **Positivo y mutante/negativo:** *Positivo:* cámara en Narva y parada oriental recupera contornos 292 y 769 con su estado exacto de máscara. *Mutante/negativo:* colisionador del avatar delante de cámara o río fuera del cono visual es descartado.
- **Dependencias:** Metadatos de `evidence/visual-tour-20261027` y WRP `Kit7Nav8Load1`.

**COB-02** | **Dominio:** Lecho/orilla/agua y contornos compuestos 3D | **Tipo:** `TECNICA` | **Coste relativo:** Medio | **Riesgo:** Medio
- **Problema observable:** Los lechos 3D sobresalen respecto al terreno y al agua (`KIT118-VIS-01`, `CONT65-VIS-01`), mientras `bed_effect` mide diferencia vertical incluso bajo terreno enterrado y el censo nativo ignora ocultación por modelos y crestas someras.
- **Evidencia:** `evidence/visual-tour-20261027/README.md:21,33,42`; `evidence/native-shore-census-20261028/README.md:27,57-62`; `tools/quality/native_shore_census_ev112.py:98-118`.
- **Cambio (generador/validador/colocación):** Evaluar la envolvente visible compuesta (máximo de terreno y modelos sólidos frente a agua nativa y láminas 3D) para extraer siluetas reales de ambas orillas, crestas someras en cortes de nivel cercanos al agua y prominencia/pendiente lateral donde el lecho emerge. En generación de lechos, abatir faldones secos exteriores por debajo del terreno circundante con transición tangente sin tocar la lámina húmeda.
- **Consumidor independiente:** Muestreador de secciones transversales ortogonales sobre WRP + mallas MLOD/ODOL compiladas, independiente del optimizador NPZ.
- **Positivo y mutante/negativo:** *Positivo:* cauce con bordes exteriores enterrados suavemente bajo terreno seco pasa. *Mutante/negativo:* `KIT118-VIS-01`, `CONT65-VIS-01` y un mutante con Visual=Geometry idénticos pero hombro saliente sobre terreno/agua fallan por exposición lateral.
- **Dependencias:** Lectura completa de objetos `0WZD` y COB-06.

**COB-03** | **Dominio:** Contornos completos ríos/mar/charcas | **Tipo:** `TECNICA` | **Coste relativo:** Medio | **Riesgo:** Medio
- **Problema observable:** `route_screen` simplifica polilíneas y solo detecta rectas largas, quiebros discretos, escaleras ortogonales y rectángulos cerrados; omite L/U abiertas (`NARVA-VIS-01`), empalmes recta-arco de radio constante (`NARVA-VIS-03`), zigzags oblicuos (`ROAD49-RIVER-VIS-01`), lenguas estrechas (`RELIEF-EAST-VIS-01`) y el giro de cierre (`closure_turn_evaluated=False`).
- **Evidencia:** `evidence/visual-tour-20261027/README.md:5,7,13-15,22,50,70`; `tools/quality/shape_patterns_ev112.py:38-72`; `tools/quality/native_shore_census_ev112.py:78-80`.
- **Cambio (generador/validador/colocación):** Incorporar un validador invariante a teselación parametrizado por longitud de arco (con índice modular en lazos cerrados) que mida espectro multiescala de curvatura firmada, mesetas de curvatura constante (círculos/arcos artificiales y saltos recta-arco), alternancia periódica de signo (zigzags no ortogonales), esquinas abiertas L/U y estrangulamientos por eje medial, separando estructuras antrópicas catalogadas (`DESIGNED_STRUCTURE` en canales P3 o presas) de riberas naturales.
- **Consumidor independiente:** Ajustador de primitivas recta/arco/clotoide por longitud mínima de descripción sobre contornos compuestos COB-02.
- **Positivo y mutante/negativo:** *Positivo:* meandro de curvatura continuamente variable y canal histórico catalogado en San Petersburgo se discriminan sin falso rechazo. *Mutante/negativo:* escalera con codos redondeados mediante arcos uniformes o ruido sub-celda falla por periodicidad macroaxial y mesetas de curvatura.
- **Dependencias:** Censo nativo existente y COB-02.

**COB-04** | **Dominio:** Lecho/orilla/agua y máscaras | **Tipo:** `DECISION_USUARIO` | **Coste relativo:** Bajo | **Riesgo:** Medio
- **Problema observable:** `shore_ramp_v31.base_protection` protege en bloque toda la máscara Narva, impidiendo corregir la L emergente delante de la presa (`NARVA-VIS-01`, contorno 292) y bordes regulares adyacentes (`NARVA-VIS-03`).
- **Evidencia:** `evidence/native-shore-census-20261028/README.md:33-38,83-84`; `evidence/visual-tour-20261027/README.md:5,7`.
- **Cambio (generador/validador/colocación):** Solicitar decisión acotada para escindir la máscara Narva en: (a) submáscara estructural estricta de cimientos/estribos de presa y puentes derivada de su huella 3D real (inmutable), y (b) subzona húmeda/somera residual editable bajo invariantes hidráulicos. *Alternativas concretas:* (1) sumergir el espolón residual en L bajo la lámina local conservando el pie de presa; (2) reperfilarlo como barra/orilla irregular emergente.
- **Consumidor independiente:** Verificador de empotramiento 3D de todas las piezas de la presa (cero pérdida de soporte) + re-evaluación COB-03.
- **Positivo y mutante/negativo:** *Positivo:* desaparecen los giros de 90°–105,59° del contorno 292 manteniendo intacto el contacto presa-terreno. *Mutante/negativo:* cualquier rebaje que alcance un triángulo portante de la presa es rechazado.
- **Dependencias:** Huellas 3D de Narva en WRP y COB-06.

**COB-05** | **Dominio:** Generación de contornos y deltas hidrográficos | **Tipo:** `TECNICA` | **Coste relativo:** Alto | **Riesgo:** Medio-Alto
- **Problema observable:** Modificar solo Y de un kit MLOD no puede corregir siluetas angulosas en charcas/costas (`RELIEF-EAST-VIS-01`, contorno 769) ni trazados en zigzag (`ROAD49-RIVER-VIS-01`).
- **Evidencia:** `plans/ev112-visual-geometry-reassessment-20261028.md:8-13,87-92`; `evidence/native-shore-census-20261028/README.md:40-44`.
- **Cambio (generador/validador/colocación):** Reemplazar el suavizado local por optimización variacional de flujo de variación de curvatura sobre el campo `H-W` en dominios libres de máscara (contorno 769), sujeto a barreras duras de topología (sin fusionar el islote 772), extremos, receptores y gálibo P9 (24 m / fondo 1 m / calado 0,95 m). Si eliminar zigzags en ríos modulares (`ROAD49-RIVER-VIS-01`) exige reajustar XZ de piezas intermedias, emitir propuesta `DECISION_USUARIO` con delta aislado manteniendo fijos extremos, receptores y cruces.
- **Consumidor independiente:** Verificador de invariantes topológicos (componentes secas/mojadas), conservación de receptores/extremos y sección navegable P9.
- **Positivo y mutante/negativo:** *Positivo:* contorno 769 elimina codos agudos preservando separado el islote 772. *Mutante/negativo:* deformación que cierre el canal del islote, mueva un extremo o reduzca el corredor navegable bajo 24 m es rechazada.
- **Dependencias:** COB-03 y, para tramos modulares XZ, autorización expresa.

**COB-06** | **Dominio:** Generación, WRP y colocación de modelos | **Tipo:** `TECNICA` | **Coste relativo:** Bajo | **Riesgo:** Bajo
- **Problema observable:** En `RoadB2` permanecen sin adjudicar en motor las alternativas `RAW` frente a `ORIGIN` (`bounding_center` antes de rotar) y orden fila/columna, bloqueando validación exacta de puentes (`NARVA-VIS-02`) y huellas 3D.
- **Evidencia:** `evidence/road-b2-recipe-20261029/README.md:3-8,17-18`; `evidence/b3g2-native-pair-20261029/README.md:9-15`.
- **Cambio (generador/validador/colocación):** Adjudicar en una sola corrida nativa sobre las 3 instancias oblicuas cuya separación offline alcanza `10,77 m`, contrastando consultas físicas del arnés `B3G2` contra las 4 predicciones pre-registradas y congelando la transformación ganadora para todos los colocadores/validadores WRP.
- **Consumidor independiente:** Lector nativo `B3G2` por `FileID` NTFS comparando impactos observados frente a las 24 huellas congeladas por hash.
- **Positivo y mutante/negativo:** *Positivo:* una única hipótesis reproduce las superficies dentro de tolerancia de cuantización float32. *Mutante/negativo:* trasposición fila/columna u omisión de `bounding_center` diverge por metros y queda bloqueada en código.
- **Dependencias:** Receta `RoadB2` y lector `B3G2` aprobados.

**COB-07** | **Dominio:** Carreteras/puentes/accesos | **Tipo:** `TECNICA` | **Coste relativo:** Medio | **Riesgo:** Medio
- **Problema observable:** Existen carreteras partidas por ríos (`CROSSING-VIS-01` cerca de cadena 49 arista 301), puentes desalineados (`NARVA-VIS-02`), extremos de río solapando carretera (`KIT118-VIS-02`, fuera del censo de agua nativa) y el terraplén `c1` sin revisar.
- **Evidencia:** `evidence/road-water-census-20261028/README.md:6-7,16-19,34-37`; `evidence/visual-tour-20261027/README.md:6,34,58-62,74`.
- **Cambio (generador/validador/colocación):** Reconciliar el polígono 2D completo del corredor viario (ancho humano P5 + taludes, sin exclusiones de `verify_roads_v30.py`) contra agua nativa, láminas/lechos 3D y mallas `Roadway` de puentes/terraplenes (`c0`, `c1`). Clasificar cada contacto en paso continuo, puente desalineado (eje, tangente o rasante), cruce partido o intrusión lateral de cauce. En colocación, ajustar pose/accesos de puentes a la tangente de ambos estribos y retranquear caps secos fuera del corredor; si falta un puente nuevo no decidido (`product-spec.md:23`), elevar opciones de puente vanilla o desvío.
- **Consumidor independiente:** Trazador de doble rodada paralela sobre las 124 cadenas exigiendo soporte seco o `Roadway` continuo sin escalones superiores a `chord 0.03`.
- **Positivo y mutante/negativo:** *Positivo:* puente centrado con empalmes continuos en ambas riberas pasa. *Mutante/negativo:* `CROSSING-VIS-01`, `NARVA-VIS-02` y un cap de `kit118` que invade el carril sin tocar el eje central fallan con diagnóstico diferenciado.
- **Dependencias:** COB-02, COB-06 y censo `road-water-census-20261028`.

**COB-08** | **Dominio:** Lecho/orilla/agua y bajos P14 | **Tipo:** `TECNICA` | **Coste relativo:** Bajo | **Riesgo:** Medio
- **Problema observable:** El censo descubrió 5 discontinuidades bajo la misma clave de arista (hasta `1,0646 m`), 65 saltos `WATER_STEP_AT_CELL_CUT`, 4 caras `H==W` y riesgo de agua intermitente en bajos (P14).
- **Evidencia:** `evidence/native-shore-census-20261028/README.md:16-20`; `evidence/road-water-census-20261028/README.md:11`; `product-spec.md:20`.
- **Cambio (generador/validador/colocación):** Imponer en generación de `footprint.npz` continuidad de cota de agua en toda arista interior compartida por caras mojadas o separación mediante cresta seca explícita entre láminas de distinto nivel, auditando además submuestreo interior a triángulos frente a envolvente dinámica de agua para eliminar rezumes no intencionados en depresiones secas sin drenar humedales P13.
- **Consumidor independiente:** Verificador sobre los 8.380.418 triángulos que exige salto nulo de agua en aristas mojadas conectadas y francobordo positivo fuera de máscaras hídricas.
- **Positivo y mutante/negativo:** *Positivo:* salto hidráulico de presa separado por dique seco cerrado y llanura baja seca entre vértices pasan. *Mutante/negativo:* arista mojada con salto de `1,06 m` o triángulo seco cuyo interior cae bajo agua dinámica es rechazado.
- **Dependencias:** `footprint.npz` y perímetro de humedales/reserva P13.

**COB-09** | **Dominio:** Relieve multiescala | **Tipo:** `TECNICA` | **Coste relativo:** Medio | **Riesgo:** Bajo
- **Problema observable:** El detector piramidal (`pyramid_radius_cells=[2,4,8]` sin tope de pendiente base) solo detecta picos locales; omite facetas y transiciones ásperas de ladera a meso-escala como la zona oriental (`RELIEF-EAST-VIS-01`) o encuentros con relieve exagerado P12.
- **Evidencia:** `evidence/visual-tour-20261027/README.md:66-70`; `tools/quality/shape_patterns_ev112.py:21-25`; `product-spec.md:18`.
- **Cambio (generador/validador/colocación):** Añadir evaluación multiescala de curvatura media/gaussiana en múltiplos crecientes de la celda de 6 m más allá de 8 celdas, combinada con difusión anisótropa en tierra seca que suavice quiebros de pie de ladera y aristas facetadas preservando líneas de cresta y cotas de `plans/selective-relief.md`, corredores P11 y orillas.
- **Consumidor independiente:** Analizador espectral de gradientes de terreno, pendientes de acceso peatonal y conservación de cuencas visuales desde cotas P12.
- **Positivo y mutante/negativo:** *Positivo:* colina P12 con falda cóncava progresiva mantiene cota máxima y líneas de visión sin facetas. *Mutante/negativo:* cambio brusco de plano de ladera a escala media o suavizado isótropo que hunde la cima diseñada es rechazado.
- **Dependencias:** Máscaras de `plans/selective-relief.md` y agua congelada.

**COB-10** | **Dominio:** Colisión/navmesh/física nativa | **Tipo:** `INVESTIGAR` | **Coste relativo:** Medio | **Riesgo:** Medio
- **Problema observable:** En `B3G2`, pese a corregirse `RV 700/723`, persisten fallos horizontales `RH349/350/1425` y `agua723`, Bullet sigue sin capa calibrada y la causalidad permanece `UNPROVEN`.
- **Evidencia:** `evidence/b3g2-native-pair-20261029/README.md:4-7,35-36`.
- **Cambio (generador/validador/colocación):** Investigar y calibrar las máscaras de colisión Bullet en un banco mínimo de piezas vanilla conocidas (terreno, agua, Geometry, Roadway) para aislar si `RH349/350/1425` y `agua723` provienen de filtro de capa, caras laterales ausentes/invertidas en LOD físico o huecos en costuras modelo-terreno; integrar después un gate de paridad Visual–Colisión–Navmesh tras cada regeneración P10.
- **Consumidor independiente:** Trazador offline sobre LODs de colisión del PBO compilado confrontado contra logs nativos `B3G2`.
- **Positivo y mutante/negativo:** *Positivo:* fixture vanilla reproduce exactamente impactos verticales y horizontales en motor y offline. *Mutante/negativo:* malla con LOD visual cerrado pero hueco lateral en colisión (`RV` pass, `RH` fail) o isla desconectada de navmesh bloquea aceptación.
- **Dependencias:** Lector `B3G2` y COB-06.

**COB-11** | **Dominio:** Vehículos/barcos/ferrocarril (P9, P11, P15) | **Tipo:** `TECNICA` | **Coste relativo:** Medio | **Riesgo:** Bajo
- **Problema observable:** P9 carece de prueba de paso 3D bajo puentes con agua máxima y margen parametrizable de oleaje/barcos medianos; carreteras y terraplenes (`c0`, `c1`, carretera49) no tienen validación dinámica de conducción P11; y la futura red ferroviaria/estación de San Petersburgo (P15) necesita reserva geométrica previa sin infringir P10.
- **Evidencia:** `product-spec.md:15-17,21`; `evidence/road-b2-recipe-20261029/README.