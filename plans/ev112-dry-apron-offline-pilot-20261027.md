# Piloto offline: alisar el delantal seco de kit-7

Estado: EJECUTADO_REJECTED_OFFLINE. Continúa P7/P10/P14 por encargo de corrección
de ríos/terreno. Codex ejecutor/integrador; revisión independiente Fable.
No empieza council ni hereda PASS nativo o de RAM.

## Evidencia y única hipótesis

[EXACT] bank-source-attribution-20261027 atribuye14waypoints (7FAIL/7PASS)
a q≈±6, todos OUTER_APRON. Residuo fuente/Roadway nativo máximo4.84e-7m.
La lámina y water_ext son distintas; los fallos están0.634–0.658m sobre Wvisual.
No están en el lecho. El terrainWRP bajo esos puntos queda1.005–1.229m.
La fuente y las copias collision-only tienenSHA9d8caf0f…, autor8b340a2a…;
PBO3d9550bf… y ODOLs locales ligados por hash. Es atribución local, no prueba
de toda la cadena de generación. Geometry se conserva separado de Roadway;
la revisión señala diferencias de hasta0.008m, no un cap uniforme.

[EXACT] continuous_stream_pilot_v31.py:300 sube el perfil exterior desde
W+.4(q4) hastaW+1.3(q18), antes de mezclarlo con el terreno y fair_support.
fair_support:68-89 acepta current,prior,free,floor,ceiling; conserva primera/
última fila/columna, L-BFGS-B≤500, cotas explícitas. VerificarSHA antes de usar.

[HIPÓTESIS] Usar como prior exterior la interpolación lineal entre los bordes
q4/q18 puede reducir la elevación artificial del delantal y su curvatura,
manteniendo interior, extremos, agua, terreno y apoyos protegidos exactos.
No se supone que la regeneración conserve polígonos o alturas Nav12.5.

## Implementación aislada autorizada si revisión favorable

Una función de piloto separada, sin modificar el autor de producción. Entrada:
bed/axis/level/station congelados, terreno soporte y máscara de protección
original construida por las mismas fuentes/cotas verificadas del autor.
Un único candidato en salida nueva; sin NMG, sin PBO/MLOD, sin despliegue.

[DESIGN] Para cada fila y cada lado, prior lineal en q entre bed[q=±4] y
bed[q=±18]. Conservar XY y todas las muestras |q|≤4, extremos/tapas y bordes.
Reutilizar fair_support con máscara4<|q|<18, excluyendo TODO punto que toque
protección (interpolación de máscara>0). Floor=terreno+.02 como el autor;
en muestras originalmente≥W+.025, mantener ademásW+.025. No elevar por
encima de bed original: ceiling=bedoriginal. Si floor>ceiling, fijar ese punto
a original y registrarlo, sin relajar cotas. Donde no sea libre, exactitud byte.
Cuantizar Y a1/512 como el autor, con redondeo dirigido al intervalo admisible.
Si no cabe un valor de rejilla, fijar original y registrar. No tocar otras arrays.

## Criterios y salida

VERDE offline (solo candidato): hashes de entradas intactos, finito, XY/agua/
eje/estación/terreno exactos, dominio y cotas satisfechas tras cuantización;
energía de curvatura geométrica no mayor que baseline sobre la misma rejilla
(fair_energy weight=0), pendiente máxima no mayor que baseline. Conservar
distribuciones/deltas completos y extremos. Si no mejora curvatura o viola
cualquier protección: REJECTED_OFFLINE, no construir. No basta con bajas Y.
Fixtures de invariantes: suelo alto protegido, intervalo sin punto cuantizado,
interior/agua exactos, NOOP sin puntos libres. Probar fallo explícito de inputs.

Consultar los14XZ con las mismas caras fuente: publicar alturas candidatas y
delta, sin llamar PASS al comparar con Ynavvieja. Ese dato NO predice una nueva
navmesh. Registrar muestras antes/después y su distancia real a lámina.
No mover consultas, reducir0.801/0.011/2.1,RAM1.10 ni dispersión5%.

Presupuesto: una revisión conjunta atribución/plan, una implementación y su
revisión, una ejecución con solver≤500iter y≤15min; máximo una corrección de
código por contraejemplo concreto. Si no converge geométricamente, conservar
REJECTED y cambiar hipótesis; no variar pesos/perfiles en barrido.
Un candidato offline favorable necesita revisión del resultado y un plan de
build/navegación607/RAMABBAAB antes de generar/desplegar. El cauce y la malla
Nav8 válidos anteriores se conservan; nada se publica como aceptado global.

## Adjudicación Fable5.1

bank-attribution-pilot-review-20261027: atribución SOUND, plan SOUND-with-fixes.
Fuente exacta del apoyo: R/river-kit7-merged-byteexact-20261026/terrain-buried.npz,
SHA815ef8b7…; coincide con el terreno del autor guardado. Probar previamente
bed≥ground+.02−1/1024 en dominio libre, permitiendo solo2e-6 de representación
float32 del soporte guardado; no cambia tolerancias de navegación. Si no cuadra,
abortar por fuente incompatible. Sacar intervalos infactibles de free antes del
solver; registrar exclusiones. Peso del solver fijo.002,500iter máximo.
Pendiente en distanciasXZ físicas, tanto transversal como longitudinal; se añade
máxima pendiente de las caras con la diagonal real. Comparar baseline y candidato
en la rejilla1/512; protecciones/cotas comprobadas DESPUÉS del redondeo.
La atribución localiza los casos, no aísla causa: PASS y FAIL comparten banda.
No aceptar sin comprobar la afirmación del revisor de que todos son vértices;
guardar pesos y posiciones, sin convertir su prosa en prueba.

Revisión de código: SOUND-with-fixes. Corrección única de la comprobación
histórica de floor: incluir desplazamientoXZ por redondeo±1/1024. Se usa cota
Lipschitz de los gradientes exactos de las caras nativas incidentes en ese cuadro,
porque solo cuatro alturas de esquina pueden omitir un valle diagonal interior.
La cota solo valida procedencia histórica; floor del solver sigue ground+.02
en el XZ guardado. Se prueban rampa, valle diagonal e identidad de input errónea.
El ejemplo aritmético del revisor tenía una suma desplazada0.02m; se adopta el
mecanismo de redondeo, no sus cifras. Wrapper externo limita wallclock a900s.

Evidencia: evidence/navigation/bank-source-rejected-apron-20261027. No relanzar scripts consumidos. Nuevo plan dry-bank-domain está revisado, pendiente de implementación.
