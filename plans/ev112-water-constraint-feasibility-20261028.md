# Factibilidad de forma con agua y protecciones fijas
Estado: PROPUESTO_PARA_REVISION; no habilita otra generación de terreno.
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
