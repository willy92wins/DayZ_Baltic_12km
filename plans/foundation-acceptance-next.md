# Continuación de la aceptación de la base V10

Estado de partida: `@DayZ_Baltic_FoundationV10Native`, mundo d1008dd6, WRP
compilado b46c7fce y NM e8348efc. Hashes completos y pruebas en el informe
nocturno. Conservar esa terna y el editable reabierto; no volver a importar
ASC ni generar capas solo para investigar un fallo de sonda.

Producto: P9 cauces navegables, P10 base antes de mapeado, P11 conducción suave,
P12 relieve selectivo y P13 reserva. El trabajo pendiente es aceptación y
corrección demostrada de defectos; no cambiar encuadre ni dilatar SPB.

1. **IA del puente (BALTIC-002).** Control humano sin infectado PASS; persecución
   V1/V2 conserva FAIL por trayectoria del humano. [DESIGN] Registrar estado de
   movimiento/combate del humano y coherencia entre cliente/servidor durante la
   interacción. Verificar firmas antes de instrumentar. No desreferenciar
   GetTargetEntity().GetType(), antecedente de access violation. Un objetivo que
   pierde contacto, corredor o continuidad invalida ese ensayo de persecución.
   Después exigir control local y cruce físico completo en ambos sentidos,
   actor sin escrituras de pose/velocidad, salud positiva, piso real y trazas
   continuas. El PASS de ocho FindPath no sustituye este gate. No relajar FAILs.
2. **Cauces largos (BALTIC-003/004).** Los12tramos visitaron todos sus puntos con
   salud600;9PASS/3FAIL conservados. [DESIGN] Evento por transición de waypoint,
   separado del muestreo físico500ms, y desaceleración antes del punto final.
   Congelar el nuevo consumidor; repetir primero Narva6 y delta8/10 manteniendo
   radios y salud. Si pasa, recorrido continuo/retorno y tripulante. El casco
   mediano necesita dimensiones y ensayo propios; no inferirlo del gálibo.
3. **Render (BALTIC-001).** Repetir solo las vistas pendientes de Neva, reserva,
   sur y conjunto; foco estable y captura dentro del intervalo asentado. La
   imagen tiene que mostrar la región prevista. Telemetría, pantalla negra,
   bruma, menú y otra ventana no bastan. Agrupar CU y liberarlo al acabar.
   La carga directa SPB y7grupos regionales no prueban corregir el crash del
   salto distante Narva→SPB; mantenerlo separado del uso normal del mapa.
4. **Conducción.** Narva medido a26.9km/h ida/vuelta. [DESIGN] Ampliar velocidades
   y sectores de la red preparada sin mover límites después del resultado.
   Las rasantes del terreno no son piezas de carretera ya colocadas.
5. **Carga.** 100infectados locales son una medición acotada. Antes de prometer
   80–100jugadores: escenario representativo de clientes/CE/persistencia y,
   después del mapeado, bosque denso de la reserva y ciudades. El escritorio
   compartido y los cambios de foco impiden atribuir las variaciones actuales
   deCPU/FPS a densidad; definir aislamiento y presupuesto antes de comparar.

Por ensayo: nueva carpeta, referencia previa, positivo real y negativos
pertinentes, límite temporal, log completo y cierre propio. Si el discriminador
no separa causas, resultado INCONCLUSO; cambiar de estrategia, no acumular
variaciones de parámetros. Comenzar el mapeado tras cerrar los gates anteriores
o documentar su aceptación con alcance; regenerar NM después de colocar objetos.
