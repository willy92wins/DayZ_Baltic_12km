# Auditoría regional de agua y render

P2/P3: conservar la distribución de agua y el closeup de San Petersburgo.
Narva ya tiene corrección visual y cruce medido; su sonda de agua fue local.
No extrapolarla a la región. Esta fase solo observa el paquete5030cb74.

[DESIGN] Congelar una cuadrícula regional de1024 puntos y muestras densas en
localidades ya georreferenciadas, más Kronstadt/Shlisselburg/Mshinskaya de los
datos OSM existentes. Clasificar contra los polígonos de mar/agua y WorldCover;
tierra interior conservadora: fuera de agua, a más de24m de sus bordes y clases
10/20/30/40/50/60. Excluir humedales90 de la afirmación de tierra seca.

Sonda de misión de solo lectura: SurfaceY, SurfaceIsSea/Pond, GetWaterDepth y
rango de mar; APIs en P:/scripts/3_game/global/game.c:1162,1174-1187.
Comparar cada altura con ASC nativo actual por el registro ya medido.
Capturas de cámara independientes para San Petersburgo/Kotlin/Neva/reserva.
No derivar agua física del color del satélite.

PASS acotado: alturas nativas coinciden y ningún punto terrestre interior
conserva profundidad positiva o cota inferior al máximo del mar observado.
FAIL: punto seco interior inundado; documentar coordenadas/evidencia antes de
proponer corrección regional. INCONCLUSO: log incompleto o discrepancia de
registro. No modifica relieveZ, costa, lagos ni navegación. Una pasada de
muestreo; no inferir área inundada exacta de puntos ni geografía de las capturas.
