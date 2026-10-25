# Consumidor físico de los sectores corregidos del Luga

Subpaso de P9/P10 y del plan aprobado de agua/suelo. No cambia el mapa,
la navmesh, la sonda de entrada ni los criterios de aceptación.

Se conserva el eje Luga_0 de navigable_samples.npz, reconstruido uniendo
sus posiciones X/Z en el orden original. Las distancias se calculan sobre
esa polilínea real, sin reutilizar la columna de distancias del productor:
sus longitudes son distintas (16.862,41 frente a 16.931,01 m).

Cuatro sectores, fijados antes del motor: 24–230, 5.850–6.245, 6.280–6.580
y 6.870–7.020 m. Incluyen las proyecciones de los 23 vértices corregidos.
Dos spawns independientes por sector, ida/vuelta. Puntos cada ≤4 m;
profundidad nominal del eje comprobada cada ≤0,5 m. Los vértices corregidos
están cerca del borde: recorrer el eje no mide físicamente todo el ancho
útil de 24 m. El contrato geométrico continuo sigue siendo necesario.

Mundo916948ec, WRPdaca4196, NMeece8e5e, aguae9b52b8c; ASC64d4f160.
Boat_01_Orange vacía con el addon c5414ffe, mismo init de RegionalBoatV3,
solo cambia el nombre del log. No hay cambios de API/algoritmo.
Referente: tools/navigation/prepare_regional_boat_consumer.py:24–48,
missions/BalticRegionalBoatV3.BalticTrial/init.c, consumidor
tools/navigation/verify_regional_boat_consumer.py.

PASS exige END completo, todos los destinos y waypoints, propulsión efectiva,
salud conservada y criterios históricos: intervalos≤0,8s, pasos≤3m,
distancia al eje≤7m, destino≤6m, error de suelo≤2mm. Timeout450s/caso.
Registro parcial o arranque no acreditado = INCONCLUSO, no PASS.
Un fallo de control/timeout no prueba por sí solo defecto de terreno.

Una ejecución inicial, sin repetir ni mover rutas para conseguir verde.
Diagnosticar antes de decidir cualquier segundo intento. Cerrar el run exacto,
liberar lease y archivar logs. Sin aceptación de río entero, tripulación,
barco mediano, giros completos, navmesh de IA o rendimiento multijugador.
