**Veredicto: SOUND-with-fixes.** El plan es coherente con el código real y no abre otra autoría; necesita tres precisiones para que el certificado no sea circular y para que la elegibilidad reproduzca exactamente el piloto.

**1. Índice min/max: reproduce la protección de otras cadenas/S6, con una condición.**
La protección real está en `small_native_water_pilot_ev112.py:95-98`: celdas de todos los segmentos ajenos, `c2v`, dilatación S6. El conjunto de IDs que protegen un vértice v es S(v) = {id : v ∈ S6(c2v(celda))}. "Existe otra protectora" ⟺ S(v)\{C} ≠ ∅ ⟺ (min≠max) ∨ (min==max≠C). Es exacto porque min/max de una unión son min/max de mins/maxs. Condiciones de implementación:
- Una celda puede alojar dos segmentos de cadenas distintas (una por triángulo): calcular min y max por celda con acumulación sobre la lista de segmentos, no asignación directa.
- Operadores de vecindad en modo constante con centinela (inf / -inf). `binary_dilation` usa borde 0; un filtro min con modo reflect daría falsos protectores en el borde.
- IDs ligados al hash del censo b6612009…; sin ese hash la atribución no es trazable.
- Contraste real además de fixtures: para 769, base ∪ índice debe ser byte-igual a `fixed` de domain.npz (hash 427b95…). Es una sola reconstrucción, no 1030.
- La fracción de elegibilidad del piloto se define por claves de arista con ambos extremos fijos (línea 100), no por vértices; el censo debe replicar esa definición.

**2. Certificado de anillo entero: válido, pero hay que definir "congelado" sin la propia cadena.**
Cada segmento depende sólo de las tres alturas de su triángulo huésped y del nivel (`extract_segments`, líneas 181-209). Si cada cara (cell,tri) de `chain_order` tiene sus tres vértices fijos y el footprint no cambia (delta_guard lo exige), los segmentos son idénticos en cualquier candidato. Además cada arista que cruza el nivel tiene un único punto compartido por exactamente dos caras, y `chain()` une por clave y punto, así que ningún segmento nuevo puede adherirse: el anillo sigue siendo la misma cadena cerrada. `closed_screen` toma el peor giro de todas las rotaciones, luego su resultado es determinista. Por tanto "anillo congelado que ya falla .25/45" es un certificado suficiente verificable.

Riesgo circular: la cadena C protege sus propios vértices vía c2v si se usa la protección global. Con ella todo anillo queda trivialmente congelado y todo anillo nativo con giros >=45° aparecería "imposible". El plan debe fijar que "congelado" se evalúa con fixed_C, la máscara construida con C como objetivo (otros excluyen C), que es justamente lo que el índice min/max permite. Para 292 la congelación proviene de la base Narva (18 vértices en máscara), no de otras cadenas; el informe debe etiquetar la clase de protección por cara.

Parcial: `simplify(.25)` es global sobre el anillo; los giros simplificados de un subarco congelado no son invariantes. Es correcto no inferir nada para 769 (pin 0.138) salvo listar sus 88.5354°/69.0152° como giros fijos e INCONCLUSO.

Control positivo propuesto más fuerte que el del plan: un anillo de fixture totalmente congelado cuyos segmentos nativos ya pasan el screen debe salir "compatible exacto", y uno congelado que falla, "imposible". La curva suave con soporte libre sólo prueba que el certificado no se aplica.

Usar `closed_screen` del verificador, no `screen()` del censo, que tiene closure_turn_evaluated=False.

**3. Prominencia por enumeración: suficiente y barato.**
`despike.prominence` usa seis formas (1,2,2,2,3,3 vértices) con anillo = vecinos NB menos la forma; pico = min(forma) − max(anillo). Para cada una de las 9 regresiones, enumerar las formas que contienen el vértice, recomputar la extrema y exigir igualdad flotante con `after` del JSON guardado. Eso es la verificación independiente sin recalcular el campo completo. Reportar qué vértice del anillo determina el valor, si está en MASK y en qué collar (distance de domain.npz). Las dos Y no editadas (1650,1957) y (1650,1958) comparten after 0.39354…, lo que apunta a la misma forma par con anillo editado; la enumeración lo confirmará o refutará.

**Coste.** Varias rejillas 2048² int32 (~16 MiB cada una), censo de 107611 segmentos, screens de ≤512 segmentos: muy por debajo de 120 s/2 GiB. Definir el tope en segmentos, no "estaciones" (pts = segmentos+1). Medir con psutil dentro del intérprete y publicar os.getpid, como ya exige el plan.

**Contradicciones.** Ninguna de fondo. Línea 49 contradice implícitamente la línea 43 si "congelado" incluye a C; corregir. El negativo del plan está respaldado por closed-curve-preflight (objetivo 4 giros, original 19, final 10).

**Cobertura.** Sólo anillos cerrados totalmente congelados reciben certificado; cadenas abiertas, parciales y >512 quedan NOT_EVALUATED/INCONCLUSO sin convertirse en PASS. Correcto y explícito.

**Siguiente paso útil.** Un único script de diagnóstico con tests: fixture de conjuntos explícitos; igualdad byte con fixed de 769; clasificación de 292 y 769; certificado en anillos congelados; soporte de las 9 regresiones con igualdad de valores. Salida JSON con fracción fija, giros fijos y clase de protección por cara; nunca estado PASS.

FIN_REVISION
