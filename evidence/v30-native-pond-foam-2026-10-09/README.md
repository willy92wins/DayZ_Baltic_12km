# EV35 — control de espuma inconcluso

El cielo ya es magenta en las tres referencias intactas, ANTES de cambiar FoamColor. La atribucion inicial al parametro se rechaza al cotejar referencias. FoamColor marca las charcas; al restaurar, estas recuperan el color. Durante FoamPower0 cambian tambien cielo y carga de texturas: la referencia no es estable y no prueba un arreglo. Se detiene el experimento, se solicitan resets y se cierran cliente/servidor orderly. Perfil y PBO exactos, lease liberado. No modificacion de produccion ni nueva ronda de parametros.

La cuenta de pixeles documenta la referencia inestable; no identifica su causa interna ni acredita que FoamPower solucione nada. No hubo crash. Parametros aceptados/indices validos no son lectura del estado de dibujo. Continuar con geometria y consumidores; residual grafico sigue abierto.
