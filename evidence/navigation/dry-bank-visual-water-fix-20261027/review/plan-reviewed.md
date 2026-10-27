# Orilla seca: corregir la referencia de agua cuantizada

Estado: PROPUESTO_PARA_REVISION. Ejecutor/integrador Codex por petición viva;
revisor independiente Fable. P7/P9/P10/P14; encargo de preservar agua/extremos
y pasar controles sin rebajar tolerancias. Continúa el objetivo, no el run consumido.

## Evidencia y decisión de orquestación

[EXACT] El piloto de dominio seco completo df0c5994… mejoró energía
561.733058929→534.285533905 y no empeoró pendientes; conservó los arrays de
agua y CAP. Su consumidor dio OFFLINE_CANDIDATE_ONLY, pero el postcheck contra
agua visual real encontró4puntos que perdían el margen seco exigido: mínimo
0.001953125m frente al piso invariable0.025m. Queda RETIRADO/REJECTED_OFFLINE.
Evidencia: evidence/navigation/dry-bank-domain-pilot-20261027/analysis y
water-reference-diagnosis. No se compila ni se vuelve a ejecutar ese candidato.

[EXACT] continuous_stream_pilot_v31.py:323-328 cuantiza water a1/512;:337
guarda level=W sin cuantizar. Author y checker nuevos usaban level tanto en
was_dry como en floor. Los4puntos estaban13ticks sobre el agua guardada,
pero el level algo mayor hizo que no se clasificaran secos y perdieran ese
piso. Todos los fallos reproducen ese mecanismo; agua visual-level difiere
entre−0.000975523 y+0.000971529m. No es un problema de tolerancia ni del solver.

El presupuesto anterior está consumido: una candidata y una corrección de test.
Se retira ese artefacto. Como integrador, se abre esta reparación acotada del
contrato con causa aislada y revisión nueva ANTES de ejecutar. No se amplía el
bucle viejo ni se permite un barrido favorable de pesos, cotas o geometría.

## Cambio único

[DESIGN] En NUEVOS scripts autor/consumidor, usar baseline.water[:,0,1] para
clasificar was_dry y construir el piso. Exigir ambas orillas de water con Y
idéntica en cada fila. Usar esa misma lámina guardada en distribuciones q3/q4.
El consumidor sigue sin importar autor ni su máscara: compara archivos guardados.
Level se mantiene byteexacto como dato de procedencia; deja de representar el
agua física cuantizada a efectos del piso. Ninguna otra ecuación cambia.

Mantener fuente original9d8caf0f; prior lineal2.25→18, peso.002/500iter,
dominio2.25<|q|<18, CAP≤6m, lecho≤2.25, bordes±18/XZ/protecciones exactas,
ground+.02, ceilingoriginal, piso seco0.025 y cuantización dirigida1/512.
Ni source anterior ni el candidato rechazado son punto inicial de optimización.

## Puertas, contraejemplos y presupuesto

Una revisión Fable de plan/código. Una implementación de estas sustituciones
con como máximo una corrección de código demostrable. Un candidato≤900s y
500iteraciones. No aceptar identidad, igualdad de energía o pendiente mayor.
El consumidor corregido DEBE rechazar el NPZdf0c5994 por bounds. Añadir mutante
con uno de los cuatro puntos y comprobar la puerta concreta, no solo exit!=0.
Conservar los controles CLI de CAP interior, lecho, waterY, XZ, borde, techo,
no finito, identidad sin mejora, timeout124 y comparación de bytes. Mutante
de zona protegida queda NOT_APPLICABLE porque el kit tiene0puntos en ella.
Mismo intérprete GIS-I; pruebas independientes en directorios propios, hasta
3hijos de pruebas en paralelo, sólo lectura de entradas. No afecta a DayZ.

VERDE offline exige preservación/bounds/retícula y la comprobación adicional
independiente de todos los puntos previamente secos frente a water guardada;
energía estrictamente menor, pendientes físicas máximas no mayores, mismos14XZ
históricos únicamente descriptivos. Solver puede agotar500iter si produce
factible, según contrato histórico; nunca es aceptación por sí solo.

OFFLINE_CANDIDATE_ONLY permite preparar/revisar build de todos los LOD;
REJECTED_OFFLINE obliga a conservar rechazo y localizar mecanismo nuevo antes
de otro plan. No build/NMG/MCP/RAM aquí. Mantener0.801/0.011/2.1,RAM1.10,
dispersión5%,015-45/agua/islas/reserva. Commit/push sólo unidad validada y
evidencia fiel desde public-repo; jamás publicar el candidato como mapa probado.
