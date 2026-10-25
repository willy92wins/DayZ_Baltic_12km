# EV30 — mipmaps de todas las teselas desplegadas

BALTIC-019/010, lectura y diagnostico sin editar texturas. La prueba cercana carga; la lejana queda limitada por bruma. Comprobar en todo el paquete que los datos usados a distancia existen, se pueden descomprimir y no apuntan a offsets incorrectos. Consumir PBO EV28, y comparar inventario EV25. No atribuir un problema de streaming a los mipmaps sin un fallo medido.

Referente operativo leido: P:/DZ/worlds/chernarusplus/data/layers/s_000_000_lco.paa y m_000_000_lca.paa; ambos tienen niveles512,256,128,64,32,16,8,4, sateliteDXT1/mascaraDXT5. TexConvert.cfg:91-122 confirma formatos y dynRange0. PAAFile del pack permite padding de datos incompletos; el consumidor exigira bytes completos y OFFS exactos antes de decodificar. LZO local ya disponible en el lector ODOL, std_m4=True, validado contra ImageToPAA. No instalar ni modificar dependencias del entorno GIS.

Una auditoria completa: 2048 texturas actuales, todas sus versiones reducidas; cache por SHA para comparar tambien EV25 sin repetir contenido identico. Cadena, formato, payload completo, offsets, longitudes descomprimidas y alpha opaca. Inventario de medias/negros, sin llamar fallo a la perdida normal de detalle por distancia. Controles negativos: truncado, offset adulterado y nivel eliminado deben rechazarse. Comparacion de decoder con el ImageToPAA actual al nivel mayor y muestras64/16/4 nativas aisladas; la diferencia observada de hasta2/255 entre decodificadores se registra. Si un consumidor discrepa, no bajar la exigencia para obtener verde.

Esta prueba solo puede descartar defectos de los archivos bajo sus controles; no demuestra que DayZ cargue cada mipmap en todas las sesiones, ni rendimiento80-100 jugadores, ni corrige halos/espuma.
