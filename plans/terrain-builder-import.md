# Importación y validación en Terrain Builder

**Estado: importación parcial ejecutada el 29-09-2026.** Probe y región física guardados; ASC exportados y comparados; sat/mask y capas generadas; reapertura regional y render Buldozer observados. Evidencia: `evidence/tb-import/informe.md`. Continuación: registro centro/vértice observado, seis anclas y contornos de agua pasan el roundtrip; diagnóstico de avisos y agua funcional pendientes. Evidencia nueva: `evidence/tb-registration/informe.md`.

## Gate A — registro desechable

Crear un proyecto desechable de 128 × 128 muestras, celda de 6 m, e importar `tests/registration-probe/probe_128_6m.asc`. Extensión exterior esperada según AAIGrid/GDAL: E 200000..200768, N 0..768. Importar como referencia `sample_centres.shp`, sin convertir a otro CRS. Comprobar las cuatro posiciones/alturas de `expected.json` y la distribución NW/NE/SW/SE.

Registrar cómo sitúa TB las muestras sobre la malla. Un desfase de 3 m por eje indica posible diferencia centro/vértice: medirlo, no aplicar automáticamente −3/+3. Si el formato/tamaño no es aceptado, registrar mensaje y parámetros y adaptar una copia de prueba sin cambiar la base aprobada. El probe ya se importó y su exportación conserva todas las alturas y la georreferencia raster; la comparación UI con SHP observa −3 m E/+3 m N mediante cuatro selecciones positivas y cuatro negativas. El ensayo analítico `tests/vertex_sampling_probe` pasa el consumidor TB (16.129 muestras interiores exactas); no valida todavía una corrección de costa regional.

## Gate B — maqueta regional

1. Crear proyecto nuevo en el dev; conservar separadas las variantes Z. Importar **uno** de `source/baltic_physical_2048_6m.asc` o `source/baltic_relief3x_2048_6m.asc`.
2. Confirmar 2048 × 2048, 6 m y extensión exterior de ingeniería E 200000..212288, N 0..12288. Primer centro AAIGrid: (200003,12285). No interpretarlo como UTM de Estonia/Rusia. No añadir reproyección ni invertir filas.
3. Importar `sat_preview.png` y `mask_preview.png`, ambos 2048², con sus `.pgw`: tamaño 6 m/píxel, centro superior izquierdo (200003,12285). Asignar `layers.cfg`; leyenda esperada en `P:\DayZ_Baltic_12km_dev\source\mapLegend.png`.
4. Usar copias de `derived/tb_vectors_v1` con PRJ del consumidor (solo etiqueta de ingeniería, sin reproyectar geometría). Para agua, importar `derived/tb_water_outlines_v1/water_outlines.shp`: la importación directa poligonal pierde ocho entidades y huecos. Los polígonos GIS originales siguen siendo autoridad. `water_coverage_union` no fija cotas de lagos. La capa `border` también puede contener frontera marítima.
5. Comprobar contra base-geografica.png: Kotlin y dos orillas del golfo, San Petersburgo/delta/Neva/Ládoga, Narva y territorio occidental, Peipus, Luga y esquina de Ilmen. Contrastar controles de `validation-report.json` y registrar cualquier diferencia.
6. Guardar el proyecto y evidencia de importación. Solo entonces probar Buldozer, texturas y posición de cámara. No exportar un WRP como “verificado” sin inspección.

## Gate C — sector funcional

Los ASC llevan DSM comprimido y fondo marino sintético. **No llevan lechos fluviales diseñados ni objetos de agua interior.** Con altura física, Ládoga queda alrededor de 0,18 m sobre referencia marina: la separación de agua/terreno necesita ensayo; no se deduce viabilidad por ese número.

Medir y colocar assets vanilla para un cruce representativo, entradas/salidas del agua, orillas y un pequeño grupo de edificios. Probar colisión, profundidad/nado y cruces con jugador; rutas de infectados y loot por separado. Los canales pequeños pueden quedar por debajo de una celda de 6 m tras comprimir: registrar ajustes locales de anchura manteniendo posición y conexiones, y consultar cualquier cambio material de la silueta acordada.

Existe el primer config/WRP/PBO de ensayo BalticTrial, verificado por contenido; misión independiente con CE vacía preparada. No hay carga en juego ni navmesh/CE de producción. Evidencia: evidence/playtest/README.md.

## Evidencia mínima para cerrar

- Proyecto TB guardado y parámetros observados, hashes de los ficheros importados.
- Cuatro controles del probe y al menos seis anclas regionales medidos; resultado centro/vértice explícito.
- Capturas propias de TB y Buldozer, errores/logs y configuración usada.
- Para afirmar “jugable”: hash del PBO desplegado, carga en juego y ensayos funcionales documentados. Para afirmar “80–100 jugadores”: ensayo de carga y hardware declarado.

Referencias consultadas 29-09-2026: [AAIGrid/GDAL](https://gdal.org/en/stable/drivers/raster/aaigrid.html), [Terrain Processor](https://community.bistudio.com/wiki/Terrain_Processor:_Introduction), [Test_Terrain](https://github.com/BohemiaInteractive/DayZ-Samples/tree/master/Test_Terrain).

## Parámetros observados en esta instalación

Salida del marco regional: `tb/baltic_physical`; probe: `tb/registration_probe` (el guion en la carpeta de salida del marco fue rechazado, el subrayado aceptado). Zona 31N como wrapper técnico, E 200000/N 0. Regional: grid 2048, cell 6, tamaño 12288, imagen 2048² a 6 m/px; tiles 512, overlap 16, texture layer 12 m. La configuración de textura es provisional de validación.

`source/layers.cfg` con cuatro materiales; export satellite + mask, cuatro materiales por celda, ASCII RVMAT y conversión PAA. La generación concluyó pero produjo avisos: conservar logs antes de nuevas pruebas. `tools/verify_tb_roundtrip.py --repo P:\DayZ_Baltic_12km_dev` compara las salidas auténticas de TB con los ASC originales. No demuestra posición de vértices ni jugabilidad.

## Repetir la evidencia de referencias

Con el Python GIS aislado y los proyectos/exports nativos preservados:

```powershell
python tools/verify_anchor_export.py --repo P:\DayZ_Baltic_12km_dev --out evidence/tb-registration
python tools/verify_water_outlines.py --repo P:\DayZ_Baltic_12km_dev --out evidence/tb-registration
python tools/verify_vertex_sampling.py --repo P:\DayZ_Baltic_12km_dev --out evidence/tb-registration
```

Los generadores `prepare_tb_vectors.py`, `water_reference_outlines.py` y `vertex_sampling_probe.py` requieren un directorio `--out` nuevo y no sobrescriben. `record_mesh_observation.py` registra capturas revisadas manualmente; no es un test automático de UI. Geometría SHP PASS no equivale a DBF fiel: decimales/nombres se degradan al exportar. No usar esos exports como fuentes maestras.

Antes del sector Narva: evaluar muestreo del DSM en vértices sin promediar ciegamente alturas ya recortadas por mar, comprobar canales estrechos y límites externos. Una corrección productiva requiere gate específico de costa y no cambia el recorte ni escala XY global. El ensayo plano solo verifica la aritmética y serialización del consumidor. Requisitos trazados: P1/P2/P3/P4/P8.

## Gate C — checkpoint de Narva 29-09-2026

Alcance trazado a P2/P3/P4/P8: ensayo local de agua/cruce vanilla, sin variar recorte ni escala global. Proyecto `tb/narva_trial`; evidencia y reproducción en `evidence/narva/informe.md` y `tools/narva/`.

V2: 289 lecturas de cuadrícula + 289 de perfil separadas sostienen la fórmula nativa local X=200000+6*col, N=6*(2047-row), diagonal NW-SE. Corrige la predicción derivada de la observación UI; no es una demostración global. Se preparó/importó una corrección local reproducible: 202 vértices en radio 48 m; ASC nativo PASS en 4194304 muestras. Puente a cota de tablero 2 m, cota TB 1.476612; restaurado tras rebuild y guardado. La lectura V3 de ambos extremos pasa, y la consulta de agua detecta mar; no cerrar Gate C hasta prueba real con jugador.

Discriminador V3 ya ejecutado: fijo sin refit, 289 alturas en rejilla, 289 de perfil, 34 extremos (ancho 8 m) y consultas de mar/pond/profundidad. Rechazar incompletos; tolerancias detalladas en el informe. Pond oculto por asociación con crashes de cierre. Los tests de superficies no prueban locomoción, agua elevada ni navmesh.

Continuación de Gate C: candidato de agua guardado, reabierto y exportado otra vez; alturas/materiales/registros de objetos conservados, PBO compilado. Falta sonda posterior. El acceso MCP se recuperó y permitió ensayos reales, pero el mundo sigue fallando antes de confirmar Mission con aviso de navmesh. NavMeshGenerator fue rechazado por Computer Use; autorización específica pendiente. Usar misión BalticTest.BalticTrial y observador automático cuando exista carga de mundo. Las sondas V3 y basal de agua ya se recogieron; el recheck del candidato es distinto. El gate P2/P4 exige además cruce/agua reales. Un arranque posterior de Buldozer fue detenido por Steam; discrepancia de registro local/host corregida, prueba de consumidor pendiente. Evidencia: `evidence/render-water/post-reopen/`.
