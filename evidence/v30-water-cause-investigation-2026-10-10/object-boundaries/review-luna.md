# EV73: correlación espacial de límites de agua

**Resultado:** dos transiciones visibles de EV73 coinciden con aristas exteriores de P3D `globalvis_*` compilados: la línea lisa→ondulada cerca de `(x=635–780,y≈707)` queda a 0,44–0,46 px de las aristas y la arista superior del parche lejano cerca de `(x=890–936,y≈660)` queda a 1,75–1,79 px. Las aristas proyectadas cubren 145/145 px y 45,28/46 px de las líneas visuales seleccionadas. Es evidencia espacial concreta de que límites entre instancias participan en ambos cambios; no determina por sí sola alpha, profundidad ni shader. Las cajas ROI suministradas son regiones de muestreo, no los contornos visibles.

## Anclajes y método

- Captura EV73: `E:/DayZ-Baltic-Build/v30-base-surface-runtime-20261009/capture_20261009_233431_541.jpg`, 1920×1080, SHA256 `6c441506e2ae34e4f459e63971c59b0f1d3fd614d68497ece04241d6cfd8885c`. Hash comprobado localmente contra la captura; no usé la captura magenta de EV76.
- Calibración EV76: grupo nativo final `101848`; cámara `[2417,65,6745]`, dirección `[0,-0.302244,0.953231]`, FOV de API y `Camera.GetCurrentFOV` ambos `1.1`, viewport 1920×1080. Ajusté de forma independiente centro `(960,540)` y focal `(654.54548,654.54532) px` con 16 puntos nativos; error máximo `0.000054 px`. La validación retenida de EV76 (8 puntos impares) informa error máximo `0.000073 px` en `calibration.json`.
- WRP 0WZD EV71: `E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp`, SHA256 `D89B92AF86F3B376E50B2B0D107A94DD94A380F966CA9C666BA9FBC8D95F88D7`; 18.024 instancias `baltic_water_v30\...` de 18.033 objetos. P3D compilados leídos de `E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30`; PBO registrado por EV76: `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`.
- Para cada objeto candidato transformé la geometría visible LOD0 (resolución 1) por `world = pos + vertices @ matrix` y proyecté sus triángulos. El formato de matriz/ID/nombre coincide con el lector 0WZD (`tools/terrain/wrp0wzd.py:38-50`) y con la transformación de piezas del proyecto (`tools/water/engine_water_model.py:60-72`). El lector ODOL leyó 175/175 candidatos sin excepción; los diez objetos que intersectan los ROIs muestran `scan_fallback` para localizar la tabla de LOD (`odol_reader.py:884-921`), así que conservo ese límite del parser.
- No usé `roi-world.json` como evidencia: el owner informó que lo sobrescribió un análisis anterior y su estado final está pendiente. Las cajas mundiales para buscar objetos se obtuvieron por inversión de la proyección calibrada en plano de referencia `y=2`; la prueba de intersección sí transforma y proyecta vértices 3D de cada P3D.

## ROIs proporcionados

Para el ROI gris `[770,620,860,680]`, la unión de siete superficies proyectadas cubre 5.400/5.400 px²; al sumar polígonos individuales hay 3,99 px² de solape. Cuatro instancias `globalvis_*` aportan casi toda el área: `16800157` 34,5%, `16800158` 28,7%, `16812769` 20,9% y `16812770` 15,4%. `16800156` añade 0,5%; dos `seamfix_*` suman menos de 0,2 px². No intersecta ninguna pieza `edge_*` ni `full_*`. Ningún objeto completo cabe en el ROI: sus lados atraviesan varias piezas.

Para el control ondulado `[470,845,575,900]`, la unión de tres superficies cubre 5.775/5.775 px². `16812763` explica 71,2%, `16812764` 28,8% y un `seamfix_*` aporta una fracción despreciable. Los dos `globalvis_*` comparten una arista que cruza el área del control. Por tanto, tampoco es un control de “una sola pieza”. Estas cifras describen la intersección de las cajas dadas con la malla proyectada; no identifican el contorno de cambio de apariencia.

Ejemplos de cruces entre aristas exteriores de objetos y lados de las cajas, interpolados sobre las aristas 3D:

| Instancia | Cruce en pantalla | Coordenada mundial (x,y,z) |
|---|---|---|
| `16800157` / `globalvis_16800157.p3d` | `(833.54,620.00)` | `(2388.000,2.144,6882.542)` |
| `16800158` / `globalvis_16800158.p3d` | `(770.00,632.38)` | `(2375.239,2.162,6876.000)` |
| `16812769` / `globalvis_16812769.p3d` | `(770.00,658.16)` | `(2378.559,2.185,6864.010)` |
| `16812770` / `globalvis_16812770.p3d` | `(860.00,672.90)` | `(2397.643,2.184,6858.000)` |

## Transiciones visibles medidas en EV73

Elegí visualmente dos segmentos aproximados de la captura y comparé aristas exteriores proyectadas. El filtro exige desviación perpendicular máxima de 2 px, diferencia angular ≤5° y solape longitudinal ≥2 px; descarta aristas que solo cruzan una selección.

| Cambio visible aproximado | Instancia y arista mundial (x,y,z) | Proyección | Resultado |
|---|---|---|---|
| Lisa→ondulada, `(635,707)`–`(780,707)` | `16812771`: `(2358.000,2.2125,6846.000)`–`(2364.000,2.2125,6846.000)` | `(624.93,706.54)`–`(659.00,706.54)` | La unión de segmentos colindantes de `16812770` y `16812771` cubre 145/145 px; offset 0,44–0,46 px, orientación <0,06°. Ambos IDs tienen aristas coincidentes en `z=6846`, desde `x≈2358` a `x≈2388`. |
| Borde superior del parche lejano, `(890,660)`–`(936,660)` | `16812815`: `(2400.010,2.175,6863.990)`–`(2412.000,2.175,6863.990)` | `(876.01,658.25)`–`(935.28,658.25)` | Unión de bordes coincidentes `16812805`/`16812815`: 45,28/46 px (98,4%); offset 1,75–1,79 px, orientación <0,06°. Sus líneas de mundo están separadas ≈2 cm. |

El objeto `seamfix_0906_0397` también cruza la primera línea cerca de `(761,706.5)`, pero solo durante 2,8 px y casi perpendicular; queda excluido como coincidencia longitudinal.

## Interpretación y límites

La alineación paralela, el solape casi completo y la distancia de subpíxel/pocos píxeles en dos transiciones visibles apoyan que límites entre instancias `globalvis_*` se manifiestan como bordes en la captura. El control ondulado comparte la fragmentación, de modo que la partición de malla por sí sola no explica el color gris. Tampoco se ha demostrado qué instancia gana en el render, ni el papel de profundidad, alpha, culling, LOD o shader; la correlación geométrica no es evidencia de draw calls. No cambio de constructor ni candidato productivo se desprende de esta auditoría espacial por sí sola.

## Artefactos

- `intersection-report.json`: proyección, transformación, bounds y áreas por instancia.
- `roi-union-coverage.json`: unión de superficies por ROI, sin contar solapes varias veces.
- `edge-crossings.json`: aristas, cruces en píxeles y coordenadas mundiales corregidas por perspectiva.
- `visible-transition-matches.json`: comparación de los dos segmentos visibles con filtro de paralelismo/solape.
- `actual-transition-edge-match.png`: captura EV73 anotada con las coincidencias; `roi-boundary-edges.png` muestra las aristas dentro de las cajas, no contornos de transición.
- `project_wrpl_water_rois.py`, `edge_crossings.py`, `match_visible_transitions.py`: scripts de diagnóstico; no modifican WRP, P3D ni DayZ.



