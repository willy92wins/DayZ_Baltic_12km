# EV82-B — revisión independiente del consumidor y superficies

**Veredicto offline: PASS_EV82_CONSUMER + PASS_EV82_AFFECTED_SURFACE.** El candidato `terrain.npz` (`f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`) conserva la identidad EV79/P/F esperada y añade 3.046 alturas frente a EV80; el total respecto EV79 es 4.091. El consumidor geométrico independiente pasó sus 38/38 puertas. El consumidor de superficie pasó sus 10/10 puertas sobre la referencia compuesta EV72+EV80. No se empaquetó ni desplegó este candidato, y no se abrió DayZ.

## Geometría

- Fuente: EV79 `dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c`; referencia incremental: EV80 `0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b`; plano y campo visible conservan SHA `768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0` y `f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`.
- El selector recorrió 4.329/4.329 nodos. Cambio máximo absoluto: 2 m; cambios fuera del selector: 0; caras de agua nuevas: 0; margen de piso mínimo: 0 m; exceso máximo de pendiente: 0° frente a fuente y EV80.
- Para las 31.960 aristas incidentes a vértices cambiados, la suma de cuadrados angulares baja 13,50% frente a EV80. El control contra EV79 muestra 22,58% de reducción. No aparecen aristas nuevas >30° desde una base ≤30°; p99, conteos >30° y máximos por sector pasan la comparación EV80. No hay una puerta de energía de banco: su media cuadrática sube de 1,38948 a 1,42257, así que el resultado traslada parte de la curvatura y no demuestra una mejora uniforme.
- Los campos `ev81` que aparecen dentro de `ev80_comparison.distributions` son nombres heredados del esquema del informe; el propio reporte fija `candidate_sha256` al hash EV82-B indicado arriba. No deben leerse como referencia a otro candidato.

## Superficie afectada

- Se seleccionaron 462 teselas por intersección de celdas nativas cambiadas con huella acolchada; 562 quedaron excluidas tras comprobar que sus celdas acolchadas no contienen vértices cambiados respecto de EV80. Referencia: `reference-inputs.json` B, `PASS_EV80_COMPOSITE_REFERENCE`, SHA `358960dd95ef5bd2687190909b033306f8d0e82366a40461af46396f52cc9a8c`.
- Las 924 capas PNG, 924 PAA y 924 decodificaciones fueron verificadas. Los 2.324 solapes de vecinos comparados coinciden exactamente. En 68.076.288 píxeles hay 4.282.586 píxeles mojados; agua de origen sin grava: 0; píxeles interiores mojados no grava tras compilar/decodificar: 0. Quedan 2.426 píxeles mojados no grava dentro de la banda de orilla, fuera de la puerta que exige grava solo para interior.
- Alpha, paleta, control negativo, identidades PNG de referencia y selección/exclusión pasan. Los conteos de píxeles cambiados son 3.021 satélite y 784 máscara.

## Límites

Esto verifica geometría, selección de teselas, capas y PAA compilados offline. No verifica mips (estado `PENDING_ROOT`), empaquetado/PBO de EV82-B, despliegue, lectura nativa del WRP nuevo ni aceptación visual/en motor. El PASS de exposición y compilación WRP de EV82-B comunicado por root es evidencia paralela, no se incluye como una ejecución independiente de esta lane.

Artefactos: `verify.py`, `report.json`, `build_changed_surface.py` y `surface-verification.json` en este directorio EV82-B. El builder se reanudó tras un error de serialización del informe: las capas ya generadas se conservaron; el verificador de reanudación omitió reconstruir PNG→PAA y comprobó que hashes PAA y decodificados permanecían iguales.
