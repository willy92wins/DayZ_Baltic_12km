# Continuación del mapa: agua gris, cruces y suavizado

La base 1.0 sigue sin aceptar. Este bloque corrige comprobadores y conserva diagnósticos; no cambia el terreno desplegado ni declara resueltos los recuadros grises.

## Resultado local completo

El consumidor recovery-v5 terminó sobre el diagnóstico rechazado 2209df75. Informe `b2ae1ed9f32b24bc4d09dc085aa3eb6c920aeffb1ff34069d34554f2fe278dff`: 17 de 19 puertas pasan; fallan topología local y energía. La arista focal baja de 47,9525 a 37,1978 grados, sin nuevas aristas mayores de 30 grados. 116 cruces, 150 testigos D8 y 392 conos y las nueve puertas de cobertura compilada pasan. Esto no acredita toda la forma del mapa.

Se corrigieron errores del comprobador: vínculo de `approved_control_sha` al JSON del control; claves lógicas de la preparación confundidas con rutas; uso de matrices 15×15 frente a índices globales en topología; y aplicación de la máscara bruta de protección sin la excepción cls5/agua explícita del preparador. Todos los intentos previos se conservan. Los 15 tests de v5 cubren, entre otros casos, que cls5/agua nunca libere P9, carretera ni la máscara efectiva. El resultado real confirma 16 cambios permitidos y cero cambios en esas protecciones. Los fallos de ejecución previos no fueron fallos del terreno ni pruebas de aceptación.

La topología física elimina una pequeña componente de agua de 0,0283188364 m² en celda 860/1186; el área física expuesta total del contexto disminuye 15,2123652 m². La superficie visible cambia también su conteo, con fragmentos muy pequeños y huecos del orden de 1e-13 m². El diagnóstico local reprodujo las áreas y firmas sin aplicar umbrales para descartarlas. La igualdad de componentes por objeto es una puerta añadida por el consumidor; el plan focal permite desplazar cruces hasta 1 m y cambiar área de orilla, pero no autoriza por sí solo perder una componente. Su compatibilidad con el diseño sigue pendiente. El exceso de energía respecto al raw es 2,2454372e-5 frente al allowance 1,5594405e-5. No se relaja ninguna de esas dos puertas ni se empaqueta el diagnóstico.

## Agua gris y cruces

La referencia underlay A conserva tres capturas alineadas con el defecto, un control de pan/restauración y 1.225 alturas nativas que coinciden con B. Los archivos actualizados de análisis enlazan el recibo real de cámara. La comparación B/A′ sigue pendiente; bajar el terreno en una copia diagnóstica no constituye una reparación de producción ni demostraría por sí solo qué LOD selecciona el motor.

La comprobación fresca de los 45 intervalos de cruces usa EV95 y reproduce las 4.592 estaciones centrales históricamente secas. Ninguna está cubierta por P/F sobre terreno; 2.426 carecen de plano en los campos fuente. Pasa cuatro controles y el readset inicial/final es idéntico. Es un diagnóstico central de esos intervalos, no una inspección de todo el ancho ni de las caras ODOL y no atribuye los recuadros grises a esos cortes.

## Preparación global y bloqueo vigente

La ruta de build global revisada exige un PASS real del consumidor V2, los ocho gates exactos y las identidades REC/EV95. Recalcula todas las teselas afectadas frente a B, verifica metadatos y reemplaza únicamente WRP/PAA previstos con agua idéntica. No se ha ejecutado stage ni build. La revisión de fuente y los fixtures de admisión no sustituyen la ejecución.

El diagnóstico de energía con cotas duales queda como preparación matemática, sin LP real ni nuevo optimizador del terreno. No se usa para afirmar inviabilidad global ni para excusar las puertas fallidas.

A las 21:03:39 UTC, la sesión ajena LFSkateboard continuaba activa, con lanzamiento/adopción no disponibles y nuestra sesión sin lease. Se observaron 4,834 GiB libres, por debajo de los 9 GiB exigidos por el consumidor global. No se cerró ni adoptó esa prueba. La pregunta previa de prioridad permanece pendiente; reconsultar el estado antes de actuar.

Siguiente unidad operativa: liberar el banco de forma coordinada, completar underlay B/A′ con el mismo motor, cámara, probe y PBOs fijados; ejecutar el consumidor global idéntico cuando haya 9 GiB libres; construir solo si pasa. Mantener abiertos los cruces de reserva, forma global, bajos protegidos, apariencia dinámica, navegación final y Terrain Builder → navmesh/IA. No transferir las pruebas históricas de coche o IA a una preview nueva.
