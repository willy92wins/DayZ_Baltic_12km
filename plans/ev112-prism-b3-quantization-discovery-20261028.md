# B3C: descubrir el dominio de cuantización antes de otra reparación

Estado: BORRADOR_PENDIENTE_REVISION. No autoriza modificar MLOD ni compilar.
La pareja B3B está consumida. R1 es REJECTED_BINARY en component1335: cuatro
caras difieren por un paso float32 mundial Y, 4.76837158203125e-7 m. No se ha
evaluado el resto de puertas después del primer fallo; no extrapolar su alcance.
No empaquetar el candidato b2c8 ni presentar el rechazo como fallo de DayZ.

## Hipótesis y anclas

[HIPÓTESIS] Una parte de los valores Geometry pierde un bit al restar el centro
del modelo en float32 y sumar después la traslación WRP. El control nuevo no
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
