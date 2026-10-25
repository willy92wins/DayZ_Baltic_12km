# Cobertura fisica prolongada de los cauces V10

Extension de P3/P12 dentro de la sesion nocturna y posterior a los ocho sectores
locales. No cambia terreno, navegacion ni agua. El consumidor completo mantiene
lancha vanilla vacia, propulsor/entrada nativos y criterios del ensayo V3.

Congelar antes del motor rutas trazables a fairways-main-game.json: canal
principal Narva entre Peipus y desembocadura (rama conectada mas corta; puente
por el corredor V3 ya probado), Luga principal completo, Neva principal y cuatro
rutas del delta. No afirmar todas las ramas fluviales ni barco mediano.

Dividir las rutas mayores en tramos de hasta unos3.5km con40m de solape. Cada
lancha recorre un tramo fisico continuo; se puede acreditar cobertura conjunta,
no un viaje unico entre extremos. Salidas separadas60s y mismo sentido para
evitar colisiones introducidas por el ensayo. Hasta12 consumidores independientes
en un servidor sin cliente; registros separados e identidad de cada ruta.

Conservar cadencia de control100ms, muestras500ms, throttle0.22, limite2.5m/s,
corte por perdida de salud/desvio7m y verificador V3. Solo ampliar timeout de450
a4200s por tramo. Para evitar un barrido de miles de segmentos en cada tick,
distancia de seguridad en ventana de24segmentos alrededor del objetivo actual;
el verificador independiente mantiene distancia contra la ruta completa y exige
acuerdo15cm. Una discrepancia falla; no cambiar umbral tras observarla.

Antes de lanzar: geometria simple, continuidad exacta de origen, ningun hueco
entre tramos, profundidad>=3m en puntos cada0.5m y muestras laterales+-4m,
fuentes/mision/addon/mundo por SHA. El motor sigue siendo necesario para aceptar
transiciones entre aguas, propulsor y colisiones. Conservar cualquier fallo
offline en un informe; no desplazar la ruta para esconderlo.

PASS por tramo requiere final completo, todas las posiciones intermedias,
continuidad, salud, propulsion, corredor y superficie real de acuerdo con ASC.
Control nuevo: registros deben cubrir el tramo previsto; omision o intercambio
de logs entre tramos falla. No extrapolar a tripulacion, giro ni navegacion a
alta velocidad. El resultado global exige todos los tramos previstos.

No empezar este ensayo despues de09:00UTC sin acotarlo expresamente al tiempo
disponible. El cierre nocturno sigue siendo10:42:43UTC. Mantener lease/heartbeat;
cerrar solo el run propio mediante lifecycle. Guardar parciales si expira el
plazo. La prueba sintetica de carga y las vistas del cliente son runs separados.

## Correccion del ensamblado de rutas, antes del motor

El grafo que solo usaba extremos de features produjo211 intersecciones entre
segmentos no adyacentes en Narva; partes3/17 ya se retrazaban por si mismas.
Evidencia conservada: full-river-preparation-attempt01.json. Ese recorrido no
se lanza. Se nodifican intersecciones/solapes del linework original y se obtiene
el camino conectado mas corto entre los mismos extremos Peipus/desembocadura.
Cada segmento procede de la union de ejes existentes (con el corredor V3 del
puente ya declarado). Exigir camino simple y ausencia de longitud nueva fuera
de la union, salvo10micrometros de error numerico acumulado. No cambia poligonos,
alturas, agua ni puntos de los ocho ensayos regionales ya congelados.

La concatenacion del delta norte mostro el mismo tipo de retrazado. Aplicar el
camino simple sobre su propia union, conservando extremos y registrando longitud
original y resultante; sin seleccionar puntos nuevos fuera de los ejes.
