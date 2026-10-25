# Censo cardinal multiescala sobre B

Fuente base: EV82-B, sin candidato nuevo ni solver. Para cada vértice con contexto completo y d∈{1,2,4}, se calcula por separado EW y NS: max(0, Hc−max(H−d,H+d)); d equivale a 6, 12 y 24 m. “Ambos ejes” significa prominencia estrictamente positiva en EW y NS. El selector EV87 de 6 m se reconstruye antes de la separación de ventanas: elegible, bisagra incidente >30.0001° y prominencia de un paso >0.1 m en cualquiera de los dos ejes.

Las máscaras bank/interior son las de `author_ev87.population_masks`; elegibilidad y unión de protecciones explícitas siguen `author_ev87.py`. Nodos bloqueados solo por estar bajo/equal al nivel P/F/SEA se cuentan aparte de la unión explícita de máscaras fijas. El sector de 384 m se indexa por bloques raster de 64×64 nodos. Los rankings contienen todos los positivos, no una cuota de modificación.

Esto es prominencia cardinal respecto a dos muestras, no prominencia topográfica de silla, curvatura de superficie, artefacto visual ni una decisión de diseño. No implica elegibilidad de cambio ni autorización para alterar alturas. Identidades y fórmulas completas en `summary.json`; arrays y rankings completos en `multiscale-arrays-and-rankings.npz`.
