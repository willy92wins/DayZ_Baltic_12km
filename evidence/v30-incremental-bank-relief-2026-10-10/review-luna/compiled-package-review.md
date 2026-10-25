# EV82-B — auditoría independiente del PBO desplegado

**PASS_EV82B_COMPILED_PACKAGE_REVIEW**. PBO real EV80 y EV82-B comparados contra sus artefactos empaquetados; 6.827 entradas, propiedades PBO y hash de agua verificados.

El PBO EV82-B cambia exactamente 92 entradas: el WRP y 91 PAA; las otras 6735 entradas permanecen byte-idénticas a EV80. Los 924 PAA generados para las 462 teselas se compararon con sus cargas desplegadas.

El WRP editable 0WZD conserva alturas exactas de las fuentes EV80/EV82-B y sus 18.033 registros de objeto serializados, cabecera, materiales y terminador son idénticos entre versiones.

Límite: el OPRW real del PBO se ancla por hash y firma, pero este auditor no decodifica los registros internos del OPRW. Tampoco carga DayZ ni prueba SurfaceY/render/mips/navegación.

La superficie se generó y verificó antes del fallo inicial de serialización del informe por clave de conteo. La reanudación omitió regenerar PNG→PAA y comprobó que los hashes PAA y decodificados no cambiaron.

Detalle máquina: `compiled-package-review.json`.
