# Adjudicación del plan B3

Codex, ejecutor/integrador por petición viva. Fable5.1:183.437s, entradas intactas,
SOUND-with-fixes. Presupuesto: una implementación offline y una revisión de código;
sin DayZ/compilación. Plan revisado antes de implementar.

- Aceptado: medir interior tras redondear coordenadas mundiales float32, además
  del fichero local; cobertura local no acredita el motor.
- Rechazado como gate necesario el umbral sugerido de2ULP. No está derivado del
  consumidor operativo y ev112-rv-vertex-contact-20261025.md:54-57 documenta
  cuatro contactos nativos aceptados por debajo de1ULP. No es relajación de un
  gate vigente: era una nueva propuesta. Se retiene el gate nativo posterior.
- Aceptados: no utilizar verify_dry_road_mlod_ev112; explicar solapes; reportar
  ULP/error previsto sin subir1e-6; normales correctas después de cuantización.
  La reescritura de normales seleccionadas se justifica por esos nuevos XYZ.
- No certificada la equivalencia índice motor=ComponentNNNN-1: correlación no
  demuestra contrato. No incorporarla al verificador. La lista real incluye
  Component1333 que la enumeración del informe omitió.
- Mutantes: contracción y operador deformado sí. Centroide XZ de la base en
  lugar del techo no cambia nada para prismas verticales, se rechaza ese test.
- Las cifras geométricas ilustrativas de la revisión no son un oráculo:
  todas las medidas deben salir de los triángulos guardados. No aceptar su
  estimación de overlay sin ejecutar el consumidor independiente.

Original47FAIL21inciertos intactos. OFFLINE_CANDIDATE_ONLY nunca cierra mapa,
agua, RAM ni prueba nativa. B2 y research de agua no se repiten.
