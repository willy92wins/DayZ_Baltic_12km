# Adjudicación B3B

Fable5.1,265.485s,SOUND-with-fixes; entradas intactas. Codex ejecutor/integrador.
F1: añadir predicción local float32(MLOD−centro) y residuos. Mantener también
igualdad exacta de caras en mundo float32 como gate fuerte predeclarado; no
rebajar tras observar compilación. Gate de distancia<.001m conserva su límite.
F2: fórmulaODOL+pose y contains estricta se fijan; frontera0 rechaza, subULP>0
no es rechazo por sí solo. Ambos marcos se informan, sin certeza de motor.
F3: campos derivados se reportan porbits y sus cambios no se ignoran.
F4: preflight fresco ejecutado en prism-b3-binary-preflight-20261028. Origen y
copiaarchivada SHA verificados; única diferencia literalr, skill sin editar.
F5: aceptado no recorrer junctions. No es necesario borrarlas: el driver y
consumidor enumeran sólo rutas explícitas. No rglob del árbolbuild ni borrado.
Otros: pin contrato/consumer/original; ODOL desdePBO; mutantes control/pose/orden.

Una revisión de código; dos builds nuevos acotados, consumidor y paquete sólo
si verde. No ejecutar DayZ. No reusar el gate histórico ni modificarlo.47FAIL21
inciertos y demás protecciones intactos. COM/inercia quedan no certificadas.
