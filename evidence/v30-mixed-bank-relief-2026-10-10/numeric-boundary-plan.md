# Discriminador numérico posterior a EV80 — solo lectura

EV80 está empaquetado y su lectura nativa completa pasa. Su autor rechazó 1275 nodos al cuantizar a float32 junto al límite p99; otros 82 por nuevo >30, 34 por máximo de sector y uno por pendiente. Un rechazo no demuestra imposibilidad geométrica. Antes de autorizar otra pasada hay que distinguir redondeo de restricción real.

Un replay determinista de author-executed.py desde EV79, sin invocar main ni escribir ningún NPZ. Debe reproducir exactamente las alturas EV80 actuales y sus 2591 cambios. Instrumentar localmente solo la devolución del rechazo para guardar propuesta float32/límite/violación. Para cada rechazo float32, evaluar como diagnóstico uno y dos np.nextafter hacia la altura previa; no incorporarlos al replay. Comprobar mediante fórmulas directas las seis pendientes, doce bisagras, límites p99/30/sector, piso, ±2m y beneficio local >=1e-4. No relajar tolerancias ni parámetros.

Máximo 180 s y un replay; si no termina o no reproduce, resultado INCONCLUSO/FAIL sin candidato. Resultado: cantidades y ejemplos de casos rescatables en <=2 ULP, no un mapa ni autorización automática de distribución. La cuestión es el mecanismo numérico de los rechazos, no la aceptación artística ni el motor. EV80 permanece intacto y vigente.
