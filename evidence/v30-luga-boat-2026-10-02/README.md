# Luga — consumidor físico del candidato V30

Actualización 03-10 local: el único discriminador Cases45V2 ya se ejecutó.
Run0428d12b: caso4 PASS (máximo0,702s), caso5 FAIL solo reloj0,929s>0,8s;
ambos llegan/frenan, salud600, demás criterios PASS. Evidencia completa en
`runtime-0428d12b/`. Intento consumido; no repetir hastaPASS ni relajar el criterio.
Servidor cerrado orderly_close y lease liberado. El texto inferior conserva
la preparación y los dos bloqueos de disponibilidad anteriores al ensayo.

Mundo916948ec, WRPdaca4196, NMeece8e5e y aguae9b52b8c. Referencia y criterios
congelados antes de lanzar, en `reference.json` y `plans/v30-luga-boat-validation.md`.
Cuatro ventanas del eje reconstruido, ida/vuelta (2.102m sumados). Cobertura de
los intervalos con23vértices corregidos; estos vértices quedan fuera del eje,
por lo que esta prueba complementa la geometría continua y no la sustituye.

## Run inicial d0f7811a

`runtime-d0f7811a/verification.json`: **FAIL_OR_INCOMPLETE**. Los ocho casos
llegaron y frenaron, salud600 constante; seis PASS. Casos4/5 fallan únicamente
`monotone_continuous_clock`: huecos3,435/11,046s frente al máximo0,8s. Pasos
físicos máximos respectivos1,2583/1,3455m. Error máximo de suelo0,000159294m.
3.786muestras, registro finalALL_CASES_COMPLETE; cierreorderly_close confirmado.

El ensamblado propio de imágenes coincidía con la primera pausa y fue detenido.
La segunda pausa ocurrió después. La contención del equipo queda como hipótesis,
no causa aislada. La lease caducó una vez y se recuperó tras comprobar la identidad
del mismo run y la ausencia de otro propietario; no hubo propiedad continua.
Recibos: sampling-interruption.json, lease-gap.json y closure.json.

## Discriminador fijado antes de la ejecución

Un solo intento adicional de casos4/5 con la misma ruta, controlador y criterios,
sin cálculos ni Computer Use propios concurrentes. MisiónCases45V2; referencia
`cases45-isolation-reference.json` SHA256df205b7ad5ecd068e4601a31962d3cbd69314afa6213856280b42a4dbab8d8a4.
La preparaciónCase4V2 anterior no se ejecutó y queda sustituida.
Resultado pendiente; no reclasificar el registro inicial ni repetir hastaPASS.

Las dos esperas de 600s terminaron sin crear un run: primero ocupaba el banco
b573e3af y después3afed8ef. Son bloqueos de disponibilidad, no ensayos fallidos
del terreno. El único intento aislado sigue sin ejecutarse. Al cierre, self none,
pending_commands0 y sin cola propia; los dos recibos de timeout están preservados.

No acredita navegación de todo el río, barcos medianos, pasajeros, flotas,
envolvente completa del agua dinámica ni rendimiento con80–100jugadores.
