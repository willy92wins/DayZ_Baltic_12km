# Conducción física sobre la base V10

Continúa P11: carreteras lisas para conducción vanilla. Este ensayo mide la
rasante del terreno y el puente de Narva, antes de colocar piezas de carretera.
No acredita percepción del conductor, tráfico, tripulación ni carga multijugador.

[DESIGN] Sedán vanilla vacío, piezas nuevas y fluidos completos solo al spawn.
Primero tramo de calibración recto de80m en el acceso oeste; después recorrido
completo oeste–puente–este en ambos sentidos con spawns independientes. Referencia
congelada de solve.json V10, ASC V10 y eje del puente. Velocidad objetivo25km/h.
El controlador solo usa throttle, steering, clutch, brake y gear desde OnInput;
no aplica fuerzas, velocidad, teletransporte, reparación ni cambios de terreno.

Cada caso:15s de asentamiento, arranque, movimiento desde20s; máximo300s,
muestreo0.2s, llegada<=5m y parada<=0.2m/s durante5s. Abortar el caso ante
daño>1, pérdida del motor, desvío>3m o inclinación>30 grados. PASS necesita
movimiento medido continuo (huecos<=0.5s, pasos<=3m), salud y ruedas intactas,
velocidad de crucero>=4m/s durante5s, todas las ruedas presentes y ninguna
pérdida total de contacto>0.4s tras asentarse. Registrar las cuatro posiciones
de contacto y contrastar cada contacto con superficie ASC/tablero independiente
(0.12m); terreno consultado por el motor dentro de2mm del ASC. Medir también
velocidad vertical, pitch/roll y contacto mínimo; no convertirlos en FPS.

Un fallo del controlador se conserva como INCONCLUSO para conducción del mapa.
Una colisión o falta de contacto observada exige discriminar rasante, pose del
puente y control antes de cambiar el terreno. No relajar criterios a posteriori.
El verificador tendrá negativos de falso destino, hueco, salto, daño, flotar,
ruedas ausentes, terreno equivocado y no movimiento; positivo real obligatorio.

APIs leídas en instalación local: P:/scripts/4_world/entities/vehicles/carscript.c
:1303 OnInput y:1980 CheckOperationalRequirements;
P:/scripts/3_game/vehicles/car.c:196–376 controles, ruedas y fluidos;
P:/DZ/vehicles/wheeled/config.cpp:5098 CivilianSedan y sus attachments.
Se comprobará compilación Enforce en el consumidor; CfgConvert solo valida config.

## Correcciones del consumidor, antes de aceptar el terreno

V1 fallo al compilar restas adyacentes a literales numericos. V2 conserva sus
operandos/criterios y separa las restas con espacios; compilo y ejecuto la recta.
La recta paso continuidad, salud, contacto (error maximo2.127mm), crucero12.2s
y parada5.4s; fallo solo la posicion inicial, desplazada unos24cm del punto
congelado. Se conserva el FAIL, sin ampliar el umbral de2cm.

V3 registra posicion despues de CreateObjectEx, orientacion y montaje. Alinea
una vez con SetPosition al punto de spawn original antes de activar la sonda
y de los15s de asentamiento. API leida: object.c:300. No cambia posicion ni
velocidad durante el asentamiento o recorrido. Su referencia y registro son
nuevos; exige de nuevo los tres casos. Las observaciones de colocacion aislaran
en que etapa se desplaza el origen; no inferir el mecanismo interno del motor.
