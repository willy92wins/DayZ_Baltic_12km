# Grok 4.7 y Gemini 3.8 — arbitraje de fase 0

Ambos encargos fueron autorizados expresamente por Guillermo después de una revisión automática inicial que pidió acotar el envío. Se transmitieron región pública aprobada y diseño técnico. La aprobación posterior resolvió ese bloqueo; no se enviaron credenciales ni material privado del vault.

Grok: revisión de proyección, sin herramientas. Modelo efectivo `grok-4.7-build`, 330,4 s, coste declarado 0,06651964 USD. Gemini: candidato de validador CLI mediante Gemini 3.8 Flash High, 77,8 s, coste no informado. Respuestas finales y métricas en sus subcarpetas; se excluyen los logs de razonamiento del entregable.

| Hallazgo/propuesta | Arbitraje | Evidencia propia |
|---|---|---|
| Grok: semejanza de Web Mercator conserva el marco; escala terrestre varía con latitud | YA-CUBIERTO; confirmado, se cuantificó | tools/geo_common.py:53 y evidence/coordinate-contract.json. Compresión sur 19,967×, centro 19,357×, norte 18,759×. |
| Grok: orden de filas y media celda | ACEPTADO: control consumidor explícito; no afirmar TB probado | tools/geo_common.py:59; tests/registration-probe/expected.json y plans/terrain-builder-import.md. |
| Grok: metros de ingeniería no son UTM | YA-CUBIERTO; confirmado | tools/geo_common.py:63 y WKT local exportado. |
| Grok: multiplicador Z = distancia geodésica / 12288 | RECHAZADO-FALSO si se usa como multiplicador. Corregido al recíproco: metros de juego / metros reales | tools/geo_common.py:53; factor 0,0516602, no 19,357. |
| Grok: verificar Web Mercator con GeographicLib | No adoptado como receta ejecutable; no se verificó una API Mercator de esa biblioteca | tools/validate_prototype.py usa la expresión esférica independiente para registro de controles y GDAL para consumo. |
| Grok: posible necesidad de 2049 vértices | ACEPTADO-DEGRADADO a incógnita del consumidor. No cambiar 2048 por una convención genérica | tools/geo_common.py:64; gate TB pendiente. |
| Gemini: validador AAIGrid con cabeceras, filas, NoData y controles | Implementación candidata aceptada tras revisión y modificaciones propias | tools/validate_ascii.py + 13 fixtures positivos/negativos en evidence/validator-tests.json. |

Cambios propios al candidato de Gemini: igualdad exacta para sentinel NoData, rechazo de especificaciones/tolerancias no finitas, límite de dimensiones, salida no cero si falla escribir el informe, evitar reserva de memoria con dimensiones incompatibles, resultados JSON sin NaN. “Coinciden las muestras de control” no se etiqueta como orientación geográfica demostrada por sí sola.

Este arbitraje no convierte respuestas de proveedores en pruebas de funcionamiento de DayZ. No se lanzaron rondas adicionales sin un hallazgo que las justificase.
