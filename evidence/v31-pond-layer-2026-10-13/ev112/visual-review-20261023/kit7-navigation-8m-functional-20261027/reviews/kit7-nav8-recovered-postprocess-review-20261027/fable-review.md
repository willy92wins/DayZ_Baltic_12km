**Veredicto: SOUND-with-fixes.** La clasificación es correcta y acotada; falta cerrar un hueco de congelación en el packer y ampliar dos controles.

**Confirmado contra fuentes**

- `verify_c_orderly_close.py` y `package_and_deploy_kit7_nav8.py` coinciden con los hashes del gate original (`accepted.json` líneas 45 y 47). No modificados.
- Verificador: exige una sola intención con UTC exacta (l.15), ausencia de ambos recibos (l.16), identidad generador+parent idéntica en 10 campos (l.22), `before < INTENT < after` (l.26), `started_utc <= before` (l.31, rechaza wrapper relanzado porque `generate_navmesh_console.py` exige directorio fresco), returncode `int == 0` (timeout del wrapper da `None` y se rechaza), progreso posterior mayor (l.39), servidor readoptado con 6 claves idénticas (l.45). La vista derivada quita solo ese objeto por identidad (l.50) y el validador original sigue imponiendo CLOSE_INTENT único, sin SERVER_EXIT, códigos 0/-1 y ventana ≤30 s.
- Nombres de recibos coinciden entre coordinador original (`orchestrate…js` l.81), resume (l.41) y verificador (l.55). El cancel script escribe el recibo tras `Kill()` (l.19/25), pero la recaptura a 02:59:44 con mismo PID/creation refuta cualquier kill con independencia del recibo.
- Deadline del resume (`01:59:33.83Z + 18300 s`) es ≤ el original (`Date.now()` en l.67 ≈ 01:59:44 + 18300 s). No relajado. Timeline y progreso actuales son consistentes: 5% a 02:34:18, 7% a 02:44:32, 10% a 03:08.
- Evidencia archivada: dos copias con hash idéntico (4cd8…/58d8…), estado `OWNED_RECOVERY_REQUIRED`, `close: null`, `preserve_for_recovery: true`.
- Los 21 controles del JSON coinciden con el test y los hashes de `sources` con la lista. El control `legacy` prueba que el validador original rechaza el timeline crudo.

**Fixes requeridos**

1. `package_and_deploy_kit7_nav8_recovered.py` l.30: el conjunto obligatorio del gate de recuperación solo incluye packer, verificador y resume. El verificador lee de disco en tiempo de packer `generator-identity.json`, `generator-after-unexecuted-cancel.json`, `completion-before-lease-recovery.json`, `cleanup-before-lease-recovery.json`, `mcp-recovered.json` y `mcp-before.json`; si el `accepted.json` futuro omitiera alguno, una edición posterior pasaría. Fix: añadir esas seis rutas más `lease-recovery.json`, `nav8-recovery-addendum.md`, `test_nav8_recovered_exit.py` y `kit7-nav8-recovered-exit-controls.json` al subconjunto exigido en l.30. Mecanismo: fallo cerrado si el gate no congela la evidencia.
2. `test_nav8_recovered_exit.py` l.29: faltan dos rechazos que cubren el escenario de reinicio: `('generation','started_utc','2026-10-27T02:00:00Z')` (wrapper relanzado tras la captura) y `('generator_after','created_utc','2026-10-27T02:40:00Z')` (PID reutilizado). Ambos ya son rechazados por l.31 y l.22 del verificador, pero no están probados.

**Observaciones menores, no bloqueantes**

- `validate_generation_exit` (verificador l.52–61) no tiene control; un nombre de recibo mal escrito devolvería `exists()==False` silenciosamente. Verificado manualmente que los nombres coinciden; aceptable mientras el gate congele el verificador.
- El packer no cruza `lease-recovery.json.source_sha256` con el hash real del resume. El gate ya lo cubre vía fix 1.
- Si el packer se invoca con ruta relativa, `str(Path(__file__))` en l.30 no estará en el gate y fallará cerrado, igual que el original l.25.

**Respuesta a la pregunta de suficiencia**

La prueba es suficiente como preparación: usa identidad y progreso reales más terminación sintética claramente marcada (`native_acceptance: false`), sin tocar la RUN viva ni las tolerancias. No sustituye la evidencia nativa; el packer sigue bloqueado hasta `completion.json` y `cleanup.json` frescos con cierre ordenado.

No hay que relanzar nada ni reejecutar el resume. Siguiente paso: aplicar fix 1 y 2, regenerar los hashes de packer y test, y entonces crear `accepted.json` con toda la evidencia listada.
