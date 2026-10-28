# Cruces de carretera contra superficies desplegadas

Censo de las124cadenas y36467aristas de referencia, sin excluir agua, Narva
ni extremos y sin usar la lista del generador para descubrir cruces. Usa las
caras y poses reales selladas de la unidad A.32fixtures y consumidor independiente
Shapely verifican2413contactos; residuo máximo1.69914e-12m.

El diagnóstico identifica715.422m de eje bajo agua de modelo sin Roadway de
puente, en7cadenas. Coinciden casi exactamente con la capa nominal de charcas:
no sumar ambos. Otros1024.828m corresponden al mar nominal en14cadenas. Estas
son longitudes sobre ejes; NO son cantidades de puentes ni aceptación visual.

La posición reportada4789.51465/5516.52197 queda a11.601m del contacto
cadena49/arista301: mar nominal y ninguna cara de puente observada. En Narva
sí hay tablero sobre agua; eso no acepta su alineación. En la arista más
próxima medida, eje y PCA del tablero difieren6.666grados con separación
lateral2.228m; diagnóstico de ejes, no umbral nuevo. Kit118 tiene una pieza de
lecho/Roadway que intercepta6aristas de la carretera76. Esto localiza el solape;
la exposición del Visual completo y su reparación todavía están pendientes.

Se separan agua enterrada/expuesta respecto al terreno fuente, mar/charca
nominal y agua de modelo, tablero sobre/sumergido/ausente y geometría incierta.
Ninguna Roadway water_ext se acepta como puente. Proxy enterrado conserva
INCONCLUSIVE_WATER; caras ambiguas conservan ambos fans y rango de alturas.
Los nodos incluyen todas las cadenas incidentes sin duplicar observaciones.
Microhuecos no se sueldan; se guarda procedencia y ULP, e incertidumbre dentro
de una misma instancia. No se modifica ninguna tolerancia ni geometría.

Fable5.1 revisó plan y código. Se corrigieron el conteo de candidatos por
mutación de defaultdict, el filtrado de proxy enterrado, procedencia de huecos,
capas nominales, diferencias de agua, duplicación de nodos y cierre de recursos.
El preflight histórico conservado tenía candidate_edges incorrecto; el censo
verificado da994aristas candidatas/1399pares/129191caras.32tests incluyen
orquestación con carreteras secas, nodos compartidos y falsa Roadway de puente.

Censo4.437s,453042176B de commit; consumidor2.969s. Presupuesto120s/2GiB cumplido
en PID real. H coincide byteexact con el WRP editable vinculado al mundo de
la visita. No se ha decodificado la totalidad del terreno compilado: exposición
relativa al terreno de autoría, no prueba de motor. Ningún run DayZ utilizado.

Reportes resumidos y tramos están aquí; contacts.json/nodes.json completos y
NPZ de cobertura permanecen externos por tamaño, ligados en artifact-hashes.
Los intervalos de categorías pueden solaparse; no sumar ni contar como cruces.
25de28piezas de puente intersectan algún eje: lasotras3no se borran ni se
consideran defectuosas por este dato. Persisten RAM, contornos, relieve, lechos,
aceptación visual/global y c1 SIN REVISAR; council ampliado sigue pendiente.
