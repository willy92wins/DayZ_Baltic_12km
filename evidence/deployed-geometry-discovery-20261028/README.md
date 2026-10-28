# Procedencia e inventario de geometrÃ­a desplegada

Se han vinculado el paquete y WRP de la visita a todos sus objetos y modelos.
Las mallas no vegetales se han leÃ­do desde los PBO reales, con hashes de la
visita y lÃ­mites de recursos. Este descubrimiento no acepta ningÃºn cruce,
puente, orilla ni aspecto visual del mapa.

- Mundo: 2.578.398 objetos; 5.509 modelos, identidades fuente/compilado iguales.
- Puentes: 28 piezas en 4 modelos. No son 28 cruces.
- Presas: 2 instancias; piloto: 201; charcas: 10.264; familia streambed: 7.323.
- 5.443 payloads decodificados, incluidos 6 proxies; sin errores de LOD,
  Ã­ndices ni particiÃ³n de caras por secciones en el lector usado.
- Complemento explÃ­cito: 72 modelos vegetales / 2.560.580 instancias sin
  inspecciÃ³n de mallas; el nombre no prueba ausencia de Roadway.
- 717 poses de piedras difieren del editable, mÃ¡ximo 9,536743e-7 por componente.
  Se conservan las matrices compiladas reales. Las demÃ¡s poses no vegetales
  son idÃ©nticas en bits; no se rebaja una tolerancia para aceptar las piedras.

El primer filtro omitiÃ³ agua por separadores Windows: se conservÃ³ el catÃ¡logo
completo, se corrigiÃ³ la selecciÃ³n y se aÃ±adieron 30 fixtures de normalizaciÃ³n.
La hipÃ³tesis posterior de igualdad binaria de todas las poses fallÃ³ antes de
leer mallas. El discriminador localizÃ³ las diferencias; no se ocultÃ³ ese fallo.
El censo final tardÃ³ 18,453 s en el PID126588, con picos de 278.286.336 bytes
residentes y 270.131.200 bytes de commit. Estos recursos no miden DayZ/Chernarus.

PBO raÃ­z f0e0e6b9 contiene WRP0da63d3f, origen editable b108352f. Se conserva la
limitaciÃ³n del lector OPRW heurÃ­stico, acotado por hashes e identidad completa.
Los archivos de geometrÃ­a de terceros y los NPZ de matrices quedan fuera de Git;
se publican catÃ¡logo, hashes y metadatos, no los recursos originales.

Pendiente: fijar marcos de proxies, superponer caras reales a todo el grafo de
carreteras, medir huecos y desalineaciones y despuÃ©s revisar la reparaciÃ³n.
C1 sigue sin revisiÃ³n humana. RAM, aceptaciÃ³n visual y calidad global abiertas.

Plan siguiente revisado por Fable5.1 (247,797 s, SOUND-with-fixes) y adjudicado
contra las fuentes. Se corrige normalización de materiales, no se inventan
MLOD originales de puentes, se separan residuo numérico y separación de juntas.
El dato de cancelación de centros del punto8 del revisor se rechazó al comparar
los valores reales; el marco de los proxies sigue condicionado a validación.
Ver plans/ev112-deployed-mesh-road-overlay-20261028.md. Su implementación aún
no se incluye en este checkpoint documental.
