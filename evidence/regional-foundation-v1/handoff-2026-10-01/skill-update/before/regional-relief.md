# Relieve regional sin perder las protecciones

Congela máscaras y prioridades antes de construir el candidato. En Baltic se
mantuvieron exactas agua, humedales, reserva, SPB, piloto Narva y corredores
principales. El perímetro conservador de diseño incluía la reserva OSM y un
margen adicional; no se presentó como límite legal ni como bosque colocado.

Una cota objetivo puede ser incompatible con el espacio entre valles. Aísla
la restricción antes de quitar protecciones: en Baltic quitar carreteras no
recuperaba la altura del sur, mientras que quitar cauces/humedales sí. Se
redujo el objetivo local y se conservaron esas prioridades de producto.

Para limitar pendientes, mide las dos caras triangulares reales de cada
celda del terreno, usando la diagonal verificada en ese proyecto. Un gradiente
centrado puede ocultar pendientes: el candidato Baltic V2 tenía80 triángulos
modificados sobre35°, hasta38.689°, aunque el gradiente sugería menos. El V3
pasó con34.170° como máximo afectado.35° era el contrato de esa capa, no un
límite universal de DayZ ni una prueba de conducción.

## Importar no basta para cambiar el WRP

En el ensayo Baltic, el ASC aparecía importado y guardado, pero el primer WRP
conservaba1.672.627 alturas antiguas. Tras fijar la carpeta aislada del mapframe
y ejecutar Processing > Rebuild terrain, la siguiente exportación coincidió
con los4.194.304 vértices previstos, materiales y tres objetos. No se ejecutó
Generate Layers. Guardar, cerrar, reabrir y exportar a otro nombre produjo
exactamente el mismo WRP SHA256. El resultado anterior se conservó como FAIL.

Comprueba el heightfield exportado, no solo la capa visible. Esta secuencia
es evidencia de ese proyecto; no demuestra que toda importación requiera los
mismos pasos ni identifica todos los mecanismos internos de Terrain Builder.

Fuente: DayZ_Baltic_12km_dev, evidence/regional-outline-v3:
verification.json, native-export-first.json, native-export-rebuilt.json y
native-export-persisted.json. Día30-09-2026, Terrain Builder instalado localmente.

## Precisión del grafo y coste de teselas

Congela puntos, rutas y tolerancias antes de comparar. Baltic mantuvo el WRP,
279 puntos, seis rutas cortas y radio3D de2m. tileWidth50/25/12.5 produjo
26/3/0 discrepancias y2/4/6 rutas válidas. Cambiar solo la configuración no
regenera NM: crear un archivo nuevo ligado al PBO del servidor de datos y
reempaquetar comprobando las otras entradas. No quitar muestras que fallen.

En ese ensayo NM creció31.3/111.7/439.5MB. Dos runs vacíos de120s, sin
data-server, observaron1444/2185MiB residentes para25/12.5. Una pareja en
escritorio compartido no demuestra causalidad de CPU ni capacidad multijugador.
Teselas menores fueron un discriminador útil localmente, no una recomendación
universal ni una prueba del mecanismo interno. Un PASS del grafo tampoco
demuestra locomoción física de IA; comprobarla por separado.

Evidencia: nav-generation*.json, runtime-nav*.json, nav-cost-comparison.json
en evidence/regional-outline-v3 del mismo proyecto. Guardar50/25 FAIL junto al
PASS12.5. El parser local comprueba un subconjunto TESM6/DNAV11, no topología.

## No confundir detección, trayectoria y contacto con el suelo

El consumidor Baltic de colina seguía en estado0 con ruido1× aunque las
consultas del grafo pasasen. Con ruido4× completó las travesías; eso acota el
ensayo de estímulo, no prueba el mecanismo interno ni percepción vanilla normal.
Una restricción lateral4m heredada de un puente de8m rechazaba su trayectoria
por terreno abierto. Conservar ese FAIL. Si el criterio no mide la intención,
explicarlo y congelar un ensayo nuevo antes de ejecutarlo: en V4 se exigió meta
3D<=4m, longitud<=3×directa, contacto con el suelo, salud y continuidad. No
reclasificar el resultado anterior cambiando sus límites después de verlo.

GetMindState devolvió enteros fuera de rango justo después del spawn. No usar
`max(mind)>=1` sobre esos registros como prueba de respuesta. ZombieBase.Init
(P:/scripts/4_world/entities/creatures/infected/zombiebase.c:54) registra rango
-1..4; V4 esperó1s y exigió valores0..4, alguno1..4. Registrar los estados
iniciales sin acreditarlos; probar también el falso positivo con entero enorme.

Evidencia: runtime-chase-tile12p5-v2/v3/v4.json, chase-reference-v4.json y
consumer-v4-controls.json. PASS local V4 con estímulo4×, una cima y un actor;
no se extrapola a caminos regionales ni capacidad multijugador.
