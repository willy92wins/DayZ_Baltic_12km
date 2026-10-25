# EV112 — corrección de ríos y relieve, 25-10-2026

Petición viva: corregir los fallos de ríos y terreno, repetir controles hasta cumplir y avanzar autónomamente para una revisión conjunta. Se autorizan commits de avances verificados y, posteriormente, crear GitHub público. Codex ejecuta e integra en el worktree existente; la revisión cruzada usa Fable 5.1 por su CLI nativo, sin escritores concurrentes en los mismos archivos.

## Base y alcance

S3 inmutable: terreno `6a081028120778d3821574878d4b3845f419c411e661a97d1dc17f3440a4c8a1`, WRP `f07926200627c24f26a8da4df54a03df03e5776f92e2821dd676bbb07dab3f77`. Resultados y POLICYv3 de `shape-gates-20261025` se conservan. Todo candidato nuevo se guarda fuera de OneDrive en `E:/DayZ-Baltic-Build/shape-repair-20261025`.

La petición autoriza preparar la corrección completa de forma autónoma; la aceptación visual del piloto y del mapa sigue reservada a la revisión conjunta. No se convierte un candidato offline en producción aceptada. Agua/islas, c2 limitado a11vértices, Narva y apoyos, carreteras verificadas y disco015-45 de60m se conservan. Un conflicto con ellos permanece explícito.

## Unidades funcionales

1. **Checkpoint Git público.** Auditar el contenido y el historial antes de publicar. Commit de herramientas, pruebas y evidencia verificadas, conservando los informes rojos como tales. Crear `willy92wins/DayZ_Baltic_12km` público si el nombre está disponible; conectar origin y push sin force. No alterar cambios de otras sesiones ni publicar credenciales.
2. **Ríos.** [MECHANISM VERIFIED] `streambed_kit_v31.py:775` ya conoce los tres enlaces declarados mediante `extend.partner/to`; el piloto `continuous_stream_pilot_v31.py:156` los rechaza y `:228` rechaza todo vecino a42m. [DESIGN] Inventariar los51ejes originales y las restricciones, corregir por grupos completos y permitir conexiones solo contra esos receptores declarados. Primero grupos independientes; los solapes requieren soporte común y una geometría de unión, no omitir las aserciones. Conservar ambos extremos originales, agua visual, water_ext, profundidad, lecho, colisión y bosque. Geometría guardada y compilada son puertas separadas. Medir coste de modelos/colisión antes de ampliar una solución cara a todo el mapa.
3. **Terreno.** [DESIGN] Relajación local con transición amplia y límites de altura/topología sobre S3. No mover carreteras, apoyos y disco protegido para apagar el contador. Inventariar picos/pozos por sus caras, visibilidad y dominio; el lecho sumergido no se confunde con el terreno visible. Los casos protegidos o incompatibles quedan rojos, no aprobados por exclusión. El detector de formas no se modifica para aceptar el candidato.
4. **Integración.** Regenerar bury/huella y comprobar agua, protecciones, islas y carreteras contra referencias congeladas. Reasentar y comprobar bosque afectado. Compilar, contrastar binarios/poses, preparar y ejecutar sondas propias con lease cuando el banco esté libre. Capturas/vista humana posteriores. Commit de cada unidad que supere sus puertas; push verificado contra SHA remoto.

## Puertas, contraejemplos y parada

- Suite71actual + regresiones del cambio, Python GIS aislado y worktree indicados en HANDOFF; cero errores/skips. Control de entradas por hash y sin cambios ajenos.
- Ríos:51sitios cubiertos; receptor y extremos conservados; no codos/escalera nuevos; sin huecos de agua, pliegues, autointersecciones ni componentes de colisión abiertos. Pruebas negativas: eliminar cola, cortar unión, alterar receptor, mover pose y ocultar sitio.
- Relieve: mismos umbrales de prominencia/formas, sin nuevos picos/pozos o aristas fuertes; seco/mojado y conexiones conservadas; ninguna violación de carreteras/protecciones. Pruebas negativas: invadir015-45, hundir islote, cambiar agua y degradar una carretera entre muestras.
- Un disparador geométrico solo se adjudica con evidencia independiente de su causa/superficie visible; no se borra ni se convierte enPASS por máscara. El resultado global sigue abierto mientras haya fallos o cobertura necesaria no demostrada.
- Por unidad: hasta tres candidatos de implementación motivados por mecanismos concretos, una revisión independiente y una ronda de reparación de contraejemplos. Dos intentos sin progreso cambian el diagnóstico antes de otro ajuste. No se impone un presupuesto global que autorice entregar fallos como resueltos.

No se alteran estándares ni umbrales para fabricar un verde. El paso siguiente lo decide el resultado observable de las puertas, conforme a gates-ledger §Cuándo para un bucle.
