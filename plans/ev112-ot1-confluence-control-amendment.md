# EV112 OT1 — propuesta de corrección del control de confluencia

Estado: APROBADA por Guillermo el 18-10-2026 mediante picker: «Sí, corregir el control de confluencia (recomendado)». Implementada y validada offline sobre run-f. No autoriza saltar G7 ni cerrar OT1.

## Contraejemplo verificado

Fuente: `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-ot1-20261018/confluence-contract-counterexample.json` y script independiente `prove-confluence-conflict.py`.

[EXACT] En run-d, el control lateral 4785 de 100.0-0 (pieza 737) está en (3780.363688,2256), a 0.363688 m del eje de la rama 100.2-0. El constructor de la sonda exige `dry` porque el punto está a 6 m del eje principal, aunque pertenece al cauce de la rama declarada.

[EXACT] Con las poses actuales, G4 exige terreno ≤1.347716 m en el eje de esa rama. Las dos caras nativas incidentes admiten 35 grados por G5. Por interpolación, en el control lateral el terreno puede alcanzar como máximo 1.602374 m. G7 exige ≥1.677500 m para enterrar la lámina de la principal. Déficit: 0.075126 m. Subir el terreno para aprobar G7 rompe G4 o G5 con estas poses. Es un contraejemplo a la clasificación universal de todos los controles laterales como secos, no una prueba de imposibilidad para todas las poses alternativas.

## Cambio propuesto [DESIGN]

1. Mantener los dos controles laterales a 6 m de cada pieza y los controles secos actuales. No mover el control conflictivo para esconderlo.
2. Introducir un tipo explícito `kit_confluence` únicamente cuando las dos ramas consten enlazadas en la lista de trabajo, ambas estén construidas, el punto esté dentro de 1.8 m del eje continuo de la otra rama (el semiancho HW actual) y su superficie de agua real cubra el punto con margen positivo sobre el terreno.
3. Registrar `other_site` y expectativa `wet`. La puerta reconstruye independientemente relación, distancia al eje, geometría de la otra rama y estado mojado; no confía en la etiqueta del generador. Los dos controles por pieza siguen siendo obligatorios: seco o confluencia demostrada, nunca `test` ni sin expectativa.
4. Todo lateral que no demuestre esas condiciones sigue obligado a ser seco. La regla no se aplica a charcas, láminas aisladas ni meros ensanchamientos de la misma rama. G2, G3, G4, G5, G6 y G11 conservan sus límites.
5. Negativos: cambiar un lateral mojado ordinario a `kit_confluence`, inventar `other_site`, usar una rama no enlazada, quitar expectativa o indicar `test` deben dar FAIL. El contraejemplo anterior debe aceptarse como control mojado de confluencia; una rama sin agua debe fallar.

## Alcance y límites

Solo corrige el contrato entre `probe_points_kit.py` y `gate_g7_probe.py`. No cambia terreno, agua, poses, presupuesto de 3000, ni el ancho pedido. El selector debe conservar estas referencias y al menos un control de cada confluencia declarada.

No resuelve por sí solo los otros fallos de OT1. Esos continúan bloqueando integración. La prueba de motor G8 sigue pendiente de OT8.

## Evidencia de implementación

`E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-ot1-20261018/g7-approved/gate-g7.json`: cuatro laterales de confluencia aceptados; posiciones y referencias originales conservadas. Sonda de 3000 puntos con cobertura y referencias válidas. Los otros 19 laterales mojados siguen dando FAIL; no se ha convertido G7 en PASS por la enmienda.

El generador mide la distancia a las líneas centrales continuas de las piezas reales de la otra rama. La puerta las reconstruye independientemente con sus matrices y verifica relación declarada, ambas ramas construidas, distancia, altura del terreno y superficie de agua de la otra rama. El selector retiene un control por pareja de ramas y el eje y ambos laterales de ese control.

`E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-ot1-20261018/confluence-controls.json`: caso real PASS y ocho rechazos esperados (lateral ordinario disfrazado, rama inventada, rama construida no enlazada, expectativa ausente, etiqueta test, rama sin superficie de agua, pérdida de cobertura runtime y altura declarada no finita). Script reproducible: `evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates/negative_confluences.py`.
