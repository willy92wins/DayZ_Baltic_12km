# Estado al 2026-10-01T17:21:34.793050+00:00

## Checkpoint V33 — navmesh y agua comprobadas; carreteras pendientes

La petición sigue siendo terminar terreno y navmesh, suavizar el contorno y evitar
agua intermitente en tierra. Computer Use se detuvo por Escape físico del usuario;
no hubo más uso del escritorio. DayZ se cerró ordenadamente, lease liberado y
session_status confirma sin procesos propios ni ocupación. Neva quedó sin captura
y con protocolo de cámara incompleto: su FAIL permanece guardado.

Candidato aislado @DayZ_Baltic_OutlineV33: mundo SHA256
38ebe847b5dd553ac31bd0d51bd9d1c192965352a8a04188b7bdcef5c8eaea0c,
WRP compilado 2ccb8dc4b34d3064100d130a2421ebd77d3f3fcc5ef8a5618c1d7c4221ac92f0.
ASC9d2954fc y referencia8e84d5ce. Importación y reapertura nativas verificadas.
Las exportaciones literales 5/6 conservan670 residuos Y de agua de hasta0.954µm;
el paquete usa un derivado explícito que restituye solo esas Y. No llamarlo
exportación literal. V10 estable d1008dd6 sigue intacto.

Navmesh nueva generada sobre ese WRP:966289/966289 tiles,
446230080bytes, SHA256425b84885d05a588c4c80e0561eb01d02849816f7ff9c0c61f6b49922a4fc842.
Adjunta sin rebinarizar:6826 entradas restantes idénticas.
Consumidor regional V6 PASS:81212 puntos de agua/tierra,0 fallos,
314 muestras de navegación/15 rutas; no equivale a locomoción física completa.
Evidencia: outline-v33-native/, outline-v33-consumer/acceptance.json.

Agua dinámica local PASS:664 épocas/15936 muestras en24 coordenadas congeladas,
20..189.846s, COMPLETE198.006s. Margen seco mínimo0.28706m; profundidad mojada
mínima0.487773m; mar observado0.500012..1m. Positivo real y18 negativos PASS.
No acredita máximo global de oleaje ni todas las orillas.
Evidencia: outline-v33-water/{acceptance,real-negative-controls}.json.
Sur y reserva tienen imágenes originales y protocolos de cámara/restauración
completos. Textura provisional gruesa y franja azul visual siguen pendientes;
no declarar arreglados todos los píxeles. Neva V33 necesita repetición al retomar.
No utilizar sus41 métricas parciales como aceptación de rendimiento.

La auditoría idéntica a1m/17 offsets sobre8m detectó regresión vial:
V10 1781/88452 secciones fuera de3cm y1 intervalo central >6.5%;
V33 7261/88452 y147. Son muestras, no baches contados. El filtro protegía
vértices sueltos y el incremento de bajos incluía carreteras; contribuciones
individuales no aisladas. BALTIC005 y007 siguen abiertos.

Plan nuevo: plans/road-network-v24-on-outline-v33.md. Restricciones congeladas
con247503 variables/9713332 filas y transición48m sobre V33; agua+30m, fairways,
Narva480m y suelos de islas protegidos. Delta<=6m respecto a V33 y V10 para evitar
acumular dos cambios máximos. Solver iniciado a17:16UTC, sesión88223, límite600s
con padre650s/1 hilo/guardia2GiB. Al checkpoint sigue vivo; sin candidato aceptado.
Identidades exactas: road-v24-process-checkpoint.json. Revisar progress.json,
solve.json y resultado de sesión antes de actuar; el estado de progress no prueba
que haya terminado mientras el worker siga vivo. No iniciar otro cálculo igual.

Después de cualquier ASC: consumidores independientes de banda0.37m×0.25m,
hidrología, regiones continuas de costa y81212 puntos congelados, negativos,
reserva/Narva y límites compuestos. Las extensiones de los consumidores a padre
V33 solo están comprobadas sintácticamente; no han validado candidato V24.
No importar ni sustituir paquete sin esas puertas. Si cambia el terreno,
repetir nativo/compilación/navmesh/consumidor y conducción aplicable.

Referencias de la skill local dayz-terrain-workflow actualizadas con persistencia
Y, empaquetado derivado, regresión vial y superficie local de lagos. UTF-8/enlaces
locales PASS; sin validación YAML completa ni nueva skill innecesaria.
No commit: HEAD4ff154b7 y cambios anteriores compartidos preservados. No mapa1.0
ni aceptación global. La automatización nocturna sigue cerrada; ningún reset nuevo.
