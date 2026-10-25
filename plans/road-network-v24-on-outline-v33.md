# Carreteras sobre el outline suavizado V33

Petición viva: completar la base, conservar el agua y hacer las carreteras lisas.
Sesión única executor/integrador. Deriva de P9/P10 y del plan de outline; no
incluye piezas de carretera ni edificios. V10 permanece como referencia estable.

## Evidencia y corrección del enfoque

[EXACT] `audit_dense_road_sections.py:13-68`, mismo consumidor a estaciones
de como máximo1m y17offsets sobre8m: V10 tiene1781/88452 secciones con más3cm
de desnivel transversal y1intervalo central sobre6.5%; V33 tiene7261 y147.
Los recuentos son muestras, no baches ni fallos físicos de conducción. Los
recibos fijan ambos NPZ. V33 pasa costa, islas, Narva y agua dinámica local,
pero eso no acepta toda la red de carretera.

[EXACT] `prepare_outline_smoothing_v24.py:50-65`: la protección usa vértices
de carretera y un peso de transición; la elevación de bajos se aplica también
a la carretera. No impone un perfil a todos los triángulos de su anchura.
La atribución de cada regresión a esas operaciones requiere descomposición;
no se afirma que un único término explique todas.

[EXACT] `refine_road_network_v16.py:62-98` construye bandas completas y juntas;
`solve_road_network_v23.py:55-77` conserva un certificado de inviabilidad cuya
combinación elimina las variables libres: aumentar solo el límite de cambio
no elimina el conflicto. El trace V23 identifica seis bordes secos, fuera de
agua/fairways, a31..36m del eje. Abrir únicamente la primera ladera V22 no bastó.

## Candidato acotado

[DESIGN] Reconstruir las mismas bandas y restricciones sobre V33, NPZ
8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a.
Transición uniforme48m alrededor del soporte nativo de la carretera seca,
con envolvente geométrica independiente60.5m. Sustituye las ampliaciones por
rectángulos de V22. Mantener exactos agua+30m, fairways y Narva480m; pisos
de islas intactos. Conservar8m de anchura, gradiente lateral0.0032,
longitudinal6%, cuerda6m<=2.2cm en producción y talud35grados.

Delta máximo6m respecto a V33 y, adicionalmente,6m respecto a V10 en esta
región seca. Esta intersección evita acumular dos excepciones de6m.
No tocar el collar de orilla; todas las restricciones continuas de agua y
los81212puntos deben verificarse de nuevo antes de importar.

Una construcción y una resolución L1 por generación de restricciones;
600s de solver/650s de worker,1hilo y guardia RAM2GiB. Cada iteración examina
la matriz completa. Si falla, preservar certificado/timeout y explicar el
conflicto; no ampliar cotas automáticamente ni declarar terreno preparado.

## Aceptación

PASS offline exige consumidor distinto del productor: secciones cada0.37m,
laterales cada0.25m, transversal<=3cm, pendiente<=6.5%, cuerda6m<=3cm,
ninguna regresión fuera del tramo, dominio/deltas/agua/islas/reserva, geometría
finita y taludes. Controles negativos deben rechazar agua modificada, salida
de dominio, pendiente y discontinuidad. La referencia no se mueve para pasar.

Solo después: editable aislado, dos exports tras reapertura, alturas/materiales/
poses verificadas, nueva navmesh, consumidor regional, conducción y carga.
El pipeline de poses relativas de V33 conserva literales y cualquier derivado
por separado. Ningún PASS de cálculo equivale a importación ni prueba física.
