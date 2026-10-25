# EV94: incorporar la pendiente de una cara al problema restringido

Alcance autorizado por la petición viva de corregir las elevaciones y fallos del mapa. Esta modificación de implementación se presenta antes de ejecutarse: se añade una cota derivada de la única regresión detectada, sin cambiar el diseño, los límites angulares ni las protecciones. El candidato rechazado 3360b1e8 y su consumidor FAIL se conservan.

## Mecanismo y restricción exacta

El consumidor independiente `consumer/full-run-02.json` (SHA 259c87fa01894eb3db409f6087e7cd3b787918e1e08629b4e53ad0fdd2e24030) encuentra una sola pendiente fuera de contrato. Cara nativa 0 (NW, NE, SE) de la celda RC (899,445). NW=7.2344970703125 y NE=3.1139774322509766 son fijos por ingeniería; SE (900,446) es móvil, con base=2.2943551540374756 y cota superior=2.7943551540374756. La pendiente subió de 35.0000009839 a 35.0477442956 grados al bajar SE 0.0373954773 m. Fuente geométrica: `verify_ev87.py:248-258`, NW-NE-SE sobre celda de6 m. Coordenadas X=6c, Z=12282-6r; el diagnóstico inicial usa por error12288 para Z, sin afectar RC, alturas ni pendientes.

[EXACT] La norma del gradiente es `hypot(NE-NW, NE-SE)/6`. Como todo el intervalo `[SE_base, hi]` queda debajo de NE, elevar SE dentro de él reduce `(NE-SE)^2`; el otro término permanece fijo. Por tanto basta añadir `lo(SE) = max(lo_fisica, SE_base)` para que esta cara no supere su pendiente B. No se consume la tolerancia de1e-4 grados ni se fija artificialmente SE: puede subir hasta su cota superior existente. Se rechaza la preparación si cualquiera de esos dos vecinos es móvil o si `hi>NE`.

## Preparación y prueba

Derivar un preflight NUEVO del05 a6ae4b91cf5ebabbfc57352e4f988150eea2a7506b74a610b6aa4ce79a2bf4d7, preparado2df4ad67280c656025843f6528147a68c03dfcf6ecdfbe9cce2ee4818e15a2eb. Cambiar exactamente una entrada de `lo`; todas las otras entradas/arrays, `bound_lo_local` físico, A/C/RHS, x0, dominio, D8,499 ventanas+halo2 y foco permanecen byte-exactos. El recibo nuevo declara su propio driver, plan y artefacto; no se hace pasar por un run anterior. Readsets original, unidades y nuevos se verifican al inicio/final.

Pruebas: identidad de todos los arrays salvo esa cota; índice único del nodo; vecinos fijos; intervalo demostrado completo y extremos comprobados; base factible D8/cotas y proyección float32 de base exacta. Negativos para vecinos móviles, intervalo que cruza NE, base fuera de cotas y datos no finitos. Consumidor independiente reconstruye las matrices y cotas físicas originales y deriva la nueva cota sin llamar al autor. Conserva las15 puertas geométricas anteriores; añade identidad del delta de preparado y prueba de los vecinos fijos.

## Ejecución y parada

Tras revisar preparación y consumidor, una única llamada fresca a `solve_ev94.py` (ebb53986d69e4ec080356883db15091983fef3bb01715714177d2d504283abf0) con el nuevo preflight y su SHA. Driver y matemáticas sin cambios: máximo20000 iteraciones,600 s numéricos,1.5 GiB pico,3 GiB libres y2 GiB de salida. No continuación ni reparación posterior del candidato viejo. El KKT y allowance de cierre se evalúan contra el nuevo problema; no se modifica el allowance.

FAIL, timeout o inconcluso preservan artefactos y detienen esta unidad sin repetir por ajuste de parámetros. Solo un consumidor independiente PASS permite componer el sector y verificar el mapa resultante. Esto no acredita contornos húmedos, pruebas nativas/gráficas, ni BASE1.0.
