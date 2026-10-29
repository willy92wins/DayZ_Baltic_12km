# Q02B2 — trasladar el núcleo certificado a contornos reales

Estado: BORRADOR_PENDIENTE_DE_REVISION. No autoriza código, censo o reparación.
Sigue Q02B/P14 y el council, después de Q02B1. Su contrato numérico se conserva;
no añade umbrales de naturalidad ni vuelve a generar Q02A/Q17A/Q02B0.

## Problema y fuentes

Q02B1 verifica 53 consultas propias, incluidas degeneraciones, fronteras y un
control deliberado de agotamiento de recursos. No midió las 538390 ventanas del
mapa. El kernel reconstruye aristas y prefijos por consulta; copiar ese patrón
al censo repetiría trabajo y puede superar 100000 operaciones por consulta.
El coste observado en fixtures pequeños no demuestra capacidad sobre la cadena
de 13421 puntos. No ampliar caps ni deducir una duración global por regla de tres.

Fuentes fijadas: native-shore.npz b661; discovery Q02B0 98adb3e8 (magnitudes);
Q02B1 contrato R1 4162c53e, aprobación y reportes de
evidence/certified-shore-kernel-q02b1-20261029. Los dos módulos Q02B1 se leen como
primitivas verificadas, no se relanzan sus CLIs consumidos ni se modifican.

## Diseño a revisar [DESIGN]

Separar una certificación por cadena (aristas, longitudes y prefijos) de las
consultas. Reutilizar por identidad los testigos enteros ya comprobados dentro
de esta nueva ejecución, con un presupuesto propio explícito de precomputación.
Cada consulta sigue teniendo 4096 bits y 100000 operaciones, p48 y umbral
binario estricto de 1e-8. Un cache no permite omitir el binding a la cadena,
orden, cierre y coordenadas; mutar un punto debe invalidarlo.

Hay una decisión numérica por cerrar ANTES de código: restar prefijos globales
intervalares crea envolventes distintas de sumar aristas dirigidas desde cada
ancla. Ambas pueden ser conservadoras, pero no son bitidénticas. Comparar sus
extremos por una tolerancia inventada o escoger la envolvente más estrecha sin
prueba no es válido. El revisor debe elegir y demostrar una formulación:
consulta intervalar respecto al prefijo del ancla, o prefijos dirigidos y
reutilización exacta demostrada. Mantener h0 exacto, costura, soporte estricto,
final abierto e incertidumbre de frontera. La prueba del consumidor camina la
fuente de forma separada y verifica la inclusión/identidad que el contrato haya
demostrado, sin aceptar simplemente el resultado cacheado del productor.

Primero piloto acotado con fixtures literales Q02B1 y una selección determinista
de cadenas reales desde el NPZ fijado: cadena más larga, una abierta, una cerrada
corta y la degenerada. Selección por propiedades e ID, nunca por apariencia de
una fotografía. No regenerar discovery; sólo leer sus selectores y revalidar
contra el NPZ. Fijar IDs, offsets, estaciones y hashes en contrato externo antes
de implementación. Ventanas h=6/12/24/48/96 m y una selección explícita de anclas
que incluya extremos/costura. La cadena degenerada emite cero ventanas.

No decidir todavía el número máximo de anclas con datos inventados: la revisión
debe cerrar una cota de operaciones/tamaño y la lista exacta antes del productor.
Una captura piloto de hasta 120 s/512 MiB y consumidor 120 s/512 MiB es el techo
propuesto, sin reintentos ni aumento al fallar. Revisión del plan 120 s. Los
presupuestos de autoría/código/suite se fijarán al cerrar el algoritmo, no se
consideran autorizados por este borrador.

## Criterios de salida

Rechazar mutantes de identidad de cache, cierre omitido, orden, anchor desplazado,
prefijo recortado, consulta puntual que pierde incertidumbre, registro faltante,
agotamiento oculto y promoción humana. Conservar certificados verificables por
cadena y consultas acotadas en NDJSON; no duplicar un transcript gigante por cada
ventana. Deben medirse bytes, memoria y operaciones reales, no sólo segundos.

Salida posible: REAL_CONTOUR_NUMERIC_PILOT_ONLY o INCONCLUSIVE/RESOURCE_LIMIT,
con estados por consulta. Ángulos PENDING_CERTIFIED_ANGLE, referentes naturales
independientes y calibración pendientes. No calidad global, nueve humanos
GEOMETRY_UNBOUND/0 resueltos y C1 NOT_REVIEWED. Sólo después se revisa el censo
completo y su presupuesto; Q03/Q05 y RoadB4B siguen abiertos en paralelo.
