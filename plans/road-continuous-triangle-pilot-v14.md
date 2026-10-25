# Corredor continuo y transición al terreno, piloto V14

P10/P11/P13. V13 no se importa: consumidor independiente detectó20secciones
fuera de3cm y24triángulos nuevos>35°; había mejorado los puntos del solver,
pero faltaban curvas intermedias y la transición lateral. V10 sigue desplegado.

[DESIGN] Cambiar el modelo geométrico, manteniendo las mismas tres rutas y
protecciones: cada segmento de carretera define una banda de8m. Encontrar
por intersección geométrica todos los triángulos nativos tocados por esa banda;
acotar su derivada transversal, no solo muestras de altura. Gradiente lateral
<=0.0032m/m y longitudinal<=0.06. Incluir también normales de las uniones.
Rasante/cuerda siguen los límites previos. El soporte editable se extiende
12m alrededor de los vértices del corredor para transiciones, sin entrar en
agua/fairway/bank/islas/Narva; fuera de ese soporte queda exactamente V10.

Para todo triángulo afectable, imponer una aproximación interior de16lados
al círculo de gradientes tan(35°). Conservar>=1.4m de suelo seco (o la altura
anterior si era menor), sin tocar agua. Primero minimizar el máximo cambioT
como diagnóstico, <=120s/un hilo. Si T<=2m, un solve L1 con cotaT+0.05m,
<=120s. Ese límite es una decisión del piloto de rasante local: si requiere
más movimiento, no producir candidato y revisar el corredor; nunca variar
el recorte, las cotas de agua ni el relieve regional para salvar este piloto.

El verificador independiente anterior se amplía solo para leer la cota del
nuevo manifiesto; conserva estaciones0.37m, anchura0.25m,3cm/6.5%/cuerda3cm,
talud35°, protecciones exactas y ausencia de empeoramiento fuera del núcleo.
Una ejecución piloto y una comprobación: si falla, preservar resultado y parar.
No hay importación, empaquetado ni navmesh mientras sea un piloto parcial.
