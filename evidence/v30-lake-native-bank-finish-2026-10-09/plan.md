# EV39 — taludes exteriores de los dos lagos, niveles intactos

Alcance autorizado: suavizar toda la superficie, incluidos terraplenes. PLAN: v30-rumbo-agua-1.0 §3 reserva la decisión de niveles de los dos lagos; este lote no cambia nivel, lecho, agua ni sus soportes triangulares. La reserva de niveles continúa abierta.

Mecanismo: EV19 filtraba alturas con gaussiana y luego truncaba cotas, aumentando curvatura. EV25 minimiza directamente saltos de gradiente de las caras nativas con restricciones de pendiente, pero excluyó la banda de72m de estos lagos. Aplicar ese método a la banda seca exterior excluida, una sola solución acotada. No repetir el barrido global EV25 ni variar radios, cotas o pesos buscando un PASS.

Una propuesta, máximo60 barridos/600s y una reparación de implementación si falla la ejecución. Soportes de agua, ingeniería, playas, periferia66m, metadatos y exterior exactos. Solo descenso ≤1,5m, conservando suelo actual si es inferior al objetivo; suelo objetivo max(nivel+0,30m,mediana anillo12–36m,1,80m). Nada cambia por debajo de los planos de agua.

PASS de forma: reducir ≥10% la curvatura de cada banco0–36m del consumidor EV19 y no elevar p90 de la cresta; reducir saltos nativos en cada banco. Pendientes de cada cara ≤max(anterior,35°). Identidad fuera de alcance y de todos los soportes de agua. Consumidor independiente sobre float32 guardado, controles negativos para geometría fija/alcance/pendiente/agua. Si pasa, paquete aislado y lectura nativa antes de integrar. No declara resuelta la política de niveles ni la base1.0.
