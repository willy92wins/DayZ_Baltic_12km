# Adjudicación B3G1 coordinador — 29-10

Fable5.1 CLI2.1.310,177.094s, SOUND-with-fixes. Revisión entregada sobre cápsula
sellada. inputs_unchanged=false porque se corrigieron dos scripts PowerShell
mientras el revisor leía su copia: sólo PSModulePath del proceso hijo añadido.
El fallo Get-FileHash no disponible se reproduce en suite R0; suite final verde.
Las postimágenes y diferencias completas quedan adjuntas, sin alterar el recibo.

1. Aceptada obligación de retirar run conocido aun si falla adopción. Rechazada
la receta if(run) close sin lease: fuente oficial server.py5777 exige adopción;
en caso fallido se libera token propio y usa dayz_test_stop(run propio) oficial
(server.py5703), con protección ajena y cola. Nunca cerrar el run ajeno que
devuelva una adopción equivocada. Nuevos negativos foreign/adoption/close.
2. DeploymentB2 incluido obligatoriamente en aprobación externa; no autopin.
3. Regex y patrón de error comprobados sobre bytes reales R0 archivados.
Campo creation_time_utc y BOUND con no_base_mods true confirmados en recibosR0.
4. Texto de logs decode replace conserva SHA de bytes; ASCII de error intacto.
5. Cadencia pasa a10s manteniendo guarda20s; no se relaja deadline180s.
6. Errores host retienen ruta del log y recibo, sin copiar stderr arbitrario a
outcome público. No se pierde evidencia; se rechaza esa ampliación innecesaria.
7. Finally conserva cierre/release/status incluso fallo de escritura; return
FAILED_RECEIPTS si no puede escribir outcome. Escritura CreateNew+Flush evita
pisar recibos existentes. Readiness/HB/preflight enlazados por consumidor nuevo.

Suite final Python y Node positivas/negativas; no prueba Enforce ni física.
Misma misión cbb4, mismos90puntos/low_y y paquetes. Nueva pareja autorizada por
plan B3G1, control primero y candidato sólo con captura/identidad completas.
Sin reintentos internos; si falla instrumento, mantener fallos físicos abiertos.
