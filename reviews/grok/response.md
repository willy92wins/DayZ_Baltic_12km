Revisión numérica de registro. No es una importación DayZ probada ni un gate de producción: eso lo cierra el agente de otra familia. El ΔY de abajo es aritmética manual, no PROJ.

**(1) Sobre y captura.** El diseño puede conservar el territorio aprobado sin deformación respecto a una captura Web Mercator. El marco es cuadrado (1135×1135) y el ráster EPSG:3857 usa esos cuatro bordes con un solo escalar en x e y. Es una semejanza: traslación más escala uniforme. El primer plano de San Petersburgo, Narva y el oeste viajan en esa misma afinidad.

Δλ = 4.168467043833282° y R = 6378137 dan ΔX = R·Δλ = 464031.64 m. Entonces a = 12288/ΔX = 0.026480953 y 1/a = 37.76299 m mercator por metro de juego. La celda sale exacta: 12288/2048 = 6 m = 226.578 m mercator.

Si la y de imagen crece hacia abajo y la y de juego hacia el norte, el recorte (x=558, y=38, 444.25×353.5) cae así: x = 6257.678 m, ancho = 4809.642 m, y norte = 11486.844 m, alto = 3827.144 m, y sur = 7659.700 m. Son consecuencia del marco, no una medida sobre el mapa. El enunciado no fija el sentido de y. Con y de imagen hacia el norte, ese rectángulo pasaría a la franja sur. Hace falta dejar escrito «y de imagen hacia abajo»: es la lectura que sitúa el recorte entre el 6.52 % y el 37.67 % desde el borde norte.

**(2) Metros reales.** El cuadrado mercator no es cuadrado sobre el elipsoide. Estimación manual de k ≈ R/(N cos φ), sin certificar: ~1.891 al sur, ~1.950 hacia 59.23° N, ~2.013 al norte. Un metro de suelo en el norte ocupa ~6.5 % más metros de juego que en el sur. Lados elipsoidales aproximados: E-O sur ~245.4 km, E-O medio ~238.0 km, E-O norte ~230.5 km, N-S ~237.5 km. El desajuste medio E-O/N-S es ~0.2 %; lo grande es el gradiente con la latitud. A escala física media, 1 m de juego ≈ 19.37 m de suelo E-O. El candidato Z×3 no mueve el plano. Esa comparación usa distancia geodésica elipsoidal y EGM2008; EPSG:4326 no aporta datum vertical.

Una TM o LCC con las mismas cuatro esquinas conserva las esquinas, pero el interior deja de coincidir con el cuadrado de la captura. Volver a un cuadrado de juego obliga a inscribir (se pierde franja del sobre) o a circunscribir (entra área de fuera). No hay motivo para cambiar la geografía aprobada.

**(3) Media celda y filas.** Hay 2048 centros, no 2049 esquinas. Con el borde exterior en el sobre, los centros van en 3, 9, …, 12285 m de juego: en ingeniería, x = 200003…212285 e y = 3…12285. Cabecera: xllcorner=200000, yllcorner=0, cellsize=6, primera fila al norte (ESRI). Media celda = 3 m de juego = 113.289 m mercator ≈ 58 m de suelo a k~1.95. Declarar xllcenter=200000 con muestras de centro desplaza el terreno 3 m al suroeste. Leer la fila 0 como sur invierte el mapa; yllcorner no dice el orden. El ASC está en metros de ingeniería. Xmin, Ymin y a van en un sidecar float64: en float32 la longitud del borde pierde unas décimas de metro.

**(4) Controles que no se autoverifican.** game_x(Xmax)=12288 es una identidad, no una prueba. Gates útiles:

1. |ΔX−ΔY| < 0.01 m con PROJ y con GeographicLib, antes de calcular a.
2. Un lon/lat publicado, no usado al ajustar: PROJ → px=−20+1135·(X−Xmin)/ΔX, py=−36+1135·(Ymax−Y)/ΔY, medido en la captura.
3. SW y NE de vuelta a W,S y E,N con el otro programa.
4. xllcorner+2048·6 = 212288 e yllcorner+2048·6 = 12288. 2049 filas es fallo.
5. Un pico conocido cae en su centro; un residuo de 3 m exactos es el bug de media celda.
6. La fila 0 coincide con la franja norte de una máscara independiente.
7. Este x no es UTM. El huso se parte en 30°E dentro del sobre y el falso este UTM es 500000. EPSG:32635/32636 queda a cientos de kilómetros.
8. Z sale de (geodésico E-O medio)/12288, y ×3 solo en la capa de comparación. La ondulación EGM2008 se muestrea; no es una constante sacada de la latitud.

**Vértices de Terrain Builder.** No está demostrado si el ASC son 2048 centros o nodos de malla. Un heightmap habitual usa 2049 vértices para 2048 intervalos, con muestra en la esquina y el borde sobre el vértice. Si el consumidor espera eso, 2048 centros no cubren ni 0 ni 12288: hace falta un remuestreo escrito, o el terreno queda metido media celda por lado (6 m de juego en cada eje). No afirmo cuál contrato aplica. El +200000 en x y el +0 en y son ingeniería de Terrain Builder, no un este de fuente.

FIN_PROJECTION