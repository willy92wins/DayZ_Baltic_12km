# Sensibilidad offline con factores de la malla nativa — EV95

Estado: sensibilidad geométrica muestreada; no mide el LOD que DayZ selecciona ni establece causalidad.

## Método

- H nativa tiene separación de 6 m y ancla `x=0,z=12282`. Se evaluaron factores anidados 1/2/4/8/16/32, equivalentes a 6/12/24/48/96/192 m. Cada submalla lee solo `height[r,c]` con `r % factor == 0` y `c % factor == 0`; se triangula con diagonal NW-SE y se conserva el mismo anclaje. No hay remuestreo previo de alturas nativas.
- El ROI es la envolvente de bbox visuales WRP para `16812770`, `16812771`, `16812805` y `16812815`. El muestreo usa centros cada 1,5 m; sus máscaras bbox se informan por objeto. Los matrices WRP completos, origen y bbox local/world están en cada resumen por estado/factor. Los bbox no equivalen a footprints de caras.
- B y EV95 se evalúan separadamente. P es por celda y F usa sus cuatro esquinas, trianguladas NW-SE sin promediar entre celdas. Se cuentan puntos donde H nativa está bajo cada superficie y H de la malla factor queda por encima.
- `report.json` incluye todos los vértices de soporte fuera de la envolvente ROI con índices nativos y coordenadas XYZ para cada factor/estado. Son nodos requeridos por los triángulos de muestra, no una afirmación sobre límites de LOD del motor.

## Resultados

Las alturas en muestras de factor 1 son idénticas a H nativa para B y EV95. Readset start/end coincide. El cálculo duró 0,378 s con pico de working set 82.2 MB, dentro de los límites 180 s/512 MiB.

En la unión de bbox, ambos estados producen el mismo conteo observado: para F, factores 2/4/8/16/32 elevan 17/47/17/425/1333 de los puntos que estaban bajo F; máximo uplift aproximado +0,398/+0,773/+0,380/+2,777/+5,676 m. Para P son 17/47/16/425/1334 y máximos +0,396/+0,775/+0,369/+2,777/+5,665 m. Factor 1 no produce cruces. Son resultados de muestras en bbox, con posibles zonas vacías y superficies P/F muestreadas.

## Límites

Esto demuestra únicamente que ciertos remuestreos anidados pueden elevar H sobre P/F en puntos de este ROI. No demuestra que el motor use esos factores, que coincidan con los LOD reales, ni que expliquen tiles grises. Faltan selección de LOD runtime, visibilidad/oclusiones, material/shader y wave state. No se consultó el motor ni se modificaron terreno o PBO.

## Artefactos y verificación

- `analyze_native_grid_factors.py`: fuente. SHA-256 `4bcbbcb011e8de97daa98e6fe601af332fc42eaf9b7768b1afe9647f441a9dca`.
- `report.json`: medidas, readset, coordenadas del soporte, matrices WRP y fixtures. SHA-256 `5470725d4ac0e70eDE3685a06ff8f965451025c2871d6a0139e4dc5ae0699db6`.
- `samples.npz`: muestras H/P/F B/EV95 y submallas por factor. SHA-256 `d7c931c0bf77edd162cbaA88fe6585a2b6d101834a727800151d1110c98156a2`.
- GIS Python: `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe`; `py_compile`, fixtures y ejecución real pasaron.
- El diagnóstico anterior con pasos arbitrarios de 2/4/8/16/32 m permanece intacto en la carpeta padre.
