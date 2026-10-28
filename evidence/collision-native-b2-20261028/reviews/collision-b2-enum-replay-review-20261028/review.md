**Dictamen: SOUND-with-fixes.** La corrección conserva la evidencia y no reclasifica nada físico, pero tal como está redactada introduce una asimetría que convertiría un futuro valor 2 en "verificado" sin ninguna verificación. Ese es el contraejemplo concreto.

## Qué verifiqué

- La captura imprime 8 en el campo 14 de la primera Q. El report de layer-discovery registra 270 ocurrencias de 8 y ninguna otra.
- La misión sellada usa el mismo símbolo en las dos llamadas Bullet y al emitir la Q. El campo 14 es la conversión a cadena que hace la VM de script de ese símbolo, en el mismo proceso y misma unidad compilada que las llamadas. Eso acredita consistencia intra-proceso, no el entero que recibió el motor ni su semántica.
- El consumidor archivado rechaza en una línea por fila con igualdad estricta a 2. El fixture de tests emite 2 y afirma lista de confusores vacía.
- El receipt de replay preserva el rechazo original, los hashes de las nueve entradas del run y las dos copias archivadas. El binder no escribe nada; lee del root original y el llamador decide dónde va el resultado.
- La declaración archivada contiene un comentario que llama a FIREGEOM "redefinición" de otro miembro. Eso no explica el 8, pero sí muestra que contar posiciones nunca fue un método fiable para este enum concreto. Lo cito como apoyo a retirar la hipótesis, no como causa.

## Contraejemplo contra el plan tal como está escrito

El plan dice "mantener 2 como hipótesis previa documentada y emitir confusor para cualquier valor diferente", y en fixtures "positivo 2 conserva contrato; positivo 8 uniforme produce confusor".

Escenario: una captura futura, con otro scripts.pbo o tras un parche, imprime 2 uniforme. Con el plan actual el consumidor acepta sin confusor y el test de "sólo diagnóstico" afirma confusores vacíos. Nadie habría verificado el mapeo símbolo-entero. El valor 2 quedaría tratado como correcto por el único motivo de coincidir con una hipótesis que la primera captura real ya desmintió. Eso es exactamente "reemplazar una asunción falsa por otra asunción", sólo que ahora latente.

El mapeo es INCONCLUSO para cualquier entero, incluido 2. El confusor debe ser incondicional mientras no exista una verificación independiente del mapeo. La hipótesis 2 puede sobrevivir como texto documental en limits, nunca como rama de código que decide si hay confusor.

## Qué sí hace bien el plan

- Conserva el 8 crudo y prohíbe convertirlo. Correcto.
- Estado final INCONCLUSIVE_DIAGNOSTIC, sin PASS físico. Correcto.
- Uniformidad en 270 y rechazo por deriva. Correcto, y el fixture existente de una sola Q con 3 sigue rechazando porque altera la primera Q y las demás quedan en 2.
- Reanálisis en directorio nuevo, binder sin cambios, hashes antiguos y nuevos contra receipt y sello. Correcto, con la salvedad de que el binder debe invocarse con el root original y el resultado escribirse fuera. Eso ya es compatible con la comprobación de ausencia de result.json en el root.
- No atribuye causa al 8. Correcto.

## Fix mínimo

1. **Parser.** Sustituir la igualdad a 2 por dos comprobaciones: entero positivo y igual al primer valor visto en la captura. Nombres sugeridos: bullet_layer_nonpositive y bullet_layer_drift. Rechazar 0 y negativos es una asunción leve y debe quedar escrita como tal en limits.

2. **Evaluador.** Añadir el confusor native_bullet_layer_ordinal_unverified a todas las filas sin condición. Añadir al resultado un bloque con el valor crudo, el símbolo emitido, la hipótesis previa marcada como no verificada y una línea de limits que diga que ni el entero ni la semántica de capa quedan certificados.

3. **Tests.** El test de "sólo diagnóstico" debe afirmar que los confusores son exactamente ese motivo en 270 filas, no lista vacía. Añadir: 8 uniforme acepta con el mismo confusor; 2 uniforme acepta con el mismo confusor; 16 uniforme acepta con el mismo confusor; una Q cambiada rechaza por deriva; 0 y negativo rechazan. Ninguno produce PASS.

4. **Contrato de observación.** Documentar en el consumidor que el campo 14 observa la representación en cadena del símbolo en script, no el argumento recibido por el motor. La única garantía es que Bullet usó lo que ese símbolo signifique en ese build.

## Incertidumbre que permanece

- Identidad histórica de scripts.pbo durante el run: no demostrada, correctamente declarada como límite.
- Si Bullet con ese símbolo consideró las superficies que el experimento asume: no demostrado. El confusor incondicional es lo que mantiene esa pregunta abierta de forma explícita en cada fila.
- Los 47 FAIL y 21 inciertos originales no se tocan.

FIN_REVISION