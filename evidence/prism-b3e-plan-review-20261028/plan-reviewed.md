# B3E — comprobar el testigo numérico en el ODOL guardado

Estado: BORRADOR_PENDIENTE_REVISION. Codex ejecutor/integrador por petición viva.
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
