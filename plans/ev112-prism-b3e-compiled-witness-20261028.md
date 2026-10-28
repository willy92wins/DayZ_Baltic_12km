# B3E — comprobar el testigo numérico en el ODOL guardado

Estado vigente: CONSUMIDO_INCONCLUSIVE_PREFLIGHT. El intento agotó 60.047 s
antes de sellar el entorno y sin compilar control ni candidato. Código y 41
tests validados; no ODOL nuevo. Plan y aprobación tal como se ejecutaron en
evidence/prism-b3e-preflight-20261028/plan-executed.md y approval.json.
No relanzar el preparador. Siguiente unidad sólo lectura:
plans/ev112-b3e-preflight-timeout-discovery-20261028.md, revisada para implementar.
Los estados que siguen describen las puertas históricas antes de ese intento.

Estado: REVISADO_PARA_IMPLEMENTAR. Fable5.1 nativo105.985s, SOUND-with-fixes,
adjudicado; todavía no hay código B3E ni autorización técnica para compilar.
Codex ejecutor/integrador por petición viva.
Consumidor de esta fase: una pareja compilada nueva y su verificador independiente.
Sólo compilación aislada y lectura de binarios; no paquete completo de 201 modelos,
despliegue, misión ni DayZ. No espera decisión humana ya concedida: exige revisión
técnica y pruebas del nuevo instrumento antes de ejecutar la pareja.

## Producto e hipótesis

EV112 conserva agua, extremos, poses y navegación mientras repara la Geometry
de orilla seca. B3D publicado en148da18d acredita un MLOD con17Y corregidas,
50caras/normales incidentes,4560pares de grosor exacto, planos/overlay/cajas y
controles originales conservados. No es una reparación aceptada en el motor.

[HIPÓTESIS] La compilación nueva mantiene el centro y las coordenadas locales
previstas por B3D, de modo que las caras mundiales guardadas coinciden exactamente
con el nuevo MLOD bajo la pose WRP existente. La prueba mide ODOL y cálculos de
marcos; no observa todavía el algoritmo de colisión del motor.
No reinterpretar B3B REJECTED_BINARY ni B3C FEASIBILITY_ONLY.

R = E:/DayZ-Baltic-Build/shape-repair-20261025.
Entradas obligatorias, externas al nuevo candidato binario:
- B3D MLOD R/prism-b3d-candidate-20261028/candidate.p3d,
  f2b7018bea6a692ef5964bae4894172e0a73eeabe8be55ea68244a774cb7e634.
- Contrato B3D R/prism-b3d-execution-20261028/contract.json,
  b44553ee67478e597511e6a075452b07858d6f2457f9a035c3f1101d4bdbf31a.
- Prueba B3D R/prism-b3d-consumer-20261028/report.json,
  ae5eea19e819cc7c5f61041b77cea0c15f4269ed080dcb470c2acf2a994d25b6.
- Control MLOD d130 y ODOL histórico3514, paqueteef229, posesNPZ6c0a,
  original2658 y12componentes: rutas y hashes heredados del contratoR1
  5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244.

Nuevo contrato conserva íntegra esa cadena y fija fuentes/config/herramientas,
lector y pruebas. No sustituye hashes heredados por los observados ahora.
Origen[8262,7,8934], centro[-4.0107421875,.396484375,-5.59375],
pose19394363 identidad+traslación[8257.9892578125,7.396484375,8928.40625].
700dry y723wet mantienen etiqueta,posición y margen del informe B3D.

## Anclas leídas y compatibilidad

[EXACT] tools/water/pack_continuous_stream_pilot_v31.ps1:1-29 recibe -Pilot,
exige salidas nuevas y llama AddonBuilder con prefix/project/temp propios.
Sus junctions DZ/bin/core son dependencias: no recorrerlas ni borrarlas.
tools/water/continuous_stream_pilot_v31.py:41-48 model_config(instances)
genera config con Land_<stem>, HouseNoDestruct y dependencias DZ_Water/Surfaces.
tools/quality/compiled_dry_road_gate_ev112.py:42-49 read_backend valida los
tres hashes del lector, instrumenta sólo offsets en memoria y devuelve ODOL.
tools/water/review_compact_collision_v31.py:16,24,45 contiene load,vertices
y overlay; límites vigentes vertical±.02m/horizontal.01m.

[EXACT] tools/quality/prism_b3_binary_ev112.py:159-171 verify_saved está ligado
al candidato c769 y contrato447d: NO es invocable como CLI B3E. Sus primitivas
control_identity:47, pose_check:63, source_faces:82 y verify_pair:123 permiten
reutilizar comprobaciones de estructura/identidad/geométricas; el nuevo wrapper
debe ligar B3D antes de usarlas. No editar ni ejecutar los CLI B3B/B3C consumidos.
face_counter:52-56 compara valores numéricos; B3E añadirá comparación de bits
float32 para las caras mundiales, incluyendo signo de cero, sin tolerancia.

## Construcción aislada y secuencia

[DESIGN] Primero preflight fresco. Ejecutar las comprobaciones oficiales mediante
la copia local archivada con la corrección sintáctica documentada y hash5fb69872,
verificando su procedencia/diff contra el original; no editar la skill gobernada.
Registrar el fallo del original si persiste. Verificar P:,DZ/bin/core/scripts,
Mods junction y herramientas existentes; la ausencia de Diag es advertencia para
esta fase sin motor, nunca una acreditación del entorno nativo. Si falla una
dependencia necesaria para compilar, no construir. Sellar AddonBuilder,Binarize,
CfgConvert/FileBank utilizados y config idéntica de ambos lados; si difieren
respecto a las herramientas de la referencia, tratarlo como cambio de entorno
y reevaluar antes de compilar. No renovar lanzadores ni tocar procesos ajenos.

[DESIGN] Nuevo preparador con salida exclusiva. No reautoriza el MLOD ni llama
al solver. Copia d130 y f2b7 a sus fuentes aisladas, compara bytes con sus pins.
Una compilación de control; extraer el ODOL del PBO guardado y comprobarlo
contra3514/ef229, incluidos winding y caras d130, antes de iniciar el candidato.
Si control no cumple, detener sin consumir la compilación candidata.
Después una compilación candidata con la misma config y parámetros; extraer
su ODOL guardado, preservar logs/hashes. El verificador no consume arrays del
preparador: abre de nuevo esos PBO/ODOL. Comprobar pins y salidas antes/después.
No recorrer árboles con junctions. El límite de memoria/procesos sólo alcanza
al árbol creado por este preparador, identificado por PID y create_time.

## Puertas sobre binarios guardados

[DESIGN] El consumidor nuevo exige, en este orden:
1. Identidad del contrato B3D, proof ae5e y candidato f2b7; poses originales,
   pins transitivos y resultados originales700/723. Cuatro LOD completos con
   strict=True, sin errores ni EOF inconcluso. Payload ODOL igual al PBO y
   config.bin idéntica entre los dos paquetes aislados de un único modelo.
2. Control nuevo semánticamente idéntico a3514 y su payload del paqueteef229;
   caras/winding respecto d130, sin exigir contacto interior al control histórico.
3. Protecciones de verify_pair: header,LOD0/2/3 completos, flags,masas,agua,UV,
   normales/materiales/secciones, campos desconocidos incluso None. ModelInfo
   sólo permite center_of_mass/inv_inertia como antes, valores reportados y
   semántica física NO_CERTIFICADA. Centro/bbox/pose exactos. Geometry conserva
   9120/12160/1520,6p/8caras por componente y asignación única completa; fuera de
   los12componentes72vértices conserva raw coordenadas/normales exactamente.
4. Censo completo1520/1520 de correspondencia por componente, sin extrapolar
   el primer rechazo: localraw guardado bit-idéntico a float32(MLOD-centro).
   Caras orientadas del MLOD+origen y ODOL+pose, ambos convertidos a float32,
   iguales bit a bit; inversión de winding justificada por control. Emitir
   todas las discrepancias/residuos/ULP antes de rechazar. Conservar también el
   error bidireccional previo al redondeo mundial<.001m ya vigente, distinguiéndolo.
   No imponer grosor local recentrado exacto: no era requisito y17pares del
   testigo no lo cumplen; los4560pares MLOD exactos vienen acreditados por B3D.
5. Overlay completo del lecho Visual intacto sobre techoGeometry compilado,
   cobertura total y límites±.02/.01.700/723 estrictamente dentro de una cara
   de techo en el marco mundial float32, con margen exactamente igual al B3D
   conservado. Reportar ULP sin inventar mínimo de1/2ULP. Sin cambio de etiquetas.

Sólo todas las puertas pasan => COMPILED_B3E_CONDITIONAL. Error geométrico
explícito => REJECTED_BINARY. Lectura,identidad,campo imprevisto o error interno
=> INCONCLUSIVE_BINARY. No falsos PASS por excepción vacía, campo desconocido
o censo parcial; después de una puerta fallida no declarar probadas las siguientes.
No ejecutar FileBank para201 ni desplegar. El paquete completo y la sonda nativa
necesitan su siguiente plan, usando únicamente este resultado si cumple.

## Contraejemplos, presupuesto y parada

[DESIGN] Fixtures guardados/no triviales: positivo de marcos exactos; cambios
de un ULP en base y techo (dos casos de B3C),cara invertida/duplicada/omitida,
componente incompleto/duplicado, signedzero, centroid distinto, pose rotada,
Visual/agua/UV/Roadway tocados, campo nuevoNone, modelo/control intercambiado,
proof ajena o desfasada, payloadPBO distinto, entrada mutada entre lecturas,
contacto en borde y margen alterado, overlay fuera de±.02/.01. Reusar fixtures
de helpers anteriores sin volver a lanzar experimentos históricos.

Una revisión del plan210s y una del código300s; una corrección agrupada con
repros, sin rondas de opinión nuevas. Suite120s por proceso. Preflight60s,
dos builds150s/2GiB por árbol como máximo, gatecontrol180s/2GiB y consumidor
final180s/2GiB. Un control y un candidato, sin barrer parámetros ni reconstruir
tras fallo geométrico. Al agotar presupuesto conservar evidencia y reevaluar;
no aprobar por ausencia de dictamen. Criterios y presupuesto antes de ejecutar.

Original47FAIL21inciertos, RAM, referencia independiente de agua, nueve
regresiones visuales, C1 y aceptación global permanecen abiertos. El council
ampliado sigue después del trabajo previo; esta revisión no lo sustituye.

## Adjudicación del plan — 28-10-2026

Una entrega Fable5.1 nativo105.985s completa, fuentes intactas, sin herramientas.
R/prism-b3e-plan-review-20261028 conserva dictamen y adjudicación. No code review
ni builds ejecutados. Los siguientes detalles se incorporan antes de implementar:

- F1: censo nuevo completo1520/1520, no las12entradas sugeridas en el dictamen.
  No llamar source_faces antiguo para obtener el censo: aborta al primer fallo.
  Repro con dos componentes distintos debe conservar ambos y el denominador
  completo; errores estructurales se informan INCONCLUSIVE, nunca como ausencia
  de discrepancias. verify_pair sólo después del censo; sus otros gates se
  conservan y no se declaran ejecutados si falló una puerta anterior.
- F2: claves cíclicas orientadas de vértices float32 vistos como uint32, sin
  convertir primero a float64. Signedzero y dos discrepancias1ULP son negativos.
  En contactos se reporta componente y cara testigo del ODOL, ligando componente
  y margen al proof B3D; no exigir igualdad del índice físico de cara entre
  formatos, porque un reordenamiento no cambia la superficie.
- F3: gate_control autónomo, con centro del control, no del candidato inexistente.
  Consumirá baseline/control/d130/pose y emitirá recibo sellado antes de construir
  candidato. Repro controlfallido => ningún archivo de compilación candidata.
- F4: no se acepta que comparar ODOL leído con MLOD independiente sea tautológico.
  Sí se limita la inferencia: winding invertido reproduce d130 en esta pareja de
  control y éste coincide semánticamente con3514; no prueba una ley universal
  del compilador ni el algoritmo físico del motor. Así se describirá el resultado.
- F5: binding nuevo, no bind_context antiguo. Contrato b445 aporta seleccionados,
  targets y fuentes; proof ae5e aporta candidato/contrato y medidas. Validar esquema,
  presencia y pins sin rellenar campos ausentes. Excepciones internas/KeyError =>
  INCONCLUSIVE con tipo y traza conservados. Estado CLI no se infiere del texto.
- F6: resultado propio COMPILED_B3E_CONDITIONAL y límites explícitos sin motor/201.
- F7: preparador sella config y herramientas, comprueba config.bin de ambos PBO,
  excluye junctions de cualquier recorrido. Hash de ejecutable instalado no
  demuestra por sí solo que el builder lo haya usado: distinguir comando lanzado,
  hijos observados y binarios sólo inventariados; no inferir identidad retrospectiva.

La cápsula no contenía contrato b445, lector ni reparación local de preflight:
se incluirán esas anclas verificadas en la code review. Los módulos antiguos ya
leídos no se mutan. Ningún cambio de tolerancia, etiqueta, geometría o producto.

## Puerta de ejecución — 28-10-2026

REVISADO_PARA_EJECUTAR. Fable 5.1 nativo entregó SOUND-with-fixes en 271.875 s;
adjudicación en R/prism-b3e-code-review-20261028/adjudication.md. Corrección
agrupada: errores internos inconclusos, telemetría exe opcional manteniendo
memoria fail-closed, nacimiento de descendientes, reproducción de métrica MLOD
antes de exigir el margen ODOL y mismo dominio de 12 contactos. Censo y overlay
siguen completos. No se mutaron helpers sellados ni tolerancias. Suite final
privada 41 PASS en 31.872 s (proceso 44.484 s), postimágenes intactas.
La aprobación mecánica fija código, plan, revisión y recibo de tests antes de
preflight fresco y la única pareja compilada. Ningún paquete 201 ni motor.
