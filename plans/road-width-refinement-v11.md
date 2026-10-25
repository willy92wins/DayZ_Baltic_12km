# Afinado de la anchura de carretera, candidato offline V11

Traza: product-spec.md P10/P11/P13. El producto pide rasante progresiva,
sin baches/escalones y agua/reserva conservadas; no colocar objetos ahora.
El paquete V10 y su navmesh permanecen disponibles e inmutables.

Descubrimiento: dense-road-sections-v3.json muestrea17puntos cada0.5m a lo
ancho, cada<=1m a lo largo. Hay6854secciones por encima de3cm de amplitud,
de88452elegibles; el eje tiene un par>6.5%. El antiguo muestreo solo sobre
estaciones del ajuste e izquierda/eje/derecha no detectaba esas ondulaciones.
Los cruces de agua y Narva usan gates distintos y quedan excluidos.

[DESIGN] Piloto sobre las tres rutas ya elegidas para diagnóstico de coche:
costera5, colinas13 y sur68, con50m de margen longitudinal en la misma cadena.
Resolver alturas de vértices en una capa separada mediante programación lineal:
objetivo minimizar cambio absoluto frente aV10; límites iniciales±0.5m;
17puntos transversales, diferencias respecto al eje<=0.014m (amplitud<=0.028m),
pendiente central<=6%, desviación de cuerda6m<=0.022m. Congelar todo lo ajeno
al soporte local, agua, islas y la zona Narva480m. No tocar raster satélite,
objetos, cauces, encuadre, ni la asignación de biomas.

VERDE offline: formato2048²/6m exacto; cambios solo en soporte declarado,
protecciones bit a bit; auditoría independiente a estaciones0.37m distintas
y anchura0.25m; amplitud<=0.03m, pendiente<=6.5%, cuerda6m<=0.03m, ningún
triángulo nuevo>35°. Guardar FAIL si no cumple. Verificar perturbación de
altura fuera de máscara y ondulación intermedia como negativos cuando exista
positivo real. No llamar al solver una aceptación.

Presupuesto: un solve piloto<=120s en un hilo; si es inviable, registrar las
restricciones y parar ese ajuste. Si pasa, extensión a red completa requiere
medir tamaño/coste y nueva referencia antes de ejecutar. Ningún uso de Terrain
Builder ni nuevo navmesh para un piloto parcial. La conducción V10 diagnóstica
se mantiene separada; la versión refinada necesitará importación persistida,
WRP/navmesh propios y prueba física después. Agrupar ese Computer Use final.

## Discriminador de dominio: piloto V12

V11 fue inviable en0.14s y no escribió terreno. La inspección de las matrices
demuestra335restricciones imposibles sobre vértices completamente congelados.
domain-diagnostic.json encuentra86estaciones fuera del dominio seco>48m en
los márgenes de50m, pero ninguna dentro de las tres rutas de coche. El código
no había aplicado la exclusión de cruces de agua prevista en este plan.

Corregir solo ese error de dominio: exigir sección seca>48m y fuera deNarva,
y construir relaciones longitudinales solo entre estaciones elegibles.
Rechazar si se excluye alguna estación del núcleo de las tres rutas. Agua,
islas, límites±0.5m y todas las tolerancias se mantienen. V12 en carpeta nueva,
una ejecución<=120s; si no resuelve, conservar diagnóstico sin más ajustes.

V12 también es inviable, aunque ninguna restricción individual contradice sus
cotas. El bucle de candidatos queda parado. Diagnóstico separado, sin exportar
alturas: tres problemas de factibilidad para aislar anchura, rasante/cuerda y
la interacción con el límite±0.5m. Máximo120s cada uno, un hilo, sin interpretar
un solve sin cotas como terreno apto. Fijar una nueva estrategia solo con ese
resultado; no seguir variando parámetros de un candidato hasta que pase.

## Medir el movimiento mínimo de vértices

El diagnóstico por familias aisló la incompatibilidad entre anchura y cota
de cambio±0.5m; rasante/cuerda solas son factibles y el conjunto sin esa cota
también. [DESIGN] Un único solve diagnóstico minimax, <=120s/un hilo: minimizar
T sujeto a las mismas restricciones y -T<=delta<=T. No exportar ASC ni terreno.
Registrar T, residuo y localización de mayores cambios. Esto cuantifica el
movimiento necesario antes de decidir si el soporte local o la geometría del
corredor necesitan otro diseño; no relaja las tolerancias de conducción.

El minimax midió1.263453m (residuo<5e-16), sin generar terreno. Nuevo pilotoV13:
mantener soporte y restricciones, minimizar cambio absoluto con cota±1.35m,
derivada de esa medida con margen0.0865m. Añadir suelo seco>=1.4m, sin bajar
ningún vértice que ya estuviera por debajo; la cota solo protege los vértices
editables alejados>42m del agua y no cambia cotas de lagos/ríos. Una ejecución
<=120s. Si falla el solve o consumidor independiente, no importar ni repetir
este candidato. No hay cambio de límites de anchura, pendiente o suavidad.
