Delegar: JUICIO de plan a Claude Fable5.1 CLI nativo2.1.310 verificado hoy, identidad real devuelta en revisión anterior. Codex ejecutor/integrador autorizado. Una lane independiente read-only, herramientas deshabilitadas, sin escrituras/hijos. <=180s y <=850palabras. Devuelve SOUND/SOUND-with-fixes/NEEDS-WORK, problemas concretos, consecuencia y corrección; FIN_REVISION al terminar. Usuario hoy: continua con las pruebas, tambien hay que ir preparando las carreteras. Plan A sólo inventario de PBO instalado, no build/DayZ/colocación. B/C requieren descubrimiento y planes posteriores. Revisa trazabilidadP5/P6/P9/P10/P11, separación preparación/base, falsoPASS de ancho/ejes, cobertura de entradas, parseo, controles independientes, presupuesto. No inventar APIs; los métodos citados son anclas a leer ANTES de implementar. P3D reader estricto y read_pbo son existentes; catálogo nunca certifica conducción. Producto no autoriza un ancho global nuevo. No revisar cómo reparar río B3E. Fuente/readmes debajo; no acceso fuera de cápsula. Los datos de carretera49 son locales, cruce49/301 sin puente observado, Narva71 sólo diagnósticoaxis, kit118/76 conflicto existente. Capturas humanas requieren reparación procedimental de todos los equivalentes. Receptor Codex adjudica hallazgos frente a fuentes reales y actualiza plan antes de código. No fingir ejecución ni solicitar revisión infinita.

FILE ev112-road-preparation-20261028.md
1: # Preparar carreteras: pavimento, cruces y empalmes
2: 
3: Estado: BORRADOR_PENDIENTE_DE_REVISION. Petición viva: continuar las pruebas y
4: preparar carreteras en paralelo. Codex ejecutor/integrador. Esta preparación
5: no depende de obtener un nuevo PASS de colisión del río, pero la integración
6: de un piloto que lo cruce sí depende de resolver el conflicto correspondiente.
7: 
8: ## Producto y límites
9: 
10: P5/P6: conexiones existentes, piezas vanilla y anchuras humanas. P9: conservar
11: navegación, gálibos y agua. P10/P11: preparar ahora; emplazamiento físico global
12: y conducción después de la base de terreno/navegación. Esta petición permite
13: avanzar catálogo, corredores y prototipos aislados; no aprueba extender pavimento
14: a todos los ejes ni cambiar clases/ancho de producto para encajar una pieza.
15: No tocar recorte, reserva natural, islas, agua, extremos o protección015-45.
16: 
17: ## Descubrimiento y cuatro pilotos
18: 
19: El censo independiente ya recorre124cadenas/36467aristas/107180.669m. El overlay
20: contra modelos desplegados verificó2413contactos; sólo mide ejes, no anchura de
21: pavimento. Los715.422m de agua de modelo sin tablero coinciden con charca nominal;
22: no sumar ambas categorías. Otros1024.828m son mar nominal. NO son cantidades
23: de puentes omitidos. Recibos: evidence/road-surface-overlay-20261028.
24: 
25: | Piloto | Fuente/localización | Preparación | Puerta específica |
26: | --- | --- | --- | --- |
27: | R-PAVE-49 | Parada5296,6000; cadena49 | Primer corredor seco para comparar encaje de pavimento vanilla con la reserva vial | Elegir límites por geometría/agua, no sólo por la parada; 11secciones tienen evidencia nativa local, no toda la cadena |
28: | R-CROSS-49 | Personaje4789.51465,5516.52197; contacto cadena49/arista301 a11.601m | Resolver cruce completo, entradas y salidas | No colocar un puente en las coordenadas del personaje; verificar continuidad terrestre y navegación bajo cruce |
29: | R-NARVA-71 | Cadena71, contexto2391,6941 | Medir encaje del tablero real y accesos | Diagnóstico previo6.666grados/2.228m no es tolerancia; exigir cobertura del corredor, no sólo proximidad de ejes |
30: | R-END-76 | Kit118; cadena76/aristas124–129; instancia19394363 | Separar corredor y final del río con superficies reales | Solape medido en6aristas; Visual201 midió24m² de lecho sobre terreno en corredor. B3D/B3E no acreditan todavía resolución nativa |
31: 
32: La carretera49 recibió visto bueno visual local, con pavimentado y conducción
33: pendientes. Bosque/c0 no certifican estos pilotos. C1 sigue SIN REVISAR.
34: 
35: ## A. Catálogo instalado, antes de generar poses
36: 
37: [EXACT] PBO instalado de referencia descubierto en la configuración B2A:
38: E:/SteamLibrary/steamapps/common/DayZ Exp/Addons/structures_roads.pbo,
39: 318217469bytes en lectura de metadatos28-10. Hash histórico34c1cabe608823dc09ec25dd62c3738a84075a7187484fc99dbdf4e1c2ed2f5f;
40: debe comprobarse vivo, no atribuirle identidad actual por fecha/tamaño.
41: P:/dz/structures/roads/parts contiene familias asf1/asf2 y curvas; P: no es oráculo
42: del instalado. El piloto FTT03-10 exportó17piezas, no acreditó importación.
43: Su asf1_25 tenía bbox12x25m: NO se equipara bbox con ancho útil de calzada.
44: 
45: [DESIGN] Un inventario nuevo sólo lectura del PBO instalado: lista exhaustiva de
46: entradas parts/*.p3d y modelos de puente separados, sin filtrar sólo los usados
47: por FTT. Validar prefijo, rutas, duplicados y hash de PBO antes/después; conservar
48: orden/lista fuente. Leer cada modelo estrictamente con lector ya fijado por hash,
49: registrar errores por entrada sin borrarla del denominador. Geometría Visual,
50: Roadway, Geometry/Fire/View, puntos/selecciones/properties/materiales, cajas y
51: centro del modelo; ningún LOD ausente se fabrica. Exportar sólo medidas/metadatos
52: y hashes, nunca binarios vanilla al repositorio público.
53: 
54: Anclas a leer antes de implementar: tools/playtest/attach_navmesh.py:read_pbo
55: (Path, no str); tools/quality/compiled_dry_road_gate_ev112.py:read_backend;
56: lector C:/temp/moto_lanes/review_g3/tools/odol_reader.py. from_bytes/from_file,
57: campos y resolución de LOD se revalidan en sus definiciones. No importar ni
58: relanzar CLI de B2A/FTT/B3E consumidos. Si el formato de parts no es el esperado,
59: conservar INCONCLUSIVE_PARSE y proponer adaptación separada, no lector permisivo.
60: 
61: El inventario distingue superficie dibujada, superficie de apoyo y semántica
62: de carretera nativa. Un modelo plano sin Roadway no se descarta ni se acepta
63: como carretera por su bbox: investigar su consumidor nativo/configuración antes
64: de elegir objetos sueltos o RoadNetwork. La vía de generación no queda decidida
65: por el éxito del TXT FTT. Evitar introducir nuevas herramientas mientras no
66: exista un impedimento demostrado en el flujo actual.
67: 
68: Consumidor: cobertura exacta de entradas y hashes del PBO, muestras de geometría
69: analítica con bbox conocido y LOD ausente, y referentes vanilla documentados.
70: Negativos: entrada duplicada/omitida, prefijo erróneo, parse parcial, NaN, escala
71: no unitaria y Roadway ausente no pueden convertirse en aceptación de conducción.
72: El status de cierre será CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE, o
73: INCONCLUSIVE_CATALOG con lista de entradas no leídas; nunca PASS de carretera.
74: 
75: Presupuesto A: revisión de plan180s; code review180s y suite120s antes de una
76: lectura de catálogo120s/2GiB. Un censo, sin compilar/DayZ ni modificar P:/vanilla.
77: Parar ante datos cambiados o formato no soportado; no barrer versiones/lectores.
78: 
79: ## B. Corredores y plantilla del piloto seco
80: 
81: [DESIGN, después de A] Cargar las cadenas de referencia y máscaras/superficies
82: selladas actuales. Seleccionar ventana seca en49, conservando estación, XZ y
83: dirección; asignar el ancho a partir de calzada/material/regla de producto,
84: sin usar el nombre de la pieza ni bbox como única medida. Si falta esa regla,
85: dejarla pendiente explícita y agrupar una decisión nueva de producto.
86: 
87: Preparar footprint continuo de pavimento y márgenes/empalmes, no sólo eje.
88: Comprobar intersección geométrica de toda su anchura con agua, lechos, apoyos,
89: vegetación/objetos y plataformas. Conservar contactos de menos de una muestra,
90: extremos y cruces en nodos: no reutilizar exclusiones del gate de terreno para
91: declararlos resueltos. No eliminar obstáculos para conseguir PASS.
92: 
93: Se conservan los límites existentes de verify_roads_v30.py: cross0.03m,
94: grade0.065, chord0.03m. Ese gate excluye48m del agua,470m de Narva y18m de
95: extremos; son ámbitos NO EVALUADOS, no aceptación de cruces. El nuevo gate de
96: pavimento debe añadir juntas, ancho útil, apoyo continuo y cobertura de accesos,
97: con tolerancias justificadas por el consumidor real y revisadas antes de autoría.
98: No se inventa ahora una tolerancia de desalineación, hueco o velocidad segura.
99: 
100: Sólo tras revisión específica: un candidato aislado, poses/modelos sellados,
101: relectura WRP/PBO, pruebas nativas de superficie y conducción vanilla a velocidades
102: predefinidas. Medir saltos/golpes/atascos y coste de render; navmesh se regenera
103: tras mapeado según P10. No publicar el candidato como colocado antes de demostrarlo.
104: 
105: ## C. Cruces y extensión
106: 
107: R-CROSS-49 y R-NARVA-71 requieren prueba de espacio libre bajo tablero, apoyos
108: y continuidad completa del corredor a ambos lados. R-END-76 requiere que el lecho
109: no invada el corredor y que el agua y extremos sigan intactos. Estos son casos
110: de regresión del generador/validador, no parches locales sin censo global.
111: Después del piloto seco, proponer por clase las correcciones del resto de la red,
112: con detección de huecos basada en agua real y geometría de carretera independiente
113: del inventario de puentes. Nuevos candidatos/builds necesitan su plan/presupuesto.
114: RAM, aceptación visual, mapa completo y council ampliado permanecen abiertos.

FILE product-spec.md
1: # Producto y aceptación
2: 
3: Fuente de autoridad: peticiones de Guillermo en esta conversación, límites v0 aprobados el 29-09-2026. El handoff heredado se usa como orientación, no como prueba de herramientas o datos.
4: 
5: | ID | Requisito | Criterio de aceptación |
6: |---|---|---|
7: | P1 | Región condensada, propuesta 12,288 × 12,288 km | 2048² celdas de 6 m; encuadre aprobado completo y orientación norte, confirmado también por Terrain Builder. |
8: | P2 | Conservar agua, costa, islas, ríos y zona natural | Geometrías de referencia trazables; posteriormente costas recorribles y agua funcional; no sustituir todos los lagos por mar. |
9: | P3 | Conservar íntegro el acercamiento de San Petersburgo | Misma transformación global, sin escalado local. Huella aproximada 4,81 × 3,83 km. Verificar canales y cruces a escala de juego. |
10: | P4 | Narva, frontera y territorio occidental | Localidad y ambas riberas presentes; cruce jugable diseñado y probado; futura base/búnker occidental pendiente de ubicación. |
11: | P5 | Conexiones principales | Referencia topológica coherente y una selección jugable medida; las vías se construyen con piezas y anchuras humanas. |
12: | P6 | Assets vanilla primero | Inventario y medidas reales antes de colocar edificios/puentes; futuros assets distintivos se priorizan después. |
13: | P7 | Objetivo 80–100 jugadores, experiencia tipo Chernarus; optimización comparada con Chernarus (petición24-10) | A/B con la misma versión, hardware, ajustes y escenas equivalentes; frame times/tirones, RAM/VRAM y carga de servidor por separado. Ensayo de jugadores, IA, loot y persistencia aparte. Plan `plans/ev112-performance-chernarus-20261024.md`; inventario estático disponible, rendimiento todavía INCONCLUSO. |
14: | P8 | Fuentes y generación reproducibles | Originales identificados por hash/fecha/licencia; transformaciones, excepciones, deltas y resultados registrados. |
15: | P9 | Ríos navegables y puentes elevados | Petición30-09: lancha vanilla y margen para barcos medianos. Continuidad de agua, anchura útil, profundidad con agua mínima y gálibo con agua máxima; paso real de embarcación por cauce y puente, además de cruce terrestre. Decisión08-10: conservar el fondo de 1 m y aceptar 0,95 m de calado geométrico mínimo en los corredores actuales de 24 m; conservar las excepciones previas de bajos/Narva y comprobar la lancha. No equivale a envolvente máxima de oleaje ni prueba de barcos medianos. Contrato trazado en evidence/v30-navigation-contract-2026-10-08/decision.json. El antiguo ensayo de Narva a tablero2m no satisface este requisito; el candidato posterior debe acreditarlo con su geometria y consumidores identificados en el HANDOFF. |
16: | P10 | Terreno y navegación antes del mapeado | Petición30-09: terminar primero relieve, hidrografía, cauces, orillas y navegación base. Posponer población, edificios, vegetación colocada, carreteras físicas y decoración. Los objetos de ensayo solo reservan gálibos y cruces; después del mapeado habrá que regenerar y validar de nuevo la navmesh. |
17: | P11 | Carreteras lisas para conducción DayZ | Petición30-09: perfiles longitudinales progresivos, superficie sin baches ni escalones, y empalmes suaves entre terreno, piezas y puentes. Medir cambios de pendiente y caída transversal, además de pendiente máxima; validar después con vehículos vanilla a distintas velocidades, sin saltos, golpes ni encallamientos atribuibles a la vía. Preparar la reserva del terreno ahora; mapeado físico después según P10. |
18: | P12 | Relieve selectivo por jugabilidad | Aprobación30-09: exagerar alturas de zonas concretas por encima de ×3 si conviene, sin fidelidad obligatoria a la escala vertical. Conservar XY, agua/islas/closeup, conexiones y P9/P11; medir perfiles, accesos, cobertura y líneas de visión. Cotas y máscaras de diseño en plans/selective-relief.md; aceptación posterior de terreno y navmesh regenerada. |
19: | P13 | Reserva natural y variedad de biomas | Petición30-09: conservar la reserva como punto clave, con alta densidad de árboles en ciertos sectores. Reservar ahora terreno, humedales y mosaico de bosque denso/claros; contrastar el perímetro antes de editar Z. Colocar vegetación después según P10, comprobar contraste entre biomas desde jugador, accesos, colisiones/navmesh y rendimiento del sector más denso. No equiparar cobertura WorldCover con densidad de instancias. |
20: | P14 | Contorno suave y bajos sin agua indeseada | Petición01-10: suavizar el outline general y corregir el agua que asoma intermitentemente en zonas bajas. Separar forma del terreno, textura y agua dinámica; comprobar margen y transiciones en las orillas, sin sacrificar canales navegables, islas, humedales ni la reserva. Validación visual con cámaras comparables y muestreo entre vértices, además de alturas nativas. |
21: | P15 | Red ferroviaria de circunvalación, radiales y estación de San Petersburgo | Petición03-10: diseñar una red principal que dé la vuelta al mapa, con algunas radiales y bifurcaciones adicionales. Al menos el tramo de San Petersburgo debe seguir su posición y recorrido reales, con la misma transformación XY aprobada, para colocar su estación emblemática en el emplazamiento correspondiente. En la fase de diseño se concretarán estación, corredores y cruces, conservando cauces navegables, gálibos y reserva. **Alcance futuro: no ejecutar ahora**; diseño y colocación física pendientes, respetando P10. |
22: 
23: El criterio de relieve selectivo está aprobado; las cotas del candidato regional ya estan implementadas y medidas, con aceptacion final segun HANDOFF. No confundir ese candidato con una decision de cerrar todos los niveles de agua. No están decididos densidad urbana, número de puentes jugables, economía militar ni ubicación/diseño del búnker. No se cambian silenciosamente para adaptar los datos al motor.

FILE README.md
1: # Cruces de carretera contra superficies desplegadas
2: 
3: Censo de las124cadenas y36467aristas de referencia, sin excluir agua, Narva
4: ni extremos y sin usar la lista del generador para descubrir cruces. Usa las
5: caras y poses reales selladas de la unidad A.32fixtures y consumidor independiente
6: Shapely verifican2413contactos; residuo máximo1.69914e-12m.
7: 
8: El diagnóstico identifica715.422m de eje bajo agua de modelo sin Roadway de
9: puente, en7cadenas. Coinciden casi exactamente con la capa nominal de charcas:
10: no sumar ambos. Otros1024.828m corresponden al mar nominal en14cadenas. Estas
11: son longitudes sobre ejes; NO son cantidades de puentes ni aceptación visual.
12: 
13: La posición reportada4789.51465/5516.52197 queda a11.601m del contacto
14: cadena49/arista301: mar nominal y ninguna cara de puente observada. En Narva
15: sí hay tablero sobre agua; eso no acepta su alineación. En la arista más
16: próxima medida, eje y PCA del tablero difieren6.666grados con separación
17: lateral2.228m; diagnóstico de ejes, no umbral nuevo. Kit118 tiene una pieza de
18: lecho/Roadway que intercepta6aristas de la carretera76. Esto localiza el solape;
19: la exposición del Visual completo y su reparación todavía están pendientes.
20: 
21: Se separan agua enterrada/expuesta respecto al terreno fuente, mar/charca
22: nominal y agua de modelo, tablero sobre/sumergido/ausente y geometría incierta.
23: Ninguna Roadway water_ext se acepta como puente. Proxy enterrado conserva
24: INCONCLUSIVE_WATER; caras ambiguas conservan ambos fans y rango de alturas.
25: Los nodos incluyen todas las cadenas incidentes sin duplicar observaciones.
26: Microhuecos no se sueldan; se guarda procedencia y ULP, e incertidumbre dentro
27: de una misma instancia. No se modifica ninguna tolerancia ni geometría.
28: 
29: Fable5.1 revisó plan y código. Se corrigieron el conteo de candidatos por
30: mutación de defaultdict, el filtrado de proxy enterrado, procedencia de huecos,
31: capas nominales, diferencias de agua, duplicación de nodos y cierre de recursos.
32: El preflight histórico conservado tenía candidate_edges incorrecto; el censo
33: verificado da994aristas candidatas/1399pares/129191caras.32tests incluyen
34: orquestación con carreteras secas, nodos compartidos y falsa Roadway de puente.
35: 
36: Censo4.437s,453042176B de commit; consumidor2.969s. Presupuesto120s/2GiB cumplido
37: en PID real. H coincide byteexact con el WRP editable vinculado al mundo de
38: la visita. No se ha decodificado la totalidad del terreno compilado: exposición
39: relativa al terreno de autoría, no prueba de motor. Ningún run DayZ utilizado.
40: 
41: Reportes resumidos y tramos están aquí; contacts.json/nodes.json completos y
42: NPZ de cobertura permanecen externos por tamaño, ligados en artifact-hashes.
43: Los intervalos de categorías pueden solaparse; no sumar ni contar como cruces.
44: 25de28piezas de puente intersectan algún eje: lasotras3no se borran ni se
45: consideran defectuosas por este dato. Persisten RAM, contornos, relieve, lechos,
46: aceptación visual/global y c1 SIN REVISAR; council ampliado sigue pendiente.