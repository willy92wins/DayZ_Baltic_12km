# Ejecución del council ampliado: validación y colocación procedimental

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
