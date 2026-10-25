# Recuperar el editable del candidato V30 — 02-10-2026

Subpaso de la fase 5 aprobada en `water-ground-rebuild-v1.md`. No cambia
geometría, diseño, materiales ni el paquete usado por las pruebas de navegación.
Terrain Builder instalado muestra File → Import → Maps y archivos WRP en su
selector (observación nativa del 02-10, proyecto vacío).

## Procedimiento y aceptación

1. Copiar el source de `v30-delta-preview/world/stage/BalticTrialWorld` a una
   carpeta nueva en E:. El WRP `3e7d298f` contiene las alturas a84dfff0 y 17.631
   objetos. Resolver las rutas de material en un namespace de editor nuevo,
   conservando sus bytes salvo el prefijo; registrar cada transformación.
   Montar solo aliases nuevos de los recursos propios. No escribir en DZ.
2. Importar la copia WRP completa en un proyecto vacío y guardar el TV4P en E:.
   No reconstruir el relieve ni regenerar texturas por defecto. Observar las
   opciones reales del importador antes de confirmar.
3. Exportar, cerrar y reabrir el TV4P; exportar otra vez. Comparar todas las
   alturas, rejilla de materiales y poses/modelos. Si el importador renumera
   IDs, declararlo y comparar además el multiconjunto exacto de modelos/poses;
   no esconder pérdidas o duplicados detrás de un nuevo ID.
4. PASS solo con igualdad semántica completa, persistencia y dependencias
   resueltas. La importación o un archivo TV4P por sí solos no pasan. No sustituir
   el PBO desplegado ni invalidar su navmesh si el editable difiere.

Presupuesto: una importación de mapa completa; si falla, conservar el resultado
y evaluar el importador ASC conocido como segundo camino. No repetir clicks
sin progreso ni inventar el formato ALB1. Liberar CU durante copia/cálculos.

## Anclas

- `tools/terrain/wrp0wzd.py:15–76`: lector/escritor del WRP editable real.
- `tools/terrain/derive_world_v30.py:35–49`: alturas, nueve puentes y piezas.
- `tools/terrain/apply_surface_v30.py:28–50`: materiales de cuatro superficies.
- `tools/navigation/verify_native_persistence.py:10–34`: comparación completa
  de exports; IDs de importación nueva se diagnostican por separado.
- El importador es opaco: aceptación por experimento de ida/vuelta, sin
  afirmar un contrato universal de Terrain Builder.

## Resultado del importador y alternativa ASC

El 02-10 el importador WRP rechaza expresamente la cabecera0WZD; cero objetos
y cero mapframes. Captura y mensaje íntegro en import-result.json. No se
varía a ciegas la cabecera ni se interpreta la selección de WRP como soporte
de todos los formatos.

Se ejecuta la alternativa prevista: copia íntegra verificada del editableV29
a native-asc en E:, ASC64d4f160 añadido, apertura/Save As nativos y raíz de
mapframe aislada antes de Rebuild. Primero comprobar todos los vértices; luego
resolver materialesV30 y sustituir el aguaV29 mediante importador de objetos
nativo. Mientras haya agua/materiales antiguos la copia NO representaV30.
Los archivos ALB1 se copian opacos; no se reconstruyen sus formatos.

CSV preparado: `E:/DayZ-Baltic-Build/editor-v30-delta/water_objects_v30_absolute.txt`,
17.622 piezas, posiciones tomadas del WRP canónico y guardadas en altura absoluta.
No incluye los nueve puentes. Los nombres de plantilla de V29/V30 coinciden:
resolverlos exclusivamente contra `P:/baltic_water_v30`, no contra la biblioteca
anterior. La conversión decimal vuelve exactamente a los float32 de referencia;
el importador nativo y la persistencia siguen pendientes. Evidencia:
`water-import-preparation.json`. `pre-open-dependencies.json` enumera las
14 referencias absolutas que conserva la copia TV4P antes de Save As.

Satélite y máscara completos preparados en `world/native_sources`: 12.288²,
1m/píxel, equivalencia de todos los píxeles y 3.968 solapes comprobados.
`surface-source-preparation.json` fija hashes y límites. El layers.cfg nuevo
usa rojo=coníferas y verde=hierba, como `build_surface_v30.py:38–41,150–151`;
el archivo legado `source/layers.cfg` conserva la correspondencia inversa.
No es un defecto demostrado del paquete actual, sino una incompatibilidad
que se evita al regenerar capas desde estas fuentes. Abrir/importar/reexportar
sigue pendiente. Actualización 03-10: la copia se abrió y Save As creó
`native-asc/delta_v30_native.tv4p` (SHA inicial `2e5de2c8`). Después Guillermo
aplicó la raíz `P:/baltic_editor_v30_delta` y se guardó por CU: SHA actual
`fd8b3905`, original `road_v29.tv4p` intacto. La raíz aislada está verificada en
disco; el ASC V30 todavía no se ha importado. Estado y límites del control
nativo en `evidence/v30-native-editor-2026-10-02/README.md` y su recibo
`root-isolation.json`.
