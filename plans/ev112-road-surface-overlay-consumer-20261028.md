# Etapa B: consumidor de cruces carretera–superficies reales

Estado: EJECUTADO_DIAGNOSTICO_VERIFICADO. Codex ejecutor/integrador; Fable revisor.
Completa el diagnóstico P8/P9/P11/P14 del plan desplegado, sin autoría ni banco.
Las reparaciones se planifican después de medir. No se rebajan tolerancias.

## Entradas verificadas

A publicada6c125cca:539009caras de prototipo y17818matrices de instancia.
362554Roadway,176390agua directa,65agua proxy condicional,43caras ambiguas.
23fixtures fuente/exportación, consumidor de cobertura independiente y201pilotos
contrastados con MLOD actual: error máximo de vértice0m. Artefactos sellados en
evidence/deployed-surface-prototypes-20261028/artifact-hashes.json; raw externo
E:/DayZ-Baltic-Build/shape-repair-20261025/deployed-surface-prototypes-20261028.
Prototipos no son caras expandidas ni veredicto de calzada/cauce/puente.

Consumir grafo completo del checkout principal y hashes del plan padre:
reference.npz94ecbca6, road-grade-chains-v6.jsonb31fb7d7;124cadenas/36467aristas.
Terreno815ef8b7 y footprint084171b0; censo nativo y contactos guardados del28-10.
No usar crossings-ev106 ni inventario del generador como universo esperado.
Resolver claves Windows/POSIX sin alias ambiguos. Leer snapshots JSON/NPZ y
ligar bytes a hashes; recomprobar fuentes al terminar. No relanzar A.

## Método

[DESIGN] Usar STRtree de bbox de INSTANCIA calculados desde caras reales
transformadas por la matriz compilada. Preservar capas/modelos/instancias/caras,
slots de proxies y flags del extractor. Bbox sólo elimina pares imposibles;
la clasificación depende del narrow phase, nunca del bbox ni del nombre solo.
No materializar94millones de caras visuales de lecho vanilla. Esta etapa ve
agua y Roadway; no certifica exposición del lecho visual completo.

Para TODA arista del grafo, intersectar su eje XZ con las caras candidatas.
Triángulos y quads convexos coplanares: intervalos exactos del parámetro t por
semiplanos; quads mediante fan contrastado con el polígono independiente.
Conservar también puntos tangentes, caras verticales/degeneradas y ambigüedades.
Un intervalo estrecho o entre muestras no puede desaparecer. Unión exacta de
intervalos por capa; no sumar solapes ni cerrar huecos con tolerancia.

Caras ambiguas de A no son superficies vacías: recortar una huella proyectada
conservadora (envolvente convexa de sus vértices) y etiquetar su posible alcance
INCONCLUSIVE_TRIANGULATION. No usarlas para aceptar soporte ni afirmar ausencia
de puente en el mismo tramo. Incluir el motivo y residuo de coplanaridad.
No elevar ni aplanar vértices para resolver esa ambigüedad.

Resolver dos condiciones distintas:
- Agua NATIVA: conservar intervalos húmedos/contactos del censo guardado.
- Agua de MODELO: un cruce XZ puede estar bajo tierra. Cortar el intervalo
  también por caras del terreno nativo, evaluando Wmodelo(t)-Hnativo(t), lineal
  en cada subintervalo. Separar EXPOSED_MODEL_WATER, BURIED_MODEL_WATER y contacto.
  Las caras con PROXY_CONDITIONAL mantienen su estado hasta verificación del
  marco del motor, aunque la altura calculada parezca razonable.

Así una placa ancha enterrada bajo una orilla no se cuenta como carretera
inundada. Guardar todas las capas superpuestas y sus alturas, no escoger una
ganadora sin prueba. El censo nativo y la lámina nominal del modelo pueden
discrepar: registrar la diferencia; no ajustarlos para hacerlos coincidir.

Superponer Roadway de los28objetos de puente del catálogo real y separar
presa, lecho/agua y piedras. Textura water_ext.paa no es soporte de puente;
texturas vacías no excluyen una cara. Presencia de Roadway no prueba soporte
físico, conducción ni altura útil: medir Ytablero-W para cada capa y registrar
caras superpuestas, desniveles con terreno y separación entre módulos.

WET_AXIS_WITHOUT_BRIDGE_ROADWAY sólo donde exista agua expuesta/nativa
acreditada, falte superficie de puente y no haya geometría de puente ambigua
que pueda cubrirlo. Significa contacto sin tablero observado, no decisión de
construir puente: vados/intención y ancho real aún no están acreditados.
Donde un proxy sea condicional, el hallazgo también será condicional. No usar
falta de intersección bajo un marco condicional para certificar sequedad global.

En cada nodo evaluar todos los extremos incidentes, incluso entre cadenas;
conservar huecos y saltos exactos. Medir separación y ULP local sin declarar
una tolerancia de junta nueva.1e-9m sigue siendo residuo del solver, no umbral
para arreglar puntos ni para aceptar la conducción. Magnitudes de alineación
del eje con el tablero son diagnóstico, sin umbral inventado.

## Pruebas y entrega

Oráculo independiente: recorte Shapely de polígonos conocidos y alturas de
planos analíticos, frente al solver paramétrico. Casos positivos/negativos:
puente presente/retirado/rotado/desplazado/sumergido, hueco entre piezas,
agua totalmente entre muestras, tangencia, extremo/nodo compartido, dos alturas,
agua bajo orilla seca y cruzando H-W dentro del mismo tramo, water-Roadway que
no puede contar como puente, proxy condicional y cara ambigua que impide falso
puente ausente. Omisión de arista/instancia, hashes o referencias inválidas fallan.

Cada arista y cadena queda contabilizada aunque no tenga contacto. Guardar
tramos y contexto Narva,kit118,4789.51465/5516.52197 en coordenadas locales XZ,
sin adjudicar una foto automáticamente por cercanía. Calzada pavimentada,
anchura lateral, vehículos, gálibo de barco y apariencia siguen no evaluados.
No declarar aceptación global ni cierre de los defectos de la visita.

Antes del censo: revisión de código/fixtures y preflight del número de pares
bbox/segmento y caras candidatas. Si no cabe, revisar partición/presupuesto
antes de ejecutar, sin omitir regiones. Una ejecución120s/2GiB del PID real,
salida nueva; fallo conserva evidencia y exige hipótesis verificable diferente.
Una corrección conjunta de hallazgos reproducibles por revisión. Publicar sólo
código y evidencia validada desde public-repo, sin recursos de terceros.

## Adjudicación de revisión antes de código

Fable5.1 CLI nativo,227.469s, SOUND-with-fixes; inputs inmutables, sin denegaciones.
Se incorporan los ocho puntos de la revisión y la precisión propia sobre agua nominal:
- Cortes de arista de malla con clave canónica por sus dos vértices XZ; vecinos
  comparten t bitexact. No soldar microhuecos. Reportar tamaño/ULP y procedencia.
- Tablero sumergido conserva su presencia geométrica: ROADWAY_AT_OR_BELOW_WATER
  es distinto de ausencia. ROADWAY_ABOVE_WATER tampoco acepta gálibo ni conducción.
  El nombre WITHOUT_BRIDGE_ROADWAY queda reservado a ausencia de geometría,
  evitando convertir el diagnóstico de altura en una afirmación de puente ausente.
- Quads ambiguos conservan ambos fans, intervalos y alturas posibles, más
  envolvente conservadora XZ/Y. Mantener INCONCLUSIVE_TRIANGULATION incluso
  con un intervalo numérico estrecho; no subir la tolerancia de planitud.
- H es terreno de autoría. Comprobar igualdad con alturas del WRP editable
  vinculado a A; no sustituye decodificar el terreno del WRP compilado completo.
  EXPOSED/BURIED se etiquetan RELATIVE_TO_SOURCE_TERRAIN, no prueba de motor.
- Pinear contacts.json3827291e y chain-coveragee53011aa desde publicación
  verificada. El consumidor recorre todas las aristas guardadas y no depende
  de partitions.npz para cortar: usa cuts/faces_at/bary del módulo pineado.
- Cara vertical/degenerada: intersección puntual/colineal XZ y rango Y,
  INCONCLUSIVE_VERTICAL_FACE; no desaparece como polígono de área cero.
- Roles por grupo del catálogo sellado; Roadway water_ext nunca es tablero.
- Preflight preserva pares totales, máximo por arista y caras candidatas.
Además, separar mar nativo nominal de charca nominal: el footprint expresa
la capa esperada, no demuestra por sí solo una cara3D desplegada. Hallazgos
sólo nominales se etiquetan NOMINAL_WET_AXIS_WITHOUT_BRIDGE_ROADWAY. Agua directa
de malla y mar, siempre relativos al H fuente, conservan su procedencia explícita.
No se usa la capa nominal para rellenar ausencias de geometría ni para certificar
sequedad del mapa. Todo el censo es diagnóstico del snapshot y no aceptación.

## Resultado y límites conservados

Código revisado Fable338.157s; corrección conjunta y32fixtures PASS.
La pieza proxy hipotéticamente enterrada permanece INCONCLUSIVE_WATER; las
observaciones por nodo no se duplican y el mar/charca nominal se distingue
desde plane084171b0. Huecos dentro de una instancia conservan procedencia y
estado inconcluso, sin soldarlos ni declarar automáticamente ausencia de puente.
Comparador de polígonos comprueba longitud Y extremos; fixture completa cubre
clipping/lookup/agua Roadway/proxy enterrado/nodo entre cadenas/arista seca.

Preflight consumido2.093s:1399pares/129191caras/max1568porarista. El dato original
candidate_edges36467 era erróneo por defaultdict; se conserva y explica en
adjudication.json. Producción corrige a994aristas con bbox candidato; no se
repitió el preflight. Censo único4.437s,430604288Bres/453042176Bcommit.
124cadenas/36467aristas completas,996aristas con contacto de algún dominio.
Consumidor Shapely independiente:2413contactos exactos de superficie,
residuo máximo1.69914e-12m,2.969s; hashes antes/después exactos.

715.422m de eje bajo agua de modelo sin Roadway de puente (7cadenas); el mismo
conjunto casi coincide con715.422m nominales de charcas, NO se suman.1024.828m
nominales de mar sin Roadway en14cadenas. Son longitudes de diagnóstico, no
número de puentes ni orden de colocarlos.25de28piezas de puente intersectan
algún eje; la ausencia de eje en las otras3 exige diagnóstico, no borrado.
Una pieza de piloto intercepta6aristas de carretera (kit118 próximo); aún no
está probado cuánto lecho visual queda expuesto. Narva tiene tablero sobre agua
pero conserva el defecto visual de alineación; PDA/eje sólo son medidas.

Siguiente: reconstruir cruces contiguos y corredor lateral a partir de geometría
independiente, contrastar mecanismos del generador antes de autoría; para los
lechos medir Visual real contra H/W e incluir extremos, no aceptar sólo Roadway.
Las9regresiones de visita, contornos/relieve, RAM, c1 y council siguen abiertas.
