# Aislar la discontinuidad temporal del sector 3 del Luga (casos 4/5)

**Actualización tras verificación completa:** también el caso5 tuvo una pausa
de11,046s después de la observación parcial. Los casos4/5 fallan exclusivamente
`monotone_continuous_clock`; todos los demás checks pasan en ambos, y seis
casos pasan íntegros. El intento adicional queda fijado a **4 y5**, ambos sentidos
del mismo sector, conservando las rutas y criterios. Misión Cases45V2 y referencia
`cases45-isolation-reference.json`, congeladas antes de lanzarlo. La preparación
Case4V2 anterior no se ejecutó. Un solo run adicional; ninguna imagen/build/CU
concurrente propia. No atribuir la pausa posterior al preparador ya detenido.

Continuación del mismo consumidor P9, sin editar terreno ni cambiar criterios.
Run inicial d0f7811a completo: caso4 con hueco de3,435s y caso5 con11,046s frente
al límite0,8s. Casos0–3 tenían máximos0,726/0,573/0,581/0,583s. El proceso propio
de preparación de imágenes coincidía con el primer hueco y fue interrumpido;
memoria libre antes1,12GiB, después2,53GiB. El segundo hueco fue posterior a la
parada de ese proceso. Contención es hipótesis, no causa aislada.

Antes de lanzar, terminar y archivar la ejecución inicial y verificarla íntegra.
Solo ejecutar este discriminador si los casos4/5 fallan continuidad temporal
y conservan llegada, salud, waypoints, suelo e inputs. Otros fallos requieren
diagnóstico antes de reintentar. Nunca reclasificar como PASS el registro inicial.

Una ejecución aislada adicional de los casos4/5, spawn independiente y los mismos
waypoints congelados. Mismo mundo916948ec, aguae9b52b8c, NMeece8e5e y controlador
c5414ffe. Misma lógica de misión salvo inicio en4, final tras5 y fichero de log nuevo.
Sin cálculo de rásteres, build ni CU durante el recorrido. Resto del escritorio
compartido no está bajo nuestro control; no equivale a un ensayo de rendimiento.

PASS aplica todos los criterios originales, incluido0,8s/3m, sin mover extremos.
Un PASS posterior acredita ese recorrido aislado; no demuestra causalidad de la
pausa ni navegación de flotas, todo el río o barcos medianos. Un segundo FAIL se
conserva: no hay más reintentos autorizados por este subplan. Cerrar run exacto,
liberar lease y registrar ambos resultados.
