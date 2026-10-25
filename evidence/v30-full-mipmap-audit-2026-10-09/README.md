# EV30 — integridad de mipmaps completa

Se consumen los PBO desplegados EV28 y EV25,2048 texturas por paquete y16384 mipmaps por paquete. Las cadenas512 a4, los formatosDXT1/DXT5, los offsetsOFFS, payloads y longitudes descomprimidas pasan. No niveles truncados/vacios ni alpha inesperada. Los582 payloads anteriores identicos reutilizan el mismo resultado por hash.

Todos los niveles mayores actuales se contrastan con ImageToPAA: diferencia maxima2/255 entre decodificadores. Doce niveles inferiores64/16/4 se extraen manteniendo sus bloquesDXT y se leen tambien con ImageToPAA; diferencias<=2/255. Truncado, offset adulterado y nivel final omitido son rechazados. Referencia vanilla con la misma cadena y formatos preservada por hash. LZO local, sin instalar dependencias ni modificar el lector.

No hay evidencia de mipmap ausente o corrupto como causa del gris intermitente: ambos paquetes pasan. Esto comprueba archivos, no streaming nativo ni residencia GPU. El informe completo comprimido conserva cada nivel y media; no constituye aceptacion estetica ni cierre019. La consulta web a la especificacion de Bohemia devolvio403; el resultado se apoya en codigo local leido, archivos vanilla y consumidor nativo, no en esa pagina inaccesible.
