# EV64 - discriminador de bandera de agua bajo puentes

FuenteA:EV61censo de servidor, agua/terreno porhash. EV58 encuentra cinco puntos mojados nominales con SurfaceIsPond=false debajo de roadway de tres instancias:16787374/375/376, modelo vanilla bridge_metal_25. Ese solapamiento es hipótesis, no explicación confirmada.

B diagnóstico reversible: omitir exactamente esos tres registrosWRP. Todas las alturas, P/F, modelos yobjetosdeagua yotros6826archivos delpaquete exactos. Sin modificar producción, sin cliente ni ComputerUse. Misión de censo completaEV61connombre/log nuevos yreferencia dePBO B. No tocar material, mar ni tiempo.

Discriminación: ambos4.194.304vértices coinciden; los cinco puntos deben estar siempre bajo el plano nominal por>=0.10m. Si desaparecen las diferencias de bandera exactamente en ellos al omitir puentes, con lasotras13diferenciasclase3 constantes, atribuir la bandera al solapamiento roadway de los puentes. Es una prueba de consumidor de la consulta, no aceptación física/IA de puentes ni cura de un hueco. No usar variaciones de puntos marinos/escalares positivos por fase de ola como efecto delpuente.

Un B, presupuesto90s tras servidor listo. Si no discrimina, INCONCLUSO, no cambiar parámetros. El mapa de trabajo permaneceEV61y sus nuevepuentes; B nunca se promociona. Cerrar servidor, liberarlease yestado libre. Conservar punto/objetos/hashesantesydespués.
