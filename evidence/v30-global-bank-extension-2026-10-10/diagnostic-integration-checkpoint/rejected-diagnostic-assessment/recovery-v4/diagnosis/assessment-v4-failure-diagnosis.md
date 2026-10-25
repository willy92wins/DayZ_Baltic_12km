# Diagnóstico de los fallos nuevos de recovery-v4

Informe v4: `E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\rejected-diagnostic-assessment-v1\recovery-v4\run-01\assessment.json` (SHA256 79a4f1b09b30e98cf210e35bfc12e81388ed977c272dffd44612aec1df013279). Estado `DIAGNOSTIC_ASSESSMENT_ENERGY_AND_OTHER_GATES_FAIL`; no aceptado, sin terreno escrito.

## Protección y máscara efectiva

De 114 vértices modificados, 16 intersectan `other_fixed_context`; los 16 son simultáneamente `cls=5`, `water=true` y `wet_support=true`, es decir, la excepción de liberación declarada. La intersección con `effective_fixed_context` es 0; con P9 y carretera es 0 y 0. Preparación informa reserva=0, plataforma=0 y halo ingeniería=0 en contexto.

El preparador define `nonreleased_fixed = other_rebuilt & ~((cls==5)&water)` y `effective_fixed` incorpora large-lake banks, halo, Narva, reservas, plataformas, P9 y carretera. El consumidor v4 intersecta cambios con el `other_fixed_context` bruto, que aún contiene la parte liberada `cls=5/water`; por tanto ese gate parece un falso FAIL de interpretación de máscara, no un cambio en reserva/civil. El resto del recibo de protecciones sigue siendo evidencia necesaria; no se modifica el gate aquí.

## Topología compilada local

Se repitió solo el clipping/topology de las 200 caras preparadas sobre 144 celdas, usando la misma rutina geométrica EV87. Las áreas reproducen las del informe (ver JSON). Para las dos claves afectadas se guardan áreas de componentes, áreas de huecos, matrices de solape B/H y diferencias simétricas. No se aplicó umbral ni se reclasificó el FAIL como sliver.

| Medida | B | H |
|---|---:|---:|
| physical_object_16804567_model7443 área expuesta (m²) | 234.98670811 | 230.107325165 |
| physical_object_16804567_model7443 componentes / huecos | 2 / 0 | 1 / 0 |
| visible_object_16804567_model7443 área expuesta (m²) | 235.319943885 | 230.536494536 |
| visible_object_16804567_model7443 componentes / huecos | 1 / 5 | 2 / 4 |
| physical_unique_union área expuesta (m²) | 697.906494623 | 682.69412939 |
| physical_unique_union componentes / huecos | 2 / 0 | 1 / 0 |
| visible_unique_union área expuesta (m²) | 698.80506567 | 683.65179232 |
| visible_unique_union componentes / huecos | 1 / 3 | 1 / 3 |

Los cambios topológicos no se pueden atribuir a precisión de overlay sin mirar tamaños: el JSON conserva magnitudes absolutas de cada componente/hueco y áreas B-only, H-only y simétrica. Las áreas totales expuestas cambian aproximadamente 15.2 m² en cada superficie; esto es una diferencia geométrica sustantiva, aunque el cambio de conectividad puede depender de un cuello estrecho. La puerta topológica sigue fallida según el contrato actual.

## Energía y alcance

La puerta de energía sigue fallando: 155.9440734841285 − 155.94405102975674 = 2.24543717593e−5, por encima del allowance 1.55944051030e−5; la mejora frente a B (279.185592812943) no basta para satisfacer cierre-vs-raw. Este artefacto no corrige eso ni reevalúa otras puertas.

El JSON ancla hashes del assessment, preparador, máscaras, diagnóstico rechazado, B, EV87 y ayudante, y comprueba que el readset no cambió durante el análisis. No se modificó solver, candidato ni gates.
