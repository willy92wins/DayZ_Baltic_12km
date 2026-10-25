# EV86 — revisión independiente

**Veredicto: PASS_EV86_REVIEW.** El único candidato `85b09e55954811edfa3933d979db1513898ea9ea328421f68c87007ac79f6076` cumple todas las puertas del consumidor independiente, incluidas las puertas nuevas del punto medio. No se produjo paquete ni se ejecutó DayZ.

La verificación reconstruyó el midpoint en float64 desde B (`f9fb23de…061f0`) y la dirección EV85-R rechazada (`a4434bf7…1e196`), lo cuantizó una vez a float32 y comprobó igualdad exacta con el candidato. Metadatos del candidato coinciden con EV79 (`dbc59ec5…a22c`) y B. Los 220/220 bordes originalmente estrictos conservan signo, sin empates nuevos; las diferencias originales empatadas son 0. La retención mínima de pendiente fue 0.4999982212, explicada por error de redondeo máximo de 4.7683716e-7 m; la menor diferencia final contra la cota de media pendiente menos redondeo fue 0.0010657310 m.

También pasan: dominio exacto de 39 nodos en dos parches; 33 alturas cambiadas; descensos de 0.85771656 m en (1146,1002) y 0.78028536 m en (2196,1572); cero extremos axiales nuevos; cruce máximo 0.45046768 m; cero bisagras nuevas >30°; p99, conteos y máximos sectoriales no empeoran; energía angular incidente baja 43.31% y 35.82% en los focos, 28.10% en el conjunto medido. Las máscaras P/F/SEA, soporte mojado local y fronteras de componentes permanecen iguales.

La cobertura física y visible del diseño P/F frente a las superficies ODOL compiladas queda dentro del límite de 0.002 m². El crecimiento fuera del diseño fue 1.0719e-5 m² y no hubo ganancia sobre caras previamente secas ni ganancia compilada sin P/F. Esta comparación usa transformaciones fuente 0WZD vinculadas por hashes al WRP de B; no es lectura de transforms desde DayZ ni aceptación gráfica.

**Corrección del harness:** `terrain_metadata_exact` es una puerta de aceptación y pasó. `diagnostic_metadata_not_supplied=false` quedó en `informational`, junto con `candidate_metadata_present_and_equal=true`; ya no participa en `all(gates.values())`.

Artefactos: [verificador independiente](E:/DayZ-Baltic-Build/v30-strict-bank-profile-20261010/review-independent/verify_ev86.py), [resultado JSON](E:/DayZ-Baltic-Build/v30-strict-bank-profile-20261010/review-independent/ev86-review.json), [fixtures](E:/DayZ-Baltic-Build/v30-strict-bank-profile-20261010/review-independent/fixture-self-test.json). Las fixtures de EV86 confirman summit reconstituido, empate B conservado y rechazo de gradiente que colapsa a empate en float32; el consumidor heredado también pasó los negativos de cobertura, cruces, orden, bisagras y V de EV83.
