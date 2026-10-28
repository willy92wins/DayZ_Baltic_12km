# Preparar carreteras: pavimento, cruces y empalmes

Estado: A_CONSUMIDO_CATALOGO_COMPLETO; B/C_PENDIENTES_PLAN_ESPECIFICO. Petición viva: continuar las pruebas y
preparar carreteras en paralelo. Codex ejecutor/integrador. Esta preparación
no depende de obtener un nuevo PASS de colisión del río, pero la integración
de un piloto que lo cruce sí depende de resolver el conflicto correspondiente.

## Producto y límites

P5/P6: conexiones existentes, piezas vanilla y anchuras humanas. P9: conservar
navegación, gálibos y agua. P10/P11: preparar ahora; emplazamiento físico global
y conducción después de la base de terreno/navegación. Esta petición permite
avanzar catálogo, corredores y prototipos aislados; no aprueba extender pavimento
a todos los ejes ni cambiar clases/ancho de producto para encajar una pieza.
No tocar recorte, reserva natural, islas, agua, extremos o protección015-45.

## Descubrimiento y cuatro pilotos

El censo independiente ya recorre124cadenas/36467aristas/107180.669m. El overlay
contra modelos desplegados verificó2413contactos; sólo mide ejes, no anchura de
pavimento. Los715.422m de agua de modelo sin tablero coinciden con charca nominal;
no sumar ambas categorías. Otros1024.828m son mar nominal. NO son cantidades
de puentes omitidos. Recibos: evidence/road-surface-overlay-20261028.

| Piloto | Fuente/localización | Preparación | Puerta específica |
| --- | --- | --- | --- |
| R-PAVE-49 | Parada5296,6000; cadena49 | Primer corredor seco para comparar encaje de pavimento vanilla con la reserva vial | Elegir límites por geometría/agua, no sólo por la parada; 11secciones tienen evidencia nativa local, no toda la cadena |
| R-CROSS-49 | Personaje4789.51465,5516.52197; contacto cadena49/arista301 a11.601m | Resolver cruce completo, entradas y salidas | No colocar un puente en las coordenadas del personaje; verificar continuidad terrestre y navegación bajo cruce |
| R-NARVA-71 | Cadena71, contexto2391,6941 | Medir encaje del tablero real y accesos | Diagnóstico previo6.666grados/2.228m no es tolerancia; exigir cobertura del corredor, no sólo proximidad de ejes |
| R-END-76 | Kit118; cadena76/aristas124–129; instancia19394363 | Separar corredor y final del río con superficies reales | Solape medido en6aristas; Visual201 midió24m² de lecho sobre terreno en corredor. B3D/B3E no acreditan todavía resolución nativa |

La carretera49 recibió visto bueno visual local, con pavimentado y conducción
pendientes. Bosque/c0 no certifican estos pilotos. C1 sigue SIN REVISAR.

## A. Catálogo instalado, antes de generar poses

[EXACT] PBO instalado de referencia descubierto en la configuración B2A:
E:/SteamLibrary/steamapps/common/DayZ Exp/Addons/structures_roads.pbo,
318217469bytes en lectura de metadatos28-10. Hash histórico34c1cabe608823dc09ec25dd62c3738a84075a7187484fc99dbdf4e1c2ed2f5f;
debe comprobarse vivo, no atribuirle identidad actual por fecha/tamaño.
P:/dz/structures/roads/parts contiene familias asf1/asf2 y curvas; P: no es oráculo
del instalado. El piloto FTT03-10 exportó17piezas, no acreditó importación.
Su asf1_25 tenía bbox12x25m: NO se equipara bbox con ancho útil de calzada.

[DESIGN] Un inventario nuevo sólo lectura del PBO instalado: lista exhaustiva de
entradas parts/*.p3d y modelos de puente separados, sin filtrar sólo los usados
por FTT. Validar prefijo, rutas, duplicados y hash de PBO antes/después; conservar
orden/lista fuente. Leer cada modelo estrictamente con lector ya fijado por hash,
registrar errores por entrada sin borrarla del denominador. Geometría Visual,
Roadway, Geometry/Fire/View, puntos/selecciones/properties/materiales, cajas y
centro del modelo; ningún LOD ausente se fabrica. Exportar sólo medidas/metadatos
y hashes, nunca binarios vanilla al repositorio público.

Anclas a leer antes de implementar: tools/playtest/attach_navmesh.py:read_pbo
(Path, no str); tools/quality/compiled_dry_road_gate_ev112.py:read_backend;
lector C:/temp/moto_lanes/review_g3/tools/odol_reader.py. from_bytes/from_file,
campos y resolución de LOD se revalidan en sus definiciones. No importar ni
relanzar CLI de B2A/FTT/B3E consumidos. Si el formato de parts no es el esperado,
conservar INCONCLUSIVE_PARSE y proponer adaptación separada, no lector permisivo.

El inventario distingue superficie dibujada, superficie de apoyo y semántica
de carretera nativa. Un modelo plano sin Roadway no se descarta ni se acepta
como carretera por su bbox: investigar su consumidor nativo/configuración antes
de elegir objetos sueltos o RoadNetwork. La vía de generación no queda decidida
por el éxito del TXT FTT. Evitar introducir nuevas herramientas mientras no
exista un impedimento demostrado en el flujo actual.

Consumidor: cobertura exacta de entradas y hashes del PBO, muestras de geometría
analítica con bbox conocido y LOD ausente, y referentes vanilla documentados.
Negativos: entrada duplicada/omitida, prefijo erróneo, parse parcial, NaN, escala
no unitaria y Roadway ausente no pueden convertirse en aceptación de conducción.
El status de cierre será CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE, o
INCONCLUSIVE_CATALOG con lista de entradas no leídas; nunca PASS de carretera.

Presupuesto A: revisión de plan180s; code review180s y suite120s antes de una
lectura de catálogo120s/2GiB. Un censo, sin compilar/DayZ ni modificar P:/vanilla.
Parar ante datos cambiados o formato no soportado; no barrer versiones/lectores.

## B. Corredores y plantilla del piloto seco

[DESIGN, después de A] Cargar las cadenas de referencia y máscaras/superficies
selladas actuales. Seleccionar ventana seca en49, conservando estación, XZ y
dirección; asignar el ancho a partir de calzada/material/regla de producto,
sin usar el nombre de la pieza ni bbox como única medida. Si falta esa regla,
dejarla pendiente explícita y agrupar una decisión nueva de producto.

Preparar footprint continuo de pavimento y márgenes/empalmes, no sólo eje.
Comprobar intersección geométrica de toda su anchura con agua, lechos, apoyos,
vegetación/objetos y plataformas. Conservar contactos de menos de una muestra,
extremos y cruces en nodos: no reutilizar exclusiones del gate de terreno para
declararlos resueltos. No eliminar obstáculos para conseguir PASS.

Se conservan los límites existentes de verify_roads_v30.py: cross0.03m,
grade0.065, chord0.03m. Ese gate excluye48m del agua,470m de Narva y18m de
extremos; son ámbitos NO EVALUADOS, no aceptación de cruces. El nuevo gate de
pavimento debe añadir juntas, ancho útil, apoyo continuo y cobertura de accesos,
con tolerancias justificadas por el consumidor real y revisadas antes de autoría.
No se inventa ahora una tolerancia de desalineación, hueco o velocidad segura.

Sólo tras revisión específica: un candidato aislado, poses/modelos sellados,
relectura WRP/PBO, pruebas nativas de superficie y conducción vanilla a velocidades
predefinidas. Medir saltos/golpes/atascos y coste de render; navmesh se regenera
tras mapeado según P10. No publicar el candidato como colocado antes de demostrarlo.

## C. Cruces y extensión

R-CROSS-49 y R-NARVA-71 requieren prueba de espacio libre bajo tablero, apoyos
y continuidad completa del corredor a ambos lados. R-END-76 requiere que el lecho
no invada el corredor y que el agua y extremos sigan intactos. Estos son casos
de regresión del generador/validador, no parches locales sin censo global.
Después del piloto seco, proponer por clase las correcciones del resto de la red,
con detección de huecos basada en agua real y geometría de carretera independiente
del inventario de puentes. Nuevos candidatos/builds necesitan su plan/presupuesto.
RAM, aceptación visual, mapa completo y council ampliado permanecen abiertos.

## Revisión adjudicada y contrato del catálogo A

Fable5.1 nativo,75.937s, SOUND-with-fixes; fuentes intactas. Recibos en
R/road-preparation-plan-review-20261028. Esta sección concreta A y prevalece
sobre formulaciones amplias anteriores; B/C siguen sin autoría autorizada.

- Denominador: TODAS las entradas del PBO, orden original, ruta original y
  normalizada, tamaño, método y hash. Todos sus P3D se intentan leer, incluidos
  modelos fuera de parts y candidatos de puente identificados por ruta/nombre.
  Esa clasificación nominal no demuestra uso del motor. No buscar otros PBOs.
- Pin externo del PBO:34c1cabe608823dc09ec25dd62c3738a84075a7187484fc99dbdf4e1c2ed2f5f.
  Si cambió, parar antes de extraer. Prefijo requerido dz/structures/roads;
  un prefijo distinto deja INCONCLUSIVE, sin reinterpretar rutas.
- Lector estricto fijado: odol_reader.py fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57,
  bis_reader.py c9e5194aaf03e3c1a54578fa52950a1e0236c52ecb6b2597756b6a9ee618b70b,
  math_types.py b6ac444ca190a5cb8a7e5c0f423fafeceb31ddc8a805f2374b466ae5da6fdd10.
  No necesidad de duplicarlo ni instrumentarlo: importar definición sin CLI;
  strict=True, n_lods exacto, lod_end_ok y errores vacíos. Liberar cada modelo.
- Dos lectores de tabla ya existentes contrastan orden, rutas, tamaños y payload:
  attach_navmesh.read_pbo:20-66 y deployed_surface_inventory_ev112.pbo_table:49-73.
  El primero rechaza MIME comprimido; no es decoder. Método no soportado conserva
  inventario de tabla y cierra INCONCLUSIVE_CATALOG, sin lectura parcial verde.
  Comprobar suma de cabecera/payload y forma del trailer; registrar sus bytes.
  Identidad íntegra por SHA256 externo antes/después. No atribuir semántica SHA1
  a un trailer sin referente verificado: el wiki BI advierte que es opcional y
  describe ambiguamente sha[20]/md5 (https://community.bistudio.com/wiki/PBO).
  Esto no pretende validar todas las variantes posibles del formato.
- Metadatos públicos: conteos, bbox por LOD, centros, materiales, propiedades,
  nombres/conteos de selecciones y hashes de bloques; sin arrays de vértices/caras.
  usable_width=UNDETERMINED siempre. Ningún bbox de Visual o Roadway es ancho útil.
  Escala de entrada unitaria, espacio local; ninguna pose mundial todavía.
- Fixtures analíticos prueban el consumidor con objetos de datos simples, NO un
  escritor ODOL nuevo. Negativos de tabla/PBO son bytes de cabecera documentada.
  Cruce independiente: bbox desde vertex_raw float32 con struct, frente a campos
  de vértices decodificados. FTT es histórico/P:, sólo comparación si hash igual;
  no exigir igualdad instalada por nombres ni rechazar una versión legítima.
- Puentes no hallados en este PBO: informar ausencia acotada, no inventario global.
  P9 exige agua mínima para calado y máxima para gálibo. Recibo recuperado del
  Git público f9700cc, SHA d510af67: fondo1m/calado0.95m/corredor24m. La afirmación
  anterior de ausencia en main era errónea; ver road-preparation-receipts-20261028.
- Las11secciones: evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/
  quality-continuation-20261025/README.md. La cifra24m² de la tabla es contexto del
  handoff, no guarda de este catálogo; recibo recuperado:23.95666642052773m²
  sobre el corredor histórico8m, sin extrapolar a la huella de piezas12/9m.

Presupuestos sin cambio: code review180s, suite120s, un censo120s/2GiB.
Un método de parseo incompatible se conserva como inconcluso; no barrer lectores.

Resultado A:501entradas/265modelosstrict,154piezasRoadway,6puentesnominales.
4.25s/675405824bytes,20testsPASS. evidence/road-catalog-installed-20261028.
No repetir catálogo. asf1_25=12m y asf2_25=9m superan banda8m del gate previo;
B debe comprobar footprint completo sin tratarlo como anchoútil ni aprobarlo ahora.

Siguiente B0: plans/ev112-road-consumer-discovery-b0-20261028.md (borrador),
consumidor/pivotes/materiales/huella completa antes de proponer poses o ancho.
