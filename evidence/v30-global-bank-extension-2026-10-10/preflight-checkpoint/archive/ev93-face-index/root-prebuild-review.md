# Revisión de integración previa a build EV93

Autorizada una build readonly del índice con fuente SHA256 `d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e`. Root leyó la cadena de identidad, enumeración, escritura exclusiva, presupuesto, clasificación de caras y API de consultas. El agente independiente confirmó los 18.024 objetos y 13.128 modelos distintos: todos los modelos reales tienen cabecera ODOL55 y SHA conforme a bounds.

Hallazgo corregido antes de build: Shapely marca como inválida una cara degenerada. El builder rechazaba `is_valid` antes de clasificar su área, contradiciendo la conservación de todas las caras. Ahora conserva área0 con sentinel explícito y valida geometría positiva. Dos fixtures nuevas llaman al helper de LOD completo con collinealidad e índices duplicados; la suite del autor da10/10. Fuente/tests finales se entregaron al reviewer.

También se evitó reabrir y rehashear todos los shards por ventana: la API los verifica/carga una vez, consulta en memoria y exige reverify al cerrar el batch. El formato usa `numpy.savez` sin compresión; el presupuesto de2GiB incluye los arrays persistidos. Memoria libre antes de build:9.353.344KiB. La build no instancia el índice; se evaluará el tamaño real antes de consumirlo.

No se cambia terreno, agua, paquete ni juego. La enumeración y exposición independiente posterior aún debe aprobar la salida real; esta revisión no declara PASS del índice ni del mapa. Un resultado incompleto/error conservará su manifest y no será consumible como completo.
