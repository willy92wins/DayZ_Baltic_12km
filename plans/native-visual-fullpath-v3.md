# Una prueba acotada de captura nativa con ruta explícita

NevaV2 pasó cámara/restauración y registró app activa + petición de captura,
pero no produjo imagen en el perfil (ScreenShotes/ScreenShots incluidos).
Conservar FAILED_CAPTURE_PROVENANCE; no equivale a vista aceptada.

[EXACT] `P:/scripts/1_core/proto/proto.c:136-142`: MakeScreenshot admite un
nombre que comience por `$` como ruta completa, documentada en DDS.
[DESIGN] NevaV3 repite exactamente poses/timing/probe, cambiando solo salida
a `$profile:baltic_foundation_visual_native_neva_v3_0.dds` y nombres de evidencia.
Un único run. Si tampoco deja DDS, no seguir probando rutas: agrupar las
capturas con Computer Use y observación de las ventanas reales.
