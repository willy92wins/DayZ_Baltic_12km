# Revisión técnica y decisiones

Grok CLI 1.0.44, OAuth: 402, saldo agotado. No revisión recibida. Gemini 3.8
Flash High por agy 1.2.14: respuesta exitosa, una intervención, sin llamadas a
herramientas reportadas ni archivos delegados. Salida original conservada.
Aviso del CLI: `--mode plan` no tiene efecto con expansión de slash desactivada;
no volver a tratar esa combinación como aislamiento de solo lectura. Este
encargo solo recibió diseño técnico público y pidió respuesta sin herramientas.

Se adoptan las separaciones de pruebas: agua dinámica frente a WRP, juntas y
pendientes, flotación frente a apariencia, y agua frente a filtros de navmesh.
Coinciden con el plan previo; no constituyen confirmación independiente del motor.

No se adoptan como hechos sus explicaciones de BVH/PhysX/voxelización ni su
afirmación sobre todos los sistemas de agua: carecen de fuente verificada. La
aritmética de celdas depende de orientación y registro; seguimos usando todos
los triángulos intersectados. Se rechazan el estrechamiento a4m de ancho, la
reducción de profundidad a1.5m y el vado añadido: contradicen o amplían el encargo.

Descubrimiento local: `game.c:1183–1187` expone GetWaterDepth y superficies de
agua con/sin onda falsa. El ensayo dinámico midió profundidad dependiente de Y
(aproximadamente nivel con onda menos Y), no profundidad del cauce. SurfaceY
permaneció1.39m y la superficie sin onda pasó del mar a6m. Aceptación numérica y
física en el informe asociado; no extrapolar a WRP ni pendientes sin esos ensayos.
