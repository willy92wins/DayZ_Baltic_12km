# B3B: rechazo binario conservado, sin despliegue

El candidato B3B **no pasa** la igualdad exacta de caras en float32 mundial.
El replay R1 devuelve `REJECTED_BINARY`, `compiled_face_counter:component1335`.
Cuatro caras difieren en una coordenada Y por un paso float32 mundial:
**4.76837158203125e-7 m**. El máximo error bidireccional antes del redondeo
mundial en ese componente es2.421152116249788e-7m; son medidas distintas.
No se redujo ninguna tolerancia ni se omitió el requisito de igualdad exacta.
No se ejecutaron las puertas posteriores al primer fallo: no afirmar que los
contactos del candidato ni el overlay binario hayan pasado.

El control recién compilado conserva la identidad semántica del histórico3514,
aunque su hash binario es0fcc; también reproduce exactamente las caras del
MLODd130 bajo la poseWRP. Sus1520componentes dan error de vértice0. Ambos
controles700dry/723wet permanecen en borde/fuera del interior estricto, margen0.
Eso caracteriza el control y no autoriza cambiar sus coordenadas o etiquetas.

La pareja compiló en5.422s/4.047s y con picos menores de252MB. CandidatoODOL:
`b2c8bd4b45b56d139e0f97e14220aef6ed31e965eddc6fdbc040990f05eb5d62`.
No se compuso el paquete201, no hubo DayZ, lease ni despliegue.

## Fiabilidad del instrumento

Se conservan el primer consumidor y su excepción de interfaz: entregaba str a
read_pbo, que exige Path. R1 sólo corrige esa llamada; usa exactamente la misma
pareja y añade los hashes de sus cuatro archivos. No se recompiló. El contrato
original45d6bd48 se conserva y R1 es5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244.
Fable5.1 revisó plan265.485s, código396.844s y corrección/replay133.969s; recibos,
identidad, informes independientes y adjudicaciones se incluyen.34tests pasan.

Además, se corrigió un falso negativo del comparador: un campo añadido con
valorNone se confundía con la ausencia de la clave. Ahora se rechaza como
metadato desconocido; hay regresión primitiva y sobre el consumidor de pareja.
Las pruebas recorren también Visual/Memory/Roadway/UV/agua, datos fuera del
dominio permitido, winding, control, caras, contactos, poses y orden del PBO.
El preflight fresco pasó con una copia archivada que sólo corrige un literal
inválido de la herramienta; la skill instalada no se editó.

## Continuación y límites

B3B, R1, preparadores, compilación y revisiones quedan CONSUMIDOS. No reejecutar.
Siguiente borrador: plans/ev112-prism-b3-quantization-discovery-20261028.md,
censo completo de cuantización sólo lectura antes de otra autoría/compilación.
La discrepancia sugiere una hipótesis numérica, todavía sin causa global probada.
Los47FAIL/21inciertos originales, agua independiente, RAM, nueve regresiones
visuales, C1 sin revisar y aceptación global siguen abiertos. Nav8 conserva sólo
sus607PASS históricos. El council ampliado sigue en cola tras el trabajo previo.

Los binarios permanecen en el área local de build y están sellados por hashes;
este checkpoint público incluye código y evidencia, no los activos vanilla.
