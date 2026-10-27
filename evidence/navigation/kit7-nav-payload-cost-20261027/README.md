# Censo del coste serializado de navegación

Lectura de los cuatro NM reales por SHA256. **Diagnóstico, no optimización ni
perfil de memoria del proceso.** No se ha cambiado el mapa, el NM, los PBO ni
ninguna tolerancia. No se ha iniciado DayZ en esta unidad.

|Malla|Teselas|Con cero polígonos|Con un polígono|Bytes totales|
|---|---:|---:|---:|---:|
|kit7_8m|2359296|0|1996338|1338007300|
|kit7_12m|1048576|0|782505|741138936|
|kit7_12p5m|966289|0|709675|704535052|
|chernarus_50m|94249|0|27954|640312416|

Nav8 tiene un84,62% de teselas de un polígono. No hay teselas declaradas vacías
que justifiquen una poda. La contabilidad por prefijos y resto de payload
cuadra con el tamaño de cada archivo, pero no revela las asignaciones del
heap ni predice cuánto ahorraría una variante. Los totales de polígonos y
vértices coinciden con inspectores archivados; nueve controles positivos y
negativos pasan. La primera tentativa rechazó una suposición incorrecta de
orden de coordenadas; se conserva y se sustituyó por unicidad y cobertura.

Fable confirmó el censo y señaló que otro ancho aún carece de discriminador.
Su propuesta de regla por esquinas queda sin adoptar: un éxito retrospectivo
no la haría oráculo y su fallo no demostraría que todo ancho es inviable.
Además, el censo real contiene1255/1257/1248waypoints para8/12/12,5m; varias
rutas tienen3–16puntos. No son simplemente607rutas de dos extremos.

La siguiente sonda propuesta comprueba una diferencia real de configuración:
Baltic declara dos flags como texto "true" y Chernarus como número1. Solo se
observarán sus getters nativos sobre el Nav8 intacto. Una diferencia numérica
no probará cómo consume esos campos el cargador ni que cause el excesoRAM.
El plan está revisado; implementación y prueba nativa siguen pendientes.

Nav8 conserva607PASS de altura y FAILRAM. El original12,5 conservaPASSRAM y
cuatroFAILaltura. Nav12 conserva tresFAILaltura. El council ampliado sigue
en cola; este trabajo es el diagnóstico del pendiente actual.
