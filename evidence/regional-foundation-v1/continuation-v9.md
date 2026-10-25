# Continuación: alturas v9 y consumidor regional

Trabajo abierto; no es una entrega del mapa ni una navmesh nueva.

## Fuentes verificadas

- ASC v9 SHA256 `335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2`.
  Copia para el editor: `tb/regional_foundation_v1/foundation_v9.asc`.
- `combined-geometry-v9.json`: pendientes afectadas máximo34.16955°, cero
  triángulos fuera del límite;29772 muestras interiores de rasante y1472 de
  cruces/intersecciones sin fallos. Cruces de agua y accesos cercanos siguen
  excluidos de esa afirmación y requieren sus puentes, no rellenos de cauce.
- `contour-water-consumers-terrain-v9.json`:79420 consultas en los corredores
  principales, cero agua ausente y cero profundidad<3m, ancho muestreado24m.
- `lake-interior-audit-v9.json`:239 lagos tienen cinco vértices interiores con
  agua. No acredita toda su superficie, conectividad ni navegación de todos.
- `protected-island-native-plane-v9.json`:283 islas, mínimos de planos sobre
  intersecciones reales; orillas no inferiores al agua salvo1.11e-6m de
  redondeo, interiores a6m del borde y representantes con resguardo0.35m.
- `lake-217-island-tradeoff-v9.json`: el borde alto deV8 secaba indebidamente
  gran parte del lago217;47 vértices corregidos.785/965 muestras mojadas enV9,
  frente189 enV8 y901 enV4. La malla sigue aproximando esa orilla pequeña.
- `combined-protected-area-review-v9.json`: reserva seca5.941332km²,
 0.126360km² editados; mediana3.93→3.95m. La reserva es la máscara de diseño
  conservada, no delimitación legal. Vegetación pendiente.

## Prueba de la sonda en el motor

Run `a8d23890-8019-4328-a1df-5ed4a24ee22a`, servidor de ensayo sin cliente,
mapa anterior `@DayZ_Baltic_Tile12p5V1`, PBO SHA256
`55d7163c06b53ebc8a5b9336a8b653e14d78eb06722b232d1a6550cd1581bebc`.
Misión V2 compiló y leyó80615 muestras de agua, pero terminó
`MALFORMED_WATER_INPUT` al primer registro terrestre con campo vacío.
`P:/scripts/1_core/proto/enstring.c:396–421` explica el mecanismo: Split
inserta solo fragmentos no vacíos. Registro
`consumer-v2-incomplete-water.log` SHA256
`000773c18514dfa2226352469ba6d2e9ee55438a49036f8ff6df5fe0b486771b`.
`consumer-v2-incomplete.json` rechaza el final ausente y nav sin ejecutar.
No contar este run como control negativo completo ni como aceptación regional.
PluginInventoryDebug y avisos de CE auxiliares siguen apareciendo; no son un
fallo de compilación de la sonda.

V3 sustituye el campo vacío por cero explícito, sin cambiar consultas ni ASC.
`consumer-reference-v3.json` SHA256
`25a79815f5ad64b0fcd5a0dbedd3497ae3e70c32b9cd57a202bbd46db82635ea`.
81212 consultas agua/tierra,314 muestras nav y15 rutas. Misión SHA256
`728d470c8ddcce247d7a0c2b26a64e10e49ec298fc5fd2adf97f8bbbe2456e5c`.
Lint1 archivo, cero errores/avisos. Cinco tests de protocolo pasan: dos formatos
válidos,10 mutaciones de esquema,6 fallos semánticos y controles de navegación.
Son controles del verificador. Después, V3 ejecutó el motor en el run
`3edbd6e3-229f-43dd-a50f-04ed27a16814` contra ese mismo baseline: completó
81212 consultas agua/tierra,314nav y15rutas. Registros inmutables:
`consumer-v3-baseline-water.log` SHA256
`a60c1d64fb0ed606b31026e066b978cc5f363a4469e7cc1fc1e2427ad309883d` y
`consumer-v3-baseline-nav.log` SHA256
`3ab8b81feff6acb0327cdde55a17877fb40455e6487a9b3b6fb1c46a2c836d9f`.
`consumer-v3-baseline.json`: FAIL esperado contra V9,80629 consultas
agua/tierra fallan, error máximo13.29254963m. Nav: cobertura, rutas y filtro
negativo pasan; alturas fallan, máximo12.51346797485m. Prueba del lector y
control de mundo antiguo, no aceptación del nuevo terreno.

## Bloqueos y siguiente secuencia

SUPERSEDED 01-10: el bloqueo anterior de Import > Terrains fue resuelto.
V9 está importado, reconstruido, guardado y exportado en la copia.
TV4P SHA139d2423cecff69ba1952ab26779da915820a4ad2bb0f075265adcfe12b51bb2.
Último WRP SHAfe02d6e059e307ffd9ef49af87ee6ccaf264ce0c5f8ca88bde3807b9bdb0ad8b.
Se corrigió la cota absoluta de los tres puentes tras Rebuild. La comparación
actual conserva22 diferencias de borde<=5.96e-8m y dos cotas de puente<=7.16e-7m;
XY/rotaciones/modelos y materiales exactos. Gate estricto sigue FAIL.
Agua no importada:3 puentes/0 aguas, solo Narva_Vanilla.tml guardado.
CU detenido por Escape al intentar crear biblioteca Baltic_Water_V2.
Ver [handoff canónico](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-01-dayz-baltic-handoff-terreno-v9.md>) y
[lectura actual de archivos](handoff-2026-10-01/state.json).
Permisos anteriores no requieren repetirse; este cierre no reactiva CU.

Run V3 cerrado ordenadamente en1.7003s, retired=true, exit_metrics_valid=true,
stop_required=false. Release confirmado con cleanup terminal_safe=true y
session_status self=none. Sin run ni lease propio pendiente.

`prepare_foundation_package.py` exige dos exports nativos completos aceptados
por el verificadorV9, compara terreno/materiales/objetos entre ambos y preserva
SAT1M4775RVMAT/2048PAA. Prueba negativa con los exports antiguos los rechaza y
no crea el paquete: `package-baseline-negative/first.json`. Camino positivo
completo pendiente de exports. El NM antiguo solo sirve como bootstrap
etiquetado para arrancar el servidor de datos; no acredita navegación nueva.

`package-config-preflight/verification.json`: CfgConvert real compiló y volvió
a texto la configuración, Baltic_Water requerido y tileWidth12.5 conservados;
pins de agua/NM y paleta verificados. PASS_OFFLINE_DEPENDENCIES_AND_CONFIG_COMPILE,
sin paquete de mundo nuevo ni prueba de carga nueva.

`tools/navigation/build_foundation_package.ps1` preparado para compilar en
carpetas nuevas, con dependencia baltic_water y verificación de los hashes del
stage antes de copiar. Conserva SAT1M sin helpers de materiales antiguos;
verifica paridad PBO/compilado y etiqueta la navegación bootstrap como obsoleta.
Parser PowerShell sin errores. Ejecutado contra el stage regional anterior:
exit1 esperado y ninguna carpeta de build creada (`build-baseline-negative.json`).
Camino positivo sin ejecutar; requiere los dos exports nativos aceptados.
Consulta MCP de la sesión anterior (histórica): self=none, box.occupied=false, pending_commands=0; advierte
SERVER_CODE_FRESHNESS stale en el cliente MCP. No se modificó infraestructura.

1. V9 ya importado: comprobar reapertura/export y resolver el gate de precisión explícitamente.
2. Biblioteca de agua desde `P:/baltic_water`, CSV `water_absolute_v2.txt` en altura absoluta.
3. Guardar/reabrir/exportar completo, comparar alturas/poses/SAT1M con
   `verify_foundation_native.py`. No Generate Layers.
4. Empaquetar, generar NM12.5 nueva, fijar hashes y ejecutarV3/lancha/IA/cliente.
5. Carga descriptiva y archivo reproducible;80–100 jugadores sigue sin probarse.

No commit de integración: native/WRP/NM pendientes, hay cambios anteriores
sin commit conservados y `diagnostics/` ajeno intacto. `git diff --check` pasa
con cr-at-eol. Skill local `dayz-terrain-workflow` amplía lecciones de islas y
Split; su helper quick_validate no pudo ejecutarse por PyYAML ausente en los
entornos comprobados, aunque no cambió el frontmatter ni los enlaces existentes.

01-10: session_status no devolvió respuesta durante el cierre. Dos DayZDiag nuevos
(274188/287828) tienen propiedad desconocida; no tocados. No declarar caja libre.
