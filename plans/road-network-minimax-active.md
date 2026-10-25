# Medir la mínima modificación vertical antes de producir otra variante

V19 reprodujo la inviabilidad a4m usando solo317.978 filas activas de la matriz
V18 y obtuvo un certificado válido: los mismos dos vértices de la colina
necesitan al menos4,384321m. No generó ASC. La reducción de memoria permite
resolver el diagnóstico directamente, sin nuevas pruebas de cotas sucesivas.

[DESIGN] Minimizar t sujeto a todas las restricciones V18 y -t<=delta<=t,
pisos de islas intactos. Sembrar las filas activas del certificadoV19;
añadir toda violación hallada en la matriz completa después de cada solve.
Tope de diagnóstico12m,600s/650s de proceso/un hilo/RAM>=2GiB. Sin ASC.
Si el subproblema es óptimo y el primal cumple todas las filas originales,
es también óptimo para el problema completo. Si solo hay primal factible,
registrar únicamente una cota suficiente, sin afirmar mínimo.

La aceptación de una cota de producción requiere revisar magnitud, localización
y protecciones del resultado. Este diagnóstico no amplía automáticamente el
límite de edición de terreno ni cambia el paquete o la navmesh.
