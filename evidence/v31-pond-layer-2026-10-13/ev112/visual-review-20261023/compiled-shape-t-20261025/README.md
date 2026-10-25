# EV112 T: mundo compilado, sonda preparada

Continúa el checkpoint `collision-integration-20261025`; no modifica su evidencia histórica. Resultado del25-10-2026: **objetos y contenido empaquetado verificados; sonda de servidor NO ejecutada**.

Mundo compilado y empaquetado: `06aae98a7763c131d97a55774da01b9af9db575c37216ebc9d13aaf082579bdb`. Se contrastaron todos los2.578.725IDs/modelos/matrices y las62poses de pilotos son exactas. Los controles negativos de objetos ausentes, añadidos y desplazados fallan como deben. Recursos previos idénticos; solo cambian WRP/config. El lector OPRW ubica la tabla mediante heurística y verifica su contenido completo; no decodifica alturas.

Despliegue separado en `P:/Mods/@DayZ_Baltic_EV112_ShapeRepairT`. Piloto62modelos `988354f4488c0a31c6ab57b3768b24447879aa815e0afdb056864dac2435423f`; agua `97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43`. Se releen y comparan hashes tras copiar. El despliegueR y la base aceptada para pruebas se conservan.

La sonda contiene2823puntos: tres cauces,6extremos originales, márgenes secos, juntas, Narva, cada uno de los1648vértices modificados (7ya estaban en la muestra inicial),86centroides de triángulos y los2extremos del certificado de colisión. Usa el consumidor existente `eval_visual_probe_v31.py`; la calibraciónvanilla previa es `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/collision-diagnostic-20261024-a/runtime-v3.log`. Registrar su hash, versión del motor y nuevo log completo al ejecutar; si difiere el margen, repetir la calibración y diagnosticar antes de juzgar.

El preflight del launcher1.30 pasa con la misión en su raíz autorizada `C:/temp/DayZ_MCP_130_dev/mpmissions/BalticShapeRepairT.BalticTrial`. Dos solicitudes anteriores apuntaban a la raíz de la instancia normal y se rechazaron como `mission_not_allowed`; se corrigió la ubicación, sin editar políticas. La espera de lanzamiento terminó en `active_run_exists/box_taken_before_launch`: otra prueba `LF_CodeLockFix` tomó el banco. No se creó run propio ni se interrumpió el ajeno. `cleanup-status.json` confirma lease/ticket propios ausentes, cola vacía,0órdenes pendientes y cierre sin degradación.

Visita personal preparada, sin iniciar, en `BalticBasicShapeRepairT.BalticTrial`;13paradas en `route-personal.json`. Usar `launch-server.json` primero; después de obtener `run_id`, adoptar mediante `session_acquire_wait`, comprobar bridge y mantener heartbeat durante la prueba. Cerrar ese run exacto y verificar limpieza. No lanzar la visita personal sin Guillermo para el foco.

Censo literal del terreno combinado:327grupos de picos,1156depresiones,5transiciones rectangulares; los hallazgos siguen abiertos. Bosque:0fallos medidos,3727discos del borde inconclusos. Faltan motor/contactos/coste, vista, otros ríos, dominios protegidos,015-45/60m, densidad/contexto del bosque, carreteras físicas, navegación y comparación A/B conChernarus. **EV112 no está cerrado.**
