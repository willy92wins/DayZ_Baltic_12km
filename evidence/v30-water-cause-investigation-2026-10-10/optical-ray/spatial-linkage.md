# Enlace espacial del frame EV73 (solo lectura)

**Resultado corregido:** el eje óptico intersecta el plano de agua dentro de la celda r889/c402. Los cuatro vértices y ambas caras de terreno de esa celda son clase 3; todas sus alturas están debajo del mar del motor. Esto liga el centro óptico con la condición agua-sobre-lecho-bajo-mar, sin focal. No demuestra que los rectángulos concretos ocupen ese píxel ni identifica la capa que dibujó el color.

EV73 registra viewport de 1920×1080, cámara (2417,65,6745) y dirección de la matriz look-at (0,−0.3022438586,0.9532306194). El FOV solicitado/aplicado figura como 1.1 y el campo `camera.fov` exporta 0; no sabemos si este cero es lectura o stub, así que no inferimos el FOV real ni reutilizamos el focal EV48.

La consulta se hizo contra EV72 `candidate/terrain.npz` (SHA256 `b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36`) y `plane.npy`, cuya forma es 2047×2047. P[r889,c402]=1.975 m. El eje central `Pcam+t·dir`, al cruzar y=1.975, da t=208.523674549 m y (x,z)=(2417,6943.771151); con `r=floor((12282−z)/6)`, `c=floor(x/6)`, cae en r889/c402, celda NW(2412,6948), NE(2418,6948), SW(2412,6942), SE(2418,6942).

| Vértice | Terreno | Clase | Nivel | Agua/Narva |
|---|---:|---:|---:|---|
| NW | −2.650000 | 3 | 1.975 | 1 / 1 |
| NE | −3.416387 | 3 | 1.975 | 1 / 1 |
| SW | −2.650000 | 3 | 1.975 | 1 / 1 |
| SE | −2.650000 | 3 | 1.975 | 1 / 1 |

La diagonal nativa divide la celda en NW_NE_SE y NW_SW_SE (`tools/terrain/audit_v30_shore_triangles.py:20-32`). Ambas caras son íntegramente clase 3 y todos sus vértices tienen ground≤−2.65 m, más de 3.5 m por debajo del máximo del mar 0.85 m. En la posición exacta del rayo, la interpolación de la cara NW_NE_SE da ground=−2.748500 m, agua por encima en 4.7235 m. El eje cruza, pues, una cara de terreno bajo el mar y una superficie P=1.975 m.

**Límite:** el JPG no lleva las cuatro esquinas de una ROI gris ni coordenadas de píxel por vértice. La captura muestra parches, pero no se debe proyectar la celda central sobre ellos por similitud de color. El punto cercano x2417,z6889 (EV73 point-data) sigue siendo consistente, aunque es otra celda.

**Instrumentación mínima si hiciera falta repetir:** en la misma pose y frame, loguear `g_Game.GetScreenPos()` para las cuatro esquinas de la superficie real de la celda r889/c402 (y=1.975) y para los extremos visibles del puente como control. Marcar una ROI de parche en el frame y comprobar si el polígono proyectado la intersecta. La firma mundo→píxel está declarada en `P:/scripts/3_game/global/game.c:965`; usa la cámara y FOV activos y evita inventar focal. Aun con solape, esto probaría coincidencia espacial, no identidad de fragmento/shader. No se lanzó DayZ ni se editaron código o paquetes.
