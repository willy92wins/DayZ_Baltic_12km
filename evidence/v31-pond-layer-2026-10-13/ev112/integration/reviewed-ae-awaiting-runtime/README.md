# EV112 AE: build revisado, sonda pendiente

**Offline PASS y OT7 SOUND-with-fixes, sin críticos ni mayores.** La sonda del servidor no se ha ejecutado: otra sesión DayZ ocupa el banco y está protegida por actividad humana. No se han adquirido leases, cerrado o adoptado sus procesos ni modificado misiones vivas.

Las fuentes están en el commit local `845295f7b9b0a3ea225ba675755f34efa67a548b`, sin push. El paquete `P:\Mods\@DayZ_Baltic_EV112_LatticeForestV1` contiene los dos PBO verificados por hash.

- [Revisión independiente](review-build-ae-r1.json) y [respuesta a sus hallazgos](build-review-closure-ae.json).
- [Despliegue y hashes](deploy.json); [preflight válido, sin arrancar procesos](runtime-preflight-ae.json).
- [Cierre mecánico del bosque](forest-review-closure-ae.json): 45 etapas conocidas y 50 de 50 nuevas en las semillas 181–190; seis positivos y 25 mutaciones detectadas. Mapa final de 2.561.015 registros.
- [Vista personal preparada](personal-view-ae/README.md): 16 archivos vinculados al paquete, sin instalar ni lanzar el cliente.
- [Bloqueo externo observado](runtime-blocker-ae.json) y [manifiesto de las 386 entradas de evidencia](manifest.json).

El terreno C conserva los 12 islotes secos y solo rellena los 11 vértices de c2 autorizados. Las orillas centrales de c0–c7 cumplen el umbral de 0,03 m; el disco protegido de 60 m de 015-45 sigue pendiente.

## Alcance de la validación

G8 pasa sin exenciones por ventana y conserva las exclusiones estructurales de Narva, kit y puentes. G2/G3 global no exige que todas las ventanas pasen. G9 mantiene tres filas diagnósticas FAIL de juncos. Las mutaciones de distribución excluyen 124 traslaciones WRP fuera del recorte; cada gate principal conserva sus filtros espaciales.

Los fallos originales y sus logs permanecen archivados. El inventario de dependencias se midió después de compilar y no demuestra retrospectivamente cada importación. El readback verifica los objetos compilados, sin decodificar las alturas del terreno. No hay aceptación visual, resultado de motor ni medición de FPS.

## Continuación

1. Comprobar que el banco esté libre y adquirir lease para instalar con `install-ev112-missions.py ae`; después liberar.
2. Lanzar solo servidor mediante `dayz_test_run`, con rutas Windows normalizadas, EV112, sin base mods ni filepatching.
3. Adquirir para adoptar el run propio y esperar `END;4114`. Capturar desde el perfil devuelto por la herramienta con `capture-runtime-probe-ae.py`, antes de cerrar.
4. Cerrar el run propio, liberar lease y comprobar estado. Evaluar con `evaluate-runtime-probe-c.py`, investigar los fallos reales y conservar todos los veredictos.
5. Archivar el intento con `archive-final-ev112.py ae <intento>`. La vista con cliente queda preparada para Guillermo.

No se necesitó renovar el lanzador. Las juntas vanilla conocidas siguen siendo una cuestión pendiente del plan; un FAIL real de la sonda nunca se convierte en PASS por esa nota.

Los archivos de más de 20 MiB y las entradas externas permanecen en sus rutas originales, fijados por SHA256. Este resumen editorial no modifica los recibos originales ni sustituye la sonda.

## Comprobaciones del handoff

Los enlaces nuevos de las notas compartidas pasan (nueve destinos), los 17 enlaces del resumen/mapa existen y el índice tiene una sola entrada de esta sesión, sin duplicados exactos. Los 342 archivos de evidencia copiados coinciden con sus hashes y con los blobs preparados para Git.

La auditoría global del vault conserva **FAIL**: 597 pares vivos nuevos frente al baseline de enlaces existente; cero sesiones sin indexar. El primer comando del runbook apuntaba por error a un baseline de otra auditoría; ambos resultados se conservan, sin cambiar el baseline ni el verificador. El pin global del generador PROJECT-MAP también tiene una divergencia previa; la actualidad de ambos mapas locales se comprobó aparte. [Resultados y alcance](closeout/reviewed-ae-final-checks.json).
