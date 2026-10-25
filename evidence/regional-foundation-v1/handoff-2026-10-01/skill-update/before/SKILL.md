---
name: dayz-terrain-workflow
description: Importar, empaquetar y diagnosticar terrenos DayZ con Terrain Builder, Buldozer y NavMeshGenerator; usar para manchas negras, agua fuera de límites, WRP o errores de carga de navmesh. No sustituye el diseño geográfico ni demuestra rendimiento multijugador.
---

# Terrenos DayZ: de la fuente al motor

Conserva el encuadre y la escala aprobados. Separa importación GIS, proyecto nativo,
WRP compilado, PBO desplegado y comportamiento en juego: cada capa puede estar
correcta mientras falla la siguiente.

## ELEGIR EL DIAGNÓSTICO

- Entorno o rutas: usa `dayz-preflight` cuando hayan cambiado. Si un helper falla
  al parsear, verifica sus dependencias directamente; no declares el entorno roto.
- Empaquetado: usa `dayz-pbo-build`. Comprueba entradas y prefijo del archivo real,
  además del código de salida. Hash del PBO desplegado antes de atribuir resultados.
- UI nativa: usa el canal de computer-use disponible, observa antes de actuar y
  respeta las autorizaciones ya dadas. Tras varios clics sin efecto, cambia el
  discriminador; no repitas solicitudes de la misma tecla indefinidamente.
  En el escritorio compartido de Guillermo, prepara primero rutas/archivos y
  agrupa la UI en bloques cortos anunciados. Termina el control al pasar a
  cálculos, generación, logs o empaquetado y avisa. No lo mantengas mientras
  esperas; si no hay una API de liberación, no afirmes que el bloqueo desapareció.
- Navegación y arranque: lee [references/navmesh-bootstrap.md](references/navmesh-bootstrap.md).
- Coste de terreno y carga: lee [references/terrain-performance.md](references/terrain-performance.md).
- Relieve regional, reservas y persistencia de la importación: lee
  [references/regional-relief.md](references/regional-relief.md).
- Render o agua: aplica los discriminadores siguientes. Los resultados del caso
  Baltic son evidencia local, no parámetros universales.

## MANCHAS NEGRAS

Compara materiales compilados y recursos que resuelve el motor. En el caso Baltic
con shader TerrainX, completar los canales de detalle vacíos Stage3–10 con las
texturas correspondientes a cada paleta resolvió el síntoma en un A/B/A/B.
Cambiar el número de materiales o probar TerrainSNX no lo había resuelto.

No rellenes etapas indiscriminadamente: verifica shader, semántica de cada canal
y referente vanilla de esa paleta. Conserva la fuente previa y observa el mismo
punto con los mismos datos antes/después. Una vista sin manchas no prueba toda
la superficie ni el correcto empaquetado de cada tile.

Al reabrir Generate Layers, comprueba el selector de exportación: en Baltic,
4 materials per cell produjo Terrain15 y máscaras _lco; 6 materials per cell
(Arma 2) produjo TerrainX y máscaras _lca, conservando la paleta de cuatro
superficies. No cambies solo el nombre del shader: el empaquetado de canales
también cambia. Verifica el material generado antes de completar sus slots.

Las paletas pueden compactarse por tesela. En la exportación Baltic SAT1M,
L00_L02 usa grava y hierba en Stage3–6: Stage5 ya no significa bosque.
Resuelve cada posición mediante las etiquetas de las variantes hermanas y
contrasta todas las rutas no vacías. Rechaza contradicciones o posiciones sin
referencia; completa solo etapas existentes. El helper del proyecto y
`tests/test_terrain_material_palettes.py` incluyen el caso que salta L01 y
controles negativos. No aplicar un relleno global Stage3–10 a cualquier tile.

## AGUA Y ORILLAS

Para cauces navegables, calado, gálibo de puentes y taludes sobre curvas, lee
[references/navigable-rivers.md](references/navigable-rivers.md). Distingue
profundidad continua de malla, hueco de colisión y recorrido real de embarcación.

Mide por separado superficie del terreno, carretera/puente, agua actual y rango
de agua. Verifica las firmas en la instalación concreta antes de escribir sondas.
No infieras la altura del lecho solo de una llamada a profundidad desde Y=0.

Clasifica las muestras contra una referencia independiente de agua/tierra.
Si elevas tierra seca, protege costa, canales e islas; guarda el cambio como una
capa local con límites, transición, máscara y manifiesto. Compara también los
vértices fuera del área para detectar modificaciones accidentales. Reabre el
proyecto y exporta para demostrar que el editor persistió el cambio.

Una sonda geométrica pasa solo si su registro nuevo prueba ejecución y final.
Si una hotkey no produce marcador, primero diagnostica el módulo/despacho. Un
addon temporal con observador automático puede evitar depender de esa hotkey;
sus scripts deben compilar y ejecutarse en el motor antes de aceptar medidas.
Retira el addon por hash cuando ya no se necesite.

No generalices un registro de coordenadas local: en Baltic 2048²/6m se verificó
X=200000+6*col, N=6*(2047-row), con interpolación triangular. Ni una lectura UI
ni esa fórmula prueban el origen/orientación de otro terreno.

Después de corregir un sector, muestrea también el resto del mapa contra una
referencia congelada antes del ensayo. En Baltic, Narva seco no implicaba SPB
seco:1299 alturas correctas coexistían con20 muestras terrestres inundadas.
Exigir profundidad positiva y bandera de agua, separar margen respecto al
máximo del mar y excluir humedales de la afirmación de tierra seca. Un muestreo
de puntos no estima el área inundada. Fuente: evidence/regional-water.

El ensayo regional posterior elevó solo tierra seca baja, protegiendo polígonos
de agua, humedales y alturas ya suficientes. La referencia de1299 puntos se
mantuvo congelada: pasó de20 inundados/22 bajo máximo a0/0 en751 secos. Cambiar
el ASC esperado no debe reclasificar puntos ni moverlos; el registro anterior
contra el ASC nuevo debe fallar. No convertir la cota local1.25m en receta global.

Valida objetos además de todas las alturas después de reconstruir en TB. En
Baltic, importar el ASC conservó la geometría prevista pero el export desplazó
dos objetos1.02mm en Y; el mecanismo interno no se aisló. Se conservaron el
export original y su FAIL, y una copia derivada restituyó registros canónicos
exactos bajo guardas de identidad, pose y delta. No relajar tolerancias ni
presentar esa copia como exportación literal. El helper concreto del proyecto
es tools/playtest/restore_clearance_object_records.py; controles negativos
rechazan desplazamiento horizontal, Y excesiva y NaN.

Para una edición local, compara el WRP nuevo con el registro de cambios congelado
y exige identidad exacta fuera de él. En Baltic,1242 vértices coincidieron con
el delta; cuatro diferencias de hasta2.98e-8m frente al ASCII ya existían en el
baseline nativo. Se conservó el FAIL inicial y se verificó esa procedencia, sin
ampliar tolerancias. Productor: tools/navigation/verify_native_height_import.py;
el baseline sin editar es el negativo que debe fallar. Esto no acepta objetos,
reapertura ni comportamiento en motor.

Que exista un WRP no demuestra que el export haya terminado. Un ensayo Baltic
quedó en24+2048²*4 bytes: cabecera y alturas válidas, sin tabla de texturas ni
objetos, mientras el editor respondía. El último mensaje de éxito pertenecía
a otro archivo. Leer el archivo completo y vincular la confirmación a su ruta;
conservar el parcial para diagnóstico y repetir desde el editable guardado.
No llamar crash ni atribuir causa interna sin evidencia. Fuente del caso:
evidence/navigation/native-objects-export-incomplete-v1.json.

## CORTES Y AZUL A DISTANCIA

Separa agua renderizada y azul pintado en el satélite. Conserva cámara/altura y
observa el mismo punto cerca, a media distancia y lejos. Una sonda SurfaceY
correcta no demuestra que el LOD visual distante respete esa geometría.

En Baltic, 612 muestras de misión coincidieron con el ASC corregido hasta4.9mm;
el ASC previo al arreglo de agua falló por0.5866m. Fijar la versión de la
referencia evita llamar regresión a un cambio deliberado. Las50 PAA y400mips
decodificaron, y la asignación nativa de tiles era correcta, pero el usuario
seguía viendo cuadros: ninguno de esos checks acredita el render.

El discriminador magenta de Baltic se ejecutó: una copia con agua pintada
magenta, WRP/navmesh/materiales intactos y headers regenerados mostró grandes
regiones magenta con cortes en vista aérea. Confirma participación del satélite,
sin identificar todavía el mecanismo de selección/UV/LOD. No elevar orillas
para compensar estos cortes. Una variante posterior de Stage0 global fue
rechazada visualmente por terreno blanco y superficie distante ausente; hubo
además un cambio de clima, así que no atribuir todo el síntoma a las UV.

Para un A/B de materiales, fija cámara y clima además de paquete. Guarda el
baseline y retira por hash las variantes rechazadas. Si se usa una sonda de
cámara automática, debe quedar acotada al mundo y cliente de ensayo, restaurar
el estado anterior y registrar poses/clima; un log no sustituye las capturas.
Evidencia: `DayZ_Baltic_12km_dev/evidence/render-distance/README.md`.

El ensayo nativo Baltic de capa12→48m conservó todas las alturas y objetos,
pero siguió mostrando cortes en tres vistas distantes con clima fijo. No
presentar48m como arreglo probado. La sonda de cámara debe registrar la pose
unos frames después de cambiarla: GetCurrentCameraPosition devolvió la pose
anterior en el mismo frame; una lectura diferida3s confirmó las cuatro poses.

La exportación posterior Baltic con satélite1m/px, capa48m, tiles512px y
solape efectivo128 eliminó los rectángulos en las tres vistas elevadas, sin
alterar alturas ni objetos. Paquete5030cb74, evidencia sat1m-*. Es una
combinación comprobada aquí, no una restricción universal del motor ni una
prueba de la causa interna. Remuestrear el satélite no añade detalle al arte.

### Cámara aérea y franjas de profundidad

Antes de deformar un lago por franjas paralelas vistas desde gran altura,
discrimina la cámara. En Baltic, misma pose1300m, visión6000m, mapa/clima/FOV
constantes: nearplane0.07→10→0.07→10m hizo aparecer/desaparecer las franjas de
Ládoga dos veces. API instalada: `scripts/3_game/entities/camera.c:35,40`,
`SetNearPlane`/`GetNearPlane`; registrar el valor devuelto, guardar y restaurar
el original. Esto prueba dependencia causal de ese ajuste en esta escena,
compatible con precisión de profundidad; no prueba implementación interna.

10m sirve aquí para inspección aérea: no aplicarlo al jugador ni meter una
sonda automática en el mod entregado. `World.SetViewDistance` es temporal;
`SetPreferredViewDistance` persiste y no es equivalente. No hay getter de
distancia expuesto en el world.c leído; no inventarlo. Verificar restauración
contra el perfil conocido del ensayo, sin afirmar conocer distancia efectiva
solo por llamar al setter. Cerca y a nivel del jugador necesitan sus propias
capturas. El arco a1600 persistió con ambos nearplanes: es un síntoma distinto,
no darlo por resuelto por el PASS de las franjas. Evidencia: proyecto Baltic,
`evidence/regional-water/depth-repeat-0..3.jpg` y registro de cámara asociado.

## LOCOMOCIÓN DEL SECTOR

Una trayectoria solicitada no prueba un cruce. En Baltic, los overrides del
HumanInputController solo en cliente causaban avance predicho que el servidor
corregía al origen. Aplicar el mismo control acotado en ambos lados produjo
un recorrido real oeste→este→oeste,359 muestras servidor, sin teletransportes,
caída ni nado. GetHealth cliente devolvía0 mientras el servidor leía100:
validar salud desde su autoridad. Desactivar overrides al terminar y retirar
el addon temporal. Esta prueba no valida entrada de teclado ni navmesh de IA.
Fuentes: `plans/narva-walk-smoke.md` y `evidence/walk/README.md` del proyecto.

## ENTREGA Y LÍMITES

Guarda el vínculo fuente → WRP exacto → navmesh → PBO desplegado, más la misión,
marcadores de motor y resultado de cierre. Un objeto oculto en Buldozer puede
seguir en el WRP: verifica el registro exportado, sin alterar a ciegas el binario.

Una exportación puede quedar truncada después de escribir las alturas. Exige
lectura hasta el final, todas las poses y registros terminales. En Baltic,
objects_v1 quedó incompleto; reabrir el editable guardado y exportar a otro
nombre produjo un WRP completo,1242 cambios congelados exactos y tres poses
persistidas. No recompilar una exportación parcial porque su cabecera parezca válida.

El build aislado puede contener junctions a DZ/bin/core. No copies o elimines
recursivamente esas raíces como si fueran datos propios del proyecto.

No declares versión jugable por abrir Buldozer: exige carga cliente/servidor y
pruebas de los recorridos requeridos. Agua regional, IA, CE y 80–100 jugadores
son gates diferentes, con hardware y escenarios definidos.

## EVIDENCIA DE ORIGEN

Caso local DayZ_Baltic_12km, DayZDiag 1.29.163709, 2026-09-29. Resolver desde el
HANDOFF vivo del proyecto, no desde una copia antigua de esta skill:

- `evidence/render-water/auto-observer/runtime-checkpoint.json`: 441 muestras;
  297 secas interiores, 44 inundadas antes y 0 después. Alcance exclusivamente local.
- `evidence/render-water/README.md`: ensayos de materiales y límites.
- `tests/navmesh/config-probe/`: sonda temprana de configuración de solo lectura.
- `evidence/navmesh/`: resultados de arranque/generación y paquetes temporales.

Esta skill nueva no figuraba en `promotions/promotion-map.json` al crearla.
Las skills ya gobernadas se editan en su repositorio fuente; no modificar sus
targets ni el caché de plugins para introducir estos aprendizajes.
