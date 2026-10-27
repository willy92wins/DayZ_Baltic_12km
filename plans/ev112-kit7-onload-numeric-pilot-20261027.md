# Kit7: piloto aislado del flag numérico al cargar navegación

Estado: PLAN_REVISADO_SOUND_WITH_FIXES. Fable5.1 revisó el plan; Codex integra
los ajustes verificados. Código nuevo aún pendiente de revisión. Codex ejecutor/integrador por el encargo
autónomo vigente. Esta fase continúa el pendiente de RAM; no es el council
ampliado y no cambia decisiones de producto ni tolerancias.

## Evidencia y pregunta

[EXACT] La sonda nativa 2e1e9c77-222e-438c-955e-55b2f0ec0371 leyó nueve
campos sobre Nav8 intacto. Los dos flags Baltic escritos como "true" devuelven
0 con ConfigGetInt y ConfigGetFloat. Chernarus devuelve1 en ambos flags.
Controles de anchura8/50, textos y campo ausente pasan. La cadena "12:00"
también devuelve0, sin conversión de prefijo observada. Cierre oficial,
observador, identidad y118paquetesvanilla verificados (vanilla-packages.json,
frozen.json y identity-verification.json de la carpeta siguiente). Evidencia privada:
E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-native-config-types-20261027.

No hubo líneas de conversión/Navmesh en el RPT; el script log contiene cuatro
avisos de archivos de zonas ausentes antes de los marcadores y ninguno entre
ellos. Esto NO demuestra ausencia universal de avisos ni conversión del
cargador nativo. No se conoce su implementación. RAM no se midió en esa sonda.

[HIPÓTESIS] La representación numérica del flag de carga puede modificar el
filtrado en memoria y su coste. El objetivo es probar una variante con datos
idénticos, no asumir que la conversión script explica el exceso de RAM.

## Cambio único e invariantes

[DESIGN] Crear un mod experimental nuevo, @DayZ_Baltic_EV112_Kit7Nav8Load1,
sin sobrescribir Nav8. Único cambio de configuración:
CfgWorlds/BalticTrial/Navmesh/filterIsolatedIslandsOnLoad, "true" -> número1.
GenParams.filterIsolatedIslands sigue siendo la cadena "true"; tileWidth8
permanece. No invocar NavMeshGenerator, Binarize ni AddonBuilder.

Baseline worldSHA ac088ccbaff34ef7a5cbfe03b6e016fb6941895b9b253786f99b57578cf6d4ff.
NM 360a7348b86bb9560352f2aead028fb6ec801f8d3bdd30526f43e0cb7e9efb23.
WRP 0da63d3f258923e784a62bcb59bb1d7f2ab99866816f530bfe73cd4211b23254.
Piloto3d9550bf… y agua97edcafe… idénticos y hashes completos en manifiesto.

[EXACT] Patrón existente de extracción/empaquetado:
tools/playtest/attach_navmesh.py:20 read_pbo;
tools/navigation/package_nav8_config_ev112.py:22-36 tokenización y delta;
:63-74 CfgConvert decode/compile/decode; :79-93 FileBank y comparación de
entradas. Son anclas para una herramienta nueva; el helper de tileWidth NO
sirve sin adaptar su contrato. No se reejecutarán scripts antiguos consumidos.

[DESIGN] Verificar fuente decodificada exacta, una declaración del flag en la
clase esperada y delta de tokens independiente tras roundtrip. Controles
negativos: segundo flag cambiado, ancho cambiado, otra clase, declaración
repetida, baseline/WRP/NM equivocados y entrada extra. Tras FileBank, conjunto
de entradas y propiedades idénticos, bytes de todas las entradas salvo
config.bin idénticos. Releer el config realmente empaquetado. No basta comparar
la transformación con ella misma; fixture literal y flags no objetivo como
invariantes. Oráculo: diff posicional de tokens original/roundtrip, exactamente
un token distinto, antes "true" y después1, situado en la declaración del
OnLoad dentro de BalticTrial/Navmesh y fuera de GenParams. Duplicarlo dentro
de GenParams también debe fallar. Fixture positivo literal del config Nav8
decodificado con SHA; rechazar bin candidato sin prefijo\0raP o idéntico al
original. Control nulo decode/compile/decode sin cambio: tokens y binarios
idénticos al original; si no lo son, detener y replantear la interferencia del
compilador. Guardar todos los originales para rollback por selección de mod.

## Oráculos y secuencia

1. Revisión independiente del plan y después del código de empaquetado/sonda.
   Hasta dos rondas de corrección de instrumentación; congelar fuentes.
2. Confirmar en motor OnLoad tipo0 observado en el control numérico del mismo
   motor, texto"1", int1/float1; GenParams
   permanece texto"true"/0. Mantener los nueve controles y UUID nuevo.
   Puede compartir run con el consumidor607 únicamente con registros
   separados y sin modificar sus consultas, coordenadas ni oráculos físicos.
3. Repetir las607 consultas congeladas sobre la variante. Exigir todo PASS,
   alturas<=0,801, continuidad<=0,011 y distancia<=2,1. Si falla cualquier
   consulta, rechazar la variante y no ejecutar RAM. Conservar todos los datos.
4. Si pasa, bloque NUEVO de seis mediciones variante/Chernarus ABBAAB,
   mismos consumidores revisados,30s de calentamiento+120s de medida.
   Las seis identidades son nuevas; no reutilizar un PASS histórico.
   Congelar también read_server_baseline_ev112.py antes de la primera pasada.
   Chernarus carga solo el bridge; Baltic carga bridge y sus3PBO. Este es el
   patrón medido previo: no añadir el mod Baltic a las pasadas Chernarus.
   Config de servidor y misión normalizada comunes, paquetes constantes por mundo.
   Residente y privada<=1,10; dispersión<=5%; CPU descriptiva.
   El comparador actual es tools/performance/compare_server_baseline_ev112.py:
   compare:17-46 y conditions_identity:49-69. Sin modificar sus umbrales.

El A/B de RAM compara la variante contra Chernarus, el referente de aceptación.
La comparación con Nav8 histórico puede describirse, pero NO prueba causalidad
del flag: la carga ajena del host no está aislada entre bloques. No hace falta
afirmar una causa raíz para validar o rechazar el candidato contra los oráculos.
Un experimento causal adicional sería otra fase revisada, no una reinterpretación
de estas seis pasadas.

El filtrado puede afectar regiones fuera de607. Aunque ambos gates pasen,
esta fase solo concede candidato local funcional/RAM, nunca aceptación global
de navegación ni sustitución automática de la variante distribuida. Antes de
promoción global, ampliar testigos de navegación de tierra e islas; actores,
barcos, cliente/FPS/capacidad y revisión visual siguen abiertos. No inventar
cobertura global con un número de tests.

## Presupuesto y parada

Una variante sin generación; un intento nativo de configuración+607 y un
bloque de seis pasadas RAM si procede. Arranque300s, captura607hasta900s,
observador1200s; para RAM conservar presupuestos del corredor validado y
congelarlos antes de la primera pasada. Nada de repetir resultados favorables.
Una pasada inválida detiene el bloque; diagnosticar y replantear antes de otro.
Un agregado INCONCLUSIVE, incluida dispersión o exceso pareado, tampoco acepta
ni autoriza repetir el bloque. Guardarlo y replantear. Un RAM FAIL rechaza la
variante aunque607pase; no implica por sí mismo que el flag no tenga efecto.

FIFO directo on_busy=queue/wait_for_box_s=600/takeover=false, sin prelease ni
sondeo de ocupación. Adoptar exclusivamente run propio; heartbeat, identidad
PID/creación, observador, cierre oficial y liberación en finally. Respetar
procesos ajenos. Verificar hashes antes/después; hashes pesados fuera de medida.

Si falla RAM o funcionalidad, conservar Nav8 y el rechazo, cerrar esta variante
y replantear con evidencia; no probar otro valor o ancho en bucle. Si pasa,
publicar fuente y evidencia con alcance local explícito y plan de cobertura
pendiente. Ningún resultado de esta fase cierra por sí solo EV112 ni inicia
prematuramente el council ampliado.
