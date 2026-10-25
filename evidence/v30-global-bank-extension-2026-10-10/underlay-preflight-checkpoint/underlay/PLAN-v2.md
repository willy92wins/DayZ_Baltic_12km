# Propuesta V2: aislar el underlay del terreno en la ROI de agua media

**Estado: diseño offline; no se ha alterado terreno/PBO ni se ha lanzado otra prueba.** Esta revisión sustituye el destino y la dimensión de V1, pero no cambia ni reinterpreta sus resultados.

## Evidencia que fija el problema

V4 corrió sobre el preview `@DayZ_Baltic_IncrementalBankPreviewV1`: paquete de mundo `narva_trial.pbo` SHA `b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c`, agua `baltic_water_v30.pbo` SHA `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`. La captura B `capture_20261010_214159_815.jpg` (SHA `2f729cecd08d8c7e2c41a7ad570a7dc5ef730d56ab9783cde8e2e7770e7891ea`) muestra varias placas grises sobre el agua. El recibo `runtime-receipt.json` (SHA `0b961d635bbaaf477d3bd37f48f0dded103fad108902524799f979b56213df78`) confirma que `Shadows` cambió 0→1 y volvió a 0; `Terrain shadows` quedó en 0. El análisis de V4 (SHA `e6b189e88f094893bce4052b7765197503ec49dd897f977966d72f500f0a06ec`) declara inconclusa la atribución a sombras: hubo `render_frozen_signal`, no hubo lectura de cámara por captura, y la ROI de agua varió tanto en el control A→A2 como en B. Por tanto V4 confirma que el síntoma existe en B, pero no su causa.

La ROI manual V4 `midwater_rect_patch` es `[900,450,1015,515)` en píxeles. Para reducir la deformación a un solo tile y mantener la zona central del rectángulo visible, se fija de antemano su sub-ROI `[918,465,1012,500)`. La transferencia de cámara ya usada en `roi-world.json` (SHA `219abbe1d318bfbdfE4487996a0aa0ea127c0770a32cc95ebfee83fe1de3ce0a`) proyecta ese sub-ROI, en el plano nominal Y=1.825m, aproximadamente a X=2396–2443m, Z=6997–7068m. Está dentro del tile de factor 32 `rows [864,896), cols [384,416)`, es decir X `[2304,2496]`, Z `[6906,7098]`. Es transferencia EV73/EV74, no una calibración por captura V4; el nuevo ensayo debe verificar la pose por captura antes de usar ese ROI. Si la pose no coincide o el gris no está en el sub-ROI de A, se detiene como inconcluso.

El censo coarse anterior no probaba esta zona: sus cuatro bbox WRP están en Z `[6822,6888]`, al sur del parche medio. Allí midió muestras de 1.5m y máximo uplift factor-32 `5.676m`; ese número no sirve como cota para esta intervención.

## Deformación diagnóstica acotada

La única variable de A/B/A será la altura nativa del suelo en un mundo desechable. El baseline A y la restauración A′ usan el B anterior. En B se restan **6.10m** a los `heights[r,c]` de los 1089 vértices inclusivos `r=864..896, c=384..416`; no se cambian las demás capas del NPZ. El WRP del diagnóstico será nuevo y aislado. El PBO de agua, P/F, materiales, objetos WRP, cámara, clima, hora, resolución y ajustes de render permanecen iguales; ambos controles `Shadows` y `Terrain shadows` quedan en 0 en las tres fases.

La caída está calculada contra todos los puntos de agua finitos de la celda completa, no por muestras. Para cada factor anidado `1/2/4/8/16/32` (pasos `6/12/24/48/96/192m`, ancla nativa `(0,0)`, diagonal NW–SE), se evalúa H en cada vértice nativo. P es constante por celda; F son dos planos triangulares por celda con la misma diagonal. La diferencia entre planos es afín dentro de cada triángulo, así que su máximo ocurre en sus vértices: se comprueban los cuatro vértices de cada celda P y los tres de cada triángulo F, para todas las celdas finitas del tile. El reporte [`exact-clearance.json`](v2/exact-clearance.json) da **617 celdas P** y **3810 comparaciones de vértice F por factor**.

La cota máxima de `H_factor−P/F` en el tile es `5.838389612734318m`, en factor 32 y en el borde sur de la celda. El margen ideal sobre P y F nominales es `0.261610387265682m`. Recalculado después del cast float32 real, el mayor `H_factor−P/F` queda en `−0.261610291898251m`; el descenso almacenado por vértice varía entre `6.0999996662` y `6.1000003815m`. El cálculo reproducible está en [`exact_tile_clearance.py`](v2/exact_tile_clearance.py), usando terreno B SHA `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`, P SHA `768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0` y F SHA `f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`.

Este margen garantiza clearance geométrico frente a las superficies nominales P/F para las mallas hipotéticas evaluadas. **No** limita ondas animadas/fake ni demuestra qué LOD selecciona DayZ. Las fuentes inspeccionadas no aportan una API verificada para forzar el LOD de terreno; no se inventa un selector de LOD.

## Secuencia y lectura del resultado

Una ejecución futura usa tres sesiones limpias con el mismo probe/cámara y el orden A → B → A′. Antes de capturar cada fase, se registra SHA del mundo y del PBO de agua, posición/dirección de cámara, viewport y ajustes; los readbacks deben coincidir entre fases. El FOV que devolvió V4 era un stub 0, así que el run solo vale si la cámara fija del perfil se verifica por sus campos disponibles y el ROI gris se observa de nuevo en A. Cada fase guarda capturas múltiples y lectura de actividad; una señal `render_frozen_signal` invalida la comparación.

Se puntúa a ciegas si el rectángulo gris aparece dentro de la sub-ROI fijada. A y A′ deben reproducirlo. Si desaparece solo en B y vuelve en A′, el resultado apoya que la geometría del suelo/una de las mallas de terreno consideradas participa en el artefacto. Si persiste en B, la hipótesis de que el suelo a esas resoluciones sobresale sobre el agua no explica por sí sola el síntoma. Si A/A′ no reproducen el parche, la pose varía, la actividad queda congelada o una pared del borde de tile entra en la ROI, el resultado es inconcluso.

El B altera un tile completo de `192×192m`, incluida parte de la orilla, porque el soporte de la malla factor 32 abarca todo el tile. Es una intervención deliberadamente grande, solo en una copia diagnóstica. Sus paredes de borde pueden cambiar el encuadre/oclusión y se vigilará un ROI de borde como control. Incluso un resultado reversible no probaría que el motor usa exactamente esos factores ni descartaría material, water shader, sorting u otras etapas de visibilidad. El PBO original y su WRP no se sobrescriben; no se promueve este terreno.

## Anclas

- V4 plan/contrato: `E:/DayZ-Baltic-Build/v30-water-render-discriminator-20261010/shadow-runtime-plan/v4-probe/PLAN.md`; recibo y capturas bajo `E:/DayZ-Baltic-Build/v30-water-render-discriminator-20261010/shadow-runtime-plan/v4-probe/runtime/`.
- ROI transferida: `E:/DayZ-Baltic-Build/v30-water-pixel-calibration-20261010/roi-world.json`; su límite de transferencia EV73/EV74 sigue vigente.
- Sensibilidad coarse anterior: `E:/DayZ-Baltic-Build/v30-water-render-discriminator-20261010/coarse-terrain-sensitivity-ev95/native-grid-factors/README.md` y `E:/DayZ-Baltic-Build/v30-water-render-discriminator-20261010/coarse-terrain-sensitivity-ev95/native-grid-factors/report.json`; solo fue un muestreo sobre bbox de objetos al sur, no sobre esta ROI.
- V2 y `exact_tile_clearance.py` son preparación de un discriminador, no evidencia de causalidad ni autorización de build/run.



El bound se puede reproducir con GIS Python ejecutando `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\water-lod-discriminator-plan\v2\exact_tile_clearance.py`. El script prueba además que factor 1 reproduce exactamente la altura nativa en todos los vértices del tile.
