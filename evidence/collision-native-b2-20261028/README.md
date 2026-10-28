# B2 nativa: captura completa y diagnóstico inconcluso

La captura contiene **270 grupos / 1.080 rayos**: diez centrales originales,
ochenta offsets y tres rondas. Identidad de proceso, misión, paquetes y cierre
oficial vinculados. Run `05130b56-a47b-45d6-bcea-af3a385f0660` retirado, sin lease.
No repetir esta misión ni sus preparadores para continuar el diagnóstico.

**INCONCLUSIVE_DIAGNOSTIC**, no aceptación física del mapa. Original2658 conserva
47 puntos FAIL y 21 inciertos. Nav8 conserva su histórico607PASS; RAM, aceptación
visual, C1 y las nueve regresiones procedimentales siguen abiertas. No se cambió
geometría, vegetación, tolerancias, puntos originales ni etiquetas de producto.

## Qué se verificó

- 28 tests positivos y negativos; fuente geométrica real congelada incluida.
- Cinco revisiones independientes Fable5.1, con recibos y adjudicación en report.json.
- Ocho PBOs estáticos antes/después y puente MCP; preflight oficial antes de lanzar.
- 16.116 observaciones de pose concuerdan con el WRP bajo la convención de matriz
  declarada y el error del formato de texto. No certifica animación ni marcos internos.
- Cero discrepancias de SurfaceY frente al NPZ fijado dentro del umbral existente.
  Esa referencia no son alturas decodificadas del WRP.

## Correcciones del instrumento, con rechazos preservados

El consumidor original rechazó `bullet_layer_changed`: las270 filas emitían8 y
la hipótesis previa era2. La misión usa el mismo símbolo BUILDING para llamar y
registrar. Ahora se conserva el entero positivo estable y **siempre** se marca
su semántica como no verificada, incluso si fuese2. No se afirma cuál entero
recibió internamente Bullet. El rechazo original y sus fuentes se conservan.

El primer replay falló con KeyError height. B2A contiene1.106 registros, pero
834 son verticales/degenerados inconclusos sin altura; sólo272 tienen altura.
El consumidor corregido conserva todos, con residual nulo en los834 casos y
confusor explícito. No convierte incertidumbre en impacto ni en PASS.
El replay R1 consume exactamente el mismo log, con nuevo sello y fuentes
anteriores archivadas. El resultado completo se almacena en result.json.gz;
al descomprimir se recuperan los bytes originales cuyo SHA figura en report.json.

## Observaciones y límites

En los centrales349,350 y1425, en las tres rondas, los rayos altos devuelven el
haya y los bajos no devuelven ese árbol. Otros centrales siguen mostrando
diferencias RV/Bullet, por ejemplo723: cerca de6,0823m frente a6,9623m.
Estas observaciones separan escenarios; no autorizan podar árboles, aceptar los
centrales ni atribuir las diferencias a un margen de Bullet, al viento o al terreno.
Los resultados completos, incluidos offsets y objetos vacíos, quedan preservados.

Todos los270 grupos conservan confusor de capa y de geometría ambigua;84 además
tienen cambio de reloj entre consultas. Un cambio de reloj no demuestra movimiento.
Los objetos vacíos no prueban impacto sobre terreno; el censo estático no certifica
volumen libre nativo, animación ni objetos dinámicos.

Siguiente: revisar el contrato físico con estas observaciones y localizar un
referente independiente de agua/clases/anchuras/receptores antes de cambiar el
cauce protegido. No repetir B1, B2A, B2 o2658, ni bajar tolerancias para cerrar.
El council ampliado permanece en cola tras el trabajo previo, no realizado aquí.

## Archivos

report.json resume; centrals-all-rounds.json conserva las30 observaciones centrales;
native/ contiene captura y lifecycle; replay/ el sello y resultado R1;
replay-rejected/ el fallo previo y sus fuentes; identity-and-original-code/ el
recibo original; reviews/ las revisiones finales; validation/ los28 tests.
Los manifiestos históricos conservan rutas del host como procedencia, no son un
instalador portable. No se redistribuyen PBO/P3D ni scripts vanilla completos.
