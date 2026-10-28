# Adjudicación del plan B3F

Fable5.1 nativo62.812s, SOUND-with-fixes, entrega e identidad completas,
entradas exactas, sin herramientas/escrituras externas. Revisión consumida.

F1/F2/F7/F9 aceptados: vincular targetbaseline3514 al control real, pins
externos completos de recibos/census; verificar copias antes y después del
empaquetado y exigir un único PBO de nombre conocido en Addons.
F3 aceptado: orden físico de entradas exacto, no sólo conjunto ordenado.
La guarda package_identity ya compara list(before)==list(after); no relajarla.
F4 parcialmente aceptado: guard independiente de cabecera conserva secuencia
de propiedades y rechaza duplicados/extra/mutaciones antes de colapsar a dict.
Se fija también orden exacto para esta composición (no ley universal del motor).
F5 aceptado en sustancia, no en la prohibición textual propuesta: pinear módulo
y reutilizar sólo package_identity puro; fixture contrafactual cambia constantes
históricas CANDIDATE_SHA/ANCHORS sin alterar el consumidor nuevo. NAME se mantiene
por contrato. No reejecutar CLI/compose ni inferir permiso desde import.
F6 aceptado: read_pbo compartido para cuerpos; fixtures de PBO independientes
y guard de cabecera no constituyen un segundo decodificador completo.
F8 aceptado como inventario/límite: listado/hash de archivos PboUtils antes y
después. No afirmar identidad de módulos DLL cargados por sólo ese inventario.
Cambios en inventario fallan esta ejecución; no reemplazan pin histórico del EXE.

Plan actualizado REVISADO_PARA_IMPLEMENTAR. No código, paquete ni prueba nativa
B3F autorizados sin code review/suite nuevos; presupuestos60/120/120sinampliar.
No geometría ni etiqueta ni tolerancia cambiadas. RoadB0 sigue borrador aparte.
