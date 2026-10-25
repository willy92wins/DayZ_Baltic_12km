# EV112 — piloto de transición rectangular junto a Narva

Continuación de la corrección autónoma autorizada por Guillermo y de la unidad
de terreno de `ev112-shape-repair-20261025.md`. E queda publicado y congelado
durante su generación de navegación. Este piloto se guarda separado; no se
despliega ni se atribuye a su navmesh.

Descubrimiento: cinco componentes rectangulares persisten en E. La inspección
de sus stencils de segunda diferencia, con alturas protegidas exactas y delta
máximo de 0,75 m, muestra un caso linealmente factible: X2916/Z6834, caja nativa
filas906..910/columnas484..489. Los otros cuatro contienen stencils cuyo intervalo
alcanzable no llega a ±0,30 m o carecen de vértices libres. Esta conclusión se
limita al objetivo de suavizar toda su caja; no prueba imposibilidad universal.
Evidencia local: `guarded-relief-batch-e/rectangle-bounds-diagnostic.json`.

[DESIGN] Resolver un parche del caso factible con el mismo objetivo de energía
de flexión y las restricciones de prominencia, pendientes, aristas, suelo mínimo
y corona de extremos protegidos ya verificadas. Añadir restricciones lineales
de segunda diferencia centrada por eje: |h-centro - (h-vecino1+h-vecino2)/2|
≤0,2999 m en toda la caja original. Fuera de ella, no empeorar diferencias
existentes superiores a0,30 m ni introducir otras. Solo vértices libres dentro
de24 m del componente; mantener exactos E y sus cambios previos fuera del parche.
No modificar el detector ni fusionar componentes para ocultar un hallazgo.

Antes de generar, revisión Fable del plan/contrato. Después, fixture que falla
la segunda diferencia y la corrige sin mover sus fijos, más negativos de dominio.
Comprobar de forma independiente después de float32: stencils completos, formas,
prominencias y aristas; agua/islas/huella exactas, bury0, carreteras y protecciones.
Comparación explícita contra E y la base anterior para evitar regresiones.
Una mejora offline no acepta fuente compilada, motor, vista ni navegación.

Presupuesto: un candidato y una reparación motivada. Si falla, conservar E y
el discriminador; no reducir protecciones, variar umbrales o incrementar el delta.
Si pasa offline, revisión de evidencia antes de decidir su integración posterior.

Revisión Fable 5.1: SOUND-with-fixes. Resuelta la puerta omitida con un segundo
LP sobre el dominio euclídeo exacto: 94 vértices libres, corona de cuatro pozos
protegidos y todos los stencils que tocan un libre, incluidos centros fijos.
El resultado es factible (`rectangle-pilot-preflight-c/report.json`). Los límites
fuera de la caja son independientes por eje y firmados: [min(d0,-.2999),
max(d0,.2999)]; dentro son [-.2999,.2999]. Esto no permite invertir un fallo
existente a otro igual de grande. La factibilidad sigue sin probar prominencia,
pendiente ni aristas. El autor será específico del piloto; solver con argumento
opcional `curvature_bounds=None`, manteniendo intacta su ruta por defecto.
