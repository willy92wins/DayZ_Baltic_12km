# Diagnóstico de los fallos nuevos de recovery-v4

Informe v4: `E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\rejected-diagnostic-assessment-v1\recovery-v4\run-01\assessment.json` (SHA256 79a4f1b09b30e98cf210e35bfc12e81388ed977c272dffd44612aec1df013279). Estado `DIAGNOSTIC_ASSESSMENT_ENERGY_AND_OTHER_GATES_FAIL`; no aceptado, sin terreno escrito.

## Protección y máscara efectiva

De 114 vértices modificados, 16 intersectan `other_fixed_context`; los 16 son simultáneamente `cls=5`, `water=true` y `wet_support=true`, es decir, la excepción de liberación declarada. La intersección con `effective_fixed_context` es 0; con P9 y carretera es 0 y 0. Preparación informa reserva=0, plataforma=0 y halo ingeniería=0 en contexto.

En `prepare_wet_bank_matrices.py:407–428`, el preparador define `nonreleased_fixed = other_rebuilt & ~((cls==5)&water)` y `effective_fixed` incorpora large-lake banks, halo, Narva, reservas, plataformas, P9 y carretera. En `assess_rejected_diagnostic.py:333–337`, el consumidor v4 intersecta cambios con el `other_fixed_context` bruto, que aún contiene la parte liberada `cls=5/water`; por tanto ese gate parece un falso FAIL de interpretación de máscara, no un cambio en reserva/civil. El resto del recibo de protecciones sigue siendo evidencia necesaria; no se modifica el gate aquí.

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

La componente física pequeña de 0.0283188364 m² de B desaparece en H; su bounding box X/Z es 7119.7989–7120.3756 / 7119.5307–7120.4023 m, dentro de la celda (r=860,c=1186), donde el vértice global (860,1186) sube +0.5 m. La componente grande del mismo objeto tiene 234.9584 m² en B y 230.1073 m² en H; la pequeña no intersecta H y no es conectada por la nueva exposición. No es correcto llamar sliver numérico a esa pérdida solo por ser pequeña: la geometría calculada la elimina y la puerta de componentes cambia. El delta de área física total único es −15.2123652 m²; B-only/H-only son 16.5491985/1.3368333 m². La compresión topológica física se explica por esa isla minúscula que desaparece, no por conectar las dos componentes grandes de B (la segunda componente no intersecta H). En la cara visible del mismo objeto, aparece una componente de 1.32328086e−5 m² y desaparece un hueco de 9.0946e−13 m²; estas magnitudes son compatibles con slivers de overlay, pero no se perdona el conteo exacto ni se cambia el umbral. Las áreas totales expuestas cambian aproximadamente 15.2 m² en cada superficie. El contrato de recovery-v4 sí exige igualdad exacta de componentes/huecos por objeto y unión (helper `verify_polished_diagnostic.py:701–704`, `assess_rejected_diagnostic.py:416–417`); bajo ese gate el FAIL es reproducible y no se relaja. El plan original focal (`PLAN_FOCUS_1981.md:17,25,27`) permite desplazamiento de cruces ≤1 m y cambios de área en orilla existente, mientras mantiene agua y protecciones fijas; no enuncia explícitamente igualdad de estos conteos locales. Por eso el cambio geométrico está medido, pero su compatibilidad de producto no se decide solo con el conteo añadido: hay que contrastar la pérdida de esa componente con el requisito de conservar islas/canales antes de aceptación.

## Energía y alcance

La puerta de energía sigue fallando: 155.9440734841285 − 155.94405102975674 = 2.24543717593e−5, por encima del allowance 1.55944051030e−5; la mejora frente a B (279.185592812943) no basta para satisfacer cierre-vs-raw. Este artefacto no corrige eso ni reevalúa otras puertas.

El JSON ancla hashes del assessment, preparador, máscaras, diagnóstico rechazado, B, EV87 y ayudante, y comprueba que el readset no cambió durante el análisis. No se modificó solver, candidato ni gates.
