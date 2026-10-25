# Corrección del consumidor de rayos

Un control independiente de intersección triángulo/rayo detectó que la primera implementación trataba la entrada lateral bajo una tesela de agua como una pared vertical. En el fixture, devolvía agua a 18,8683 m en vez del terreno a 31,6228 m. Una superficie de agua finita no tiene esa pared.

Se elimina ese caso de oclusión para agua y mar, manteniendo la entrada al terreno continuo. No se cambia el mapa, la proyección estimada ni un umbral de aceptación. `validate_trace.py` conserva el negativo y compara 500 rayos sobre un relieve no coplanar contra triángulos explícitos con un algoritmo independiente.

El primer control negativo de variación temporal pedía terreno >3 m, del que solo había 24 muestras en esta llanura baja. Se sustituye por una banda de primer plano fijada (y de pantalla >=850), terreno >=1,799 m y separación en imagen de las zonas acuáticas. No se utiliza ese cambio para aceptar terreno: se calcula un umbral de candidatos RGB con una referencia de la escena, pendiente de validar en motor.
