# Continuidad V30 — NM, consumidores y reinicio (03-10)

**NM generada/cargada, aceptación global pendiente.** Paquete302b000b con WRP0255d007,
NM43916629, agua339fa17f; candidato40d8. Archivo grande en E:, copia desplegada
aislada en `P:/Mods/@DayZ_Baltic_ContinuityV30_Nav`.

| Evidencia | Resultado |
|---|---|
| generation.json | CLI8m16s,código0,453.413.960bytes |
| structure.json |983²teselas recorridas; PASS estructural empíricoTESM6 |
| package-verification.json |Solo NM reemplazada;6826entradas intactas,WRP idéntico |
| nav-runtime-verification.json + nav-engine.log |37controlesgrafoPASS,FAIL por5alturas fuera de0,801m |
| shore-readback-verification.json + shore-engine.log |1332alturas coinciden,13mojados sin profundidad positiva;FAIL |
| open-findings.json |Coordenadas/valores de13puntos y5casos; no modifica gates |
| probe-compile-fix.json + before-init.c |Identidades de la corrección de Formula too complex |
| native-pre-reboot-backup.json |206archivos respaldados con SHA256;TV4P2fa6d30b guardado |
| lifecycle.json |Tres cierres orderly_close;lease liberado,caja sin runs/foreign |

Runs: generación3d93327f, grafo944442f7, lecturas7971ec26. Las referencias de
muestreo se congelaron antes del run en `E:/DayZ-Baltic-Build/v30-continuity-dedup-package/`.
Su metadataworld identifica e556f576, anterior al cambio exclusivo de NM; el
paquete302b000b y `package-verification.json` documentan ese cambio. Las misiones
V4 cambian la concatenación, no coordenadas/esquema/tolerancias. La misión normal
visual todavía no se ejecutó con cliente.

`generation-run-compile-error.RPT` (~184MB) y backups documentales before se conservan
locales, fuera del commit; las dos fuentes before-init.c sí están versionadas; el RPT íntegro prueba que no compiló la primera sonda. No usar
ese run como readback exitoso. Extracto de error y hashes en el manifiesto local.
Los RPT de los dos consumidores son nuevos y sus logs tienen terminales completos.

Handoff completo y siguiente bloque:
[navmesh y reinicio](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-navmesh-y-reinicio.md>).
No equivalen a aceptación de locomoción, apariencia, mareas completas o80–100jugadores.
