# B3C: descubrir el dominio de cuantización antes de otra reparación

Estado: REVISADO_PARA_EJECUTAR. No autoriza modificar MLOD ni compilar.
La pareja B3B está consumida. R1 es REJECTED_BINARY en component1335: cuatro
caras difieren por un paso float32 mundial Y, 4.76837158203125e-7 m. No se ha
evaluado el resto de puertas después del primer fallo; no extrapolar su alcance.
No empaquetar el candidato b2c8 ni presentar el rechazo como fallo de DayZ.

## Hipótesis y anclas

[HIPÓTESIS] Las conversiones del contrato float32(MLOD+origen) y
float32(float32(MLOD-centro)+traslación) pueden no conmutar por redondeo.
El residuo local compilador/predicción fue cero hasta el primer rechazo. El control nuevo no
presenta esta discrepancia y conserva sus 1520 componentes. El candidato
coincidió con la predicción local hasta el primer rechazo, pero falta el censo
completo: no atribuir todavía un mecanismo global ni descartar otros cambios.

Fuentes: evidence/prism-b3-binary-20261028; contratos original45d6bd48 y
replay5df50091; MLODc769; ODOLcontrol0fcc y candidatob2c8. Históricos3514/d130,
pose19394363 y contratoB3 447d siguen fijados. No cambiar etiquetas700dry/723wet.

## Descubrimiento propuesto, sólo lectura

1. Leer los mismos binarios guardados, con el backend estricto fijado. Censar
   por componente todos los residuos fuente/ODOL, sin detenerse en el primero:
   predicción local, mundofloat32, caras orientadas, vértices/techo/base/normal,
   pertenencia al dominio autorizado y ULP por eje. Distinguir cobertura de
   censo de veredicto de aceptación; B3B permanece REJECTED_BINARY.
2. Aislar las operaciones numéricas con casos analíticos adversariales:
   redondeo al par, valores negativos, cruces de exponente, centro/traslación,
   pares verticales de grosor180/512. Comparar contra ODOL, no sólo contra la
   misma transformación implementada. Geometría completa y modelo intactos.
3. Investigar si existe un ajuste de Y dentro del dominio autorizado que
   preserve los pares de grosor EXACTO y todas las condiciones geométricas
   anteriores, incluidos plano1e-6 y overlay±.02/.01, mientras hace iguales las
   caras mundiales guardadas. Buscar representación exacta de las operaciones;
   no ampliar tolerancias ni sustituir igualdad por proximidad.
4. Entregar factibilidad con testigo verificable o conflicto concreto. No
   escribir candidato en esta fase. Si existe testigo, redactar/revisar plan
   de autoría, consumidor independiente y futura pareja antes de ejecutarlos.

Presupuesto propuesto: una revisión de plan300s, censo180s/2GiB, tests120s,
análisis numérico180s/2GiB. Cero builds, paquetes, DayZ o cambio del desplegado.
Nada de volver a lanzar scripts B3/B3B/R1 consumidos ni retocar sus resultados.
Un fallo de lectura/marco es INCONCLUSIVE; contradicción geométrica sigue FAIL.

No se cierra ninguna regresión visual, agua,47FAIL21inciertos,RAM,C1 ni calidad
global. El council ampliado sigue después del trabajo previo conforme al plan.

## Contrato mecánico para la revisión

[EXACT] prism_b3_binary_ev112.py:source_faces usa float32(MLOD-centro) local,
float32(MLOD+origen) y float32(ODOL+traslación) mundial. El lector es el backend
fijado en compiled_dry_road_gate_ev112.py:READER_HASHES/read_backend; no cambiarlo.
verify_prism_contact_b3_ev112.py:118-127 define plano y base con error<=1e-6;
prism_contact_b3_ev112.py:dilate exige diferencia de pares EXACTA180/512.
No volver a ejecutar esos autores/consumidores; consultar definiciones y usar
primitivas de lectura, comparación y overlay en un instrumento nuevo.

[DESIGN] Asociar esquinas fuente/ODOL por nombre de componente y coordenada local
predicha EXACTA, con unicidad obligatoria; nada de nearest-neighbour permisivo.
Si la asociación no existe, informar componente inconcluso y conservar conteos,
sin esconderlo del denominador. Enumerar todos los componentes y casos no
comparables. Guardar residuos por eje, índices, techo/base, caras y normales
geométricas derivadas; no equiparar esas normales con semántica física del motor.
Control histórico/nuevo y candidato se comparan bajo los mismos marcos.

Factibilidad Y: mantener X/Z y dominio de los12prismas. Por cada par, enumerar
los float32 representables dentro del intervalo ya permitido del plano fuente
(+/-1e-6), elegir el cambio mínimo que conserve base/plano, grosor EXACTO y
coincidencia mundial exacta en ambas esquinas. No barrer amplitudes de reparación
ni cambiar parámetros del compilador. Máximo100000valores por par y1000000total;
si se supera, INCONCLUSIVE_DOMAIN_BUDGET, nunca UNSAT. Dominio vacío tras censo
completo => conflicto de ese par bajo estas condiciones, no imposibilidad global.
El cero con signo y los cruces de exponente deben probarse. Testigos se guardan
como JSON numérico, nunca como archivo MLOD/ODOL ni candidato publicable.

Comprobar el testigo completo en memoria: sólo Y autorizado, X/Z exactos,
pares exactos, plano/base1e-6, cierre/convexidad, caras mundiales exactas bajo
modelo numérico y overlay completo con limites±.02/.01. Estas comprobaciones
son FEASIBILITY_ONLY, no certifican cómo compilará un candidato nuevo. Contrastar
el modelo numérico con ODOL ya guardado y fixtures racionales IEEE754 de ties,
negativos/exponentes; no usar el redondeo que se prueba como único referente.
Original700/723 conservan X/Z/etiquetas; intersecciones X/Z del testigo idénticas
al candidato de entrada, sin afirmar éxito nativo.

[DESIGN] Tests antes del censo,120s. Revisión de código300s añadida al presupuesto;
censo180s/2GiB y factibilidad180s/2GiB en una ejecución acotada360s/2GiB con salida
por fases. Una corrección de instrumento por repro; cero nuevos builds o replay
B3B. Cerrar unidad con evidencia/código/tests, no con una reparación declarada.

## Adjudicación previa a implementación

Fable5.1 nativo181.25s,SOUND-with-fixes(plan); código275.156s adjudicado abajo.
1. Hipótesis reformulada sin causa atribuida al compilador. Separar residuo local
   empírico frente a vertex_raw del residuo mundial entre marcos calculados.
2. Centro c y traslación T fijos al ODOL/WRP guardados. Testigo exige AABB completo
   de Geometry y del modelo idéntico al inicial; ningún valor saldrá del bbox ni
   moverá un extremo único. Eso no certifica el centro de una compilación futura:
   deberá comprobarlo su nueva puerta binaria, como todos los metadatos.
3. Censo registra igualdad de valor y de bits por separado, incluido cero con
   signo. El gate B3B anterior comparaba valores; su rechazo se conserva. El
   testigo buscará además igualdad de bits, sin reinterpretar resultados pasados.
4. Sólo predicción local/vertex_raw contrasta un producto del compilador. Mundo
   ODOL es cálculo del instrumento. Oracle IEEE754 basado en Fraction, fixtures
   con resultados de bits escritos a mano: ties par/impar, negativos,4/8,cero y
   subnormales. Caso2^100-1 expone pérdida en resta float64 y delimita la hipótesis;
   no asumir resta float64 exacta universalmente.
5. Informar tamaño real de cada dominio. La enumeración usa Y LOCAL MLOD, no
   Y mundial6.5–7.1: no adoptar la estimación del revisor de4–5valores por par.
6. Denominador1520por modelo; separar prefix comprobado en R1 y parte nueva,
   conservando cualquier ambigüedad o componente no comparable.
7. Testigo declara normales a rederivar en futura autoría. El aislamiento
   positions_only/normals_only anterior no prueba el nuevo ajusteY.

## Adjudicación de código antes del censo

Fable5.1 nativo275.156s, SOUND-with-fixes. Una corrección agrupada del
instrumento;26tests PASS (0.285s suite,1.036s proceso). Revisión consumida.
H1 aceptado y reproducido: dominio67,30 elegibles según contrato frente a17
con filtro adicional. Se elimina únicamente ese filtro no aprobado; grosor
MLOD180/512 sigue EXACTO. Se reportan grosores local/mundial sin convertirlos
en nuevas puertas. Testigo manual local0.3515625596046448,mundial0.3515625.
H2 aceptado: fixture12prismas con centro0.396484375/origen7, base0xbed90e97;
censo falla en Y y testigo cambia vértices con overlay/cierre/bbox conservados.
H3 aceptado: oracle racional verifica TODO el dominio (techo y base), no sólo
el elegido. Mutante en un valor descartado provoca INCONCLUSIVE. Caché por
racional; cero con signo en suma/resta probado de forma explícita.
H4 aceptado: separar pins heredados VERIFICADOS de hashes instrumentales
REGISTRADOS; ambos se vuelven a comprobar al final para detectar cambios.
H5 aceptado: control completo sin diferencias locales/mundiales/topología
es prerrequisito; fallo produce INCONCLUSIVE_CONTROL_FRAME antes del solver.
También se revalida identidad semántica histórica3514/control0fcc mediante
primitiva de comparación; no se ejecuta el consumidor B3B ni se compila.
No revisión N+1 ni tolerancias nuevas. Ningún modelo, paquete o run autorizado.
