# Lecho seco sobre carretera: candidato offline verificado

El procedimiento seleccionó104caras del censo completo201modelos/185744caras;
el solape existente estaba en kit118. Descendieron82vértices, máximo0.142578125m,
que afectan203caras. Se conservaron XZ, topología, suelo nativo, máscaras, agua,
objetos y las143caras de apoyo que tocan agua. No se desplegó un modelo nuevo.

GEOS independiente reconstruyó la selección, filas compartidas, dominio, aguaA,
agua nativa y corredor desde fuentes selladas:23.9576325072→0m² expuestos sobre
el corredor conservador (rectángulos±4m y discos exteriores64lados). En932puntos
de corte de caras semilla/modificadas, máximo B-H=-0.0272786101m. No equivale a
pavimento o conducción probados. El productor verifica también1771muestras de
todas las caras locales y obtiene máximo-0.0213438786m; son coberturas distintas.

14tests solver,5controles analíticos y6mutantes rechazados. Las dos revisiones
Fable fueron independientes y sus fixes se adjudican en el plan. El preflight
inviable y sus testigos se conservan: congelar filas/columnas secas antiguas
preservaba salientes de3.7/4.4cm. La reparación mantiene el extremo mojado y
entierra el borde seco; no rebaja el límite geométrico de1e-9m.

La LP no puede compensar un soporte casi fijo con descensos absurdos: la cota
inferior deriva del mínimo H local menos0.03m, cuantizado. El candidato no baja
ningún vértice de agua, ni toca el círculo015-45. No reutiliza la máscara del
piloto seco anterior como autorización para borrar protecciones.

Artefacto numérico: dry-bed-road-candidate-20261028/kit-118-candidate.npz,
sellado en artifact-hashes.json. Siguiente: materializar Visual/Roadway/Geometry
con fuentes vigentes, verificar compilado y probar en juego. No aprobar calidad
visual, navegación o RAM a partir de este candidato. C1 sigue sin revisión humana;
los demás lechos, contornos, puentes, relieve y council permanecen abiertos.
