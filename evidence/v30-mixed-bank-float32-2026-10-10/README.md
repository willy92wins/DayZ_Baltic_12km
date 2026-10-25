# EV81 rechazado; EV80 continúa vigente

Se corrigió una causa numérica aislada: propuestas válidas en doble precisión quedaban al otro lado del límite al convertirlas a float32. Se permite probar uno y dos valores representables hacia la altura anterior, conservando todas las tolerancias y controles. Un recorrido de 81,453 s procesó los 4329 nodos; 4005 cambios, 1382 rescatados con un ULP. Agua y metadatos idénticos.

El consumidor independiente rechaza el candidato: frente a EV80 aparecen seis aristas nuevas >30°, p99 seco de ribera 4,982072→5,004888° y máximo del sector (29,16) 41,671232→42,647964°. El detalle y coordenadas están en `review-luna/review.md`. La mejora total (3384→2819 pliegues mixtos; energía afectada −17,6975%) no anula esas regresiones.

Mecanismo leído: la autoría limita ángulos contra EV79 (`author.py`, solve_node), por lo que puede perder mejoras que EV80 ya alcanzó. El fallback corrige cuantización, pero no cambia esa referencia. No es un defecto del consumidor ni una infracción de agua. EV81 no se empaquetó ni se lanzó en DayZ; no se generó otra variante. EV80 permanece en `P:/Mods/@DayZ_Baltic_MixedBankPreviewV1`, mundo ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038.

Siguiente diseño a revisar, no implementado: separar el terreno vigente que fija los límites angulares del terreno original que fija el presupuesto total ±2 m. Partir de EV80, no reconstruirlo desde EV79; conservar exactamente sus mejoras y las protecciones actuales. Requiere un nuevo plan con fixture que falle al comparar únicamente con EV79, antes de calcular. No relajar el criterio ni promover una combinación parcial sin consumidor.

Base 1.0 sigue abierta: agua gris a distancia, residual de agua aparente sobre tierra, formas mojadas y finales, grandes lagos/excepciones pendientes, Terrain Builder y navmesh final. Los números de geometría y la lectura nativa EV80 no son aceptación visual.
