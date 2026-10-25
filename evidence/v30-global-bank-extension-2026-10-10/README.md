# EV93 — selección global, preview compilada y lectura nativa

## Continuación del piloto amplio — cerrada sin candidato

La continuación única desde el estado de solve02 convergió en la iteración10477, pero el cierre float32 falló: una cadena D8 exige elevar un nodo2ULP y el contrato limita1ULP. Resultado `8345bd17` REJECTED_LOCAL_NUMERIC_GATES; candidato inexistente. Consumidor independiente del candidato no ejecutado. Tiempo adicional8.519s; total corregido284.333s; pico1.258GB. Sin cambio de terreno/despliegue ni otra continuación.

Evidencia: [checkpoint de la continuación](real-sector-continuation-checkpoint/manifest.json),16copias exactas/2referencias grandes. Preparación independiente PASS; revisión de fuente SOUND; salida y fallo conservados. La unidad focal Narva y el diagnóstico de cuantización siguen separados y pendientes.

## Estado vigente

La selección `run-02` conserva 499 unidades (332 legadas y 167 crestas), con 30.066 alturas modificadas. El consumidor independiente global pasa 22/22 puertas; el readset de 16.480 entradas permanece exacto. Terreno `6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d`; reporte global `656e676e38817592ed96d13ddeb1693d2a9bead152770256b0b21e665cedf8ec`. La selección no acepta BASE1.0 ni elimina los defectos heredados.

La preview aislada `P:/Mods/@DayZ_Baltic_EV93_SelectedBankPreviewV1` contiene mundo `cb4ffc6b7de96c2e9de5c561ac95497b4310ca6f3ae48c6ddab80f6fcd225ab6` y agua intacta `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`. Pasan 524 teselas afectadas, 975 texturas/7.800 mipmaps y las 5.851 entradas sin cambios; OPRW empaquetado y desplegado exactos.

La prueba nativa de servidor `1ed16d48-1352-4216-b5fe-31c77358b9fc` leyó 4.194.304 vértices y 1.212 puntos, incluidos 1.205 planos. Error máximo de altura: 1,52588e-5 m. Los ocho controles negativos pasan. Snapshot `d8c610f32d3a37b3d16bb5c4cb3ab7734b78b63ee95726e60f768f2a846c239e`, procedencia revisada con 14 vínculos de identidad. Servidor cerrado ordenadamente, lease liberado y banco libre.

No se declara RPT limpio: conserva 24 firmas de error heredadas y advertencias de clases pond. La lectura detecta tres anomalías dinámicas en playa, 23 presencias ausentes y 371 consultas escalares positivas sin flags; no establece una cota universal de onda ni cierra el agua sobre tierra. El render gris continúa sin causa aislada. No se ha reintentado el cliente bloqueado por `desktop_all_black`.

El piloto de relieve amplio está separado en `global-operator-prototype/real-sector-preflight`: sector 256×256, 40.512 variables. El primer solve terminó RESOURCE_LIMIT (265,08 s; pico 1.614.667.776 B) sin candidato ni estado numérico; resultado `eedb911f`. `real-sector-resource-limit-checkpoint` conserva 29 copias exactas y tres referencias grandes. El aislamiento del medidor demostró crecimiento por tipos ctypes recreados; la enmienda `d64ad444` corrige solo esa instrumentación, conserva los límites y establece una única ejecución corregida tras revisión. El nuevo preflight `b7f4295d` contiene los mismos 19 arrays y el mismo NPZ `8a8a1cf8`, bit por bit. La revisión independiente `04177bed` pasó. El solve02 terminó ITERATION_LIMIT a 10.000 iteraciones, 275,81 s y 1.237.434.368 B de pico; resultado `bb988ab0`, estado numérico `edd87171`, sin candidato. Los 47 checkpoints numéricos compartidos con el primer intento coinciden exactamente; la instrumentación no cambió la trayectoria. El estado se conserva para diagnóstico de forma, sin promoción. El foco (840,370) sigue inmóvil en el piloto seco; el respaldo es seed3872/q620. La reproducción local de cuatro celdas obtuvo un margen suficiente conservador de 0,2905600866 m. No es la bajada máxima necesaria: se está derivando el límite exacto mediante clearance dividido por la contribución baricéntrica del foco. No hay todavía una corrección factible certificada.

`selected-checkpoint/manifest.json` conserva 328 copias exactas (36.180.269 bytes), 1.011 referencias a artefactos grandes y 65.552 referencias de lectura con propietario. SHA del manifest: `fe2a9849af33a9e5c7ff1bed3113cfdfe4e5810ed0c01c76a4210d1e107ab9f0`. El reporte global de 75,6 MB se referencia por SHA y resumen; no se duplica. Los árboles generados y junctions quedan excluidos. El recibo adicional `build-selected-output-references.json` (366b7ea3) fija cinco outputs EV93 y sus copias desplegadas; `ev93-render-package-crosscheck.md` (a4bbf855) confirma los modelos de agua problemáticos sin atribuir una causa gráfica nueva.

`real-sector-cached-checkpoint` conserva 24 copias exactas y dos referencias (prepared y estado numérico) del intento corregido. Sus archivos y el checkpoint anterior registran ambos fallos; no contienen un candidato aceptado. La investigación posterior del foco y el diagnóstico del último estado se archivan por separado cuando terminen.

## Historial previo conservado (sustituido por el estado vigente)

**Autoría terminada; candidato global rechazado y sin desplegar.** Las703filas terminaron:340aceptaciones locales,311rechazos,49no autorizadas por preflight y3inconclusas. Candidato37e6d4bd cambia20.201alturas; consumidor ed9a071d falla2de19gates: SUMA de huecos físico/visible<1e-7m². Los restantes gates y las340pruebas locales pasan. BASE1.0 y los defectos heredados continúan abiertos.

El diagnóstico reproduce los tres mayores huecos en ODOL directo, sin diferencia con el índice. Selección determinista de ventanas completas: retirar477,337,5,72,280,288,62,214 deja sumas1.49103e-8m² física y1.49725e-8m² visible. Es primer prefijo que cumple el orden de contribución elegido; no prueba mínimo global. No existe aún candidato filtrado ni PASS del resto de gates sobre ese filtrado.

El plan v2 en E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/crest-extension/EXECUTION_PLAN_V2.md (8a4afc1e) prepara228direcciones de cresta de un eje, sin nuevo solver, y una selección conjunta antes de un único consumidor global completo. El pool queda en cuarentena; no hereda ni inventa un PASS previo. No se ha ejecutado esa extensión.

`layer1-rejected-checkpoint/manifest.json` archiva2402artefactos:55copias exactas y2347referencias SHA. `support-diagnosis-checkpoint` conserva lector, selector y sus informes. Los candidatos/soluciones grandes permanecen externos con SHA. Todo el historial fallido se conserva.

## Preparación previa conservada

- Índice de las 18.024 instancias:883.308 caras físicas/visibles. Consumidor independiente:identidades completas y18celdas de exposición frente a escaneo directo, diferencia simétrica0m². No prueba render.
- Censo de las12.566.533bisagras nativas de todo el mapa. El v1 tenía un error ALL/ANY; v2 lo corrige con9fixtures y preserva v1 rechazado. El censo no etiqueta cada quiebro como defecto.
- Piloto del preflight coincide exactamente con EV90/91 (85variables,43guard,42libres,0unknownsinresolver), sin trasladar esas cifras a otras zonas.
- Primera capa703disjunta:651READY,49no factibles,3inconclusas.39.102vértices libres potenciales (9–81porREADY), antes de la autoría posterior aquí registrada. READY632con soporte de agua/15banco/4interior. No representa toda la superficie.
- Segmento01 conservó406resultados y297errores por límite200MiB de detalle. Segmento02 reusó406 sin recalcular y completó297;356.922.737bytes totales bajo400MiB. La migración cambió únicamente rutas de salida, con fuente/fórmulas constantes.

El plan de autoría aprobado está en `preflight-checkpoint/archive/author-stage-plan.md`:una solución porventana+interpolación analítica propia, pruebas de forma/collar/D8 y consumidor globalEV90/91. Tiempo/errores bloquean promoción; rechazos geométricos conservanB y siguen pendientes. La comprobación del agua escalar va después, en preview aislada; no convertir la oscilación observada0,19325m en un límite universal.

## Evidencia congelada

`preflight-checkpoint/manifest.json` contiene769artefactos,51copias exactas y718referencias externas verificadas. Los detalles y arrays grandes siguen en `E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010`. No cambiar fuentes archivadas para acomodar resultados nuevos.

| Artefacto | SHA256 |
|---|---|
| Índice manifest | c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c |
| Consumidor del índice | b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4 |
| Preflight source | a5a8537fa8b9caf092d6ba7b3d55f1f168f15e3541c242cdcc288065cb40c1cc |
| Piloto exacto | e462259614c5006c80a18175a124c29e7fceb4ae2cb9230b6912a0431429a185 |
| Ledger final703 | 63af108d80d7232d8b919c3940da64e76839d8f0d4c74d42ca8d569117913d3a |
| Inventario independiente | bb9099e359e6650ba84929308575c31578f69fb85f532ccc4cf3b7fd8ae0ecc5 |

No se han reintentado las pruebas gráficas bloqueadas por `desktop_all_black`; no hay lease ni run activo de esta unidad.

## Foco Narva y cierre de orden (10-10, 15:15 UTC)

Foco `(840,370)`: candidato `30d0ed33` baja 0.4580755 m. Consumidor real calculó las ocho puertas de cobertura pero las omitió del agregado; fuente y reporte originales conservados. Suplemento `fab5c76e` recompone las 36 puertas, verifica métricas, 33 fuentes y 8 modelos y rechaza 20 negativos. Composición `a5a5aaa1` reconcilia las 499 unidades y sus deltas, separadas al menos 82 vértices del foco. Cobertura global física/visible permanece ~1.49/1.51e-8 m². Aceptación incremental offline; build y lectura nativa pendientes.

Sector amplio: nuevo cierre determinista de cotas/D8 produce `ec1df1c7`, 36.539 alturas, curvatura −72.974%, cero nuevos mínimos o quiebros >30. Consumidor original `a9112811` conserva FAIL por exigir P completo en dos corredores con datos desconocidos heredados. Suplemento independiente `13f0b58d` distingue cobertura geométrica y preservación exacta de ese déficit: 23 puertas de no-regresión PASS, P9 y mapa abiertos. La unión directa con EV93 falla ocho relaciones D8: no es un candidato integrable. Rebase sobre terreno focal actual y congelación de ventanas ya aceptadas se preparan como unidad nueva.

33 fuentes/resultados y cuatro referencias grandes archivados byte a byte en `focal-and-order-checkpoint/`. Ningún resultado declara cierre de BASE1.0, agua dinámica o render gris.

## EV94 focal compilado (15:33 UTC)

Preview aislada: `P:/Mods/@DayZ_Baltic_EV94_FocalBankPreviewV1`. Mundo `06a5ac0a`, OPRW `ce363588`, terreno `30d0ed33`; agua `3946db8b` exacta. 30.067 alturas respecto a B, 526 teselas regeneradas, 975 PAA/7.800 mips comprobados; 5.851 entradas PBO intactas. Checkpoint exacto de 25 fuentes/recibos y cuatro referencias grandes. Misión de lectura nativa preparada, aún no ejecutada: banco ocupado por prueba externa LFSkateboard. No aceptar visualmente ni cerrar BASE1.0.

## 16:05 UTC — rebase independiente rechazado, diagnóstico localizado

Preflight05 y solve-run-01 completos. El consumidor 4a50c92c terminó full-run-01 con ERROR por comparar cinco artefactos iniciales con seis finales; fuente y recibo preservados. Fix95393c52 separa fuente estática y cinco artefactos dinámicos, con cuatro negativos/positivos PASS. Full-run-02 acaba FAIL_EV94_REBASE_SECTOR_OFFLINE: 14/15 puertas PASS, única regresión de pendiente de una cara. Sin nuevos mínimos, sin nuevos quiebros>30°, máximos de22 sectores no peores; semilla y p99 mejoran; agua/civil/P9/499 ventanas+halo/foco exactos. Candidato3360b1e8 NO integrado ni empaquetado. Luna localiza esa cara y su dependencia antes de corregir. No nuevo solver por tanteo.

Auditoría P desconocido cerrada como contexto, no como aceptación de agua:40 celdas/991m² están dentro de Narva_23/Luga_0, nivel≤0,80 y constructor prevé mar del motor. No son991m² probados de hueco visual; falta consulta runtime local. Script39cbdb48, reporte6ad4cddf, readset estable. Banco externo @LFSkateboard ocupado, sin lease propio ni procesos tocados. Render sigue abierto.

Checkpoint nuevo ev94-rebase-checkpoint:31 fuentes/recibos exactos y3 referencias NPZ externas; conserva ambos full-runs. Relieve seco y contornos húmedos siguen siendo alcances distintos. BASE1.0 no aceptada. Root continúa.

## 16:36 UTC — EV95: sector amplio aceptado offline

Una cota nueva impide bajar (900,446) por debajo de 2,294355 m: dos vecinos fijos hacían que su descenso empeorase una cara. No cambia ninguna otra cota, matriz, protección ni tolerancia. Un solve fresco de 118,98 s y 126 MB produce local88f945b2. Consumidor d111772e / full-run-01 b0b7c872 pasa 17 puertas: 35.991 alturas adicionales, cero pendientes fuera de límite nuevas, cero mínimos nuevos y soporte de agua/civil/P9 exacto. Conserva 499 ventanas+halo y foco. Costo 1930,488 a 667,064; el pico de control de 0,965 m desaparece.

Composición completa 40c174e3, recibo db732d22, verificada con lectura dispersa; fuera del sector y metadatos exactos. Checkpoint ev95-slope-checkpoint: 23 copias exactas y 4 referencias externas. El solve terminó antes de la revisión final de una nueva comprobación del baseline; el consumidor definitivo fue revisado y ejecutado antes de aceptar/componer. Original rechazado 3360 y fuentes previas se conservan.

Build-wide-slope en preparación para @DayZ_Baltic_EV95_WideBankPreviewV1, sin promoción. Banco @LFSkateboard externo ocupado, sin lease propio ni procesos tocados. Borde mojado, extensión al resto del mapa, agua/render y BASE1.0 pendientes. Investigación separada de un límite convexo por cara para el operador general y selección de una orilla alta, sin ejecutar todavía esos pilotos.

## 16:59 UTC — EV95 empaquetado, lectura nativa preparada

Preview aislada `@DayZ_Baltic_EV95_WideBankPreviewV1`: terreno40c174e3, PBO mundo f1a148ca, OPRW03dfa1c3; agua3946db8b exacta. 540 teselas regeneradas, 996 PAA modificados y 7.968 mips decodificados válidos; 5.830 entradas restantes exactas. El lector OPRW confirma identidad compilado/empaquetado/desplegado, no lectura del motor. Los 18.033 registros de objetos siguen exactos.

Misión `BalticEV95WideBankV1.BalticTrial`: 4.194.304 vértices, 1.212 puntos calibrados (69 alturas cambiaron frente EV82), 1.205 planos. Lint escanea 1 fichero PASS. Preflight MCP valida petición con rutas Windows absolutas; no se lanzó proceso porque @LFSkateboard ocupa el banco. El primer preparador falló antes de crear salida por pin obsoleto del verificador; preservados fuente/error, corregidos solo nombres EV95 y hash. Fuente del build no cambió. Checkpoint `ev95-build-checkpoint`: 29 copias verificadas, 2 PBO externos por hash. BASE1.0 y fallos gráficos/agua siguen abiertos.
## 17:06 UTC — operador de pendientes y protección civil global

El piloto sintético acoplado de 64×128 pasa el consumidor independiente (22 puertas): 7.963 variables, 16.002 caras, una restricción de pendiente activa después de float32. Una única resolución: 15,23 s y 65,5 MB; coste 217,93 a 116,89, sin nuevos mínimos ni cambios en fijos. Fuente autor d743f500, consumidor03cb269f, informe4b0fd2a4; checkpoint cone-pilot-checkpoint. El intento CLI sobre una copia no llegó al solver por ruta relativa; el runner del original resolvió una sola vez. Dos errores de forma de arrays del consumidor se preservaron y corrigieron sin tocar gates ni salida. Este PASS no es una aceptación del mapa ni prueba de escala global.

Inventario civil global reutiliza las fuentes firmadas y comprueba directamente los 18.033 objetos B/EV95 iguales. Incluye 124 cadenas, las cinco cadenas cortas que omitía el checker histórico, 41.101 células muestreadas de carretera y 150 de puente. Una corona conservadora de una celda alrededor del muestreo vial protege la franja continua de 4 m: 100.215 vértices fijos. Artefactos PROTO/global-civil-ev95/run-01, máscara46faaf22, recibocdebbbce. No modifica terreno ni demuestra por sí solo calidad vial.




## Continuación 2026-10-10T17:27:41.135153+00:00

- Piloto convexo sintético aceptado solo offline por consumidor independiente: 22 gates, coste217.93→116.89, cono activo, cuantización/cierre sin regresión. Archivo `cone-pilot-checkpoint/`; no significa aceptación global.
- Máscara civil global: 124 cadenas, nueve puentes,100215 vértices protegidos; incluye cinco cadenas cortas antes omitidas. Guarda compilada de agua:883308 caras,523044 vértices conservadores. `global-guards-lod-checkpoint/` conserva fuentes/recibos y referencias NPZ.
- LOD hipotético corregido a factores de la cuadrícula nativa6m:1/2/4/8/16/32. En bbox de cuatro objetos del fallo, factores16/32 suben425/1333muestras de terreno sobre F. No prueba selección real del motor ni causa del render gris. Intento inicial de escalas en metros preservado.
- Oredezh: consumidor geométrico exacto ya corre en todo el núcleo posible121nodos/144celdas incidentes; baseline tiene cero huecos físicos/visibles. Preparación de matrices del piloto y preflight global de recursos en curso; no solve nuevo.
- Banco sigue ocupado por @LFSkateboard ajeno. Sin lease/run propio ni acciones sobre esa sesión. BASE1.0 abierta; no push.
