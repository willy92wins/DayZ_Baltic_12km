**Veredicto: SOUND-with-fixes.** Los números del brief coinciden con los artefactos hasheados; las correcciones son de alcance y redacción, no de cálculo.

**Verificado contra fuentes**

- Conteos reproducidos en `kit7-post-load1-vertex-surfaces-20261027/result.json`: 52 XY, 6 modelos, 23+25 vértices, 16+15 con Roadway, 7+10 sin Roadway, 0 bajo terreno, 0 con |delta|>0.801, rangos 0.0194..0.1200 y 0.0110..0.1598.
- Los 6 controles nativos tienen residuo real máximo 4.0e-7, muy por debajo del umbral 2e-5 del assert. Publicar el valor observado, no el umbral.
- Los 5 XY antiguos se reproducen por assert (terreno <1e-9, LOD por modelo/resolución <1e-9). Es reproducción con la misma función `tri_h`, no control independiente.
- Signos: gap = engine − cuerda, bias = navplane − cuerda, y el assert confirma gap − bias = engine − nav en cada muestra. La ponderación baricéntrica tiene fixture positivo y dos negativos. Correcto.
- Ambas ejecuciones terminaron dentro del deadline del budget, con inputs sin cambios, 0 runs, 0 generaciones.
- La ayuda del generador lista solo opciones de consola/red. La afirmación "no expone control de geometría" es literal y correcta; no concluye ausencia.

**Conclusión justificada sobre los 3 fallos**

Las tres consultas fallidas caen en polígonos cuyas esquinas están todas dentro de 0.036..0.160 m sobre la superficie conocida, pero cuya cuerda queda 0.92..1.02 m por debajo de la Roadway empaquetada en el punto consultado. La discrepancia no está en los vértices; aparece al interpolar un plano entre esquinas situadas a cotas 1.08..1.90 y 2.45..2.66 m, es decir, el polígono une la coronación del kit con el lecho en un solo plano. Esto está sostenido por datos locales archivados y por los controles nativos en esos mismos seis XY.

Dos observaciones que el informe debe decir explícitamente:

- Como engine_roadway ≈ Roadway empaquetada en los 6 waypoints (residuo <4e-7), el "gap" es una propiedad geométrica de la malla del kit entre esquinas, no una medida independiente del lector.
- Los 3 PASS usan el mismo mecanismo: errores 0.55/0.56/0.08 con bias similar (0.12). Pasan porque la consulta cae más cerca de las esquinas altas, no por un comportamiento distinto. El fallo es cruce de umbral del mismo fenómeno, no mecanismo aparte.

**No justificado y debe quedar fuera**

- Por qué el generador abarca esas esquinas en un polígono (simplificación, muestreo de altura, entrada de colisión). No hay fuente.
- Que Nav8 pase en esas consultas por polígonos distintos: no se descompusieron abanicos Nav8 en los 6 XY, solo vértices. Es el discriminador mínimo que falta; requiere su propio gate de formato antes de decodificar polígonos 8m.
- Validez de la regla "max Roadway entre modelos" fuera de los 6 XY controlados. Con un triángulo por muestra, la regla max heredada no se ejercitó.
- Superficie del motor en las esquinas: no sondeada, como ya declaran los limits.

**Contrastes solicitados**

- Selección LOD: filtro por resolución 3e15 y max sobre triángulos interiores; validado solo en los 6 puntos.
- road_y: los limits aclaran que Roadway es la superficie fluvial del kit. Mantener esa frase en la publicación.
- Cobertura: los 17 vértices sin Roadway se publican con terreno como superficie conocida. Uno de ellos, (9137.9, 11268), es esquina de dos polígonos fallidos; su "conocida" es terreno 1.634 y nav 1.670. Si existiese otra superficie no inventariada en geometry.json, el gap cambiaría. Declararlo como supuesto.
- Generalidad: 48 vértices provienen solo de teselas testigo. No publicar "ningún vértice bajo terreno" como propiedad de la malla.

**Correcciones de redacción**

1. Cambiar "residuo<2e-5" por el máximo observado 4.0e-7.
2. Añadir que PASS y FAIL comparten mecanismo y difieren por posición en el polígono.
3. Reemplazar "5 XY reproducidos" por "reproducidos con la misma implementación".
4. Anotar que el candidato siguiente lógico es descomponer abanicos Nav8 en los 6 XY, pendiente de gate de formato, sin anticipar rejilla ni parámetro.

Estado INCONCLUSIVE_NO_VERIFIED_MECHANISM es correcto; la unidad numérica puede cerrarse y publicarse con esas cuatro correcciones.

FIN_REVISION