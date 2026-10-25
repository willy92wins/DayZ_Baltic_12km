# EV53r1 - unica reparacion del dominio de medida

El candidatoEV53 queda conservado enFAIL. `../v30-coupled-native-shore-20261009/domain-diagnosis.json` aisla la discrepancia: el consumidor quita1mm en los extremos junto al limite del sector; el autor media los segmentos completos. Al medir el mismo intervalo, la discrepancia baja de3.6e-4 a<2e-6 de energia. No fallo del perfil ni razon para bajar el umbral.

Corregir `points()` con el recorte analitico exacto de ese limite. Mantener semilla, dominio, objetivos, todos los gates y100iteraciones. Una ejecucion de reparacion. Se anade un margen interno de1e-4 a la restriccion de energia, 50 veces el error residual medido de cuantizacion; el gate independiente sigue<=0.9 de fuente y no se relaja. El margen solo hace mas estricta la autoria. No otra reparacion si falla un gate de producto.
