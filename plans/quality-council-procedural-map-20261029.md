# Ejecución del council ampliado: validación y colocación procedimental

Checkpoint RoadC1A/C1A1 29-10:4775materiales propios y2048referenciasPNG/8PAA del laboratorio localizadas. Se corrigió en una recuperación nueva el filtro léxico que omitíaPNG, conservando el informe anterior parcial. No build ni cierre de recursos ni decoderOPRW0/3/terreno. Próximo planRoadC1B stage/config aislado; sólo sonda compilada si se revisa explícitamente. Fuentes0/3C0 intactas. Nueve humanos0resueltos,C1NOT_REVIEWED. Q03C/Q05/ángulos/referentes/reparación abiertos; council ya ejecutado.

Petición humana vigente del29-10: adelantar council, proponer mejoras y aplicar
las justificadas a herramientas y mapa. Este plan reemplaza el orden temporal
«council después de todos los fallos», no sus criterios ni los de EV112.
Estado: BACKLOG_TECNICO_ADJUDICADO; cada unidad necesita diseño/API verificados y
revisión técnica antes de código/build. Primer plan concreto Q02A separado.
Registro íntegro de79propuestas y disposiciones en
`reviews/2026-10-29-council-procedural-quality/ADJUDICATION.md` y evidencia privada
`council-expanded-20261029/proposal-registry.json`. Cada idea conserva autor y
texto; duplicadas se integran por unidad sin perderlas. Argon parcial no se
presenta como informe completo ni se suple con otro modelo.

## Condiciones comunes

- Nueve rechazos visuales abiertos. Bosque/c0 sólo vistos bien localmente;
  carretera49 local sin pavimento/conducción; C1 SIN_REVISAR. No heredan PASS.
- 607PASS de Nav8 históricos; original2658 sigue47FAIL21inciertos. ParejaB3G2
  INCONCLUSIVE: RV700/723 mejora; RH349/350/1425 y agua723 abiertos, Bullet sin
  calibrar. No reusar runs/preparadores consumidos.
- Conservar P1–P15, agua/receptores/extremos/topología/apoyos/reservas y límites.
  Narva ya tiene intención aprobada de mar al pie con tierra en apoyos laterales;
  hace falta separar geometría portante, no repetir esa decisión estética.
- Distinguir forma nativa, modelo, colisión, agua dinámica, textura y percepción.
  Una proyección2.5D no certifica todo volumen3D. No inventar ola máxima,
  anchura útil de piezas desde bbox, ni trasladar tolerancia de eje a conducción.
- Orden: evidencia independiente → detector con positivos/mutantes → reparación
  por clase → consumidor compilado → recenso completo → motor/visual según caso.
  Un candidato sin hallazgo nunca equivale a aceptación global. Preservar mapas
  antes/después, ámbito exacto y complemento protegido sin cambios.

## Unidades ejecutables por dependencia [DESIGN]

| ID | Trabajo y criterio de salida | Dependencias / validación |
|---|---|---|
| Q01 | Registro de los9rechazos/cobertura por capa: no observado, correlato, hallazgo sin resolver, omitido o materialización distinta. Consumidor rechaza omisiones/duplicados y falsa promoción. | Censos guardados; no asociar fotografía por posición del avatar. C1 siempre sin revisión humana. |
| Q02A | Giros de TODOS los perímetros cerrados, incluido cierre. Diagnóstico aditivo sobre1030cadenas existentes. | Plan separado `quality-council-q02-closed-perimeters-20261029.md`; cuadrados/triángulos, giro en costura, orden/reversión/subdivisión; lector independiente. |
| Q02B | Curvatura por longitud de arco multiescala, L/U, lenguas, zigzags oblicuos, tramos recta-arco y periodicidad. Calibración natural/diseñada antes de umbrales. | Q17 y Q02A; negativos realistas más círculo/recta diseñada. No ruido aleatorio para eludir detector. |
| Q03 | Escena compuesta por capas: terreno, modelosVisual, agua nativa/3D, lechos/caps/puentes. Medir exposición y perfiles completos, no sólo eje ni altura sobre terreno enterrado. | Q04 para poses; lector completo de modelos sin filtro de nombres. Mutante pieza que oculta ribera o cap fuera del eje. No scalar máximo como prueba de volumen. |
| Q04 | Resolver transformaciones/pivotes de carreteras con piloto WRP aislado y las4hipótesis de RoadB2. | Revisar `ev112-road-b3-wrp-pilot-preparation-20261029.md`, fuente/compilado/sonda ligados a instancias, sin cercanía. Las24huellas offline no prueban motor. |
| Q05 | Clasificar TODOS los contactos viales contra paso real: huella completa, accesos, agua3D, Roadway. | Censo guardado770aristas/29cadenas, NO770puentes. Q03/Q04. Mutantes puente omitido/girado/corto/cap lateral. Vado sólo con intención acreditada. |
| Q06 | Colocador de puentes guiado por eje y tangentes de AMBOS accesos, apoyos y gálibo. | Q05; comprobar Narva71 y49/301. Optimizar pose/accesos juntos, no mover pieza por personaje. Toda huella sin escalones; paso lancha/vehículo posterior. |
| Q07 | Reserva/pavimento de carretera y perfiles de conducción completos, peralte, rasante y juntas. | Q04/Q05/Q06 yP10/P11. Pilotos49seco,Narva71,kit118cadena76; terreno antes de mapeado global; velocidades vanilla posteriores. |
| Q08 | Referente independiente de agua/clases/anchuras/receptores y correspondencia topológica. Adjudicar5discontinuidades/65saltos/H==W sin soldar. | Research ya existente; comparar componentes/conexiones por localización, no sólo cantidades. Mutante intercambio de componentes conservando conteo. Contradicción nueva → delta concreto al usuario. |
| Q09 | Piloto de contorno nativo: optimización mínima sujeta a restricciones; empezar por correlato oriental si todas las protecciones lo permiten. | Q02B/Q08/Q17. Narva residual necesita soporte separado. Fallo de factibilidad se informa; no relajar máscara ni sacrificar isla772/humedales. |
| Q10 | Regenerar ejes/orillas de cauces con variación continua de curvatura conservando referencia y anchos. | Q02B/Q03/Q08. Identificar río adyacente49 sin inventar ID. Escalera con codos redondeados debe seguir rechazándose. XZ protegido no se cambia sin resolver contrato. |
| Q11 | Integración de faldones y transiciones de lechos; medir ambos sitios antes de elegir elevar terreno o abatir modelo. | Q03/Q08; kit118 ycont65 regresiones distintas. Piloto secoNPZ no materializar hasta probar exposición lateral. Caps contra carretera incluidos. |
| Q12 | Relieve: normales/curvatura/crestas/terrazas multiescala y triangulación real; suavizado selectivo con frontera continua. | Q08/Q17; preservar cotasP12, cuencas visuales, caminos y reserva. Mutantes faceta larga/pico y control colina diseñada. No confundir charca oriental con native_spike. |
| Q13 | Vegetación existente: apoyo continuo bajo tronco, pendientes, biomas e interacciones con agua, vías, gálibos y accesos. | Q03/Q05; no sólo punto ni perímetro muestreado. Mutante pozo entre muestras/tronco sobre vía/copa legítima. Sin poda para PASS ni nueva población antesP10. |
| Q14 | Auditar rocas/props/edificios existentes por huella, puerta/acceso y colisión; investigar referentes vanilla/hermanos con procedencia. | Q03/Q04/Q13,P6/P8/P10. Autoría de población DIFERIDA. No importar técnicas/assets por parecido ni asumir licencia. |
| Q15 | Consumidores físicos y navmesh: aislar RH/agua pendientes, calibrar Bullet; luego recorridos peatón/vehículo/lancha y conectividad tras delta. | Nuevo plan sobreB3G2, sin repetirla. Q05/Q06/Q07; VisualPASS no acredita colisión/Navmesh. Textura sin geometría no fuerza regeneración ficticia. |
| Q16 | A/B nuevo completo contra Chernarus y mapa de coste por sector: RAM/VRAM/frame time/servidor separados. | PlanP7; no completar bloque interrumpido ni promediar versiones. Instancias/materiales/LOD proxy no prueban80–100jugadores. Escenas equivalentes y sector denso. |
| Q17 | Corpus versionado de casos humanos, naturales/diseñados y mutantes independientes por clase. | Positivos con aceptación explícita por dimensión, no asumir toda reserva buena. Rotación/orden/subdivisión, NaN/omisión/duplicado/pose equivocada. Reportar sensibilidad/cobertura y no sólo número de tests. |
| Q18 | Generación determinista, semillas por identidad, deltas auditables y recenso de TODO dominio aplicable. | Q01/Q17. Complemento protegido bitidéntico donde contrato lo exige; caso distante no debe mover región ajena. Independencia del consumidor. |
| Q19 | Atlas multiescala y vistas comparables de suelo/media/altura, zonas modificadas más muestra fuera dehotspots. | Q01/Q03; camera_set vetado. Atlas offline no sustituye aceptación humana; rutas de captura permitidas por investigar. |
| Q20 | Diseño futuro: composición Este/Oeste, búnker, densidad y ferrocarril. | DIFERIDO_PRODUCTO. No construir ni reservar corredores inventadosP15. Auditar referencias existentes sí; alternativas concretas cuando corresponda. |

## Control de ejecución

Prioridad inmediata: Q01/Q02A y preparaciónQ04; después Q03/Q05 desbloquean
reparación de lechos, puentes y pavimento. Q08 se investiga en paralelo al resto,
sin confundir una restricción aún no definida con permiso de cambiarla.
Cada unidad tendrá antes de ronda1: fuentes/APIs reales, plan revisado, tiempo y
memoria, positivos/negativos y salida PASS/FAIL/INCONCLUSO acotada. Los budgets
de Q02A están fijados en su plan; los restantes se fijan tras descubrimiento,
antes de su primer experimento (esta tabla no autoriza bucles ilimitados).

Todas las ideas aprobadas quedan aquí, incluidas investigación y fases posteriores.
Nada se declara reparado por estar en el plan. Se publica desde public-repo sólo
cada unidad probada y sanitizada, sin historial privado ni binarios vanilla.
DayZ requiere plan preparado/revisado, colaFIFO600s sin sondeo previo, adopción
propia, heartbeat10s y cierre/release/status oficiales. Automatización sigue
activa hasta terminar; silencio sólo ante estado sin avance/acción posible.

## Checkpoint de implementacion29-10

Q02A completo como diagnostico aditivo validado:48tests; evidence/closed-perimeter-q02a-20261029. Q04 completa solo su unidad RoadB3 fuenteaislada:53tests; evidence/road-b3-source-pilot-20261029. Q04global sigue pendiente compiled/native/pivote/accesos. Q01 completado como registro abierto con9casos/0resueltos,25testsPASS y1skip; evidence/rejection-coverage-q01-20261029. RoadB4A tiene plan revisado de descubrimiento de entradas, todavía sin extractor ni build: ev112-road-b4-build-discovery-20261029.md. El resto continua pendiente conforme dependencias; ninguna reparacion visual global cerrada.


Q04 RoadB4A ejecutado como INCONCLUSIVE_DISCOVERY, no autoriza build ni coloca carreteras. PBO/catalogo y referenciasTODOSLOD fijados; siete rutasbuild requieren captura de estabilidad B4A1 con plan revisado. Evidence/road-b4a-build-discovery-20261029. Q02B/Q03/Q05 y reparacion siguen pendientes.

Q04 RoadB4A1 consumido STABLE_CAPTURE7/7 de fuentesbuild;2texturas iguales,5recursos bytesdistintos frenteR0. No pivote/build/colocacion aprobados. B4A2 descubrimiento inicial de recursosinstalados revisado; cierretransitivo/parser ybuild requieren fases posteriores. Q02B/Q03/Q05 y nueve reparaciones siguen pendientes.

Q04 B4A2:8recursosinstalados fijados,asphalt_ext resuelto porprefix; padreinconcluso trasprimeraconversion.39testsreciboscorregidos y5mutantesaudit. B4A2R1 recuperacion guardada revisada, codigo pendiente. Q17A plan de corpus sintetico independiente revisado, sin arrays/contrato/codigo; habilitaQ02B sin fingir referentes naturales ni localizar fotos por proximidad. Nueve rechazos siguenabiertos.

Q17A completado VERIFIED_CORPUS_INCOMPLETE_CALIBRATION:11fixtures/66vertices,26tests,contratoexterno5416dbef,consumidorindependiente.9rechazos/0resueltos,calibration_readyfalse. Evidence/geometric-corpus-q17a-20261029. Q02B requiere plan de rasgos multiescala y referentes independientes antes de umbrales; B4A2R1 sigue revisado sincodigo/contrato. No repetir Q17A ni council.

Q04 B4A2R1 recuperó ambas muestras de material guardadas:16tests, una conversión2, primera sin relanzar. MATERIAL_SAMPLES_RECOVERED_ONLY; cierre transitivo/build/colocación pendientes. Q02B revisado para discovery numérico previo en quality-council-q02b-multiscale-features-20261029.md: sin código ni contrato numérico completo todavía. Priorizar ese frente geométrico; nueve rechazos sin resolver, no confundir muestreo con reparación.

Q02B0: discovery numérico completado,15tests y captura0.390s. 1030cadenas/538390ventanas candidatas; segmentos positivos mínimos7.23963e-5m, max|coord|12282m y perímetro máximo38725.342m. No cota ni calidad aprobada; siguiente contrato numérico por dimensión/condicionamiento. Revisión de integración Codex tras timeouts externos sin dictamen, limitación de contexto explícita. Q04 RoadB4A3 plan revisado61.609s para dos textos y cuatro hojasPAA guardadas; todavía sin implementación. Nueve rechazos sin resolver.

Q04/B4A3 completado como subconjunto guardado:2materiales+4hojas nuevas/8assets conservados,21tests y consumidor independiente. No build/colocación/conducción. Próximo Q02B1 núcleo de intervalos racionales revisado Fable77.093s; todavía sin implementación, ángulos/censo completo/naturalidad pendientes. Nueve rechazos humanos abiertos.

Q02B1 completo: núcleo certificado sobre53consultas propias,21tests, límites/degeneración/certificados verificados; no censo del mapa ni naturalidad. Nueve humanos siguen abiertos. Q02B2 prefijos compartidos y piloto real en borrador pendiente de revisión; RoadB4B/Q03/Q05 y referentes siguen pendientes.

Q02B2 completado como piloto numérico real:4cadenas/18943aristas/54consultas,14tests;13DEFINED,9cuerda0,32soporteinsuficiente. No censo global ni naturalidad/reparación. RoadB4B0 tiene plan revisado89.781s de correspondencia de referencias fuente/catálogos con consumo independiente; implementación pendiente. Q02Bproducción/ángulos,Q03/Q05/Q08/Q17 y nueve rechazos siguen abiertos.

Q04 RoadB4B0 verifica fuente/candidato con lectores independientes: 2.578.398 +3 instancias, 5.512 referencias; 21 pruebas privadas/públicas. Cuatro conflictos de representación de proveedor siguen en el reporte histórico; comparación guardada señala rutas/case con contenido fijado igual, sin probar precedencia actual ni autorizar build. Q02B3 plan y derivación revisados para preparar contrato externo; no código/censo todavía. Nueve rechazos siguen abiertos; Q03/Q05 y referentes independientes mantienen prioridad junto a carreteras.

Q02B3 producción limitada por2GiB y consumidor VERIFIED_PARTIAL_NUMERIC_COVERAGE; fuente inmutable,15pruebas privadas/públicas. No cobertura global ni mapa reparado. Q02B4 revisado para descubrimiento de firmas/contrato antes de compresión reversible; RoadB4B1 contrato revisado con incertidumbre de método explícita y código pendiente. Q03/Q05/referentes y nueve rechazos0resueltos permanecen abiertos.

Q04 RoadB4B1:5512identidades de contenido guardado,4equivalencias sobre28instancias; método histórico no ligado, INCONCLUSIVE_METHOD_BINDING.24tests y consumidor único; ninguna colocación o reparación. Q02B4descubrimiento/runtime y contrato c814cd09 revisados para autoría, no medición. Q03/Q05/Q08/Q17 y nueve rechazos siguen pendientes: siguiente geométrico evita rehacer el censo; siguiente vial debe probar precedencia/pose/huella real.

Q02B4 completado:2618archivos/2147479730bytes roundtrip exacto;774107161bytes codificados medidos, no guardados.25tests24PASS1SKIP; no nueva cobertura ni mapa reparado. Q03A plan revisado Muse25.704s para investigar fuentes de escena compuesta antes de contrato de extraccion; todavia sin investigacion/codigo. No seguir apartandoQ03/Q05 ni carreteras por serializacion. Marco/poses/caras completas y referentes pendientes.

Q03B29-10: contrato revisado, códigoR0/R1 REJECTED antesdecaptura. Tres repros detectan defectos ignorados por deltaFable. NoNPZreal/mapacambiado. RecuperaciónQ03B1lector+tests revisadaMuse28.969s; futuroscortessemánticos propios. Q03C/Q05 no consumen índiceinexistente; humanos0resueltos. Evidence/saved-scene-q03b-rejected-20261029.

Q03B1/Q03B1A: dos noentregas dentro120s,0archivos completos/0suite/0capturas; rutas de intentos retiradas. Cambio a corte de cabecera no produjo código. Ocho fixtures literales verificadas por NumPy estándar no equivalen a lector validado. Evidence/q03b1-delivery-budget-20261029; siguiente reevaluación de reparto y mecanismo antes de autoría, no nueva ronda automática. Q03/Q05 y reparaciones siguen abiertas.

Q03B1L cabecera NPY funcional validada con7métodos/26negativos+2schema; ejecución local asignada y revisión Fable completa con corrección reproducida. NPY_HEADER_FIXTURE_VERIFIED_ONLY; snapshot/ZIP/globalbudget/proxy y escena pendientes. Evidence/npy-header-q03b1l-20261029. Oráculos/contratos históricos intactos,0mapa/0humanos resueltos.

Q03B2: snapshot/ZIP/budget sólofixtures completo;9PASS1SKIP y2checks64KiB. CRC y terminación físicaDEFLATE corregidos, caps yheader intactos. No204NPZ reales/índice/semánticaproxy ni exposición/reparación. Evidence/archive-session-q03b2-20261029. Siguiente corte semántico propio antes de Q03C/Q05, sin repetir council ni censos.

Q03B3 plan proxy/faceidentities revisadoMuse48.985s para anclas/oráculoantesdecódigo. Secciones guardadas sólocuentas: pertenenciacaraNOT_SAVED, semánticakindNOT_EVALUATED. Ruta debe seguir hijo literal y todosordinales, expectedmulticonjunto completo. Sin código ni datos reales. Q03B2 ya publicado d7d4731e; no repetir sus operaciones.

Q03B3 identidad proxy/face sólofixtures completada:4modelos/3rutas/5caras,10testsPASS; hijo literal equivocado rechazado. Cargador de fixture corregido tras falsoPASS7/14bytes. No escena histórica/semánticakind/face-sectionmembership ni reparaciones. Próximo productor/consumidor propio; expected sintético no es oráculo para datos reales. Evidence/proxy-identity-q03b3-20261029.
