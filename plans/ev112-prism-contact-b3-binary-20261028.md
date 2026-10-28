# B3B: compilación y comprobación del candidato B3

Estado: REVISADO_PARA_EJECUTAR. Fable5.1,265.485s; adjudicación en
R/prism-b3-binary-plan-review-20261028/adjudication.md. Codex ejecutor/integrador.
Consumidor: pareja ODOL guardada y puerta independiente; sólo si pasa permite
componer un paquete experimental separado. Sin despliegue ni DayZ en esta unidad.
P2/P7/P9/P10/P14; hipótesis RV de B3, sin cerrar agua, visual ni RAM.

## Fuentes, hipótesis y diferencia respecto al gate previo

R=E:/DayZ-Baltic-Build/shape-repair-20261025. B3 offline publicada6e45d6c,
17tests,12prismas6/8, conteos9120/12160/1520, otrosLOD/bbox exactos.
Control MLOD R/dry-road-mlod-candidate-r2-20261028/source/baltic_stream_pilot/
cs_kit_118_0000.p3d SHA d13069d5ec2816cdacc90891a83e5f92f517c4c33703380d534d3f7538baddef.
Candidato R/prism-contact-b3-candidate-20261028/candidate.p3d SHA
c769dd9a0631156075ec61586dc8f5a1471964899e21bdf34e8d13adad8233ad.
ODOL control histórico351424ab535a3e3eb40fc460a22360ab442776446055b116e10c0ba6134579f5
en R/dry-road-compile-pair-20261028/candidate/saved-odol.p3d.
Paquete control R/dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo
SHA ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84.
WRP inmutable; pose instancia19394363 de deployed-surface-prototypes-20261028/
instances.npz SHA6c0ae3b5b9dc9bbcbb9333bd8c6877ac0ed914a3508ea543d0af5f01829f6e37.
MLOD origen8262,7,8934; pose ODOL8257.9892578125,7.396484375,8928.40625.
Controles originales700dry/723wet no se mueven ni reclasifican.

[HIPÓTESIS] El compilador conserva las superficies de B3 y sus contactos
interiores bajo la pose existente. No se afirma cómo RV resuelve intersecciones.
compiled_dry_road_gate_ev112.py:source_geometry exige error vertical0, y sus
ANCHORS/verify_models son específicos del experimentoY/N anterior. No invocarlo
como gateB3 ni cambiarlo. Reutilizar sólo utilidades comprobadas de lectura,
normalización, overlay y comparación de identidad de paquete.

## Preparación y ejecución aislada

[EXACT] pack_continuous_stream_pilot_v31.ps1 recibe -Pilot, exige salida nueva,
crea junctionsDZ/bin/core de sólo dependencia y ejecuta AddonBuilder existente.
No toca despliegue. model_config(instances) en continuous_stream_pilot_v31.py
genera el config para un único modelo; read_pbo de attach_navmesh.py extrae
entries y propiedades. El nombre compilado debe ser cs_kit_118_0000.p3d.

Preflight fresco: verificar origen de la skill y copia local previamente
documentada con sólo un literal corregido; invocar sus comprobaciones oficiales,
registrar salida, herramientas y hashes. No editar la skill instalada. P:,DZ,
bin,core,Workshop y rutas/hashes de herramientas deben seguir siendo válidos.
No consultar ocupación ni adquirir lease: esta unidad no ejecuta DayZ.

[DESIGN] Nuevo driver, dos compilaciones: d130control y c769candidato, misma
config y entorno, directorios nuevos.150s y2GiB por árbol de compilación;
terminar sólo descendientes propios identificados por PID+create_time si exceden.
Guardar logs, PBO, ODOL extraído y hashes; cero reutilización de outputs viejos.
El control recién compilado debe coincidir semánticamente con ODOL3514 y con
su entrada del PBOef229. Si falla, resultado inconcluso y no avanzar al candidato.

## Gate binario y criterios

[EXACT] Lector estricto fijado: C:/temp/moto_lanes/review_g3/tools,
odol_reader.py SHAfa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57,
bis_reader.py SHAc9e5194aaf03e3c1a54578fa52950a1e0236c52ecb6b2597756b6a9ee618b70b,
math_types.py SHAb6ac444ca190a5cb8a7e5c0f423fafeceb31ddc8a805f2374b466ae5da6fdd10.
El lector de .agents actual no admite strict y NO es este backend.
from_file(...,strict=True),4LOD,0errores y fin exacto de todosLOD obligatorios.

[DESIGN] Consumidor distinto del autor, sobre ficheros guardados:
- Vincular hashes del contratoB3/consumer/candidato, herramientas, config,
  backend y todos los archivos leídos. Releer tras ejecución.
- Control nuevo vs3514: todos los campos decodificados iguales, salvo offsets
  físicos. canonical_lod permite sólo el reordenamiento equivalente de Roadway.
- CandidatoLOD0/2/3 idénticos canónicamente al control; posiciones, normales,
  UV, materiales, secciones/agua y metadatos incluidos. No ignorar ST ni campos
  desconocidos. Campo size_of_rest_data comprobado contra offsets instrumentados.
- ModelInfo: igual salvo center_of_mass/inv_inertia (posible dependencia de
  Geometry; reportar valores y marcar semántica física NO_CERTIFICADA, como
  el gate anterior). Bounding/geometry centers, masas y flags deben ser exactos.
- Geometry: mismos conteos9120/12160/1520. Cada componente conserva nombre,
  6vértices/8caras y asignación única. Permitir cambios sólo vertex_raw/vertices,
  normal_raw/normals y size_of_rest_data validado; los otros campos exactos.
- Comparar por componente multiconjunto de caras orientadas source/candidate
  en float32 mundial, con inversión de winding ODOL verificada en el control.
  Coincidencia exacta de esas caras y error bidireccional<.001m vigente en
  verify_compiled_stream_pilot_v31.py. No basta una bolsa de vértices.
- Overlay del lecho contra techoGeometry compilado: cobertura completa y
  límites anteriores±.02m/.01m, sin ampliar. El cero exacto del experimentoY
  anterior no es el criterio de B3: los solapes de planos vecinos se miden con
  este mismo overlay ya aprobado en B3, con errorMLOD−.000758/+ .000162m.
- Bajo poseWRP sin modificar,700/723 interiores estrictos de alguna cara de
  techo tras float32 mundial. Reportar distancia/ULP, no exigir1/2ULP inventados.
  classify() existente es diagnóstico, su etiqueta subULP no significa fallo.
- Si varía campo no previsto o identidad/control: INCONCLUSIVE_BINARY; si una
  puerta geométrica falla: REJECTED_BINARY. No descartar campos ni relajar.
- Sólo COMPILED_B3_CONDITIONAL permite FileBank en salida nueva:201modelos,
  config y propiedades/orden exactos;200entries idénticas y única sustitución
  del modelo por el ODOL validado. Paquete experimental, NO mapa ni motorPASS.

Fixtures/mutantes: control idéntico; cara invertida/retirada; punto fuera del
componente; trasladoWRP; cambioVisual/Roadway/agua/UV; campo desconocido;
masa distinta; intercambio/control viejo; candidato no ligado a su proof.
No modificar las fuentes publicadas ni reejecutar B3offline/B2.

## Presupuesto y parada

Precisiones adjudicadas antes de implementar:
- ContratoB3 SHA447d4a767183bdf95064387a7e0ef45d14a5e040aba6941c5584428e0829ff48,
  consumidorB3 y original2658 fijan700/723 y sus etiquetas. Extraer ODOL delPBO.
- Comprobar también local_predicho=float32(MLOD−bounding_center) por esquina.
  Mantener el gate exacto de caras float32mundiales del plan: es falsable;
  si falla, guardar residuo/ULP, no convertirlo a una bolsa cercana de vértices.
- MarcoODOL: float32(decoded_local+poseWRP); predicado contains en coordenadas
  float64 de ese float32, excluyendo borde. Distancia0 => REJECTED_BINARY.
  Reportar ambos marcos, sin atribuir el algoritmo interno del motor.
- Reportar b_radius,b_center,face_area (incluido NaN por bits) sin añadirlos a
  permitidos: cualquier cambio imprevisto es INCONCLUSIVE_BINARY.
- Preflight archivado exacto: R/dry-road-build-preflight-20261028/
  preflight_syntax_repaired.py SHA5fb698727b6c70e8dfa21267963b54cafa60b1ade8b4df3ebfe6b8124e5fc7f2.
  Comprobación fresca en prism-b3-binary-preflight-20261028; no repetir preparador.
- Rutas explícitas para inputs/logs/outputs, nunca rglob del árbol con junctions.
  No eliminar dependencias/junctions: se conservan aisladas, no se recorren.
  El consumidor recibe sólo los ficheros expresamente fijados, no un escaneo.
- Mutantes adicionales: control distinto, matriz rotada y ordenPBO alterado.

Plan una revisión Fable600s; código una revisión600s; tests120s; dos builds150s
y2GiB cadauno; consumidor180s/2GiB; FileBank120s. Una corrección de implementación
por repro; no recompilar por una puerta geométrica roja ni explorar parámetros.
El presupuesto no autoriza una segunda pareja. Campo imprevisto => conservar
diagnóstico, nueva hipótesis/plan antes de otra intervención. Sin DayZ en esta
unidad; después diseñar/revisar sonda originalconservada y FIFO600s.
Original47FAIL21inciertos, RAM,C1,nueve regresiones y council ampliado abiertos.

## Cierre de revisión de código

Fable5.1,396.844s,SOUND-with-fixes. H1-H6 adjudicados en
R/prism-b3-binary-code-review-20261028/adjudication.md.33tests pasan.
Control d130 contra ODOL fresco comprueba también winding/caras antes del
candidato; control fallido produce INCONCLUSIVE y no consume otra pareja.
Contacto del control se informa, no se exige que el control repare su defecto.
Campos desconocidos nulos también inconclusos. Residuos/ULP preservados.
Fixture de verify_pair reduce conteos sólo por mock local de pruebas; no es
configuración de ejecución. Producción conserva9120/12160/1520 y72vértices.
