# DayZ Baltic 12km — handoff del terreno V9

Fecha: **01-10-2026, Europe/Madrid**. Encargo de este cierre: documentar el estado
actual; no continuar la edición ni activar Computer Use. Sesión única, integrador.

**Estado: base anterior probada y conservada; terreno V9 importado y guardado,
pero integración regional de agua, aceptación nativa y navmesh nueva pendientes.
No es versión 1.0 ni base regional terminada.**

## Entrada para continuar

- Repo: `P:\DayZ_Baltic_12km_dev`, equivalente a
  `C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev`.
- Leer primero [HANDOFF vivo](<P:/DayZ_Baltic_12km_dev/HANDOFF.md>),
  [CLAUDE.md](<P:/DayZ_Baltic_12km_dev/CLAUDE.md>),
  [producto](<P:/DayZ_Baltic_12km_dev/product-spec.md>) y
  [plan vigente](<P:/DayZ_Baltic_12km_dev/plans/regional-foundation-execution.md>).
- Contexto estable: [project-brief](../10_Projects/DayZ_Baltic_12km/project-brief.md).
- Evidencia de esta lectura: [state.json](<P:/DayZ_Baltic_12km_dev/evidence/regional-foundation-v1/handoff-2026-10-01/state.json>).
  Contiene hashes completos, tamaños, fechas UTC, comparación de los tres
  puentes y los 22 vértices diferentes. Capturado 01-10 a las 02:25 UTC.
- [Continuación técnica V9](<P:/DayZ_Baltic_12km_dev/evidence/regional-foundation-v1/continuation-v9.md>) y
  [evidencia regional](<P:/DayZ_Baltic_12km_dev/evidence/regional-foundation-v1/README.md>).
  Los apartados históricos no sustituyen este estado.

## Producto que hay que preservar

Mapa de **12,288 × 12,288 km, heightmap de 2048 × 2048 con paso de 6 m**,
región báltica condensada, límites v0 aprobados. Una transformación XY global:
no agrandar localmente San Petersburgo. Conservar el closeup completo, delta,
islas, costa, lagos, ríos, Narva/frontera y ribera occidental para el lore.

Prioridad: terreno, agua, corredores navegables, rasantes suaves y navmesh;
edificios, vegetación colocada, carreteras físicas y decoración después.
Vanilla primero para edificios y vegetación. La reserva Mshinskoye y el mosaico
de biomas son esenciales; su máscara actual es de diseño, no un límite legal.
Se aprobó exageración selectiva de Z por jugabilidad. Los originales se conservan.

Lancha vanilla con margen para barcos medianos. Envolvente de diseño utilizada:
12 m de eslora, 4 m de manga, 1,5 m de calado, 4,5 m de altura; corredor principal
de 24 m, profundidad mínima 3 m y gálibo de puente 6 m. No equivale a haber
probado todos los barcos ni todos los ríos. Objetivo 80–100 jugadores; hardware
y capacidad bajo carga real aún sin demostrar. Búnker occidental sin diseñar.

## Artefactos y aceptación

| Pieza | Estado comprobado |
|---|---|
| Base 0.2 desplegada | `P:/Mods/@DayZ_Baltic_12km/Addons/narva_trial.pbo`, SHA `fd2c7023…`; intacta. |
| Candidato regional 0.3 anterior | `P:/Mods/@DayZ_Baltic_Tile12p5V1/Addons/narva_trial.pbo`, SHA `55d7163c…`, 542.360.979 bytes; intacto. |
| WRP regional anterior | `tb/regional_outline_v3/baltic_regional_persisted_v3.wrp`, SHA `9bf50853…`. |
| NM anterior 12,5 | `tb/regional_outline_v3/navmesh/baltic_regional_tile12p5_v1.nm`, SHA `eb0f131e…`, 439.493.936 bytes. **No pertenece a V9.** |
| Fuente V9 | `tests/regional_foundation_combined_v9/baltic_regional_foundation_v9.asc` y copia `tb/regional_foundation_v1/foundation_v9.asc`: mismo SHA `335554a6…`. |
| Editable V9 | `tb/regional_foundation_v1/narva_trial.tv4p`, 18.791 bytes, SHA `139d2423…`; guardado 30-09 a las 22:54 Madrid. |
| Último export nativo V9 | `tb/regional_foundation_v1/baltic_foundation_bridges_v9.wrp`, SHA `fe02d6e0…`, 17.307.994 bytes; **3 puentes, 0 objetos de agua**. |
| Addon de agua preparado | `build-output/regional_water_assets_v2/baltic_water.pbo`, SHA `f9a5cdf7…`, 26.208.358 bytes. No integrado en el WRP V9. |

El paquete anterior archivado está en
[packages/baltic-regional-v0.3-candidate](<P:/DayZ_Baltic_12km_dev/packages/baltic-regional-v0.3-candidate/README.md>).
Incluye fuentes/editor, config y misión limpia; el README conserva sus límites.
Hubo carga de cliente/servidor, 279 consultas nav, seis rutas y locomoción de IA
sobre el terreno anterior. La misión limpia incluida no se volvió a ejecutar en
ese checkpoint. El servidor vacío midió unos 2185 MiB residentes; no demuestra
80–100 jugadores. **No cargar dos variantes BalticTrial simultáneamente.**

## Qué quedó hecho en V9

Se importó `foundation_v9.asc`, se reconstruyó el heightfield, se guardó y se
exportó. La carpeta del mapframe apunta a `tb/regional_foundation_v1`.
**No se regeneraron las capas de materiales.** Cabecera y bloque completo de
materiales del último WRP son idénticos a la referencia aceptada SAT1M.

Resultados offline, antes del consumidor del motor:

- `combined-geometry-v9.json`: pendiente máxima de triángulos afectados
  34,16955°, ninguno >35°; 29.772 muestras interiores de rasante y 1.472 de
  intersecciones sin fallos. Excluye proximidades de agua y accesos reservados
  de Narva; no acredita que toda conexión pueda recorrerse ya en coche.
- `contour-water-consumers-terrain-v9.json`: 79.420 consultas de corredores,
  sin huecos y con profundidad ≥3 m sobre los planos de agua de diseño.
- `lake-interior-audit-v9.json`: 239 lagos con cinco puntos interiores mojados
  cada uno; no valida toda su superficie ni navegación integral.
- `protected-island-native-plane-v9.json`: 283 islas contrastadas mediante los
  planos de los triángulos; borde no inferior al agua salvo redondeo de
  1,11e-6 m, interior a una celda del borde con resguardo 0,35 m.
- Lago 217: corregidos 47 vértices que secaban indebidamente su entorno;
  V9 recupera 785/965 muestras mojadas frente a 189 en V8. La malla de 6 m
  sigue aproximando esa orilla; no se afirma fidelidad métrica completa.
- Reserva seca: 5,941332 km², 0,126360 km² editados, mediana 3,93→3,95 m.
  No hay árboles colocados todavía.

## Fallo nativo abierto: precisión y puente

Los informes `native-heights-v9-first.json` y `native-bridges-v9-first.json`
siguen **FAIL** y deben conservarse. El verificador exige igualdad exacta de
alturas y matrices: [verify_foundation_native.py:28](<P:/DayZ_Baltic_12km_dev/tools/navigation/verify_foundation_native.py:28>).

1. **22 de 4.194.304 alturas difieren**, todas en la última fila o columna;
   error máximo **5,96046448e-8 m**. Las demás coinciden exactamente con V9.
   En esos 22 puntos, la operación float32 `vecino + (objetivo - vecino)`
   reproduce el valor exportado. Es una pista de redondeo de interpolación,
   **no una causa interna de Terrain Builder demostrada**.
2. Rebuild desplazó los dos tramos exteriores del puente −4,798312 m y
   −0,434668 m. Se seleccionaron los tres y se fijó **Absolute height 8.476612**
   con Relative mode desactivado; después se guardó/exportó.
3. La lectura actual del último WRP confirma la reparación de esos desniveles:
   centro idéntico; oeste difiere **−5,96046448e-8 m**, este **+7,15255737e-7 m**
   respecto al baseline. Modelos, IDs, escala/rotación y coordenadas horizontales
   permanecen exactos. Falta comprobar persistencia tras reabrir y resolver
   explícitamente el criterio de precisión; no llamar PASS al gate actual.

**Propuesta pendiente, no aplicada:** tras una reapertura independiente,
documentar un criterio numérico acotado que admita únicamente redondeo medido,
con negativos que rechacen desplazamientos reales; o corregir la conversión
nativa si se aísla el mecanismo. No alterar WRP binario ni relajar el gate
silenciosamente para obtener verde. No es necesario rediseñar relieve o puentes
por diferencias submicrométricas.

## Agua preparada e interrupción exacta

Agua V2: **10.152 instancias / 6.187 modelos**, superficies propias recortadas
al contorno y a las islas, material vanilla, escala 1 y extensión máxima 48,02 m.
Son infraestructura de agua; no edificios propios ni una región ya integrada.
Ver `regional-water-assets-verification-v2.json`: modelos/poses verificados
offline. Cada modelo tiene su centro ODOL; no aplicar un offset universal.

- `P:/baltic_water` apunta al directorio de modelos compilados del proyecto.
- Importación: `tb/regional_foundation_v1/water_absolute_v2.txt`, SHA `b26cfe3f…`.
- Última UI observada: diálogo **Create new library**, nombre `Baltic_Water_V2`,
  opción de crear desde directorio marcada, ruta `P:\baltic_water` correcta.
  El intento de pulsar OK fue detenido por **Escape físico del usuario**.
- En disco solo existe `TemplateLibs/Narva_Vanilla.tml`; no se acredita una
  biblioteca de agua guardada. Observar la UI de nuevo antes de retomarla.

Ensayo local de agua recortada estática ya pasó clasificación, hueco seco y
lancha: 936 mediciones de agua, 529 controles de hueco y 116 muestras de lancha,
con salud 600. También pasó la lancha local de Narva bajo el puente anterior.
No extrapolar esos ensayos a la instalación regional V9. Las piezas grandes o
escaladas y los estanques inclinados tuvieron fallos; conservar sus negativos.

## Consumidor y empaquetado listos, pero sin aceptación V9

Misión `missions/BalticFoundationConsumerV3.BalticTrial/init.c`, SHA `728d470c…`;
referencia `consumer-reference-v3.json`, SHA `25a79815…`. Congela **81.212
consultas agua/tierra, 314 consultas nav y 15 rutas**, además de filtros negativos.

V3 ejecutó todas contra el mapa anterior: `consumer-v3-baseline.json` conserva
el **FAIL esperado** (80.629 consultas agua/tierra fallan contra las cotas V9;
error máximo 13,29255 m). Cobertura/rutas/filtro nav pasan, alturas no.
Esto acredita que el consumidor se ejecuta; no que V9 funcione. V2 terminó
incompleta porque `string.Split` omitía campos vacíos; V3 usa cero explícito.

Helpers preparados:

- [prepare_foundation_package.py:40](<P:/DayZ_Baltic_12km_dev/tools/navigation/prepare_foundation_package.py:40>) exige
  dos exports nativos completos aceptados y compara contenido tras reapertura.
- [build_foundation_package.ps1](<P:/DayZ_Baltic_12km_dev/tools/navigation/build_foundation_package.ps1>) valida el stage,
  compila aislado con `Baltic_Water` y comprueba paridad. Mantiene los 4.775
  RVMAT y 2.048 PAA SAT1M. **Camino positivo aún no ejecutado**; parser,
  configuración CfgConvert y negativos de paquetes antiguos sí comprobados.
- La NM antigua se permite solo como arranque provisional del servidor de
  datos, etiquetada obsoleta; no sirve como aceptación del nuevo terreno.

## Próximo bloque de ejecución

1. Revalidar propiedad de procesos/lease MCP y observar TB. No repetir la
   importación ASC por leer un handoff histórico: **V9 ya está importado**.
2. Guardar/reabrir/exportar para cerrar la persistencia de alturas y puente;
   resolver de forma explícita el fallo de precisión conservando los negativos.
3. Crear/guardar biblioteca nativa del agua; importar el TXT con altura
   **absoluta**, conservar los tres puentes. Esperados: 10.155 objetos.
4. Guardar, exportar, reabrir de verdad y exportar de nuevo. Verificar todos
   los vértices, materiales, modelos, poses y recuentos; **no Generate Layers**.
5. Preparar/compilar paquete en destino nuevo. Conservar dependencias y hashes;
   generar **NM nueva con tileWidth 12.5** mediante el servidor de datos y NMG,
   guardarla, volver a empaquetar y comprobar lo realmente desplegado.
6. Ejecutar consumidor V3 sin mover sus puntos; pruebas regionales de lancha,
   IA y carga cliente/servidor, incluida inspección visual a varias distancias.
   Los problemas históricos de cuadros/agua azul no se cierran para V9 por
   conservar materiales o por un PASS offline.
7. Archivar editable completo, fuentes, WRP/NM/PBO y misión limpia; describir
   límites de rendimiento y tareas de mapeado posteriores.

GIS Python: `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe`.
Usar los scripts existentes con salidas nuevas, sin sobrescribir evidencia.
Los TV4P son binarios; no leerlos como texto. P:\DZ permanece solo lectura.

## Procesos, permisos y Git al entregar

- Computer Use quedó detenido por Escape. **Este cierre no lo reactivó.**
  En una continuación expresamente solicitada: observar antes de actuar,
  agrupar UI y terminar la sesión de control al pasar a cálculos o esperas.
  Las autorizaciones previas de TB/Buldozer/NMG/Steam siguen documentadas;
  no volver a solicitarlas por rutina.
- TB PID **258320** existe y responde. No se detectó NavMeshGenerator activo.
  DayZDiag PID **274188** y **287828**, iniciados 01-10 aproximadamente a las
  04:19 Madrid, existen y responden. **Propiedad/objetivo desconocidos; no se
  tocaron.** `session_status` no devolvió resultado en este cierre: coordinación
  actual sin confirmar, no declarar la caja libre.
- El último run propio V3 `3edbd6e3-229f-43dd-a50f-04ed27a16814` sí quedó
  cerrado y su lease liberado en la sesión anterior. Ese resultado histórico
  no identifica los dos procesos nuevos.
- HEAD **`4ff154b7f60a238ddc502f026439f45d6fac0eb2`**. Trabajo amplio sin commit;
  inventario en `handoff-2026-10-01/git-status-before.txt`. **No commit nuevo**:
  este encargo es un handoff, integración y gates pendientes. No hacer reset,
  clean ni añadir indiscriminadamente. `diagnostics/` es ajeno y no se tocó.
- No existe `bugs.md` vivo en este repo; ausencia declarada en
  `AI/10_Projects/_memory-exceptions.json`. Fallos vigentes en este handoff y EV.
- Skills: existe `C:/Users/guill/.codex/skills/dayz-terrain-workflow/SKILL.md`
  con referencias del trabajo previo. No se modificaron skills en este cierre;
  la explicación interna del redondeo aún no debe promoverse como hecho.
- Delegación reciente: Gemini aportó revisión de diseño; Grok respondió 402.
  `review-reconciliation.md` separa ideas aceptadas de mecanismos no probados.
  No declarar realizado el council completo de seis proveedores por ese informe.

No se envió este handoff a terceros ni se transfirió el testigo a Exta.

## Validación de este cierre

Los 12 enlaces del handoff existen, hay una sola entrada nueva en el índice,
el historial posterior a LIVE-STATE se conserva íntegro y PROJECT-MAP fue
regenerado. `git diff --check` pasa. Copias previas y recibos de documentación
en `evidence/regional-foundation-v1/handoff-2026-10-01/`.

La auditoría global del vault termina FAIL: 14 sesiones anteriores/ajenas sin
indexar y cinco pares de enlaces vivos rotos en `20_Knowledge/prime-agent-package`.
El handoff nuevo no figura entre esos fallos. No se corrigió deuda global fuera
de este encargo ni se declaró verde el gate del vault. No hubo nuevo ensayo
in-game, cambios de producto, modificación de verificadores ni commit.
