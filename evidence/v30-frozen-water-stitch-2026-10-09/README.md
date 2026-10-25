# Agua visible continua: candidato global y cobertura completa

Preview nueva **@DayZ_Baltic_GlobalWaterV1**, preparada pero todavía no ejecutada en motor. No es aceptación de la base 1.0. HaloFixV3 se conserva como referencia con lectura nativa anterior.

| Contenido | SHA-256 |
|---|---|
| Mundo desplegado | b075de9eaa3c4ad8651f6f37b295843620a1f88fecfb665994fb26d8749acdac |
| Agua desplegada | 95ea4c6c54c868743eddc71b0a59ff31c8418a77ee2f2daf95f6b3a2e249de0f |
| WRP editable | 98b989631bd82588401076d5e54d465fd03acde30511fd3246b321988eed15d0 |
| Terreno, sin cambios | e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c |
| Fuente física congelada del agua | e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1 |

## Qué cambia y qué prueba cada consumidor

El diagnóstico anterior de extensión global usaba por error las clases del terreno actual para recalcular los planos de agua. Dieciocho vértices reclasificados afectaban 56 celdas. La fuente de agua realmente empaquetada seguía siendo e0d35db0. Por ello quedan superadas las cifras del campo conectado y de `EV10/visible-field-domain`; no se invalidan los censos físicos, las lecturas nativas ni las reparaciones HaloFixV3, que sí usaron la fuente correcta.

El campo corregido conserva los soportes de las 538 piezas del piloto y nueve esquinas de una charca pequeña. El consumidor de triángulos nativos conserva las 830 masas significativas sin divisiones, fusiones ni nuevas conexiones, sin perder más del 10 % de intersección en ninguna. Cero nueva agua en caras completamente secas. El máximo sobre la superficie previamente visible es 0,292958 m y sobre la candidata 0,268750 m: el límite de 0,35 m no se ha relajado. Ganancia/pérdida proyectada de orilla: 1.653,650/1.674,173 m²; no es un cambio del nivel físico.

Se modifican 6.419 LOD visibles. Otros 10.493 objetos conservan su geometría; el consumidor independiente de los conservados incluye las 538 piezas del piloto. Los LOD físicos de los modificados son idénticos en fuente y coinciden tras compilar con error máximo 0,000000462 m. Siete franjas de halo usan la prolongación del triángulo contiguo sobre su huella original. Se retiran 18 instancias antiguas de 1 cm por lado: todas tienen cero cobertura de agua prevista; una sobresalía del terreno. Sus modelos compartidos permanecen. No se atribuyen a ellas los grandes reflejos reportados.

Un segundo consumidor recorre **404.484 celdas de agua**, incluidas sus partes triangulares mojadas. Encontró rendijas heredadas de colocación: 0,423726 m² físicos y 0,043507 m² de huella visible. El caso de mayor área aísla 0,117 mm de desfase de centro. Se conservan el fallo y sus polígonos. La corrección añade 1.014 piezas pequeñas, simétricas respecto a centros exactos; en total 10,528 m² de huella bruta con solape de 1 mm, dentro de las celdas previstas. Tras compilar, las posiciones XZ son exactas y no hay agua nueva en caras secas.

La repetición completa da **0 m² físicos sin cubrir** y **3,8464 × 10⁻¹² m² de residuo visible**, con el mismo umbral numérico de 10⁻⁷ m². El control negativo de una rendija de 1 cm falla como debe. Hay 17.926 instancias de agua y nueve puentes. Alturas, materiales, texturas, configuración y objetos de ingeniería permanecen exactos. El archivo de mundo compilado contiene los 13.030 nombres de modelo esperados; solo cambia la entrada WRP respecto al mundo anterior.

## Evidencia y reproducción

`plan.md` registra el alcance y las correcciones antes de construirlas. `preserved-field-audit.json`, `source-seams.json`, `removal-proof.json`, `compiled-verification-r2.json`, `retained-visual-verification.json`, `seam-verification.json`, `global-coverage-final.json`, `package-final.json` y `deploy.json` son las puertas finales. Los JSON/CSV grandes se preservan comprimidos según `preservation.json`; los rechazos se conservan también.

Construcción reproducible externa: `E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009`. Scripts preservados en `scripts/`. Python GIS: `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`. No usar Python global. Los árboles de compilación contienen junctions: no borrarlos recursivamente.

Secuencia: auditar fuente congelada → conservar piloto/charca → autoría visual → compilación → reparación de siete halos y prueba de retirada → verificador compilado → empaquetado inicial → censo de cobertura → piezas simétricas → compilación/verificación → empaquetado final → censo completo → compilación del mundo → despliegue aislado. No ejecutar los scripts de autoría sobre carpetas ya pobladas. El paquete inicial con rendijas queda rechazado y sin desplegar.

## Lo que falta

- La prueba nativa está preparada en `BalticGlobalFullWaterV1.BalticTrial`: 4.194.304 vértices y controles anteriores, cabecera y log nuevos; lint real de un archivo sin errores. `global-fullwater-reference.json` fija archivos y PBO. No se ha ejecutado ni se reutiliza el PASS de HaloFixV3. Antes de lanzar, comprobar hashes y estado del banco.
- El residual gráfico del puente, los tiles a media/larga distancia, la forma global y los finales de río siguen abiertos. El censo de cobertura no explica shaders, LOD ni oleaje. Las rendijas submilimétricas no se equiparan automáticamente a defectos perceptibles en GPU; el aumento de instancias debe compararse en motor.
- El campo de agua cambia la línea visible dentro de sus límites medidos; falta aceptación de las vistas obligatorias. No convertir cobertura offline en calidad visual.
- Windows conserva UDP 2316 del proceso terminado 138984. `server_reload` admitido recicló el worker y no resolvió `port_attribution_unknown`. No hay lease ni runs activos. La reconexión solicitada sigue pendiente; no se han modificado procesos ajenos ni el control de arranque.
- Terrain Builder, Generate Layers y navmesh final van después de congelar la geometría. La navmesh de esta preview se ha copiado sin cambios y no constituye aceptación final de IA.
