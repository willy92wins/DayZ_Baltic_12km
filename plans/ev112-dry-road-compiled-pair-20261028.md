# Compilación aislada del lecho seco y control anterior

Estado: PAQUETE_EXPERIMENTAL_VERIFICADO_METADATA_CONDICIONAL. Revisión previa
Fable251.360s y revisión de evidencia153.203s, identidades5.1 verificadas,
sin denegaciones. Codex ejecutor/integrador. Ningún despliegue.
Traza: ev112-dry-road-mlod-materialization-20261028 §4, publicado294a9e1.

## Hipótesis y alcance
[DESIGN] Compilar fuente anteriorbbf4d5e4 y candidatod13069d5 con idénticos
Tools/config/datosvanilla permite aislar los efectos de bajar82Y y regenerar
normales, sin desplegar ni recompilar el mundo. Se autoriza una pareja: control
anterior + candidato; ambos conservan su propia salida. No reutilizar builds.
Sólo cs_kit_118_0000; config temporal de una clase con model_config existente.
El config temporal NO sustituirá al config.bin vigente57d0d0ae.

## Anclas verificadas
[EXACT] tools/water/pack_continuous_stream_pilot_v31.ps1:1-28 construye una
carpeta piloto aislada y crea junctions DZ/bin/core dentro de ella. No despliega.
continuous_stream_pilot_v31.py:41 model_config genera config de HouseNoDestruct
con Land_<nombre>, dependencias DZ_Water/DZ_Surfaces.
attach_navmesh.py:20 read_pbo retorna bytes/propiedades/entradas sin compresión.
ODOL.from_file(strict=True) del lectorfa0d74b6; LOD.lod_end_ok, model_info.
bounding_center y secciones leídos en verify_compiled_stream_pilot_v31.py:46-68.
Normales comprimidas10bits: math_types.py:40-50, escala−1/511.

Preflight28-10: P/DZ/bin/core/Tools/Mods pasan. Skill oficial tenía un literal
inválido de texto en línea213; copia local corrige sólo prefijo r, sin modificar
skill instalada. Recibo dry-road-build-preflight-20261028/report.json.

## Presupuesto y puertas
Revisión600s. Dos compilaciones máximo150s cada una, sin búsquedas de parámetros.
Runner registra PID y en timeout termina sólo su árbol de procesos, no DayZ.
No directorios compartidos/cachés reutilizados; nuevas source/temp/packed porlado.
Cada salida debe: retorno0, log Build Successful, exactamente una entradaODOL
nombrada correctamente y config.bin. Inputs/toolshashes antes/después iguales.
Éxito del driver = COMPILED_PAIR_READY_FOR_CONSUMER, nunca PASS de mapa.

## Consumidor siguiente
Antes de integrar: verificar fuentes→ODOL a pose real del WRP y centro anterior;
caras por multiplicidad/winding/rol, todos los prismas/cobertura/agua/Memory,
UV/materiales/normales/flags. Comparar control nuevo contra ODOL vigente para
discriminar cambios de toolchain. Inventariar campos opacos/cambios desconocidos
y cerrar con evidencia o marcar INCONCLUSO; no ignorarlos por conveniencia.
Tras validar, componer PBO cambiando sólo una entrada y preservar las200restantes
y config/prefijo exactos; comprobar corredor expuesto en geometría compilada.
Sonda DayZ sólo después de esta puerta y plan de experimento revisado, porFIFO.
RAM, visual, C1 y resto de regresiones siguen abiertos.

Adjudicación: se corrige ancla P:/bin/config.bin inexistente a config.cpp real;
verificado en host antes de ejecutar. Directorio de evidencia creado antes de
precondiciones para conservar fallo si falta un input. No cambia alcance.
Descubrimiento previo ODOL: Visual contiene845puntos pero831XYZ únicos por
agua/lecho coincidentes. No usar diccionarioXYZ sin rol para comprobar normales.
Las dos lecturas abortadas por exigir unicidad eran error del descubridor;
el tercer diagnóstico midió0distancia geométrica y duplicados, no corrupción.
Precondición adicional corregida antes del compilador: psutil no estaba instalado
y este intérprete no tiene pip. uv instaló rueda psutil7.2.2 exclusivamente en
R/dry-road-build-dependencies-20261028; versión/código nativo sellados por el
driver. Ningún paquete del intérprete compartido se modifica. Intentos previos
terminaron durante import, sin iniciar compilación ni crear su carpeta.

## Segunda ronda: separar altura y normales (diagnóstico, no candidato)
Pareja principal consumida7.485s/4.750s. Control reproduce toda semántica vigente;
candidato conserva centro/pose/agua/UV/Memory, todas sus caras coinciden con MLOD
y contacto0. Quedan cambios derivados: VisualST/area_over_tex/area; centro de masa
e inercia. No hay PASS de paquete todavía. Análisis6.625s consumido.

[HIPÓTESIS] ST/área y masa son función de las posiciones; normales comprimidas
son función de normales MLOD. Separar componentes antes de ajustar parámetros:
dos compilaciones diagnósticas Y-nueva/N-antigua e Y-antigua/N-nueva, exactamente
complementarias por bytes. Ninguna es una reparación ni se despliega. Presupuesto
2×150s, mismos Tools/config/inputs sellados; no repetir control/candidato.
Codex revisa el plan contra API/timeout ya revisados por Fable; ejecución acotada.
Discriminador: clasificar cada campo cambiado como dependiente sólo deY, sóloN,
o interacción/inexplicado. Inexplicado mantiene INCONCLUSO, no se permite ignorar.
Fuentes diagnósticas se guardan separadas con etiqueta explícita. No tocar autor,
candidato validado, tolerancias ni fuentes de la pareja ya consumida.

## Adjudicación de evidencia compilada y continuación
Ambos experimentos terminados, no relanzar. ControlODOL8b9892e1 reproduce
semántica del vigente0e3c8ef8, sólo orden canónico Roadway. Candidato351424ab
conserva centro−4.0107421875/0.396484375/−5.59375, poseWRP, todas sus caras
Visual/Roadway/Geometry exactas al MLOD, agua/UV/Memory y contacto0. No PBO201
nuevo compuesto todavía. Sólo paquetes aislados de un modelo.

Revisión Fable SOUND-with-fixes propone cinco gates; adjudicación Codex:
- Aceptar composición de una entrada,200payloads/config/prefijo exactos, nombres
  y orden. No exigir cabecera literalmente idéntica: el tamaño de la entrada
  modificada cambia. No publicar historial privado.
- Rechazar G2 como prueba independiente: A≠C implica A≠B o B≠C, su unión es
  tautológica. Usar allowlist semántica justificada y comprobar cada campo.
- Corregir G3 con medida real: size_of_rest_data incluye sus4bytes. En16LOD
  de cuatro builds coincide con declared_end−posición_postcampo+4. La regla
  sugerida sin+4 daba falsos FAIL. Lectorinstrumentado local sólo capturóposition;
  lector instalado intacto. dry-road-review-claims-20261028/report.json.
- Corregir G4 con soporte geométrico: ST puede depender de los triángulos que
  comparten vértice, no sólo de su Y.82Y,125normales,128vértices del primer anillo,
 124ST. Siete falsos FAIL de la regla sugerida están en ese anillo. Discriminador
  dry-road-st-neighborhood-20261028.json: seis invariantes locales cumplen;
 721slots constantes exactos en cuatro builds, ninguna quiralidad cambiada y
  todos los124slots modificados dentro de envolvente de control. Layout ST sigue
  HIPÓTESIS; no se convierte en hecho por medir un patrón compatible.
- No adoptar el1e-3 relativo de area_over_tex como tolerancia sin fundamento.
  Agua exacta; sección seca depende sóloY según bisección. Fórmula desconocida,
  se mantiene INCONCLUSO semántico. Debe declararse en aceptación experimental
  y contrastarse en resultado visual, sin presentar aprobación global.
- Derivar conteos porrol en consumidorfinal, no literalesTrue enreportes; normal
  Visual ya reproduce EXACTAMENTE codeword10bits en4632esquinas porbuild
  (dry-road-normal-codec-20261028/report.json). Sus dos controles aritméticos
  son sólo smoke, no sustituyen mutaciones del consumidor real.
- Censar cambios nuevos introducidos sólo por diagnósticos, incluso si
  control==candidato, y registrar sus hashes en informe final. STinteracción y
  tamaño comprimido son dominios explícitos, no permiso para ignorarotroscampos.

Próxima unidad, antes de ejecutar: implementar y revisar consumidor final de
paquete/metadata y contrapruebas reales (byte ST en vértice no influido, inversión
de marco, normalcodificada, segunda entradaPBO, campo desconocido). Presupuesto
consumidor300s/2GiB, mutantes300s, FileBank120s, una corrección por repro.
Mantener criterios anteriores±0.02m/0.01m y correspondencia de geometría exacta.
El resultado debe separar geometría/paquete verificados de ST/area_over_tex
semánticos sin demostrar y visual/motor pendientes. Sin aceptación silenciosa.
Después, preparar sonda propia porFIFO; no hay ejecución ni lease actual.

## Revisión final del consumidor antes de ejecución
Fable5.1,361.235s,SOUND-with-fixes,entradas inmutables y0denegaciones.
Adjudicación Codex: eliminar rest_data_offset_probe de la comparación semántica
en TODOS losLOD; sigue comprobado con tamaño físico+4. Es offset absoluto y
no un campo del modelo. Mutante de agua escribe una única Yfloat32 en el stream
y en el objeto decodificado. Resolver rutas de identidad del propio código.
Sustituir literal de certificado numérico por filas/puntos realmente comparados.
Mutar normal de un vértice referenciado, rechazar XZ no encontrado explícitamente
y distinguir pruebas de función/consumidor completo/paquete en el informe.
Correcciones no cambian requisitos geométricos ni tolerancias. Ejecutar una vez
consumidor, negativos y composición; preservar cualquier fallo antes de reparar.

Primera ejecución del consumidor consumida: rechazoY_only:LOD3:faces,sections.
Discriminador4.125s: caras Roadway etiquetadas/material/winding/multiplicidad
exactas; sólo reordenadas por compilador, igual que control vsbaseline.
Adjudicación: aplicar canonical_lod también al Roadway de los diagnósticos;
NO permitir cambios de caras arbitrarios. Negativo nuevo inviertewinding y debe
rechazarse. Añadir dependencia exacta de vertex_raw/normal_raw en los4LOD entre
los builds complementarios, medida4/4antes de modificar. Una ejecución r2 fresca,
presupuesto300s/2GiB sin variar límites. Fallo original queda conservado.

## Resultado ejecutado
Consumidor r2:7.438s, geometríaexacta en45744esquinas porbuild y4632normales
Visual;21filas/819puntos ligados al candidato numérico;1520prismas/contacto0.
Doce negativos rechazados en12.750s. El informe distingue5pruebas del consumidor
completo,2del consumidor geométrico,1de funciónST y4de identidadPBO.
FileBank1.500s: PBOef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84,
una entrada modificada,200modelos/config/prefijo/orden exactos. Carpeta aislada
dry-road-final-package-20261028, sin despliegue. ST/area_over_tex semánticos
condicionales; motor/visual/RAM/global no aceptados. No repetir estas ejecuciones.
