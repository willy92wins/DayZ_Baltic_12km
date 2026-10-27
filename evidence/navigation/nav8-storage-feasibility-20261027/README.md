# Nav8: coste serializado y límite del formato

Resultado: **INCONCLUSIVE_FORMAT_CONTRACT**. No hay candidato nuevo ni ahorro
de RAM demostrado. Nav8 conserva 607 PASS y su FAIL RAM anterior; no se reabre
el bloque Load1 interrumpido. Cero partidas, generaciones o modificaciones NM.

Se leyeron 1035 cabeceras de cuatro archivos por muestra determinista:
259 Nav8,259 Nav12,259 Nav12.5 y258 Chernarus. Hash antes/después intacto.
La comparación numérica con las estructuras upstream7 no explica el payload
DayZ12: ninguna fila cierra con la fórmula candidata de enlaces16bytes.
El u32 opaco en offset100 explica el residual en980filas. En las55restantes,
la ecuación posthoc añade8*campo13; encaja en1035/1035 pero es un ajuste sobre
la misma muestra, no una validación independiente ni un contrato de escritura.
El residual de esas55filas NO es constante: distribución en adjudication.json.

Los campos9:12 son cero en esta muestra. El censo completo previo ya acreditó
eso para8/12; no se repitió. Los ceros no excluyen datos adicionales de detalle.
No trasladar nombres, tamaños o código de Detour a un escritor VAND12.
Fuentes primarias fijadas por revisión/hash en primary-sources.json; comparación
de dtMeshHeader/dtPoly/dtLink y serialización, no compatibilidad afirmada.

Siete controles del lector PASS. La revisión independiente Fable5.1 es
SOUND-with-fixes: ajustes incorporados en adjudication.json sin alterar la
evidencia consumida. El lector comprueba únicamente los offsets adyacentes
muestreados, no toda la tabla ni topología, convexidad o consumo del motor.

H1: existe coste serializado por tesela; no demuestra causalidad de heap.
H2: reagrupar o recortar exige contrato de referencias/portales/sección extra;
esa vía queda sin autorizar. No probar otra anchura a ciegas ni repetir RAM.

Siguiente vía pendiente: atribuir los siete fallos originales/Nav12 al perfil
real empaquetado y estudiar corrección de geometría fuente bajo protecciones.
Antes de tocarla hacen falta plan, banda seca/húmeda, restricciones y revisión.
No se ejecutó esa corrección. EV112, cliente, actores, FPS y council siguen abiertos.
