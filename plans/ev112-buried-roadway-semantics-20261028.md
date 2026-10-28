# Discriminador de Roadway bajo terreno

Estado: REVISADO_CON_CORRECCIONES_ACOTADAS; preparación y sonda pendientes.
Traza: ev112-dry-road-native-probe-20261028 y revisión Fable143.343s.
El censo leído contiene2658posiciones únicas,1322conlecho<H−0.03m, frente a
cero de esta clase en la sonda anterior6801PASS. Por tanto el max(H,bed) del
consumidor no tiene evidencia nativa para este dominio. No llamarlo regresión
del mapa ni marcar1322casos comoPASS/descartarlos. Una sola instancia19394363.

## Experimento pequeño, antes de la sonda completa

[HIPÓTESIS] SurfaceRoadY3D UNDER puede devolver terreno o Roadway enterrado.
El productor existente mide ambas alturas en servidor; no conocemos su resultado
en este dominio hasta aislarlo. Usar el paquete experimentalef229f32 ya verificado,
mundo10e09e3f/agua97edcafe y un directorio mod nuevo, sin sustituir previewalguna.

[DESIGN] Elegir16centroides interiores:4enterrados de caras modificadas,
4enterrados intactos y8expuestos intactos. Separación |B−H|>0.08m sólo para
discriminar entre las dos predicciones con la tolerancia vigente0.03m;
NO es un nuevo umbral de aceptación del mapa. Agua real a más1m, sin otras
instanciasRoadway en la posición ni flags ambiguos. Selección determinista por
profundidad y su conteo registrado; si falta un grupo, parar antes de desplegar.
Las otras2642posiciones siguen pendientes de la sonda completa, no se descartan.
Los15puntos de frontera numérica y5testigos redondeados fuera de la malla
permanecen registrados; su tratamiento definitivo requiere adjudicación.

Usar coordenadas float32 del round-trip CSV ya descubiertas y las caras reales
del inventarioA para descartar interferencias. Alturas de agua con interpolación
baricéntrica:42triángulos inclinados, cinco instancias, flags0; no asumirplanos.

## Medidas, criterios y límites

Productor sin cambios: BalticVisualProbeV1.BalticTrial/init.c, todas consultas
servidor, sinestado cliente/RPC. Misma22columnas y cargaWRP en el mismoframe.
APIs verificadas game.c:923/1176/1178/1196/1197/1200 y dayzphysics.c:199/211.
Exigir16IDs, reloj creciente, header/BEGIN/END, suelo<=0.01m y seco sinagua.
Expuestos: Roadway y RV aB<=0.03m, identidadRV de piloto. Enterrados: clasificar
Roadway respecto aH/B con0.03m; no asignar PASS al predicado max(H,B) antesdever.
Si coincide conambos o ninguno, INCONCLUSO. RV/Bullet se registran como datos
del discriminador; no aceptar contactoBullet sin calibraciónvanilla fresca.
Resultado válido: SEMANTICS_OBSERVED_AT_SAMPLES, no cierre visual/físicoglobal.

## Adjudicación de revisión independiente

Fable5.1,378.579s,SOUND-with-fixes,0denegaciones,entradas sin cambios.
Aplicar: distancia>1m Y ninguna cara de agua bajo el control; rutas absolutas;
el cierre oficial del run adoptado propio sigue aunque el servidor ya no figure,
registrando el fallo de identidad sin actuar sobre otro run. Una adopción ajena
impide comandos y cierre. Se añade el negativo de proceso desaparecido.
Antes de FIFO, exigir accepted.json con REVIEWED_DIAGNOSTIC_READY y hashes
de deployment.json,prelaunch.json,puntos,código,plan,revisión y pruebas;
revalidar todos los inputs y los cuatro paquetes/ejecutable. La llamada de
dayz_test_run queda detrás de este gate, no basta con comprobarlo al consumir.
Si falla la adopción, conservar el run_id y recuperar sólo mediante acquire
oficial que adopte ese mismo run; no takeover ni intervención sobre terceros.

Una ejecución: preparación120s/2GiB, contrapruebas120s, admisiónFIFO600s,
arranque300s, captura180s. Sin variar parámetros trasfallo. Revisión Fable de
plan/código y positivos/negativos del consumidor antes de la entradaFIFO.
Contrapruebas: IDausente/duplicado, agua en controlseco, suelo/roadwayexpuesto
desviado, enterrado sin predicciónúnica y cambio de manifiesto/paquetes.

Lifecycle oficial, sinconsulta de ocupación ni prelease antesde dayz_test_run;
no takeover. Adoptarsólo run devuelto, heartbeat duranteoperacionesexclusivas,
verificarPID+creationtime+misión+ejecutable+PBO, cierreoficial y liberación.
camera_set vetado. El paquete no obtiene aceptación por arrancar elservidor.

Tras medir, corregir el contrato de la sonda completa según evidencia y revisar
su binder sin tocar las tolerancias. No emitir SERVER_PROBE_PASS si queda
cobertura INCONCLUSA: reportar decisivos y pendientes explícitamente.
