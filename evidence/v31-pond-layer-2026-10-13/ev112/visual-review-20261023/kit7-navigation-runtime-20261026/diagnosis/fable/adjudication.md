# Adjudicación del diagnóstico

Se conserva el informe tal como lo emitió Fable. Corrección factual: las ocho
muestras del diagnóstico inicial pertenecen a la orilla derecha; cuatro pasan
el umbral y cuatro fallan. La mención a «cuatro de orilla izquierda» es errónea.
La existencia de una sola capa no queda demostrada solo por la consulta nearest.
No se promueven esas inferencias a hechos ni se atribuye locomoción a6801raycasts.

Después de esa revisión se reconstruyó el plano de los polígonos de tres teselas
del propio archivo NM. Reproduce las ocho Y nativas con error máximo4.82e-7m.
Eso localiza la discrepancia en la aproximación guardada. No identifica qué
parámetro interno decidió esos polígonos ni prueba cómo los seguirá un actor.
La propuesta de elevar barreras en Geometry altera transitabilidad y no se aplica.
No se añade ningún parámetro GenParams no verificado ni se cambia la tolerancia.
