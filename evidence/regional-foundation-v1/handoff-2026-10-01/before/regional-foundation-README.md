# Base regional en curso

Puntero operativo: `../../plans/regional-foundation-execution.md`. La petición
sigue abierta hasta terreno y navmesh regional; este fichero es un checkpoint.
No se ha importado ni desplegado el candidato nuevo de alturas. Base0.2 y
candidato0.3 conservados por hash. Estado actual y límites:
[continuation-v9.md](continuation-v9.md). Los apartados siguientes conservan
la evolución; no sustituyen LIVE-STATE. La copia TB está abierta, con carpeta
del mapframe corregida y guardada; falta activar Import > Terrains. CU liberado.
Consumidor V3 completó81212 consultas agua/tierra y314nav/15rutas contra el
baseline: FAIL esperado por alturas antiguas. Run propio cerrado y lease liberado.

## Evidencia cerrada

- Estanque elevado a6m: dinámico y persistido en WRP diagnóstico pasan huella,
  clasificación y lancha propulsada.15 piezas vanilla,89.52m,salud600. Los WRP
  diagnósticos se derivaron del exportado: no equivalen a un nuevo guardado TB.
- Estanque inclinado1%: constructor en radianes, SetOrientation en grados;
  propulsión posible pero SurfaceIsPond=false. Descartado para producción.
- Malla reconstruida inclinada con objeto horizontal: superficie hidráulica
  constante en el eje, no la pendiente geométrica. Control plano positivo.
  Clase con ruta duplicada excluida; comparación válida por ruta P3D directa.
- Piezas vanilla horizontales de26m con centros cada25m y salto0.05m:936 muestras
  de agua,116 de lancha,89.24m,85 muestras propulsadas,salud600, cuatro juntas.
  PASS dinámico local hacia arriba; pendiente visual, regreso, WRP y región.
- Verificadores: tres fixtures reales positivos y30 mutaciones negativas pasan
  `tests/test_water_probe_controls.py`. No prueba adicional del motor.
- Inventario completo:16.263 componentes de agua conectada,2.010 anillos internos;
  no asignar una cota común al componente Peipus–Narva. Inventario separado sin
  ríos/canales:239 masas >=900m²; pequeñas conservadas como referencia.
- Red OSM:11 anclas conectadas,55 rutas por pares,109.21km de aristas únicas,
  25.188 aristas. Fuente/versiones/nodos compartidos contrastados con PBF.

## Trabajo vivo

`prepare_regional_road_grades.py`:124 cadenas,36.428 muestras, perfil <=5.5%,
128.566 vértices modificados en copia,0 vértices de agua alterados. **FAIL** de
triángulos reales:1.175 muestras transversales,173 pendientes y304 desviaciones
de cuerda. Corregir antes de importar; el perfil ideal por sí solo no basta.

`prepare_regional_fairways.py`:rutas dentro de80m del eje y protección de283
islas >=36m². Primer intento falla conectividad del corredor; discriminador por
componentes/posición añadido. No hay cauces nuevos ni archivos de aceptación.

Los archivos de modelo de `tests/water_geometry_v1` son experimentales locales,
no assets adoptados. Las nuevas compilaciones y salidas grandes están ignoradas.
Grok respondió402; Gemini dio una opinión de diseño, sin confirmar mecanismo
del motor. Ver `review-reconciliation.md` y `water-design-decision.md`.

## Continuación: candidato combinado v4 y agua recortada

Estado vivo: HANDOFF.md. Continúa el trabajo; no es cierre de fase.

- `combined-geometry-v4.json`:0 pendientes nuevas>35grados,0 fallos de rasante/interiores y junctions,0 profundidad<3m en corredores. ASC `e305b35fd8b89373de8303fb4b874f7822623e7516ddca0c4dd8d50f231c0816`.
- `combined-foundation-v4.png`:vista de ingeniería, sin arte ni vegetación colocada. Reserva seca:0.126km2 editados de5.941km2.
- `static-shape-v1.json`:FAIL de controles exteriores; se conserva. `static-shape-v2.json`:PASS tras corregir exclusivamente las poses WRP por bounding_center ODOL;936 consultas agua,529 hueco/exterior,116 lancha,89.41m/salud600. No prueba de importación TB ni visual.
- `regional-water-assets-v1.json`:9709 instancias/5744 modelos propios, material vanilla, piezas48.02m. Modelo lleno compartido;291543 triángulos en modelos únicos. No equivalen a coste medido. Build en curso.
- Próximo:objetos/alturas en editable nativo, reapertura, nuevo WRP y NM12.5, prueba regional y carga. Mantener baseline y SAT1M.

Continuación: agua regional v2 compilada y verificada. PBO SHA256 f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3, 26208358 bytes;10152 instancias/6187 modelos,28766 juntas,max25mm,0fallos. Consumidor GIS79420 muestras sin agua ausente ni fondo<3m; islas preservadas. Copia completa tb/regional_foundation_v1 verificada8958 archivos. Se prepararon ASC,CSV,verificador nativo y P:/baltic_water junction al compilado propio. El usuario detuvo CU con Escape físico al intentar abrir la copia; ninguna importación ni WRP/NM nueva confirmada. No llamadas CU posteriores. Próximo: reobservar editor cuando el usuario reanude, abrir copia e importar/rebuild, biblioteca agua,CSV,guardar/reabrir/exportar; después NM nueva y consumidor. Sin lease/run/shell propio pendiente.
