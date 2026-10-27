**Veredicto: SOUND-with-fixes.** El uso del archivo local más los controles nativos sí cierra el discriminador que faltaba, sin decodificar ningún NM ni correr nada nuevo. Los errores son de redacción y de límites declarados, no de cálculo.

**Verificado contra fuentes hasheadas**

- El diagnóstico de rejilla archivado contiene para la malla 8m (sha 360a…) 12 teselas con `vertices` y `polygons`, producto del decodificador anterior con gate propio (magic VAND, versión 9, rejilla 1536). El script nuevo solo consume esas listas; cero decodificaciones y cero runs según completion.json.
- Las 6 XZ de native12 coinciden byte a byte con las líneas P del runtime.log de Load1, y la Roadway del motor es idéntica. La malla desplegada en Load1 es la misma 360a… según deployment-parity.json.
- Residuos reconstruidos: máximo 4.19e-7, un solo triángulo candidato por punto, así que el `max` sobre hits nunca se ejerció. No hay selección por Y objetivo.
- Errores Nav8 frente a Nav12: 0.5527→0.0292, 0.8569→0.0041, 0.5554→0.6513, 0.9231→0.1012, 0.8186→0.0208, 0.0816→0.7117. Los tres fallos Nav12 bajan; dos contraejemplos empeoran. Todos bajo 0.801. Ningún claim monótono es correcto.
- Ejecución dentro del deadline del budget reutilizado, inputs sin cambios.

**Qué cierra y qué no**

Cierra: Nav8 pasa en esos XZ a través de polígonos distintos (teselas 8m con esquinas 1.97/2.37/2.77/2.87), y su altura nativa es exactamente la interpolación plana de esos polígonos. Ambas mallas exhiben el mismo fenómeno local; la posición dentro del polígono decide PASS o FAIL. Eso queda demostrado con datos ya archivados.

No cierra: la causa en el generador, la cobertura fuera de las 12 teselas testigo, ni ninguna aceptación. El informe ya lo declara.

**Errores exactos a corregir**

1. El brief y `limits[1]` dicen "límites XY". El script acota X y Z contra la tesela; Y no se acota. Escribir XZ, coherente con el campo `xz` de las muestras.
2. `limits[2]` dice "independently captured". Precisar: capturados por el motor en la corrida Load1 cerrada, no por este script; la independencia es respecto a la reconstrucción, no entre sí.
3. La triangulación en abanico desde el vértice 0 asume polígonos convexos. No se asserta convexidad. Añadir como límite; los 6 residuos lo validan solo en esos puntos.
4. El gate de formato no se re-ejecuta; se hereda del decodificador anterior vía sha del JSON y sha 360a… registrado dentro del JSON. La publicación debe citar ese script y deployment-parity.json como el eslabón que une polígonos y corrida nativa.
5. El budget consumido pertenece a la fase vertex-surfaces. Decirlo explícitamente.

Mantener las cuatro correcciones previas tal como figuran en el brief. No hace falta parser nuevo: esta corrida no lo usa y el discriminador ya está cerrado con el archivo existente.

FIN_REVISION