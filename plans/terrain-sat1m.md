# Ensayo de muestreo de satélite1m

Resultado previo: capa48m/TerrainX no elimina cuadros; vistas fijas media ylejana
fallan con clima0.1/0/0/0. No aceptar520ef como corrección. RutasPAA compiladas
son correctas, config/navmeshidénticas.

[HIPÓTESIS] La resolución6m/px de la maqueta interactúa mal con el muestreo
distante. VanillaSakhal usaTexGen3=1/512 ytiles512m; Baltic usa1/3072 ytiles3072m.
Es una diferencia candidata, no mecanismo demostrado. La guía del autorTreee
recomienda1m/px; no constituye restricción formal del motor.
Fuente: https://github.com/Treee/DayZDocs/blob/main/MapFrames/DayZGoodMapFrameValues.md
Referente leído P:/DZ/worlds/sakhal/data/layers/p_000-000_l00.rvmat.

[DESIGN] En la rama de ensayoTB ya respaldada, cambiar solo resolución de
satélite6→1m/px (dimensión calculada12288²), mantener terreno2048²/6m,
capas48m,tiles512,solape deseado16,paleta yshaderTerrainX. TB remuestrea
las fuentes georreferenciadas existentes. No se añade detalle real ni geodatos.

Un ensayo de esta configuración. Exigir alturas yobjetos idénticos con
verificadorcontraWRPbaseline; contar materiales desde exportación nueva;
completar slotsvacíos con paleta validada; binarizar yverificar paquete.
Comparar cuatrocámaras yclima fijados; PASS solo con vistaslejanas sin
rectángulos ysin regresión cercana. FAIL→rollbackbaseline; INCONCLUSO si
faltan registros/capturas. Si no corrige, abandonar variación de samplers
yanalizar datoscompilados con un referente funcional. Backup516 previo intacto.

Descubrimiento verificado: TB compacta cada paleta, incluso saltando L01. El helper resuelve cada slot por etiquetas de variantes hermanas y valida las rutas reales antes de completar N; no añade etapas ausentes. Ver sat1m-materials.json.
