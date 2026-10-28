# Factibilidad de forma con agua y protecciones fijas
Estado: EJECUTADO_DIAGNOSTICO_VALIDADO; no habilita otra generación de terreno.
Consumidor: ejecutor del siguiente piloto. Deriva de P2/P8/P12/P14 y del
rechazo medido de ev112-small-native-water-pilot-20261028.md.

## Hechos y preguntas abiertas
El único candidato conserva agua, islote, máscaras, otras orillas y pendiente,
pero falla forma y prominencia. La curva objetivo ya tenía4giros>=45°, y la
orilla nativa resultante tiene10. No basta suavizar una spline y proyectarla.
Dos tripletas de intersecciones congeladas retienen giros nativos de88.5354° y
69.0152°. Esto NO demuestra por sí solo imposibilidad del screen simplificado.
En la primera hay un vértice despike; los demás constan en el diagnóstico de
procedencia. No se pueden confundir máscaras históricas con permiso de edición.
La protección derivada de otras cadenas/S6 participa en esos puntos. Se mantiene
sin cambios mientras se estudia. Las protecciones de producto siguen obligatorias.
Tres picos/seis depresiones empeoran; dos Y no modificadas adquieren mayor
prominencia por los vecinos. Un guard limitado al delta de vértices sería falso.

## Alcance del siguiente descubrimiento
[DESIGN] Estudio SOLO LECTURA del terreno original, candidato rechazado, domain,
censo y curvas guardadas. Sin nuevo candidato, solver, MLOD, paquete ni DayZ.
1. Atribuir cada tramo/giros a caras nativas y vértices con procedencia de
   protección: producto/historial, otra orilla, entorno pond, cruces, lado B.
   Conservar IDs completos y hashes; nada de etiquetas por cercanía solamente.
2. Detectar en el censo otras cadenas afectadas por el mismo mecanismo, con
   controles de orilla libre y estructura diseñada; resultado es elegibilidad,
   no aceptación visual ni causalidad histórica.
3. Probar si hay un test geométrico suficiente de incompatibilidad con el
   criterio .25m/45° bajo las alturas fijas. Sólo declarar imposibilidad si se
   obtiene certificado analítico verificable; si no, INCONCLUSO, nunca una
   tolerancia distinta ni eliminación automática de una protección.
4. Relacionar cada nueva prominencia con su soporte de vértices nativo y el
   collar9/15m; discriminar mezcla de borde, rampa interior y proyección del lado.
   Preparar restricciones explícitas de relieve para un eventual siguiente autor.
5. Preparar una propuesta de reparación por clase que respete agua, extremos,
   islotes secos, reservas, Narva y reparaciones previas. Si ninguna geometría
   nativa factible está demostrada, comparar métodos antes de diseñar otro piloto.
   Los cambios de producto requieren decisión humana; mejoras técnicas autorizadas
   requieren plan revisado. No convertir el bloqueo local en PASS ni borrar el caso.

## Control y presupuesto
Implementación del diagnóstico [DESIGN]: formar para cada vértice el mínimo y
máximo ID de cadena cuya celda incidente y vecindad S6 lo protegen. Para una
cadena C existe otra protectora si min!=max o el único ID difiere de C. Contrastar
este índice compacto con conjuntos explícitos independientes en fixtures; no
hacer1030dilataciones de rejillas completas. Atribuir la protección base por
separado, con las mismas máscaras, entorno pond y60m de inventario del piloto.
El censo global registra fracción fija y giros nativos fijos; no certifica todos
los screens. Un certificado suficiente acotado se admite para un anillo completo
con todas sus caras incidentes congeladas y agua fija: sus segmentos son exactos
para cualquier candidato que conserve esas alturas. Ejecutar el screen cerrado
sin cambiar .25/45/60 sólo en esos anillos de hasta512estaciones, reportando los
otros como NOT_EVALUATED_COST. Para la charca parcialmente fija no inferir
imposibilidad a partir de tres puntos. Tiempos/costes nunca se convierten en PASS.
El soporte de prominencia se reconstruye por enumeración de las seis formas
nativas y sus anillos, comparando la extrema local contra el diagnóstico guardado.
No repetir el censo completo de prominencia ni regenerar el candidato consumido.

Revisión Fable5.1 nativo28-10,173.688s, SOUND-with-fixes: incorporar acumulación
de dos cadenas en una celda y centinela vacío, sin reflect; ligar IDs al censo
b6612009(107641segmentos originales). Excluir SIEMPRE la propia cadena C al
calcular fixed_C y exigir igualdad byteexacta de fixed_769 con domain guardado.
La fracción fija usa aristas con ambos extremos protegidos, no conteo de vértices.
Certificados con máximo512segmentos; otra extensión queda NOT_EVALUATED_COST.
Exigir anillo no degenerado y claves incidentes a exactamente dos caras antes
de certificarlo. Controles: anillo fijo que cumple, fijo que falla y libre.
Psutil no está instalado: usar GetProcessMemoryInfo dentro del intérprete,
con identidad os.getpid y medición de pico residente/commit, ya comprobado.
Una revisión independiente del código diagnóstico y hasta una corrección por
repro, antes de la única ejecución sobre el mapa; no se añade candidato de altura.

Revisión de código Fable5.1 nativo: SOUND-with-fixes, 269.860s; una corrección
conjunta consumida antes del censo. Coste global máximo 2.000.000 pares n²,
además del límite por anillo; exclusiones NOT_EVALUATED_COST. Inventario y
dependencias se fijan al contexto guardado, código propio se registra por hash
y se comprueba sin cambios al final. Fallos dejan failure.json; una salida con
resource-stop.json o exit distinto de cero nunca se acepta. La medición final
detiene el watchdog antes de serializar el informe. Testigos recortan coordenadas
igual que el campo padded; anclas fuera del campo se excluyen, como el consumidor.
13 pruebas PASS, incluida comparación exacta de soporte con prominencia productiva
en un campo aleatorio 2048² y 37 puntos interiores/de frontera, para pico y valle.
Queda autorizada la única ejecución diagnóstica; no otra generación de alturas.

Una revisión de este plan y un diagnóstico acotado120s/2GiB, sin iteraciones
de parámetros ni autoría de altura. Medir RAM dentro del intérprete real y
publicar os.getpid junto al proceso lanzado: el venv usa un launcher distinto.
Control negativo obligatorio: el caso actual no puede aparecer como elegible
para ejecución sin señalar sus giros fijos y curva objetivo fallida. Control
positivo: una curva analítica suave con soporte libre no se clasifica imposible.
Cierre: informe con hechos, hipótesis y siguiente plan concreto. Si no hay
certificado, informar límite y continuar las tareas independientes del proyecto;
no consumir otra ronda sobre la misma hipótesis ni pedir al usuario una elección
técnica que pueda resolverse por evidencia.

## Fronteras que permanecen abiertas
La detección/reparación de todos los cruces carretera-agua, puentes, lechos,
ríos y mar sigue pendiente. RAM, cliente, conducción y aceptación visual global
siguen abiertas; C1 SIN REVISAR. El council ampliado conserva su lugar después
del trabajo previo y no se sustituye por este estudio.

## Resultado de la única ejecución
Exit0, sin failure/resource-stop,1030cadenas cubiertas y fixed_769 idéntico al
domain guardado.33anillos FROZEN_SCREEN_CONFLICT,73parciales INCONCLUSOS,
887fuera del certificado por agua pond y37abiertos. Narva292:18/18caras fijas
por Narva,8giros del screen;769:11/94caras fijas,13.83%aristas fijadas,2giros
nativos fijos, sin certificado de imposibilidad. Ninguna exclusión por coste.
9testigos de prominencia reproducen exactamente los valores guardados; los dos
vértices no editados de fila1650,columnas1957/1958 comparten un par
inalterado cuyo máximo1.52128839 queda por debajo del mínimo del anillo1.91483378.
Los soportes afectados deben entrar en el siguiente guard. La atribución a una
etapa del solver no está aislada; no repetir parámetros como si estuviera.
Medición real: PID121212, launcher124000,7.563s, residente402149376bytes,
commit381460480bytes; presupuesto cumplido. Evidencia en
evidence/water-constraint-diagnostic-20261028. No nuevo candidato ni integración.
Siguiente plan separado: ev112-road-water-independent-census-20261028.md,
censo de cruces sin usar los puentes generados como universo. Su revisión manda.
