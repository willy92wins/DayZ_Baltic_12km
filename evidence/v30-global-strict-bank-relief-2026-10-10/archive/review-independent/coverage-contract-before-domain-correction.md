# EV87 — propuesta explícita para la precisión de cobertura

Estado: DESIGN revisado por water_evidence_review, SOUND condicionado a las
definiciones que se concretan abajo (10-10). Autorizada implementación de un
consumidor complementario, no el despliegue. No modifica terreno, P/F, modelos
ni tolerancias del informe crudo.

## Problema verificado

El consumidor EV87 acumula área entre dos líneas de orilla obtenidas al comparar
campos float64 con cotas compiladas de componentes float32. B ya excede el límite
absoluto agregado de 0,002 m²: 0,00654876 físico / 0,00582631 visible. El candidato
añade 0,00028357 / 0,00021819 m². No se usa este resultado para elegir tolerancia.
Las diferencias de coordenadas centradas no explican tres muestras; el orden
aritmético del render sigue sin conocerse.

## Referente anterior e independiente del candidato

- `v30-frozen-water-stitch-20261009/verify_compiled_global.py:99-100,143-146`:
  geometría física/visible y campo visible con error <2e-5 m.
- `v30-frozen-water-stitch-20261009/verify_retained_visual.py:58`:
  campo de piezas conservadas con error <2e-5 m.
- `v30-native-terminal-finish-20261009/audit_candidate_coverage.py:46,69-85`:
  asignación nominal de planos con error <1e-5 m y cobertura de huella sobre
  región mojada <1e-7 m². No compara solo vértices.

## Cambio propuesto

Aplicar ese contrato de representación existente al nuevo ámbito completo de
EV87. Es una sustitución explícita de cuatro gates de exposición absoluta del
piloto, no un PASS retroactivo del informe rechazado.

1. Mantener íntegro el informe de exposición cruda B/H, con sus FAIL y hashes.
2. Auditar las huellas ODOL físicas y visibles sobre toda región mojada diseñada
   B/H de las 41.008 celdas/frontera; falta de huella total <1e-7 m². Los agujeros
   de malla no quedan eximidos por una banda vertical, aunque sean someros.
3. Contrastar cotas de las caras compiladas que soportan esa cobertura contra
   P/F por triángulo nativo: plano físico <1e-5 m y campo visible <2e-5 m.
   Comparar en los vértices de las intersecciones de polígonos; las diferencias
   son afines allí. No extrapolar una cara por toda la celda.
4. Toda diferencia de exposición respecto al diseño debe quedar dentro de la
   banda vertical correspondiente alrededor de P/F. Fuera de ella, conservar
   el límite de 0,002 m². No sustituirlo por un límite ajustado al área observada.
5. Conservar los gates existentes de cero nuevas caras secas expuestas, cero
   ganancia sin diseño P/F, signos/componentes, desplazamientos <=1 m y todos los
   gates de terreno. Sin nuevas excepciones para protecciones o agua ausente.

## Definiciones de aplicación

- La huella de soporte es la proyección XZ de la cara ODOL sin recortarla por
  altura del terreno. Debe cubrir el diseño mojado nominal; un hueco de malla
  falla incluso si coincide con la banda de precisión vertical.
- Cortar cada cara ODOL por celda y por cada triángulo nativo NW-SE. Evaluar
  ambas funciones afines en todos los vértices del polígono resultante. Nunca
  asignar caras por centroide ni extrapolarlas fuera de su proyección.
- Solo caras físicas con plano de la celda P a <1e-5 m cuentan para su cobertura.
  Solo partes visibles que coincidan con F a <2e-5 m cuentan para su cobertura.
  Una cara de otra cota no puede cubrir un déficit del plano correcto. La
  existencia de una cara correcta no exime otra cara expuesta por encima del
  campo más esa tolerancia: registrar y rechazar ese caso en dominio conocido.
- Para F, validar cada triángulo únicamente si sus tres muestras son finitas.
  En otro caso es desconocido, nunca rellenado con P ni tratado como seco.
  Informar número/área; exigir que sus tres alturas B/H sean exactamente iguales,
  con todos los objetos y P/F congelados por hash. Si cambian: INCONCLUSIVE.
- Banda de precisión: puntos cuyo valor afín terreno-campo está entre -epsilon
  y +epsilon, con epsilon=1e-5 para P y 2e-5 para F. No es una expansión horizontal
  arbitraria. El déficit de exposición B/H y el crecimiento fuera de diseño H
  que queda fuera de esa banda deben conservar máximo por celda y total <=.002.
- Conservar fuera de esta sustitución todas las puertas de signos, cruces,
  componentes, nuevas caras secas y ganancias sin diseño. El informe nuevo
  consume el SHA del reporte corregido y exige que sus únicos FAIL sean los
  cuatro gates de exposición que esta propuesta sustituye explícitamente.
- La aceptación se escribe en otro archivo y usa otro nombre de estado;
  enlaza la política y el FAIL crudo. No se sobrescriben los resultados previos.

No inferir continuidad o altura del mar desde este modelo. El límite anterior
fija precisión de aceptación, no demuestra aritmética interna del motor.

## Pruebas y parada

Fixtures separadas: hueco de huella de 0,01 m² incluso dentro de la banda;
desplazamiento vertical que excede el límite; fuga fuera del diseño/banda;
plano de otra altura que no puede suplir la cobertura esperada; caso correcto
de residuo de representación sin agujero de huella. Umbrales fijos antes del run.
Una implementación, una revisión y una ejecución global sobre el candidato
congelado. Si falla, conservar FAIL y localizarlo; no ensanchar la banda.

Si pasa, el estado nuevo debe nombrar este contrato y enlazar el informe crudo.
No prueba aritmética interna, LOD, render, oleaje, ausencia global de artefactos
gráficos ni aceptación artística. El paquete sigue siendo un candidato aislado.
