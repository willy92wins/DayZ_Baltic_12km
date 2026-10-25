# EV75 — propuesta rechazada antes de empaquetar

Dos revisiones Luna señalaron el fondo bajo el mar como hipótesis prioritaria para los rectángulos. Se preparó una propuesta diagnóstica sobre EV72, sin cambiar P/F, objetos ni materiales y sin tocar reserva vial o plataformas. **No se empaquetó, desplegó ni ejecutó.** No modifica la base vigente.

La propuesta directa `14c6b0b2` elevaba2470vértices a1m. El consumidor la rechazó:904casos cara/representación tenían calado<0.95m y115caras creaban pendiente>35°; máximo57.03°. Orillas geométricas exactas no bastaban. Se conserva en `rejected-direct` fuera de Git, con hashes y resultado de rechazo.

La corrección determinista `c0e0c206` congela soporte de caras someras y limita las diferencias de altura para construir transición bajo35°. Cambia2238vértices:2123 llegan a1m y115 quedan en transición. Cero cambio de huella mojada y calado mínimo0.952835m en4872caras modificadas. **También rechazada**:14caras superan el corte estricto por conversión a float32 (máximo35.0000011°), y la celda bajo el eje óptico no queda totalmente a1m. No se relaja el consumidor ni se desplaza el objetivo para aprobarla.

La revisión independiente añade que52caras afectadas tocan reserva y150se extienden fuera del círculo aunque sus vértices modificados estén dentro. Esto distingue conservación de vértices de conservación de toda la cara. El control negativo de orilla sólo ejercita la primitiva geométrica, no todos los gates de `scan`; no declararlo suite completa.

El eje óptico no identifica por sí solo el parche gris: el crosshair tapa el píxel central y la celda queda en transición. Esta unidad termina aquí. Antes de otra propuesta se debe localizar la ROI gris real por proyección nativa, no por estimación de FOV. EV76 es sólo lectura de esa proyección con el mapa EV72 original; no es otro ensayo de corrección ni promoción de esta propuesta.
