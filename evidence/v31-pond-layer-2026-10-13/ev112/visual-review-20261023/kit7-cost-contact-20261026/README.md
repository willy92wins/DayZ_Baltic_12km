# Kit-7: coste, contacto y charcas — 26-10-2026

**Candidato aislado aceptado offline; integración en WRP, bosque y motor pendientes.** La generación C/F está activa en el instante del snapshot; no se declara navegación PASS.

Los139modelos del cauce continuo de1,66km pasan lectura MLOD, compilación ODOL y contacto global sobre el PBO. Se conservan los otros3LOD byteexactos en fuente y se derivan las poses desde el centro realmente compilado. Ninguna pose heredada de otro río.

| Medida releída | Original | Candidato |
|---|---:|---:|
| Componentes |127528|8623|
| Caras |1020224|263552|
| Vértices |765168|149022|
| Máximo individual vértices/caras |6/8|70/136|
| Bytes P3D fuente |1826042263|114200506|

Los máximos individuales aumentan y permanecen dentro de72/140, techo fijado desde C antes de autoría. Los totales y cada modelo reducen/no aumentan coste. No equivalencia de rendimiento ni FPS.

Overlay completo de127528triángulos de lecho y115055de cubierta; cero área perdida/excesiva, certificado inferior cubierto y error superior máximo0,014370m dentro de±0,02m. Cierre/convexidad y selección completa de8623componentes. Los negativos sobre las dos primeras piezas consecutivas rechazan elevar5cm y retirar media superficie. La mínima diferencia entre pares solapados no es la envolvente de contacto: se conserva el certificado de unión inferior.

PBO aislado1f27e9d3ed05036fd359b49c9fa30a5665c8056cc1f85585b63ff278852d7a8e. Fuente/entradas/manifiestos/informe final fijados por hash tras revisión Fable y cierre de sus hallazgos. La clasificación del LOD respeta precisiónfloat32; no compara con el decimal1e13 exacto.

La nueva huella de charcas conserva plane,field,visible exactos aF;36celdas inactivas retiradas de envolvente, cover intacto. Bury no modifica vértices ni expone bordes nuevos. Su primera salida falló byteparidad porque np.savez guardó sin compresión: todos los NPY eran idénticos. Se conserva esa salida FAIL y se prepara otra carpeta con el NPZ original exacto, sin recalcular ni cambiar el terreno.

Navegación: el usuario confirmó cerrar una ventana en la interrupción C anterior. Es consistente con la evidencia; no prueba al iniciador nativo ni explica la antigua salida F. Un nuevo intento C, mismos PBO/WRP/motor, está activo con observador y lease. Se corrigieron comandos largos y el lease inicial C45.23controles de cierre,5flujos,8casos de comandos y fallo real demorado pasan; Fable SOUND.0/-1solo se admiten con todas las pruebas independientes de cierre ordenado; la salida anterior sigue rechazada por prematura. C45 preparado conserva45consultas/8rutasF, sin cobertura de25piezasC ni actores.

No se ejecutó el cliente ni se cambiaron paquetes desplegados. Los230tests del checkpoint anterior siguen siendo evidencia de esas fuentes sin cambios, no una nueva corrida. EV112 global continúa abierto:268picos,1144depresiones,4transiciones censadas, otros ríos y01545/60m pendiente. Próximo: completar navegación C; integrar kit7/árboles y probar su propio WRP, agua, física, navegación y vista.
