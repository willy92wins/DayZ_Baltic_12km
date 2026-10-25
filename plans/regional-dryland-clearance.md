# Corrección regional de tierra inundada

P2/P3 y petición vigente de corregir el agua. La auditoría de solo lectura del
paquete5030cb74 confirma20 puntos terrestres interiores inundados,8 en San
Petersburgo.1299 alturas coinciden con el ASC actual hasta5.01mm. Rango de mar
API0.5–1m. Fuente: evidence/regional-water/baseline-verification-v1.json.

[DESIGN] Extender la corrección de despeje ya probada en Narva a la tierra
regional baja: elevar únicamente clases terrestres10/20/30/40/50/60, fuera de
los polígonos OSM de agua. Mantener humedales90 y agua80 sin cambios. Interior
a1.25m; transición de0.75 a1.25m en12m desde la orilla de referencia. Solo
elevar, nunca rebajar. Ningún cambio de XY, recorte o coeficiente de relieveZ.
Todo vértice con cota>=1.25m permanece idéntico, incluido el puente a2m.

Autorización: el usuario pidió arreglar agua fuera de límites y continuar
autónomamente hasta dejar la versión básica. Esta intervención corrige ese
defecto medido; no decide densidad, lagos elevados ni el relieve final.

Antes de importar: candidato y delta separados, hashes de fuentes, lectura
completa de salida y contraste con los22 puntos bajos congelados. Validar
que ningún vértice de agua/humedal o ya alto cambia. Contrastar orillas al
importar; no deducir fidelidad únicamente de la máscara de cambio.

Una importación nativa y exportación ASC/WRP. Exigir correspondencia global,
objetos intactos, mismo SAT1M; regenerar navegación después de cambiar alturas.
Repetir1299 lecturas en motor y las vistas regionales; repetir cruce de Narva
si cambia el sector. PASS de agua acotado al muestreo, no a cada costa.
Si no coincide registro o hay regresión visual, conservar baseline5030cb74
y descartar candidato. No modificar producción hasta superar esos gates.

## Ajuste de exportación observado (2026-09-29)

La exportación nativa41b32584 coincide con el ASC hasta2.98e-8m y conserva
header/materiales. Falló el gate exacto de objetos: ambos registros subieron
1.0198–1.0200mm, solo en Y; nombres, IDs, X/Z y rotación son idénticos.
No se ha aislado el mecanismo interno de TB. Conservar el WRP crudo.
Restituir en una copia los registros completos de objetos del baseline
a546e955, únicamente si el único delta es Y y no supera1.1mm. Después ejecutar
el mismo gate exacto, sin tolerancia añadida, y filtrar el estanque diagnóstico.
La compilación usa esta copia normalizada; el TV4P exporta todavía ese desfase
milimétrico. Este ajuste conserva el puente probado, no cambia su diseño.
