**Veredicto: SOUND-with-fixes.** El plan B3F es composición pura, reusa sólo `package_identity`, conserva el baseline ef229 y no toca B3E2 ni DayZ. Faltan cuatro cierres de identidad y dos definiciones que, sin fijarse, dejarían ambiguo un PASS.

**Hallazgos**

1. **Enlace control/target no está como comprobación.** La línea 18 afirma target 3514 en ef229 y el reporte B3E2 da control 3514, pero el consumidor (líneas 47-49) sólo compara el target posterior con 2581. Debe exigirse explícitamente antes de empaquetar: sha(baseline target) == control_odol_sha256 del reporte B3E2 == 3514. Es el único hecho que une la pareja real con el universo201.

2. **Pins incompletos y "ambos census" sin nombre.** La línea 32 lista contrato, proof, census, baseline, candidato y herramientas, pero no fija sha del report.json de prism-b3e2-compiled ni del segundo census. Nombrar las dos rutas y sus hashes en el plan, y exigir en el reporte final la cadena contract c370 / proof 9a54 / candidate 2581 / control 3514 leída de esos archivos, no transcrita a mano.

3. **"Orden" ambiguo.** La línea 26 dice "listaordenadaentradasigual" y la 48 "comparar orden". Hay que distinguir orden físico del PBO y conjunto ordenado. FileBank puede emitir orden físico distinto al de ef229 si el baseline se construyó con otra invocación. Definir: conjunto ordenado igual es obligatorio; si el orden físico difiere, el estado es REJECTED_PACKAGE, no PASS con nota.

4. **Propiedades: FileBank puede añadir o reordenar.** La identidad exige props iguales a (prefix, product). Añadir fixture negativo donde el PBO tenga propiedad extra, duplicada o en otro orden, y comprobar propiedades como lista ordenada por posición, no como dict.

5. **Import del módulo gate arrastra constantes consumidas.** Reusar `package_identity` obliga a importar un módulo con CANDIDATE_SHA 3514 y `meter`. El preparador nuevo debe pinear sha del módulo, importar sólo la función y no llamar a `require` sobre sus constantes. Un test debe fallar si el nuevo código referencia CANDIDATE_SHA o ANCHORS del gate antiguo.

6. **Lector "independiente" es el mismo lector.** Si consumidor y preparador usan `attach_navmesh.read_pbo`, un bug de parser pasa en ambos. Aceptable para esta fase, pero el reporte debe declararlo como límite y pinear el hash del lector una sola vez.

7. **Reverificación del candidato copiado.** Tras escribir cs_kit_118_0000.p3d en la carpeta fuente y tras rc0 de FileBank, rehash del archivo fuente == 2581 y de los 200 restantes + config == bytes de ef229. El plan lo dice en general (línea 32); ponerlo como paso enumerado con fixture "archivo modificado entre fases" sobre el candidato, no sólo sobre un modelo cualquiera.

8. **Preflight de FileBank.** Fijar sólo el sha del .exe no cubre DLL del directorio PboUtils. Registrar en el preflight el listado y hashes del directorio y declararlo como límite si no se pinean.

9. **Nombre del PBO de salida.** FileBank nombra por la carpeta fuente. El consumidor debe exigir exactamente Addons/baltic_stream_pilot.pbo y ningún otro archivo en Addons; añadir fixture con archivo extra.

**Lo que está bien**
- Baseline ef229 del final-package, no kit7, y config201 conservado tal cual.
- Candidato 2581 desde carpeta de evidencia, no desde P:/Mods.
- Código viejo sólo como referencia; estados nuevos no colisionan con el antiguo.
- Presupuesto 60/120/120s y 2 GiB adecuado para copia de 202 entradas; medición por árbol de procesos ya practicada en B3E2.
- Fixtures negativos cubren omisión, extra, config de un modelo, intercambio target/control y rc0 tardío.
- Sin reintentos, salida existente falla, sin junctions.

**Fixes a aplicar en el borrador**
- Añadir paso "control==target baseline==3514" antes de preparar.
- Listar pins completos con rutas y sha de ambos census y del reporte B3E2.
- Definir orden físico y propiedades posicionales como criterio de REJECTED.
- Añadir fixtures: propiedad extra/reordenada, candidato mutado entre fases, archivo extra en Addons.
- Declarar límites: mismo lector, DLL de FileBank no pineadas.
- Test que prohíba uso de constantes consumidas del gate.

Sigue sin cerrar 47 FAIL / 21 inciertos ni atribuir causa; el PASS condicional sólo acredita composición byte-exacta.

FIN_REVISION