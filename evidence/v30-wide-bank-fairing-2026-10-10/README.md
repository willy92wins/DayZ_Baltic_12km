# Suavizado de orillas — estado tras EV92

EV92 pasa las 27 comprobaciones offline del piloto: 42 alturas, quiebro focal 30°→12,997°, energía de curvatura −39,47%, sin nuevos hoyos o plataformas planas y con el collar idéntico. El candidato no está empaquetado; B sigue referencia operativa. BASE1.0 no aceptada.

El [checkpoint EV90–92](checkpoint-ev90-92/README.md) conserva las dos candidaturas rechazadas y la única salida EV92 aprobada offline, con hashes de archivos grandes externos. El índice y la cola global EV93 están en preparación. La prueba gráfica sigue pendiente del escritorio visible tras desktop_all_black; agua dinámica y rectángulos siguen abiertos.

## EV88-Q histórico (rechazado)

# EV88-Q — piloto ancho rechazado, sin despliegue

Una única resolución BVLS produjo96 alturas sobre EV82-B. El foco pasa de
3.7361 a1.8115m; energía de diferencias segundas−83.65%, máximo quiebro focal
30→6.91grados. Son medidas offline, no aceptación del mapa.

El consumidor completo rechazó Q: cotas/cruces excedidos por redondeo float32,
una nueva ventana casi plana, tres extremos pequeños sin pareja, condición
por fila/columna incumplida y limitaciones de representación física heredadas.
P/F/metadatos/protecciones se conservan y no se encontraron huecos nuevos de
cobertura nominal. Dos errores del oráculo (orientación del cruce y rampa
confundida con foso) fueron corregidos después, con fixtures; el FAIL original
se conserva y no es dictamen definitivo de esas dos puertas. No otro full.

La interpolación analítica B→Q no ofrece una variante aceptable bajo todas las
heurísticas: para mejorar el foco25% hace faltaalpha≥0.23117; la condición
de prominencia en cada fila solo permitealpha0. En el límite focal, la diferencia
que bloquea una fila es6.75mm. Esto justifica revisar el método, no aceptar Q.

El plan `archive/next-method-plan.md` propone EV90 con conservación física,
cotas float32 hacia dentro antes del solve y controles de forma sobre todo el
parche. Es propuesta previa a nueva autoría, pendiente de revisión y preflight;
no se extiende al mapa ni se construye candidato por este documento.

Q SHA cce4cd0c2f71355c6d8a110804b52570644e496055ada9ef17d07b4cb60c455c.
Referencia operativa EV82-B. EV87-S es otra preview aislada con margen dinámico
abierto. Base1.0 sigue NO ACEPTADA; imágenes `profiles-mesh.png` son malla offline.
Los archivos grandes quedan externos y fijados por el manifest.
