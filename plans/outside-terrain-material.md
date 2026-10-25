# Ensayo del terreno exterior — 2026-09-29

La vista regional SPB a1300m conserva un arco blanco al norte, tanto en SAT1M
como con la corrección de agua. [HIPÓTESIS] falta material del terreno exterior.
Referencia leída: P:/DZ/worlds/chernarusplus/world/config.cpp:210–222.
BalticTrial no define OutsideTerrain. Esta diferencia no acredita causa raíz.

Ensayo acotado: añadir solo satellite y Layers.Layer0 (nopx/texture) del referente
vanilla. No añadir enableTerrainSynth ni variar WRP, navmesh, capas o meteorología.
Preparar copia derivada, compilar config, reabrir PBO y exigir que las otras6826
entradas sean idénticas. Comparar configuración descompilada sin el bloque añadido.

PASS visual: mismo encuadre SPB y clima, arco blanco ausente, interior sin nueva
degradación; volver a observar Kotlin/Neva/reserva. FAIL: sigue el blanco o aparece
regresión; retirar variante. INCONCLUSO: cambia cámara/clima/streaming o no carga.
Un ensayo; si falla, cambiar discriminador antes de modificar otros parámetros.

La corrección regional de agua tiene su gate independiente ya PASS en1299 puntos
(751 secos,0 inundados,0 por debajo del máximo1m). No atribuir ese PASS al material.

## Resultado y segundo discriminador

Ensayo material solo: FAIL visual, mismo arco blanco en SPB (outside-view-0.jpg),
pose confirmada y clima0.1/0/0/0. No repetir variaciones de textura.

Fuente primaria DayZ consultada:
https://github.com/BohemiaInteractive/DayZ-Samples/blob/master/Test_Terrain/world/config.cpp
líneas99–111 define OutsideTerrain.enableTerrainSynth=false. Probar ese switch
en una copia con los mismos materiales exteriores. Es un cambio explícito de
generación fuera del límite, no del WRP jugable ni del recorte aprobado. Frente
a la variante anterior únicamente cambia ese valor; navegación propia nueva
en ambas. Si no elimina el arco, la hipótesis del exterior sigue sin confirmar.
