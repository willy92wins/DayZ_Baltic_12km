# Roadway enterrado: semántica observada en el motor

16 controles nativos completos: cuatro lechos modificados enterrados y cuatro
intactos enterrados devolvieron terreno en SurfaceRoadY3D; los ocho expuestos
devolvieron lecho. Suelo <=0.01 m, Roadway/RV expuesto <=0.03 m; controles secos
sin agua. Sin fallos ni inconclusos. Identidad de proceso, misión, ejecutable y
cuatro PBO vinculada por hash; cierre oficial y lease liberado.

Esto aporta evidencia al contrato de la siguiente sonda de 2658 posiciones.
No demuestra por sí solo las otras2642posiciones. Los 1322 casos enterrados
no estaban representados en la prueba histórica de6801puntos.

RV alcanzó terreno en los controles enterrados; Bullet BUILDING siguió viendo
el lecho bajo él. Es una observación, no aceptación Bullet: falta calibración
vanilla fresca para la sonda completa. No comparar allí Bullet con RV-terreno
como si ambos consultasen la misma superficie.

Diez pruebas del consumidor, seis controles simulados del lifecycle y revisión
Fable5.1 independiente, con correcciones documentadas en el plan. El sello de
entrada verificó los inputs antes de la cola FIFO; sin sondeo ni takeover.

El PBOexperimental ef229f32 se desplegó en un mod nuevo sólo para esta sonda;
las previews previas permanecen intactas. La geometría de reparación está
verificada offline; apariencia, resto del río, nueve regresiones, RAM y C1 siguen
abiertos. Este resultado no es SERVER_PROBE_PASS ni aceptación global.

Los scripts de source son recibos de una ejecución consumida, con rutas del
entorno original. No relanzarlos sobre sus directorios de salida existentes.
