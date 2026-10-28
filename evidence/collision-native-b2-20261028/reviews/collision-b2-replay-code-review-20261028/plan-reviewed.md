# B2: corregir una hipótesis de enum, conservar la captura

Estado: REVISADO_CON_FIXES, Fable120.281s,28-10. Codex ejecutor/integrador.
Unidad correctiva del instrumento B2, no nuevo experimento ni reparación del mapa.

## Evidencia y límite

Run05130b56-a47b-45d6-bcea-af3a385f0660 produjo270Q/1080R y terminó con
cierre oficial, selfnone y cero órdenes pendientes. accepted16afbdb6… intacto.
consume_bound verificó identidad y después rechazó bullet_layer_changed.
R/collision-b2-replay-inputs-20261028/receipt.json repite sólo la vinculación
de identidad, preserva el rechazo y archiva los dos fuentes que podrían cambiar.
Ningún resultado semántico aceptado aún. Original47FAIL21inciertos intactos.

Hecho: las270Q registran8. La misión sellada usa el MISMO símbolo
PhxInteractionLayers.BUILDING como argumento de ambas llamadas Bullet y al
emitir Q. La hipótesis2 derivó de contar posiciones en una declaración enum.
La fuente dayzphysics.c del scripts.pbo instalado es byteidéntica a P:/scripts:
279ce05c528e467cbf7de820954ee0ce98355d47f8efdd04eca4c5de50d86b07.
La lectura actual no demuestra identidad histórica de scripts.pbo, no sellado
antes/durante el run. No atribuir el8 a versión, remapeo, compilador o corrupción.
R/collision-b2-layer-discovery-20261028/report.json conserva datos y límites.

## Corrección propuesta

[DESIGN] Retirar únicamente la exigencia ordinal2 no validada. Conservar
el entero crudo; exigir que sea positivo y el MISMO en los270grupos. Un cambio
de valor dentro de captura rechaza el contrato. Mantener2 sólo como hipótesis previa
documentada. Emitir native_bullet_layer_ordinal_unverified EN TODOS LOS GRUPOS,
también si el valor es2. El mapeo numérico/simbólico nativo sigue INCONCLUSO; ni los
resultados Bullet ni la coincidencia de capas prueban identidad de superficie.
No convertir8 a2 en el log ni elegir una nueva etiqueta física por conveniencia.
La misión exacta acredita usar el mismo símbolo en llamada y log; el campo14
observa su representación en cadena, no el argumento recibido internamente
por el motor. Estado final INCONCLUSIVE_DIAGNOSTIC. Exigir valor positivo es
una restricción del instrumento, no una certificación de su semántica.

[DESIGN] Reanalizar los MISMOS bytes en un directorio nuevo. Mantener el consumidor
y rechazo originales archivados. Verificar ainputs y dinputs históricos:
para los dos fuentes supersedidos verificar SHA de las copias archivadas contra
el sello original y SHA de la versión nueva contra el sello de replay; TODOS
los demás archivos originales permanecen iguales. Repetir identidad con el
binder sin cambios. Rechazar excepciones extra, archive mutado o código nuevo
sin sello. No editar accepted/deployment/log originales. Nuevo resultado fuera
de collision-b2-native-20261028, con enlaces a ambos contratos y rechazo inicial.

## Fixtures y presupuesto

Una revisión correctiva600s de este cambio acotado; implementar sólo con
veredicto adjudicado. Tests<=120s/2GiB. Positivos2/8/16 uniformes conservan
raw y producen el MISMO confusor, nunca PASS. Cambio8→16 en una sola
Q, cero, valor negativo, captura alterada, archivo histórico alterado, copia
archivada alterada, excepción adicional o fuente nueva distinta rechazan.
Todos los fixtures existentes se mantienen salvo que el valor3 uniforme se
convierta en diagnóstico explícito; una solaQ3 sigue rechazándose por deriva.
Replay único<=120s/2GiB. NO DayZ, no FIFO, no nuevas medidas.
Sin rebajar tolerancias geométricas ni modificar centrales/offsets/estados.
Si surge otro fallo independiente del contrato, conservarlo y revisar su
discriminador; no continuar relajando condiciones hasta obtener verde.

La documentación oficial de enums describe incremento ordinal, pero eso no
resuelve por sí solo lo observado aquí. Se conserva la discrepancia:
https://community.bistudio.com/wiki/Enscript#Enums

Adjudicación: aceptado el contraejemplo de Fable.2 no recibe privilegio por
coincidir con una hipótesis invalidada. No se afirma entero recibido por el
motor. Mantener el rechazo inicial y el código archivado; corrección del
instrumento, no del mundo. Sin nuevo run ni repetición de B2/B1/2658.
