# B2A: reconstruir oclusores y espacio estático de los rayos

Estado: SOUND_WITH_FIXES_ADJUDICADO_20261028; implementación offline autorizada.
Revisión Fable nativa de323.735s: R/collision-scene-b2a-plan-review-20261028.
Adjudicación adjunta en ese directorio; ninguna autorización de lanzar DayZ.
Consumidor: Codex ejecutor/integrador; Fable revisión independiente. Unidad
offline previa a B2 nativa, dentro de P2/P8/P10/P11/P14 y las regresiones humanas.
No es el council ampliado ni un arreglo físico del mapa.

## Pregunta y hechos fijados

Original2658 permanece FAIL47/INCONCLUSIVE21. B1 publicada0ae6293 no resuelve
colisión ni referente independiente de agua. No repetir ambas sondas.
R=E:/DayZ-Baltic-Build/shape-repair-20261025.
A seleccionó antes del experimento los cinco RV fallidos349,350,700,723,1425;
sus positivos emparejados son348,311,701,725,1426. Se conservan esos10 IDs.
Tres RV altos dieron t_fagussylvatica_3fb_summer a16.7–19.0m sobre la referencia
max(H,B); Bullet también nombró ese árbol. B es effective_bed y H ground del
expected original2658, cotejados contra la selección A y el diagnóstico nativo.
no se ha demostrado qué instancia/componente ni espacio libre en el origen bajo.

[EXACT] missions/BalticVisualProbeV1.BalticTrial/init.c:118-139 usa
H+100→H−10, RaycastRV/ObjIntersectGeom/NEARESTCONTACT y RayCastBullet/BUILDING.
P:/scripts/3_Game/global/dayzphysics.c:199 declara RaycastRV. Esta unidad no
añade APIs ni afirma equivalencia exacta de Geometry estática y Bullet.
[EXACT] tools/terrain/package_visual_forest_ev112.py:29-75 lee objetos
OPRW con ancla, tabla de modelos, IDs únicos y cierre map-info. Es un lector
heurístico con comprobaciones; no un decoder de alturas ni prueba del motor.
[EXACT] tools/quality/deployed_surface_inventory_ev112.py:50-80 lee tabla y
payload PBO; :82-86 aplica vertices @ matriz3x3 + traslación. El censo anterior
:275-291 excluye vegetación. NO reutilizar sus17818 instancias como escena completa.
[EXACT] R/deployed-world-geometry-discovery-20261028/report.json conserva
ancla16787372, OPRW32/stride64,5509 nombres,2578398 objetos.
[EXACT] R/tree-source-b2-discovery-20261028/report.json: árbol instalado
ODOL56 SHA3956f60a… frente a desempaquetado ODOL54 SHA959b6b3c…; 78 componentes
Geometry y ningún proxy en ese LOD. No se deduce distinta colisión de distinto hash.
Vanilla no estaba sellado en B1; no afirmar identidad retrospectiva de esos bytes.

## Entradas y preservación

[DESIGN] Fijar antes de ejecutar: A/pares/resultado2658/B1, fuente del lector
WRP/ODOL, catálogo y bindings anteriores, mundoPBO10e09e3f…/WRP0da63d3f…,
piloto candidatoPBOef229f32…, agua97edcafe…, y PBOs vanilla instalados que
resuelvan todos los modelos relevantes. Seleccionar el candidato real, no el
piloto anterior de un binding histórico. Resolver prefijo+entry, unicidad y
hash de cada payload. Prohibido sustituir por P:/DZ por conveniencia.
La lista completa de nombres/instancias procede del WRP compilado vinculado
al PBO; cotejar counts/IDs/modelos con la referencia fijada antes de filtrar.
Datos sin binding, formato no soportado o geometría no leída => cobertura
incompleta, jamás objeto vacío o espacio libre por defecto.
Sin cota certificada de un modelo/proxy, TODOS los orígenes quedan con cobertura
desconocida: ni radio empírico ni distancia al centro permiten descartarlo.
El catálogo tiene5509 modelos; los5443 decodificados antes incluyen6 hijos de
proxy ajenos al WRP. Faltaban72 modelos WRP de vegetación, no66.
Fijar diagnóstico dry-road-full-native-diagnosis-20261028/report.json
SHAedef4d25b9d0126fa69a5d373bd01b72a3b523a42c187fcaebbbc355aa1c7b4c,
result2658 SHAe717a124c38ff61b4af932793541ab78b7dfb703aea946d497c246b59ee33390.
H/B de los diez centrales vienen de ese result, no de superficies recalculadas.
B1/result.json SHA d3781bae041179307164a0acf1c38360604b865d61c56b181b0181a5e0762edb
contiene30 snapshots (10IDs×3rondas); observations.json sólo expone ejemplos.
Reader ODOL externo fijado por compiled_dry_road_gate_ev112.READER_HASHES,
incluido odol_reader.py SHAfa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57.

## Una ejecución offline

1. [DESIGN] Construir9 posiciones por ID: central y ±0.005/±0.02m en X o Z,
   convertidas explícitamente a float32,90 puntos. Son estímulos diagnósticos;
   los centrales fallidos y todas las expectativas originales siguen intactos.
   Origen bajo fijo por grupo: max(Hcentral,Bcentral)+2; origen altoHcentral+100
   y finalHcentral−10. Usar el mismo Y para sus desplazamientos y declararlo;
   no usar un B calculado tras conocer el resultado para apartar el rayo.
   Registrar desplazamiento float32 efectivo. Muestrear H independientemente
   en los90XZ; origen bajo sobre terreno también es requisito, sin variar Y.
2. Leer Geometry real de cada modelo con instancias, también los72 tipos de
   vegetación. Obtener bounds de vértices decodificados, no sólo del header ni
   de centros. Hacer broadphase contra TODAS las poses WRP mediante cajas
   transformadas conservadoras; nunca filtrar primero por radio de40m.
   Retener todos los candidatos cuyo volumen pueda afectar puntos/rayos.
   Los objetos ajenos al piloto y sus matrices se conservan.
   Geometry = float32(1e13) exacto, a lo sumo un LOD. No incluir Fire/View.
   Registrar bounds reales frente a ModelInfo y lod.b_min/b_max/b_center.
   Marco raw @ WRP y alternativa (raw+bounding_center) @ WRP: comparar ambas,
   conservar su unión. No son prueba de exhaustividad de marcos del motor;
   ausencia de ocupación en ambas se llama CLEAR_UNDER_FRAME_HYPOTHESES,
   siempre condicional, nunca certificación nativa. Vincular poses a los
   snapshots B1 por nombre y traslación, y guardar suelo/base como diagnóstico,
   no usar que una base parezca plausible como prueba de convención.
3. Por cada candidato conservar caras, componentes, propiedades, pose y ruta
   resuelta. Geometry sin caras sólo significa vacío si se comprobaron también
   sus proxies. Los proxies no tienen marco certificado por el censo anterior:
   si no se puede acotar su posición con una envolvente conservadora de todos
   los marcos documentados, marcar cobertura desconocida y NO emitir espacio
   libre. No inventar transformaciones para completar una escena.
   Dos hipótesis de proxy: Matrix4P aplicada directa, o hijo+bounding_center
   antes de Matrix4P. Si hijo no es vacío y su marco no se resuelve, mantener
   cobertura desconocida (no es obligatorio inventar su envolvente).
4. Punto fuera de todos los componentes: usar envolventes convexas como
   SUPERCONJUNTO conservador. Para cada componente, verificar que incluye todos
   los vértices de sus caras; caras sin componente van a grupo residual. Un
   punto dentro de la envolvente no demuestra estar dentro del sólido: queda
   POSSIBLE_OCCUPANCY. Sólo una separación positiva demostrada frente a todas
   las envolventes permite CLEAR_UNDER_FRAME_HYPOTHESES. Bounds/facetas
   calculados en float se verifican contra sus vértices con margen de error
   aritmético documentado; contacto, degeneración o duda => INCONCLUSIVE.
   No usar una tolerancia física mayor para fabricar separación.
   Hull degenerada: AABB sigue siendo superconjunto; fuera de ella se puede
   separar, dentro/contacto permanece INCONCLUSIVE. Ningún componente omite
   los vértices de sus caras aunque selected_vertices esté incompleto.
5. Proyectar los rayos originales contra caras Geometry retenidas y registrar
   todos los impactos con instancia/modelo/cara/altura; no elegir el más cercano
   a la medida nativa. Conservar ambigüedad de aristas/vértices y duplicados de
   componentes. Comparar descriptivamente con RV/Bullet originales y con el
   snapshot B1 de objetos. GetPosition no es prueba de volumen ni pose completa.
   Usar result B1 completo (30snapshots), no inferir ausencia de examples.
   La identidad nativa del árbol sigue condicional sin sello vanilla del run.
6. Emitir cobertura, candidatos, pruebas de separación o incertidumbre por90
   orígenes, y diferencias de impacto por10 centrales. No corregir generación,
   terreno, modelos, árboles, agua, etiquetas, scripts anteriores ni umbrales.

## Puertas, negativos y presupuesto

PASS de la unidad = entradas verificadas, escena/ausencias explícitas,90puntos
y10centrales conservados, fixtures correctos e informe completo dentro del
presupuesto. No es PASS del mapa ni permiso de B2 nativa. La preparación nativa
necesita su plan revisado, misión/consumidor y vínculo de paquetes completos.
Si existe cobertura desconocida o posible ocupación en un origen bajo, ese
origen NO queda autorizado como libre; conservarlo y estudiar el dato faltante.

Fixtures independientes: cubo y tetraedro analíticos con puntos dentro/fuera/
contacto; pose trasladada, rotada y escalada no uniforme; cara omitida del
componente absorbida por residual; modelo faltante; proxy no resuelto;
árbol con centro fuera del radio pero volumen sobre rayo; rayo alto bloqueado
y bajo libre; tangencia/arista; copas solapadas; distinto PBO para mismo nombre;
NaN/índice inválido; falta/duplicación de punto; reemplazo accidental del central.
Cubrir casos que deben seguir INCONCLUSIVE y no sólo casos verdes.

Presupuesto cerrado: una revisión de plan600s, implementación y pruebas con
Python GIS -I del worktree, suite120s. Una corrida offline300s/2GiB/un hilo
numérico; vigía y salida nueva, sin reintento por parámetros. Revisión de código
600s; una corrección por contraejemplo reproducible. Falta de convergencia de
instrumento => degradar a diagnóstico/retirar esa afirmación, no otra ronda de
parches al mismo instrumento (gates-ledger, Cuándo para un bucle).
0 runs DayZ,0 builds,0 escrituras a activos/vanilla. No preguntar de nuevo
autorizaciones humanas existentes. Agua/producto, RAM, C1 y nueve regresiones
siguen abiertos mientras se ejecuta esta unidad separable.
