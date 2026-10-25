# Conducción regional V10, sin piezas de carretera

Extiende foundation-acceptance-next.md §4 y producto P11. Ejecutor/integrador:
sesión única autorizada. No cambia terreno, agua, navmesh ni mods de producción.

Descubrimiento: road-scope.json clasifica 91.457km de ejes elegibles sin
pendiente >6.5%; 15.711km excluidos por proximidad al agua/Narva. Los1443
pares con pendiente alta pertenecen a esa segunda categoría. No llamar a toda
la red terminada ni rellenar cauces para pasar un test. Cruces pendientes son
trabajo de diseño/colocación posterior; se conservan su agua y canales.

[EXACT] BalticFoundationDriveV3.BalticTrial/init.c:54-87 crea/arma/alinea el
sedán una sola vez antes de15s de asentamiento; :121-148 aplica entrada nativa
sin escribir pose o velocidad. verify_foundation_drive.py:72-121 contrasta
ruedas, suelo, corredor, salud, continuidad, destino y parada contra el ASC.
Se reutilizan esas APIs y gates sin ampliarlos después del resultado.

[DESIGN] Nueva misión regional: costa cadena5 (segmento193:427), colinas13
(8:362), sur68 (954:1484, primeros1000m desde20m del extremo). Cada trayecto
en ambos sentidos; separación de puntos2m. Costa25km/h, colinas/sur35km/h.
Seleccionadas por diversidad regional y relieve, no por resultado físico.
Control de acelerador/freno igual al anterior, cambiando solo velocidad
solicitada y umbral de frenado. Se conserva techo300s por caso.

VERDE: seis casos completos; mismos criterios de verify_foundation_drive.py,
incluidos desviación<=3m, todas ruedas sanas, salud sin perder>1, ningún periodo
sin contacto>0.4s, contacto contra superficie<=0.12m, destino<=5m, parada>=5s,
velocidad<=0.2m/s. Curvas y rasantes analizadas antes del arranque; error de
geometría cancela esa ruta, no se sustituye a escondidas. Positivo real y18
contrapruebas del verificador, con etiqueta de alcance regional explícita.

Presupuesto: una ejecución de seis casos (35min tope), más una repetición
acotada solo por fallo aislado del controlador. Si falla terreno, conservar
caso, coordenadas y evidencia para reparación separada. No hacer cambios de
terreno con base en fallo de la sonda. Solo servidor: ningún Computer Use.
Sedán vacío; no acredita conductor humano, tráfico, piezas de carretera,
cruces de agua pendientes ni carga multijugador.

## Enmienda previa al motor: separar calzada central y bordes

El muestreo cada2m abortó la preparación: diferencias laterales máximas de
0.105/0.230/0.174m en costa/colinas/sur. El barrido independiente de1m detecta
1781secciones con amplitud>0.03m de88452, y un par de eje con pendiente>6.5%.
Los peores casos de8m tienen diferencias mucho menores en sus2m centrales;
esto apunta a bordes de curvas, no demuestra un bache bajo las ruedas.

Se conserva el resultado GEOMETRY_FAILED. [DESIGN] Ejecutar exactamente las
mismas seis rutas como discriminador físico del centro del corredor, con todos
los límites de coche originales. Ningún resultado de este ensayo convierte
la anchura8m ni la red entera en aceptadas. El informe mantendrá explícitos
el fallo geométrico y el resultado físico separados. No sustituir rutas ni
modificar terreno antes de medir. Es un cambio del orden de diagnóstico,
no una ampliación de tolerancias ni promoción del candidato.
