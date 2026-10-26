# EV112 — reintento aislado de compilación kit-7

El primer intento agotó su presupuesto de 900 s; el wrapper terminó únicamente su árbol y registró timeout, fuentes intactas y ningún PBO producido. No se acepta ese intento ni se cambia su recibo.

Hechos: los registros rotaban unos 10 MB cada 17 s con mensajes por objeto; una dependencia muestreada etiquetada «non-binarized» sí tiene cabecera ODOL 54 en ambos caminos. Esa etiqueta por sí sola no demuestra una dependencia incorrecta. La ayuda del AddonBuilder instalado, guardada en `kit7-world-unit-20261026/builder-help.txt`, confirma `-binarizeFullLogs` (extended logging) y `-binarizeNoLogs` (disables extended logging).

[HIPÓTESIS] La salida extendida contribuye al tiempo excesivo. No se ha aislado todavía; una ejecución con menos mensajes no demostrará por sí sola que sea la única causa.

[EXACT] Un único reintento de 900 s, mismas fuentes/herramientas/dependencias y criterios, con `-binarizeNoLogs` y directorios nuevos `out-quiet`/`temp-quiet`. No se modifica la configuración global del compilador. El proceso, recibos, fuente de la ayuda, scripts y plan quedan ligados por hash. Se verifican todos los inputs antes/después y las 202 entradas reales del piloto. Al agotar el presupuesto se termina solamente el árbol propio y se conserva el fallo; no hay bucle automático.

El adaptador de empaquetado cambia únicamente los caminos de manifiesto, recibo y salida compilada. El runner exige igualdad textual con esas tres sustituciones respecto del empaquetador revisado. Se mantienen el readback de todos los objetos, las 201 poses exactas, controles negativos, configuración F exacta y conservación del resto del PBO. Una compilación técnica aceptada no cierra las alturas compiladas, los 3.727 apoyos de frontera, la sonda, navegación, vista ni rendimiento del candidato.
