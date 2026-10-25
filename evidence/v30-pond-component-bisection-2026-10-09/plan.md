# EV41 — aislar piezas de charcas frente al mar

El residual seco está en x2718,4852496 z6812,812874. EV26 traslada seis charcas y suelo juntos; EV33–35 son controles de material, con EV35 invalidado por referencia gráfica inestable. Ninguno ha separado la presencia de las piezas de la contribución del mar. No más cotas ni parámetros por tanteo.

Un diagnóstico A/B/A: paquete EV28 exacto frente a copia cuyo WRP omite únicamente los cuatro objetos identificados por el censo compilado EV26 (16800387/388/454/455). Terreno, configuración, texturas, demás objetos y PBO de modelos de agua exactos. No es un fix: retirar seis charcas de diseño sería una regresión de producto. Solo discrimina si el residual requiere esas piezas.

Antes de cambiar A→B, exigir referencia normal y estable, sin cielo magenta ni cambios de carga de textura en seis frames durante ≥25s, misma cámara/hora/viento. Si no reproduce el halo, INCONCLUSO. B y vuelta A requieren iguales condiciones y matriz. PASS de discriminación: el halo se conserva sin piezas (rama océano/terreno) o desaparece y vuelve (rama piezas pond). Un resultado ambiguo no autoriza borrar las charcas. Un A/B/A, una reparación instrumental únicamente. No lanzamiento con el conector desconectado ni lifecycle fuera de lease.

Contratos verificados: wrp0wzd.read/write (tools/terrain/wrp0wzd.py), attach_navmesh.read_pbo (tools/playtest/attach_navmesh.py), AddonBuilder y FileBank ya ejecutados con esta fuente EV25/28. Todo en carpeta nueva; no tocar P:/DZ, vanilla, perfiles ni paquetes principales. Fuente de objetos: v30-low-water-components-20261009/cohort.json, cuatro IDs y modelos fijados antes de crear la variante.
