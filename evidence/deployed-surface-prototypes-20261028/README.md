# Caras reales del mundo desplegado: etapa A verificada

El extractor conserva539.009caras de prototipo:362.554Roadway,176.390agua
visual directa y65agua de proxies con marco condicional. Las vincula a17.818
instancias con matrices compiladas exactas. No son539.009caras instanciadas
ni un conteo de cruces, ni una aceptación del mapa.

23pruebas fuente PASS. Fable5.1 revisó el código y encontró claves Windows en
el manifiesto, ventana entre hash/lectura y trazabilidad incompleta de proxies.
Se corrigió en una sola ronda: snapshots JSON/NPZ, recomprobación de entradas,
rutas completas de ranuras, pruebas de omisiones y caras múltiples/degeneradas.
Se conservan43caras ambiguas con su residuo, máximo0,354368843m; no se rebaja
el umbral para convertirlas en PASS. No aparecen caras degeneradas.

Producción única:39,343s, PID120912, pico271.597.568Bresidente/294.821.888Bcommit.
Consumidor independiente:44,031s, PID122456,255.311.872B/240.246.784B. Comprueba
recuentos e identidades de cara contra inventario anterior, poses byteexact,
rutas de proxies y201modelos del piloto contra MLOD fuente actual: error máximo
bidireccional de vértices0m en agua y Roadway; se mantiene el límite previo<0,001m.
No demuestra topología completa, render ni comportamiento del motor.

Dos referencias anteriores se rechazaron antes de comparar geometría:
145payloads diferían de revisiones originales;19 de la carpeta temporal base.
La procedencia final se resolvió con base201(paquete46244e7f) más19cambios
Geometry conservando otras superficies, en paquete3d9550bf. No se ocultaron
los fallos ni se reutilizó el PASS del build equivocado. La comprobación final
usa esa cadena exacta y los MLOD actuales con hash del autor.

Los NPZ y datos geométricos de terceros quedan fuera del repositorio, ligados
por hash. Este commit publica extractor, tests y evidencia, no otro build.
Siguiente: etapa B, cruces geométricos con TODO el eje y altura del agua frente
al terreno. La lámina enterrada bajo una orilla seca no debe contar como cruce
inundado. Ese refinamiento requiere revisión antes de ejecutar B. RAM,
aceptación visual/global, navegación posterior y C1 sin revisar siguen abiertos.
