Tengo lo necesario; redacto el veredicto.

**Revisión READ ONLY — plan ev112-kit7-post-load1-diagnostic-20261027 y CLI_FIX**

Fuentes leídas: el plan, block-result.json, launch-redacted.json de la pasada 3, terminal-coordination-receipt.json, joint-result.json, README y censo de payload, censo de detalle, cabecera de inspect_navmesh_v9, verify/test nav8_load1 actuales y la copia congelada 002, verify_nav_config_types, product-spec P7/P13. Además, diagnósticos vecinos de kit7-nav12-rejected que el plan no cita.

## PLAN

**Hechos contrastados.** Las cifras del plan coinciden con la evidencia. Dos pasadas cerradas, tercera rechazada con run_id nulo y foreign true, caja reencolada, ningún run ni lease propio al final. Las medianas de Baltic y Chernarus son las de block-result.json. El PASS nativo 607 con run f6f09de4 está en joint-result.json con ram_measured false. La decisión de conservar INCONCLUSIVE, no rellenar huecos y no usar otro puerto es correcta y coherente con P7, que exige A/B en las mismas condiciones. La pista del MCP sugiere pasar otro puerto; el plan la rechaza explícitamente. Bien.

**Hueco 1, el más importante: el plan ignora un decodificador empírico ya existente.** El plan afirma que inspect_navmesh no decodifica polígonos, lo cual es cierto, pero omite que ya hay una reconstrucción de alturas en el directorio de diagnósticos de Nav12. Ese archivo reproduce la Y nativa de seis waypoints con el abanico de polígonos del propio NM, con residuo máximo del orden de medio micrómetro. Sus límites dicen "layout empírico restringido a estas teselas exactas; no decodificador general". El diagnóstico de teselas asociado declara "offsets de vértices plausibles basados solo en límites". Esto encaja en la categoría "observación binaria" del paso 1 del plan, y ya responde a la mitad del paso 3. Consecuencia: el plan debería partir de ese layout y pedir su validación con fixtures de corrupción, no plantear como abierta la pregunta de si el payload se puede decodificar. Ahorra tiempo del presupuesto de 30 minutos y evita duplicar código.

**Hueco 2: la pregunta discriminante está mal enfocada.** La reconstrucción demuestra que nativo igual a interpolación plana del polígono. Lo que no coincide es polígono frente a carretera: los campos road_y de las muestras están entre medio metro y casi un metro por encima de las Y nativas. La hipótesis contrastable y barata es: los vértices del polígono generado están por debajo del terreno o de la carretera en su propia XY, y la rejilla de 8 m solo reduce la distancia entre vértices. Esto se puede comprobar en lectura comparando la Y de cada vértice con el terreno muestreado en esa XY, para las teselas testigo de los fallos de 12 y 12,5 m y los controles PASS de 8 m en las mismas rutas. El plan debería nombrar esa comparación como el único experimento de lectura del paso 3, en lugar del genérico "comparar alturas nativas con superficies reconstruidas".

**Hueco 3: validación del layout en 8 m.** El layout empírico se observó en teselas de 12 m. Aplicarlo a las 2,36 millones de teselas de 8 m sin los invariantes del paso 3, longitudes, índices dentro de rango, vértices dentro de los límites de tesela, sería la "conjetura" que el plan prohíbe. Hay que decirlo explícitamente.

**Hueco 4: ruta incorrecta.** El plan cita "kit7-nav-detail-census-20261027/result.json". El archivo real está en evidence/navigation/kit7-nav12-rejected-20261027/diagnostics/ con nombre .json directo. Corregir para reproducibilidad.

**Menor.** "Continúa P7/P13": P13 trata la reserva y biomas; su único vínculo es "colisiones/navmesh", así que mencionarlo no aporta y puede confundir. P7 sí aplica. La mención de "todos los waypoints disponibles" es compatible con el censo de 1255/1257/1248 puntos.

No encuentro ninguna promesa de causa, de ahorro de RAM ni de PASS. Los límites 0,801 m, 0,011 m, 2,1 m, RAM 1,10 y 5 % quedan intactos. El council ampliado sigue en cola.

**Veredicto PLAN: SOUND-with-fixes.** Incorporar los huecos 1 a 4; sin ellos el paso 3 reinventa trabajo hecho y no fija el discriminador que falta.

## CLI_FIX

**Causa original confirmada.** El stderr archivado del consumidor muestra ModuleNotFoundError en la línea 5 al ejecutar con Python -I. La copia congelada 002 no tiene el sys.path. El fix actual inserta el directorio del propio script antes del import. Es el directorio tools/navigation del repositorio, no cwd ni una carpeta de descargas, así que no reabre el riesgo que -I cierra.

**Semántica de verify intacta.** Las líneas de verificación son idénticas a las congeladas: filas 0, 2, 3 tipo nativo 0 y texto "1"; fila 1 tipo 2 y "true"; estado PASS_NATIVE_LOAD1_CONFIG con acceptance_eligible false heredado de evaluate. Ningún cambio en controles positivos ni negativo.

**Prueba de CLI real.** Lanza sys.executable con -I, sin shell, en directorio temporal, con tres fixtures. Comprobé los recorridos: expected pasa; old_flag falla en verify porque la fila 0 trae tipo 2; wrong_uuid falla en la cabecera de evaluate. Ambas excepciones son ValueError, capturadas, escritas como FAIL_LOAD1_CONFIG_EVIDENCE y salida 1. La prueba exige acceptance_eligible false en los tres casos, así que no hay agregado falso. Son 8 pruebas unitarias más 1 de CLI, 9 en total. No las ejecuté por el encargo de solo lectura; el PASS es afirmación del ejecutor.

**Hashes.** Las adjudicaciones y frozen-inputs históricos esperan 07af212c…; el archivo actual es 282959a9… en el índice de esta revisión. Correcto no rerunear el harness viejo. Cualquier bloque futuro debe congelar el hash nuevo.

**Nits no bloqueantes.** Los negativos podrían asertar el estado FAIL exacto. "Fresh result required" sigue sin probar, igual que antes.

**Veredicto CLI_FIX: SOUND.**

FIN_REVISION