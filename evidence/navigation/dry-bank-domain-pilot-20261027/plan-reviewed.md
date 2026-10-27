# Piloto de dominio seco completo, tras rechazo del delantal

Estado: REVISADO_SOUND_WITH_FIXES_PENDIENTE_IMPLEMENTACION. Codex ejecutor/integrador; revisión Fable.
Encargo vigente de corregir ríos y relieve; P7/P9/P10/P14. No abre council.

## Cambio de hipótesis y por qué

[EXACT] El piloto dry-apron-linear-pilot-20261027 terminó REJECTED_OFFLINE:
curvatura561.7330589→562.1204872, pendiente máxima de cara0.523794→0.510528;
345iteraciones, cambio máximo−0.078125m. Sus siete comparaciones descriptivas
con la navmesh vieja siguen por encima0.801; NO son una prueba de regeneración.
No se integró, no generó modelos/navmesh ni ocupó banco. No repetirlo o variar
su peso. El plano del perfil muestra dos elevaciones laterales sobre el apoyo.

[EXACT] Hallazgo posterior adicional: el piloto fijó filas primera/última, pero
omitió proteger las seis primeras/últimas estaciones de transición CAP. Repro:
comparar candidate-surfaces.npz/bed con fuente donde min(station,L-station)<6:
201Y cambiadas, mínimo−0.025390625m. Su fixed_exact solo cubría su máscara y
no demostraba preservar CAP. Mantener REJECTED, sin reparar ni relanzar ese run.
Esto debe quedar en la evidencia y en la futura discusión de falsos PASS.

[HIPÓTESIS NUEVA] La restricción técnica |q|≤4 congela también la ladera SECA
2.25<|q|≤4. Mantener esa elevación mientras se baja solo el exterior no elimina
la cresta. Alisar conjuntamente toda orilla seca puede reducirla manteniendo
exactos la lámina, water_ext, el lecho |q|≤2.25 y sus extremos. No se cambia
anchura4.5m, nivel/pendiente de agua ni profundidad; no se relajan tolerancias.
Es un cambio de dominio geométrico; no un barrido de pesos del experimento previo.

## Único candidato aislado

Partir de la fuente original9d8caf0f… (NUNCA del candidato rechazado). Mismo
solver histórico fair_support, peso.002,500iter; mismos suelo/techo y protecciones
del plan anterior, incluido cálculo conservador de incertidumbreXZ. Solo arrays.

[DESIGN] free:2.25<|q|<18, pero excluir estaciones min(s,L-s)≤6 enteras, todas
las muestras que toquen protecciones y extremos exteriores. Prior por fila
lineal desde bed[q=±2.25] a bed[q=±18]. Floor soporte+.02; si originalmente
estaba≥W+.025, mantener≥W+.025. Ceiling original; intervalos incompatibles
fijos antes de solve. Misma cuantización1/512 dirigida. XY y arrays no-bed exactos.

Puertas independientes del generador de máscara: comparar candidato vs fuente
en |q|≤2.25 y CAP(min(s,L-s)≤6), por índices derivados directamente de qs/estación;
comparar protección y bordes. Añadir mutante CAP (Y−1/512 en una fila interior
de CAP) que el checker debe REJECT, aunque el resto de la máscara diga libre;
mutante lecho, cambio de water/XY y control positivo idéntico. No comprobar la
misma máscara generada y afirmar otra protección. Mantener todos los fallos.

VERDE offline: todas esas preservaciones, cotas, identidad y finitud; energía
geométrica discreta weight0 estrictamente menor que baseline tras cuantización;
pendientes físicas máximas longitudinal/transversal/caras no mayores. No aceptar
igualdad sin cambio. 14XZ históricos conservados; alturas y diferencias contra
Ynavvieja solo descriptivas, nunca PASS. El código consumidor recibe baseline
y candidato, no un booleano del autor. Ningún archivo de mapa o fuente se edita.

## Presupuesto y salida

Una revisión de plan/código de la modificación acotada del piloto previo,
un candidato≤15min/500iter/1solver, como máximo una corrección por repro.
No variar límites/pesos/reintentar datos ni cambiar el agua si no converge.
REJECTED_OFFLINE si falla cualquier puerta; OFFLINE_CANDIDATE_ONLY si cumple.
En ambos casos conservar resultado. Solo después de evidencia y revisión,
definir plan de build con todos los LOD, pruebas de agua/colisión/forma/bosque,
navmesh12.5 nueva y607consultas completas; RAM seisABBAAB nuevas solo si pasa.
No preadquirir lease/consultar banco: FIFO directo cuando esté preparado.
0.801/0.011/2.1,RAM1.10,dispersión5%,015-45/agua/islas/reserva permanecen.

## Adjudicación de Fable5.1

dry-bank-domain-plan-review-20261027 terminó SOUND-with-fixes. Aceptar checker
de ficheros guardados baseline/candidate con identidades por dtype/shape/bytes;
no recibe free del autor. Deriva CAP≤6 de station baseline, lecho≤2.25 de qs,
bordes±18 y arrays water/axis/station/level/raw. Protección se reconstruye desde
las fuentes originales verificadas, no desde máscara emitida por el candidato.
Cada mutante CAP interior/lecho/water/XY/borde se ejecuta en CLI independiente.
El control idéntico pasa preservación pero NO acepta candidato por falta de mejora.

Publicar distribución de margen sobre Wvisual en q3 yq4. El floor.025m es
solo una restricción del ensayo; NO certifica P14, margen ante oleaje ni agua
nativa. La cifra del revisor «1.3cm» no se adopta: .025m son2.5cm y el redondeo
es dirigido hacia arriba. No cambiar ese floor tras ver el resultado.
Una pendiente excesiva en fronteraCAP implica rechazo, no ampliar el dominio.

La comprobación de procedencia del floor histórico se aplica únicamente al
dominio histórico |q|>4: el autor no imponía ground+.02 a q3/q4. En la nueva
ladera seca se aplican las cotas propuestas y se fijan los puntos infactibles,
sin atribuir un desajuste a identidad de fuente. Energía discreta por índice y
pendiente física se mantienen separadas. Este plan NO se ha implementado ni
ejecutado todavía; sus salidas deben ser nuevas y no reusar el piloto rechazado.
