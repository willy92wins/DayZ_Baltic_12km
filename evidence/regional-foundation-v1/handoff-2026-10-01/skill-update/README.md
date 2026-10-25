# Actualización de conocimiento de terrenos — 01-10-2026

Encargo: incorporar a las skills el aprendizaje nuevo del proyecto. Se amplía
[dayz-terrain-workflow](C:/Users/guill/.codex/skills/dayz-terrain-workflow/SKILL.md)
y [regional-relief.md](C:/Users/guill/.codex/skills/dayz-terrain-workflow/references/regional-relief.md).
La skill existente cubre el flujo; no se crea otra con alcance solapado.

## Cambios

- Mejor descubrimiento de la skill para ríos navegables, carreteras lisas y
  objetos desplazados tras importar.
- Comparación de objetos por ID/modelo y dimensiones de la pose: después de la
  secuencia de importación/Rebuild, los tramos exteriores tenían deltas de
  -4.798312246799469m y -0.43466782569885254m. No se aisló la operación causal.
- La corrección de cotas dejó diferencias verticales máximas de
  7.152557373046875e-7m. Se documenta la comprobación del WRP completo frente
  a la cifra redondeada de la UI y la necesidad de verificar persistencia.
- Las 22 diferencias del heightfield están en la última fila o columna y
  tienen máximo 5.960464477539063e-8m. La explicación por redondeo interno
  permanece como hipótesis; el criterio exacto conserva su FAIL.

Los conocimientos anteriores sobre render/materiales, agua recortada, islas,
sondas, rasantes, navmesh y límites de rendimiento ya tenían referencias en
la skill y se conservan. Se comprobó también el lago217: 969.478746m² y
901/189/785 muestras mojadas en V4/V8/V9; la cifra anterior de la skill era
correcta y no se cambió.

## Autoridad y evidencia

`DayZ-Modding-Knowledge-Pack/CONTRIBUTING.md:25–31` permite editar en vivo las
skills ausentes de `promotions/promotion-map.json`. La consulta estructurada
encontró 70 artefactos y cero coincidencias de dayz-terrain-workflow. Hash
del mapa: `dbeba46de5c71ab15327031cd74d46e90fb4a801f06b43a2299b64c9f5771440`.
No se modificaron targets gobernados ni cachés de plugins.

[source-check.json](source-check.json) conserva hashes, comparación de los WRP
completos contra el ASC y el referente anterior, y copias previas identificadas.
Se usó el parser existente hasta EOF; no se añadieron verificadores del mapa.
Las copias de los documentos anteriores están en `before/`.

## Comprobación y límites

[validation.json](validation.json) registra la revisión estructural de los dos
campos simples del frontmatter, los enlaces locales, la preservación de los
archivos fuera del cambio, los hashes de evidencia y el diff de documentación.
El helper `quick_validate.py` no pudo iniciarse porque el Python empaquetado
carece de PyYAML; se conserva ese resultado y no se declara ejecutada una
validación YAML general. No se instalaron dependencias para este cambio.

Esto comprueba documentación y reproduce observaciones offline sobre binarios
guardados. No es una evaluación de comportamiento de un agente ni una nueva
prueba del motor. No hubo Computer Use, gestión de procesos, importación de
agua, regeneración de navmesh, cambios del mapa o del criterio de aceptación.
La exportación V9 sigue FAIL y su reapertura sigue pendiente.

Se añadió un enlace a este recibo en el
[handoff de la sesión](C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-01-dayz-baltic-handoff-terreno-v9.md).
No se hizo commit: la skill es una fuente local fuera del repo del mapa y el
árbol de ese proyecto conserva trabajo previo sin integrar.
