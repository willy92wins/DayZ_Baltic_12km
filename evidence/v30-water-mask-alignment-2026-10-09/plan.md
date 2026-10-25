# EV23 — corregir la máscara de suelo con los planos compilados

Alcance autorizado: BALTIC-010, corrección de toda la superficie. Candidato reversible derivado de EV16; no cambia terreno, planos, objetos, materiales, satélite, niveles, caminos, plataformas ni navmesh. Se sustituye exclusivamente el peso de superficie de los píxeles efectivamente mojados: pasan a grava, cuyo character es Empty. La tierra seca conserva exactamente su máscara fuente.

La auditoría EV22 demuestra que el defecto existe antes de comprimir. El campo reconstruido desde cls/level difiere del compilado; se usa el campo congelado d59dcdb9 validado contra los modelos. No regenerar todos los colores o clases terrestres como efecto lateral.

Una construcción de las1.024 máscaras y un empaquetado con verificación de todos los bytes del archivo. Criterios de fuente: cero píxeles mojados con máscara distinta de grava; cero cambio seco; alpha conservada; identidad en solapes. Criterios compilados: cero mezcla terrestre a4m o más de la frontera mojado/seco; mezcla de frontera inventariada porque DXT puede introducirla incluso con fuente correcta, hecho ya medido en EV22. Este criterio no borra ni reclasifica el FAIL anterior.

Controles independientes: máscara adulterada en un punto mojado interior debe fallar; cuadros no planos usan muestreo triangular nativo; consumidores físicos y geometría no se vuelven a ejecutar si identidad exacta de WRP y agua demuestra su reutilización. La prueba final de motor comprobará carga y vegetación/agua en regiones afectadas sin dar por corregido BALTIC-016 por este cambio.

No finaliza TB ni congela los temas de forma pendientes. Si DXT viola el margen interior, analizar el mecanismo; no dilatar grava sobre tierra seca sin una propuesta distinta.
