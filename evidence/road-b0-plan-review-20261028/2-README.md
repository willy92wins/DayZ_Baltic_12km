# Recibos recuperados para carreteras B/C

P9 recuperado byte a byte del Git público (decision.json, commitf9700cc), no
reconstruido del README: fondo1m, calado geométrico0.95m y corredor24m; lancha
vanilla, exclusiones bajos/Narva conservadas y sin envolvente máxima de oleaje.
La afirmación anterior de ausencia en ambos checkouts era errónea: faltaba en
el worktree privado, pero estaba versionado en el público. Restaurado en privado.

Los «24m²» remiten a bed-report.json:23.95666642052773m² de lecho sobre H en
el corredor de8m del referente vial anterior, caso kit118. Fuenteconflicto
112.78593473499694m²; proyección de agua real solapada0 y distancia4.825250638m.
Son datos históricos del discriminador, no medición nueva ni anchura útil de
carretera. Ver historical-discriminator.py:36-52: rectángulos del referente y
refinado de planos; no extrapolar esa cobertura a piezas asf1/asf2 de12/9m.
El recibo conserva inventario/entradas por hash y sus límites de proxies/nivel
nominal. No se relanzó ni se cambió ese experimento.

El plan vial B/C debe cubrir geometría Visual/Roadway y accesos completos,
mantener medidas independientes de ancho útil/pivote y censar agua/cruces sin
depender de puentes ya generados. No puentes colocados por proximidad, no
conducción ni colocación global aceptadas. Preparación local compatible conP10.
