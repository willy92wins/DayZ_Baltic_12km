# Medicion de carga de la base regional V10

Continuacion autorizada de P7/P10 y de `terrain-ai-load.md`. La nueva base
persistida cambia geometria, agua y navegacion; repetir una sola medicion
descriptiva permite detectar una regresion gruesa respecto al baseline.

1. Congelar antes del run la identidad del mundo, agua, NM, mision y ejecutable.
   Mantener el escenario existente de 0/25/100/0 infectados, 25s de asentamiento
   y 60 muestras por fase. Confirmar que su cuadricula y objetivo siguen secos
   y sobre navmesh V10 antes de usarlo. No mover puntos despues de observar el
   resultado para forzar un PASS.
2. Un cliente y servidor propios; observar PID y hora de creacion de cada uno.
   Registrar CPU y memoria a 1s con `sample_server_process.ps1`, sincronizando
   por marcadores de fase. Mantener el lease activo durante todo el ensayo.
3. Usar el verificador existente con `--reference` explicito de V10. El cambio
   solo permite seleccionar la referencia congelada; no altera criterios de
   actividad, poblacion, duracion ni desplazamiento del objetivo.
4. PASS significa medicion completa y poblacion activa. Con actividad insuficiente,
   marcar INCONCLUSO y conservar costes observados. Sin una causa aislada no
   aplicar reducciones de calidad ni atribuir variacion de CPU al terreno.
5. Comparar memoria, ventanas largas y coste de proceso con el baseline,
   exponiendo diferencias de mundo y condicion. No extrapolar a 80-100 jugadores,
   CE, red, persistencia, ciudades o vegetacion aun sin colocar.

El ritmo OnUpdate y su timeslice no son FPS de render. Una revision visual
posterior usara el cliente a distintas alturas/distancias; su aceptacion no se
deduce de esta carga de IA.
