**Veredicto: SOUND-with-fixes.** El plan es ejecutable con las dependencias reales, pero dos puntos tal como están escritos fallarían o no pueden cumplirse. Ninguno exige rediseño.

**Comprobado contra fuentes**

- Informe exacto: 5443 payloads decodificados, 6 proxies, 0 fallos, 17818 instancias, 28 puentes en 4 modelos, 2 presas, 201 pilotos, 10264 charcas, 7323 streambed. 717 diferencias de pose solo en streambed_family, máximo 9.54e-7. Coincide con el plan.
- API del lector externo (SHA fa0d74b6 confirmado en inputs del descubrimiento): `ODOL.from_bytes(data, strict=True)` en línea 961, `lod.resolution`, `model_info.bounding_center`, `Section.get_face_indices`, `Proxy.transformation` con orientación y posición. En strict, `lod_errors` nunca queda poblado en un parse exitoso. Suficiente para A.
- Cobertura independiente: el grupo `bridge` se obtiene por ruta del catálogo completo del WRP compilado, no de crossings-ev106; el script resuelto afirma cero modelos no clasificados fuera de vegetación. Correcto.
- Pose compilada: `selected-instances.npz` guarda las 12 floats del WRP compilado. La fórmula Vworld = Vstored @ M + T coincide con `bridges_v31.to_world` y con la raíz calculada en package_visual_forest. Bien.
- Universo de carreteras: 124/36428/36467 verificado por el censo (107180 m). Los ficheros del grafo viven en el checkout principal, no en el worktree; el plan debe pinear ruta absoluta y hash, como hizo el censo.
- Presupuesto: descubrimiento 18 s/278 MB; censo 4.6 s/802 MB commit. 120 s/2 GiB es realista si la broad phase está indexada.

**Bloqueantes (fix mínimo)**

1. **Separadores en materiales.** El plan exige igualdad exacta con `dz/water/streams/data/water_streambed.rvmat` y `dz/water/ponds/data/pond_moss_1.rvmat`, pero el ODOL serializa `dz\water\ponds\data\pond_moss_1.rvmat` con barra invertida. La igualdad literal seleccionaría cero caras de agua y repetiría el fallo del primer filtro. Fix: comparar tras `norm()` (barras y minúsculas), conservando la cadena cruda en el inventario. Lo mismo para texturas Roadway.
2. **MLOD de los cuatro puentes.** Línea 55 pide verificar con "muestras MLOD originales de pilotos, los cuatro tipos de puente". Solo los pilotos tienen MLOD fuente; para bridge_wood_25/50/50_1 y bridge_metal_25 no existe editable vanilla y no debe inventarse. Fix: MLOD solo para pilotos; puentes y presa verificados por transformaciones analíticas más identidad bit a bit editable↔compilado, ya acreditada en pose-differences.

**Fixes no bloqueantes**

3. **Resolución Roadway.** Pinear el literal serializado 3000000028082176.0, no "float32(3e15)" en abstracto. 5434 de 5443 modelos tienen esa LOD; los 6 proxies y los grupos de piedras no la tienen y deben entrar como inventario sin Roadway, no como fallo.
4. **Roadway de agua.** Charcas (10264), pilotos y streambed tienen Roadway con textura water_ext. bridge_metal_25 lleva concrete_ext, metal_thin_ext y una sección con textura vacía; bridge_wood_25 tiene 8 vértices/3 caras (cuádruples, afecta a la ambigüedad de triangulación); la presa concrete_ext. El plan ya etiqueta, pero debe decir explícitamente que water_ext nunca alimenta la capa de soporte y que las secciones con textura vacía se conservan.
5. **Gate 1e-9 en juntas.** Las traslaciones compiladas son float32; a ~1e4 m su ULP ronda 1e-3 m. Ninguna junta entre módulos colocados por separado coincidirá a 1e-9, así que todas las 28 piezas y los lechos aparecerían como discontinuidad igual que un hueco real. Mantener 1e-9 solo como residuo del solver; en juntas reportar magnitud y relación con el ULP local como dato, sin umbral de aceptación. No es falso PASS, pero sepultaría los huecos reales.
6. **Broad phase.** 17818 bbox × 36467 aristas son 6.5e8 pares si es ingenuo. Usar STRtree sobre bbox de instancia (Shapely ya es dependencia del verificador) o bucketing por celda. El bbox debe calcularse sobre las caras transformadas que se consumen, incluida agua proxy tras su marco.
7. **Escala/ortonormalidad.** El lector OPRW acepta normas de fila hasta 100. Registrar normas y no ortogonalidad por instancia como inventario antes de clasificar caras verticales.
8. **Proxy.** Orientación observada 0.99999994 en diagonal, no identidad exacta; conservar íntegra como dice el plan. En long_straight la posición y del proxy (0.42389) anula exactamente wbc.y (−0.42389); es coherente con la hipótesis pero no prueba de motor. CONDITIONAL_PROXY_FRAME se mantiene.
9. **Lector en C:/temp.** Ruta volátil, pineada por SHA. Limitación explícita, no bloqueante; fallar cerrado si el hash difiere.

**Limitaciones ya explícitas y correctas**

Sin aceptación de puente, calzada, gálibo ni c1; vegetación fuera; agua nativa, charcas, piloto y proxy en capas separadas con unión geométrica; LOD visual de menor resolución (0.0 en streambed/pilotos, 1.0 en charcas) funciona con mínimo; no expandir los 26300 caras × 6352 instancias del LOD visual de lechos.

**Conclusión: SOUND-with-fixes.** Aplicar 1 y 2 antes de codificar; 3 a 7 en la misma pasada. Identidad del revisor: claude-fable-5-1, solo Read/Glob/Grep, sin escrituras.

FIN_REVISION
