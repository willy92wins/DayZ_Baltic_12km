# Ejecución local pendiente de revisión

El ejecutor usa el objetivo y las restricciones del `prepared.npz` final que acepte el revisor independiente. Lee alturas absolutas H. Una sola llamada al solver CP congelado, con 120 s para solve más cierre y techo de 1,5 GiB. El directorio de invocación impide repetir el cálculo.

Tras el solve se convierte una sola vez a float32 y se aplica el cierre determinista D8 ya probado en CP, dentro de las mismas cotas. Este cierre solo asegura el orden de drenaje: no se supone que conserve los cruces P/F ni los conos de pendiente. Se guardan ambas rejillas, raw y closed, y el consumidor debe volver a comprobar todas las restricciones sobre closed. El presupuesto de energía del cierre es el existente; no se introduce amortiguación, búsqueda de pasos ni ampliación del dominio o cotas para obtener PASS.

La salida se llama `unaccepted-candidate-terrain.npz`. No se empaqueta, promueve ni ejecuta en DayZ hasta pasar los consumidores geométrico y de forma. El consumer de cobertura reconstruye L32 desde las cotas absolutas float32 del mismo prepared pinneado; un archivo externo de lower solo se admite si coincide exactamente. La revisión de cotas físicas del prepared es una puerta anterior e independiente del clipper.
