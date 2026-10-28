# Lechos visibles y extremos: medir antes de materializar la orilla seca

Estado: REVISADO_CON_FIXES_INCORPORADOS. Codex ejecutor/integrador; Fable revisor.
P9/P10/P11/P14, KIT118-VIS y segundo cauce rechazado por lecho saliente.
Unidad de diagnóstico de TODOS los201modelos del piloto, no parche a un punto.
No modifica alturas, geometría, agua, colocaciones ni banco. El resultado
elige una reparación procedimental con restricciones verificadas; no la acepta.

## Hechos y mecanismo aún por contrastar

[EXACT] A y B publicados6c125cca/14e1e3d vinculan5443payloads/17818poses a la
visita. B verifica2413intersecciones de caras sobre36467aristas de referencia.
La pieza compilada cs_kit_118_0000.p3d, modelo3579/objeto19394363, intercepta
6aristas124-129de carretera76,14.602m de eje. Su Roadway no demuestra por sí
sola exposición del Visual. El agua y los extremos no se mueven.
Fuente MLOD actual de201modelos en R/pilot-kit7-fc-20261026/source/baltic_stream_pilot.
R=E:/DayZ-Baltic-Build/shape-repair-20261025. Procedencia:182payloads del paquete
base y19Geometry sustituidas; consumidor lineage y source pins ya sellados.
No reutilizar reports binarios históricos145discordantes ni temporales19discordantes.

[EXACT] tools/water/continuous_stream_pilot_v31.py:295-317 forma el lecho,
mezcla extremos y eleva el suelo de la orilla seca sobre H para cubrir soporte.
:344-361 añade8filas CAP fuera del NPZ; :369-384 crea Visual y Roadway por separado.
Estas operaciones pueden producir un saliente, pero su lectura NO demuestra
que causen la captura. Comparar superficie efectiva contra H/W, no sólo energía
del solver ni altura en los vértices. El gate de carretera usa±4m (:6 y:59de
tools/terrain/verify_roads_v30.py) y excluye cruces; ese ancho es reserva de su
criterio, NO anchura de pavimento certificada. No heredar sus exclusiones.

## A: equivalencia y superficie efectiva del piloto

[DESIGN] Leer MLOD actuales y VisualLOD mínimo de los201ODOL desplegados por
bindings sellados de A, sin volver a extraer todo el mundo. Seleccionar caras
de lecho por materiales/texturas y confirmar en cada modelo qué quedó fuera
(agua, otras secciones, vacías/desconocidas). No clasificar por nombre sólo.
Enumerar equivalencia Visuallecho ↔ Roadwaylecho ↔ fuente y posiciones reales.
Conservar triángulos/caras, campos, partes duplicadas y ambigüedades; no soldar
ni triangulaciones arbitrarias. Si equivalencia falla, medir el Visual real.
No convertir sólo una diferencia de referencia en causa raíz.

Dividir caras proyectadas del Visual contra las caras nativas H y sus niveles
nominales W. Calcular regiones y extremos analíticos de B-H y B-W en la
subdivisión común; no aceptar por muestreos de vértices originales. B es altura
del lecho. Celdas sin charca usan mar nominal0.75; resto field084171b0.
Registrar APARENTE_BAJO_TERRENO, EXPUESTO_SOBRE_TERRENO, CONTACTO y cruce con
agua nominal. Conservar todas las capas B superpuestas y la presencia de agua
Visual real del piloto; desacuerdo con agua nominal queda incierto, no se
resuelve escogiendo una altura. Proxies ajenos no se dan por probados.
Las categorías son relativas a terreno fuente exacto WRP editable; no afirman
oclusión del motor, transparencia, z-fighting ni el terreno compilado completo.

Contabilizar por pieza y sitio, cuerpo/filas CAP/bordes húmedos/extremos,
área expuesta, máximos y mínimos, perfiles, componentes y coordenadas críticas.
Comparar mapas de exposición de los cuatro cauces y reportes humanos; cercanía
sin pose de cámara no identifica automáticamente la captura.

## B: corredor de carretera y viabilidad de la corrección

[DESIGN] Intersectar Visualdelpiloto contra todo el corredor de referencia±4m.
Para segmentos rectos, unión geométrica de rectángulos; juntas/extremos conservan
disco de4m como alcance conservador, etiquetado. No decidir ocupación únicamente
por bbox. Detectar y conservar por separado agua efectiva que exige resolver
el cruce y lecho seco/cap que puede enterrarse sin cambiar el agua.
Registrar si regiones expuestas intersectan las posiciones actualmente fijas
del candidato seco (agua/XZ/extremos/015-45/etc.). No borrar una máscara para
conseguir PASS. No suponer que CAP coincide con estaciones del NPZ: mapear las
8filas añadidas según fuente y comprobar sus posiciones guardadas.

Comparar contra el candidato seco offline1e85c73f… del plan MLOD aplazado sólo
donde su correspondencia está demostrada; fuera de sus139modelos, conservar
los62actuales como SIN_CANDIDATO. No prometer que ese candidato arregla kit118.
Suavidad/energía menor sin menos saliente efectivo no autoriza materialización.

Entregable: tabla de todos los casos equivalentes y restricciones que los
afectan, casos reparables por Yseca sin alterar agua/extremos y casos inciertos
o en conflicto; presupuesto de la siguiente reparación. Mantener el límite
de colisión±.02m/.01m y los umbrales vigentes, sin ampliar tolerancias.
Si la corrección exige cambiar una protección aprobada, preparar propuesta
concreta y agrupar sólo esa decisión nueva. No fabricar autorización por silencio.

## Consumidor, presupuesto y parada

Fixtures independientes por planos/polígonos: terreno que tapa lecho, lecho
que sobresale sólo entre sus vértices, parte seca y sumergida, dos capas,
Roadway/Visual discrepantes, CAPfuera del NPZ, borde cercano a carretera pero
sin solape real, solape en extremo/junta, instancia omitida y hash incorrecto.
Conservar controles naturales/diseñados, sin inventar un umbral estético.
Una revisión de código antes de producción, fixes conjuntos reproducidos.
Preflight≤120s/2GiB sobre metadatos/coste; después una lectura/censo≤600s/2GiB
con particiones por modelo, sin materializar94millones de caras vanilla ajenas.
Timeout/dato faltante/ambiguo=INCONCLUSO; nunca cero cobertura=PASS.
Una producción y un consumidor con hash/PID real; no relanzar consumidos.

No reparar todo el mapa desde este diagnóstico. Corredor y agua que exigen
puentes se enlazan con B para un plan de generación de cruces, independiente
de la lista histórica del generador. Contornos completos/relieve/RAM y council
continúan abiertos; esta unidad resuelve el bloqueo del plan MLOD aplazado.

## Adjudicación antes de implementar

Fable5.1 nativo169.171s, SOUND-with-fixes; fuentes inmutables y sin denegaciones.
- Los201modelos son139kit7,26kit118,9cauce65.0-0 y27cauce131.0-0. El candidato
  seco previo sólo toca139kit7: NO puede reparar los dos cauces rechazados en
  visita (kit118 y65). Los6solapes carretera76 son SIN_CANDIDATO. Esta unidad
  conserva los cuatro sitios, sin recortar alcance al candidato anterior.
- Discriminador sólo lectura ya consumido: R/kit118-roadway-height-discriminator-20261028.json.
  En los6intervalos, Roadway-H varía de-0.122174m a+0.058336m; sólo2aristas
  tienen alguna parte sobre H. Conservarlo como control al demostrar equivalencia
  ODOLVisual/Roadway. No afirmar que los6intervalos enteros están expuestos ni
  atribuir la captura automáticamente. Sin nueva medición repetida del mismo eje.
- Separar APARENTE_BAJO_AGUA_PILOTO por altura respecto a la lámina Visual real.
  No llamarlo invisible: el agua puede ser transparente y este censo no evalúa
  el render. Diferenciar lecho emergido, sumergido y exposición respecto a H;
  conservar todos los valores, tanto nominales como de las caras del piloto.
- Corredor continuo±4m: extensión geométrica del ancho que el gate existente
  muestrea en17offsets, NO heredar esos17puntos como oráculo continuo. La cita
  de offsets depende de versión (:56 en la fuente revisada); mantener hash.
- Verificar planaridad/cara no degenerada antes de extremos lineales. Quads
  ambiguos, pliegues/solapes, CAPque retrocede y triángulos casi degenerados
  conservan incertidumbre. Fixtures explícitas de esas tres patologías.
- No cambiar el extractor A publicado/pineado para añadir unkind: crear la
  unidad separada que consume sus helpers de lectura/secciones y verifica sus
  hashes. Así la evidencia A/B sigue reproducible con las fuentes ya selladas.
- Separar exposición en Yseca libre, CAP y agua sobre carretera. La propuesta
  de Fable de pedir siempre permiso para CAP no se adopta automáticamente:
  congelar8filas era una restricción del plan MLOD PROPUESTO, no por sí sola
  una aprobación humana de inmovilidad. Esta unidad sólo mide. El plan de
  reparación deberá contrastar las protecciones efectivamente aprobadas y la
  petición de conservar agua/extremos; sólo cambios de producto/protección
  aprobada requerirán decisión humana nueva. No se relaja nada en este censo.


## Avance verificado: extracción Visual201 (28-10)

La primera unidad se ejecutó y verificó:201modelos,185744caras de lecho,
4760de agua,4864caras CAPfuera de los NPZ del cuerpo. Todas las caras tienen
correspondencia exacta con la fuente y con el Roadway sellado A.25fixtures.
Fable código306.469s SOUND-with-fixes; adjudicación en
evidence/pilot-visible-surface-20261028. Extracción80.703s y consumidor45.719s.
Primer consumidor detenido por ruta relativa, conservado y corregido con
contexto W explícito en un script nuevo. No se repitió extracción ni preflight.

Estado del plan: PARCIAL. A extracción/procedencia/CAP verificada; exposición
contra H/W/corredor/candidato todavía NO ejecutada. La categoría geométrica de
CAP no demuestra que esté expuesto ni que pueda moverse sin afectar extremos.
Núcleo de subdivisión nuevo en desarrollo con12fixtures iniciales, sin producción
ni publicación; falta revisión y completar consumidores antes de ejecutar.
