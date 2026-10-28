# B3: candidato de contacto, validado sólo offline

El operador conserva los9120puntos,12160caras y1520componentes del modelo.
Amplía la huella de12prismas triangulares manteniendo6puntos/8caras por prisma;
no cambia bbox, masas, índices ni los LOD Visual/Memory/Roadway. Sólo autoriza
XYZ y normales de esos componentes. No es una reparación aceptada en juego.

Los contactos originales700dry y723wet quedan interiores tras sumar origen y
redondear a float32 mundial, con margen0.641mm y0.523mm respectivamente.
Ese marco aritmético no certifica el marco compilado ni el motor. La revisión
propuso2ULP como umbral, pero se descartó: el antecedente nativo aceptaba
contactos menores de1ULP. No se rebajó ningún gate vigente.

Overlay completo del lecho visible: cero área omitida/excesiva; conserva los
límites vertical±0.02m y horizontal0.01m. Máximo error de plano2.783e-8m.
No se alteran las etiquetas de agua. El723 continúa siendo un fallo histórico
de agua además de RV; esta unidad no lo reclasifica ni demuestra causa raíz.

17tests positivos/negativos pasan. La revisión de código detectó la exigencia
equivocada de que723fuera seco: corregida y cubierta por regresiones. El riesgo
de grosor inexacto no se reprodujo:36pares tienen error0m; se mantuvo la guarda
exacta. Un primer test de cara retirada fallaba al serializar su selección;
se corrigió el fixture antes de la ejecución real, sin cambiar el consumidor.

El research de agua queda adjudicado aparte: la supuesta imposibilidad lógica
de41controles fue refutada con el juez real y observaciones SINTÉTICAS. No son
mediciones de juego, no prueban viabilidad física ni cambian los fallos.
Reproducir sólo esa afirmación: GISpython -I water-contract/verify_counterexample.py
<ruta-al-repositorio>. Las expectativas originales permanecen intactas.

Fuentes y resultados: report.json, consumer.json, author.json, contract-r1.json,
reviews/, discovery/ y water-contract/. No se publican binarios/PBO vanilla ni
transcripciones de CLI. El candidato local c769dd9a está en R/prism-contact-b3-
candidate-20261028/candidate.p3d; el contrato447d4a76 identifica el experimento.

Siguiente: plan separado de compilación y sonda nativa, revisado antes de
ejecutar. No repetir autores, consumidores, revisiones o B2 consumidos. Original
2658conserva47FAIL21inciertos; RAM, C1, nueve regresiones y calidad global siguen
abiertos. El council ampliado permanece EN_COLA tras el trabajo previo.
