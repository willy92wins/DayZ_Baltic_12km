# Agua regional: corrección verificada en motor

Estado22:20: candidato53bf52b5, run6cc3ddcf-cdac-43cb-8d9a-7e2fb22e2ef2:
**PASS_SAMPLED_DRY_INTERIOR**,1299 alturas/751 puntos secos,0 inundados y0 bajo
el máximo1m; error máximo contra ASC0.000000458m. Registro y verificación:
`candidate-engine-v1.log`, `candidate-verification-v1.json`. La referencia GIS
se mantuvo congelada. No es una certificación exhaustiva de todas las orillas.

En este run se archivaron vistas0 y3; no se capturaron1/2 a tiempo. La vista0
conserva el arco blanco lejano; la reserva mantiene agua/terreno visibles.
No presentar las cuatro poses registradas como cuatro capturas revisadas.
`candidate-player-restored.jpg` confirma el retorno real al jugador después
del marcador235s. Run cerrado normalmente; sonda retirada por hash.
La navegación posterior0fc26281 fue generada sobre el WRP corregido y cargada en
cliente/servidor; baseline vigente ebc60f4f. `navmesh-runtime.md` y recibos de
empaquetado documentan6826 entradas restantes idénticas. No es release1.0.

Consultas `nav-paths-v2.log`: cuatro rutas positivas y filtro vacío negativo,
pero el gate local de0.8m entre navmesh y superficie falla a0.833077m en el acceso
oriental. Actor IA no probado; `nav-paths-v2-verification.json` conserva el FAIL.

Render alto: `visibility-runtime.json` confirma dependencia1600/6000. Los ensayos
`outside`, `nosynth`, `ocean` e `inheritance` no corrigen arco/franjas. Se retiran
las variantes; no cambiar la geometría por ese síntoma sin aislarlo. Cámara
nearplane probado por separado; resultado actualizado a continuación.

## Render verificado después de estos ensayos

`camera-depth-repeat-v1.log` y depth-repeat-0..3.jpg: mismo mapa, cámara a1300m,
clima y visión solicitada6000m. Nearplane devuelto0.07/10/0.07/10m produce
franjas sí/no/sí/no. Restaurado0.07m al terminar. Dependencia causal del ajuste
aislada; precisión de profundidad es la explicación compatible, no código del
renderer leído. No aplicar10m a cámara de jugador ni al paquete entregado.

El arco blanco con visión1600m persiste en esa cámara extrema. Ensayo separado
`playview-runtime.json`: SPB a600m/1600, panorama1300m/12000 y orilla deLádoga
con cámara a2.95m/1600 muestran continuidad sin grandes cuadros ni franjas.
El panorama muestra el borde del mundo, no prueba terreno más allá de12.288km.
La cámara de inspección superpuesta a la cabeza del jugador quedó ocluida
(playview-spb-camera-occluded.jpg), INCONCLUSA. Tras restaurar la cámara nativa,
playview-spb-player.jpg muestra la vista de suelo limpia. No contar la captura
ocluida como fallo de materiales. Perfil del usuariofc71411a no modificado.

Regresión del cruce en paqueteebc60f4f con navegación propia: PASS ida/vuelta,
354 muestras servidor,68 por dirección sobre vano, salud100 y sin nado;
`../walk/regional-verification.json`. El arco de cámara extrema no se declara
corregido en todas las distancias; las vistas normales se acreditan por separado.

## Baseline anterior — defecto medido

La auditoría del paquete5030cb74 detectó20 puntos de tierra interior inundada:
8 en San Petersburgo,3 en Sosnovy Bor,2 en Shlisselburg y7 en la cuadrícula
regional.22 puntos no superan el máximo del mar1m. Son751 puntos terrestres
conservadores dentro de1299 mediciones; no estiman el área total inundada.

Las1299 alturas del motor coinciden con el ASC actual hasta0.00500021m.
Fuente independiente: polígonos OSM y clases terrestres de WorldCover,
separación>24m de agua; humedales excluidos. Referencia congelada antes de
medir: `reference-v1.json`. Resultado: `baseline-verification-v1.json`;
registro auténtico completo: `baseline-engine-v1.log`. Seis pruebas del
verificador pasan, incluyendo datos truncados, punto ausente, registro erróneo
y un control positivo seco. FAIL del terreno no se disfraza de fallo de test.

Cuatro capturas regionales `baseline-view-0..3.jpg`, poses y clima en
`baseline-camera-v1.log`. Kotlin, Neva y reserva no muestran los grandes
rectángulos previos. En la vistaSPB a1300m aparece una región blanca distante:
resultado visual INCONCLUSO, pendiente de discriminar altura/distancia/carga.
No se deduce agua física ni causa interna a partir del color del satélite.
El encuadre de la reserva es aproximado, no un límite legal del parque.

La cámara completó la secuencia y volvió al jugador (`restored-player-view.jpg`).
Run1be877ef cerrado normalmente, ambos procesos registran terminación,
exit_metrics_valid=true. Sonda retirada por hash, lease liberado y sesión
vacía. Solo permanece desplegado el mapa5030cb74. Ver `baseline-runtime.json`.

Siguiente paso: `plans/regional-dryland-clearance.md`. Candidato separado de
la fuente y copia nativa8926 archivos verificados (`native-branch-copy.json`).
El despeje de tierra no cambia el coeficienteZ ni añade superficies de lago.
Exige importación/WRP, nueva navegación y medición real antes de aceptar.

## Importación completada; motor pendiente

La copia `tb/regional_clearance_v1/narva_trial.tv4p` se guardó, cerró y reabrió.
Exportación nativa41b32584:4.194.304 alturas coinciden con el candidato
d21cdf2c hasta2.98e-8m; cabecera y todos los materiales/índices intactos.
El gate rechazó los objetos por un deltaY de1.02mm en ambos, sin otros cambios.
Mecanismo interno no aislado. `native-candidate-v1.json` conserva ese FAIL.

`restore_clearance_object_records.py` restituye los registros completos del
baseline en otra copia,313600cb, y rechaza cambios fuera deY, Y>1.1mm o NaN.
El mismo verificador exacto pasa (`native-normalized-v1.json`). Eliminar
únicamente el estanque diagnóstico produce WRPfc068092 para compilar.
El proyecto editable aún exporta el pequeño deltaY; el build es derivado.
`build-source-parity-v1.json`: los otros6826 archivos del paquete son idénticos.

La opción CLI `--native` también se contrastó: el ASC anterior reproduce el
FAIL20/22 auténtico; usar el ASC candidato con el log anterior se rechaza por
0.9744m, sin producir informe falso de éxito. La sustitución de navegación
exige hash previo y rechaza omitirlo o usar uno incorrecto.
