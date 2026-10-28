# B2A — diagnóstico de oclusores, todavía offline

El censo lee los 2.578.398 objetos y los 5.509 modelos del WRP compilado,
vinculado a su PBO. Incluye los 72 modelos de vegetación omitidos por el
inventario anterior. Ocho PBO proporcionan todos los modelos; no quedó
ningún modelo ni proxy con cobertura desconocida en esta ejecución.

La búsqueda usa los volúmenes transformados de todas las instancias.
Cuatro pueden afectar los rayos estudiados: un haya, un abedul y las
dos piezas contiguas del cauce. Un radio alrededor del centro de los
objetos no se usa para descartarlos.

Los diez puntos centrales originales y sus estados permanecen intactos.
Ocho desplazamientos float32 por central producen 90 estímulos diagnósticos.
El origen bajo de cada grupo conserva max(H,B)+2; la separación mínima
respecto al terreno interpolado de los 90 puntos es 1,998040845 m.
Las envolventes de todos los componentes quedan separadas de esos orígenes
bajo las dos hipótesis de marco estudiadas: vértices crudos y vértices más
bounding_center, ambos transformados por la matriz WRP.

**CLEAR_UNDER_FRAME_HYPOTHESES no certifica un origen nativo libre.**
Los marcos del motor, la animación, los objetos dinámicos y la equivalencia
con Bullet no están certificados por este cálculo. Las envolventes convexas
son superconjuntos; una inclusión sólo significaría ocupación posible.
El espacio de terreno se comprueba aparte de los modelos.

Se retienen 1.106 contactos, incluidas duplicidades y ambigüedades de
aristas/vértices. El haya produce los contactos más altos en los tres casos
que devolvían su nombre. Sus diferencias nominales frente a RV son
+0,0000046 m, −0,0022304 m y −0,0039291 m. Las posiciones XZ devueltas
por RV no coinciden exactamente con los XZ nominales; esos valores no
prueban identidad retrospectiva del PBO vanilla ni cierran los fallos.
En 700/723 hay contactos geométricos de arista sobre el lecho mientras
RV original devolvía el terreno: queda preparado un discriminador nativo,
no demostrada la causa de esa diferencia.

La ejecución consumió 31,406 s y un máximo de 520.941.568 bytes residentes (corrida corregida R1).
Los 37 fixtures analíticos y negativos pasan. Fable revisó plan y código;
los hallazgos están adjudicados y la corrección única validada. Se autoriza
publicar este diagnóstico offline, no lanzar B2 nativa sin su propia preparación.
No hubo ejecución de DayZ, build, cambio de geometría ni cambio de tolerancia.

Original2658 conserva 47 puntos FAIL y 21 inciertos. El referente de agua,
las nueve regresiones visuales, RAM y la aceptación global siguen abiertos.
C1 sigue sin revisión humana. El piloto completo de orilla seca sigue
validado sólo offline; esta evidencia tampoco lo integra en juego.

Archivos: report.json (cobertura/paquetes/recursos), models.json (metadatos),
poses.json (matrices y bounds por marco), points.json (90 pruebas de separación),
hits.json (todos los contactos), native-central.json (referente congelado),
snapshot-pose-comparison.json (comparación descriptiva con B1) y
central-comparison.json. No se distribuyen recursos PBO/P3D de terceros.


## Precisiones de la revisión

Los 1.106 contactos pertenecen a raw. plus_bounding_center no produce contactos
y aporta 360 exclusiones por AABB; raw aporta 3.825 pruebas de separación.
central-comparison.json conserva todos los contactos junto a RV y Bullet de
los diez centrales. El máximo sólo se usa para ordenar descriptivamente,
nunca para escoger el resultado más próximo a una altura esperada.

La comparación de B1 busca ahora entre TODAS las instancias del mismo modelo.
De 1.791 apariciones, 1.665 recuperan la misma posición float32 y 126 no son
idénticas bit a bit al reconvertir el texto. Estas últimas difieren como máximo
0,0000005001 m por coordenada, en la escala del redondeo a seis decimales;
no son desplazamientos geométricos de decenas de metros. Se conservan
los residuales y los no idénticos, sin inventar identidad nativa ni pose completa.

La holgura de terreno usa el NPZ fijado. tri_h es compartido con el cálculo
de expected.ground original; no es una lectura independiente de las alturas
del WRP compilado. La corrida R1 conserva byte a byte puntos, separación,
contactos, poses candidatas, modelos, proxies y centrales de la primera.
La corrección sólo añade transparencia y corrige la comparación de snapshots.
