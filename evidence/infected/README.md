# IA nativa: aceptación todavía abierta

Mapaebc60f4f, sin modificaciones de WRP/navmesh durante estos ensayos.

1. Noise-v1: crash servidor en la instrumentación ObjectGetType, no en una
   llamada de navegación. Stack en noise-v1-crash.txt; script previo conservado.
2. Noise-v2: al retirar GetTargetEntity.GetType, servidor termina normalmente.
   Control local PASS. Etapa oeste→este terminaTIMEOUT en d22.26/lateral8.84;
   sobre vano se desvía del corredor2.5m. No pasa aceptación, aunque responde
   y recorre parte del cruce. Salud100 en este ensayo.
3. Chase-v1: control local PASS. Objetivo humano y ruido asociado; actor atraviesa
   parte del vano, vuelve hacia oeste y muere antes de completar etapa1.
   Cierre normal del servidor/cliente; causa de la muerte no aislada. No se
   registró la trayectoria del humano, así que su posición solicitada no prueba
   que permaneciera allí. No atribuir muerte/retorno a navmesh sin discriminarlo.

El presupuesto de una ejecución y dos reparaciones se agotó. No seguir variando
el estímulo ni ampliar tolerancias. Próximo experimento, si se aborda IA: un
objetivo humano nacido directamente en su posición (sin recolocación entre
etapas), registro continuo de ambas entidades y eventos de daño, una dirección
por misión. Separar destino real, selección de objetivo, ruta y colisión.

El verificador recomputa eje/lateral desdeXYZ y exige continuidad, puente y
finalización. Fixture independiente y negativos: truncado, no final, NaN,
teletransporte y paso bajo el tablero. Cinco tests pasan. En registros se vio
un entero transitorio no semántico de mente al SPAWN; no usarlo como alerta.

`runtime.json` enlaza runs/cierres. Scripts experimentales fuera de la misión
de entregaBalticBasic. Las consultas de navmesh positivas y la caminata humana
PASS se mantienen como pruebas separadas; no acreditan IA regional ni CE.
