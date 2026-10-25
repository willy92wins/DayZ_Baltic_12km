# EV112 — controles de formas artificiales, 25-10-2026

**Verificadores:71/71 tests PASS. Mapa S3: REVIEW_REQUIRED. Sin aceptación visual ni corrección global.**

[MECHANISM VERIFIED] Se han incorporado y ejecutado controles de codos entre piezas, rectas encadenadas, escaleras rotadas y con esquinas redondeadas, picos/depresiones nativos, pirámides anchas y transiciones rectangulares. Los controles negativos incluyen planos, rampas, crestas, colinas redondas, círculos, arcos y meandros. Positivos/negativos y alcance: [fuente de tests](source/test_shape_patterns_ev112.py), [71resultados](tests-final.log), [plan](plan.md).

## Resultado real de S3

- 51sitios declarados frente al original fijado;49construidos.7.606poses WRP comprobadas exactamente por identidad:6.598de cauce y1.008piedras. Se consumen los2.578.822objetos delWRP y se coteja su rejilla con el NPZ.
- 43sitios con hallazgos;42con2.305empalmes de89,8grados.143detecciones de rectas largas y16de escalera.2.305giros de ruta coinciden con los empalmes: **no sumarlos como defectos únicos**. [Por sitio](river-sites.csv), [vistas](figures/river-joins.png).
- Kit-118 y65.0-0 no disparan estos patrones, incluyendo12m de delantal por piloto. Esto no acepta su apariencia ni conectividad.98.0-2 y67.0-0 siguen sin piezas.
- 4.194.304vértices de terreno:366grupos de picos,1.157depresiones y5transiciones rectangulares.40candidatos se etiquetan fuera de los dominios listados en su punto representativo:22picos,17depresiones y1transición. Otros1.309 afectan a charcas o mar. Las etiquetas pueden solaparse y no despejan toda la extensión para editar. [Coordenadas](terrain-candidates.csv), [vistas con exageración vertical](figures/terrain-candidates.png).
- 58.207candidatos y59.804parches en radios12/24/48m; ningún ajuste de pirámide cuadrada/diamante supera el detector. **No equivale a ausencia de facetas**: picos truncados, componentes rectangulares fusionados y otras formas siguen fuera de esa cobertura.

## Revisión y reparaciones

Fable5.1 independiente porCLI: SOUND-with-fixes,617,62s. [Informe original](review-fable/report.md), [recibo e identidad](review-fable/out.json), [adjudicación](review-adjudication.md). TresP1 reparados con regresiones: cadenas cortadas por tolerancia, delantal omitido y cobertura WRP unilateral. También se separa el sesgo del travesaño diagonal slanted, se detectan ápices desplazados/sobre pendiente y escaleras redondeadas. El veredicto de Fable precede estas reparaciones; la adjudicación posterior es de Codex.

Los conectores entre ejes≤0,50m se publican individualmente y solo sirven para analizar patrones; no prueban que haya agua entre piezas. Se conservan3.960diagnósticos de ejes slanted brutos. Lattice solo orienta/ordena, nunca sustituye la geometría de las piezas.

## Reproducción, integridad y pendientes

[Comando y salida2](s3-final-run.json),173,89s. [Informe con hashes](report.json), [POLICYv3](policy.json), [inventario completo de ríos comprimido](rivers.json.gz), [terreno](terrain.json), [manifest](MANIFEST.json). Fuentes y artefactos se releen porSHA al guardar este checkpoint. Las dependencias adicionales se identifican enadditional-dependencies.json. Las salidas preliminares s3-v1/v2/v3 de E:/DayZ-Baltic-Build/shape-gates-20261025 son históricas y no deben usarse como informe vigente.

S3 terreno:6a081028120778d3821574878d4b3845f419c411e661a97d1dc17f3440a4c8a1. WRP fuente:f07926200627c24f26a8da4df54a03df03e5776f92e2821dd676bbb07dab3f77. No se modifica ni despliega geometría oPBO. No hay commit/push: aceptación global abierta y árbol compartido con trabajo previo.

Continúan abiertos: corregir/adjudicar los sitios y coordenadas señalados preservando agua/islas/Narva/015-45; aprobar visualmente los2pilotos antes de expansión; cobertura de siluetas/receptores; bosque de borde3.727discos y sonda preparada; compilado/sonda nuevaS3; conducción/navmesh yA/B Chernarus. No se ha accedido a DayZ MCP en esta ejecución; el estado del banco del24-10 es histórico y debe comprobarse en vivo antes de usarlo.
