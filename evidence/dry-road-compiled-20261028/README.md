# Piloto de lecho seco: geometría compilada y paquete experimental

Geometría compilada verificada; metadata de sombreado condicional. El ODOL351424ab
reproduce exactamente el MLODd13069d5 a la pose real del WRP: agua, UV, Memory,
normales codificadas y1520prismas con cobertura total y error de contacto0.
PBO201 ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84 compuesto cambiando sólo cs_kit_118_0000.p3d;
200modelos, config, propiedades y orden permanecen exactos.

12 contrapruebas del consumidor sobre datos ODOL/PBO reales leídos,
sin usar rechazo por hash ni escribir modelos corruptos desplegables. Incluyen
ST no local, quiralidad, normal codificada, UV, agua, tamaño serializado, metadata
desconocida, segundo modelo, config, orden y candidato equivocado.

El layout ST y la fórmula area_over_tex NO están demostrados. Se comprobó su
dependencia mediante bisección Y/N, soporte local y envolvente del control.
El resultado permite un paquete experimental; NO es aceptación visual/motor,
RAM o calidad global. No se ha desplegado. La reparación reduce el área de
lecho expuesto dentro del corredor de carretera23.9576325072→0m² offline,
conservando agua y extremos. No resuelve los demás defectos de la visita.

Revisión independiente Fable5.1 y adjudicación en el plan. Sin rebajar tolerancias.
Siguiente: preparar y revisar sonda nativa aislada con calibración y controles.
