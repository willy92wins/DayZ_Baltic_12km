# Terreno e hidrografía antes del mapeado

Petición viva30-09, P10: edificios, vegetación colocada, vías físicas y decoración
al final. P1–P4/P8/P9 siguen vigentes. Los tres puentes del ensayo son útiles de
ingeniería para reservar un paso de agua, no una decisión de mapeado final.

## Orden de trabajo y aceptación

1. **Relieve y agua**. Conservar el encuadre aprobado, islas, costa y distribución
   del closeup de San Petersburgo. Cerrar cotas del agua y transición de cada
   sistema antes de excavar cauces regionales. P12 autoriza relieve selectivo por
   jugabilidad, incluso por encima de ×3: `plans/selective-relief.md` sustituye
   la elección binaria ×1/×3. Cotas y máscaras son diseño hasta validación; la
   base nativa 0.2 sigue conservada mientras se prepara el candidato regional.
2. **Rutas navegables**. Primero calibrar Narva local con Boat_01; después resolver
   Neva/delta, Narva regional y Luga por tramos. La reserva para barco mediano es
   un diseño (12×4m, calado1.5m, altura4.5m), no un asset probado. No declarar que
   una cadena OSM desconectada o un polígono azul sea una ruta navegable.
3. **Orillas y accesos**. Probar continuidad del agua, profundidad al mínimo,
   isla/tierra seca al máximo, entradas/salidas y pendientes. Conservar los
   triángulos que soportan los futuros cruces sin cerrar el canal con taludes.
   P11 añade conducción suave: medir cambios de pendiente, regularidad lateral
   y juntas, no únicamente la pendiente máxima. Las vías principales necesitan
   una rasante diseñada antes de las piezas. La pendiente5.052% del piloto no
   prueba por sí sola una carretera lisa ni una transición cómoda al puente.
4. **Persistencia nativa y render**. Importar, guardar, reabrir y exportar en TB;
   comparar todas las alturas y poses. Actualizar el arte del agua cuando cambie
   la orilla; la textura provisional no puede seguir pintando el cauce antiguo.
   No modificar Generate Layers mientras apunte a la carpeta del baseline.
5. **Navmesh base**. Generar sobre el WRP validado, guardar `.nm`, empaquetar y
   comprobar carga propia y caminos terrestres representativos. El `.nm` antiguo
   dentro del candidato V3 solo evita el bloqueo de arranque: no lo acredita.
6. **Congelar base técnica**. Paquete, editable y manifiesto reproducible, informe
   de gates y limitaciones. Después comienza el mapeado; otra generación y prueba
   de navegación será necesaria al introducir obstáculos/carreteras/edificios.

Prueba posterior de carretera: vehículo vanilla sin modificación de suspensión,
pasadas en ambos sentidos a velocidades baja, media y prevista para la vía,
registro de posición/velocidad/salud desde autoridad y observación de saltos,
impactos y juntas. Las velocidades se fijan por categoría de vía; no usar una
pasada lenta como aceptación de todas. No ensanchar ni pavimentar ahora por esta
prueba: conservar la prioridad de terreno/hidrografía/navmesh base.

## Hallazgos que condicionan el trabajo regional

`evidence/navigation/regional-hydrology-constraints.json` y su plano provienen
de las referencias GIS existentes; no modifican el terreno.

| Sistema | Muestras con referencia menor de24m | Implicación |
|---|---:|---|
| Narva |252/392|El piloto no valida la conexión entre golfo, embalse y Peipus.|
| Neva |172/312|Excavar fondo y resolver estrechamientos antes del paso regional.|
| Delta Neva |117/139|Proteger las islas; no aplicar un buffer uniforme a todos los brazos.|
| Luga |1570/1574|La compresión extrema exige diseñar secciones;451 muestras no caen en polígonos de agua.|

Las muestras no son porcentaje de longitud o área, ni acreditan conectividad.
El inventario DSM es superficie, no batimetría: referencias físicas Peipus1.395m,
embalse Narva1.214m, Ilmen0.878m, Ládoga0.181m; compararlas con mar medido0.5–1m
explica por qué hay que decidir niveles de ingeniería antes del drenaje. No son
cotas finales ni hay objetos de agua elevada colocados. Prohibido resolverlo
rebajando todos los lagos al mar sin una decisión material del usuario.

El inventario de Peipus contiene relaciones anidadas: Peipsi y Lämmijärv quedan
casi íntegramente dentro de Lake Peipus. Usar unión para área/hidrografía, sin
colocar superficies duplicadas por cada relación. La unión también contiene
pequeños residuos poligonales: no llamar isla real a cada componente encerrado
sin contrastar su geometría. Ningún conflicto ha sido borrado o simplificado.

## Resultado actual

Run c9dc7555 solo servidor: PASS_EMPTY_BOAT_LOCAL_OUTWARD.226 muestras
continuas,196 propulsadas,97.828m netos,salud600 y paso bajo el puente. No
se relajó el verificador; run ca8a8d0f conserva FAIL por hueco inicial2.387s.
Fuentes: evidence/navigation/route-input-server-v1 y route-input-complete-v1.
Seis controles negativos del registro pasan. Sin aceptación de tripulación,
regreso, embarcación mediana o red regional. El control inicial ya no bloquea
este ensayo local; los datos históricos siguientes explican los fallos previos.

TB: export literal tras reapertura9625ecf5 aceptado:1242 cambios exactos,
resto nativo idéntico, tres poses a9m/pond0. Paquete nativo fd2c7023 con navmesh
propia68450401 generada60025teselas. Medición base servidor completada;
consultas de navegación siguen en plans/terrain-load-performance.md.

Antecedente TB: ASC c1f23f24 importado; WRP literal321a9ccc acredita los1242 cambios
congelados y conservación exacta del resto. Tres tramos y retirada del pond
guardados02:03:27. Export objects_v1 quedó incompleto tras alturas; el editor
responde, causa sin aislar. Reabrir el editable respaldado y exportar a nombre
nuevo; comprobar todas las alturas y poses. No usar ese archivo incompleto para
navmesh o empaquetado. Estado/evidencia: evidence/navigation/README.md.

## Evidencia histórica conservada

El run8dbd91ff compiló la misión y produjo la sonda completa:172 vértices
coinciden con el ASC c1f23f24 (error máximo9.54e-8m), mar0.5–1m y tres
tableros a9m. La base antigua falla como negativo con diferencia4.65m.
Fuente: `evidence/navigation/runtime-verification.json` y log inmutable.
Los fallos anteriores del bridge y dos errores de la misión están preservados;
ya no son el bloqueo vigente. No mezclar logs de otras sesiones por fecha.

La lancha vacía conservó salud600, pero solo avanzó3.248m en180s y terminó
TIMEOUT_CONTROL_INCONCLUSIVE. No pasó bajo el puente; el gálibo queda medido
en el modelo, sin colisión/tripulante probados. Antes de otro recorrido hace
falta discriminar transmisión/control de la lancha frente a un referente
operativo; no repetir inputs idénticos ni sustituir movimiento por teletransporte.

P11: `evidence/navigation/approach-smoothness.json` mide ambos accesos a0.25m
sobre8m de ancho. Pendiente máxima4.905/5.052%, cambio entre pendientes de6m
0.732/1.021 puntos porcentuales, caída transversal máxima0.190/0.196%,
desviación de cuerda6m9.09/8.75mm y empalme al tablero0m. Son medidas del
terreno del piloto; no acreditan carretera regional ni conducción aceptada.

Extensión P11 hasta320m: `approach-outer-transition.json` encuentra variaciones
de6.274pp/6m y desviación133.8mm al este sobre terreno exterior sin preparar.
Diseñar continuidad con la futura vía, no aceptar toda la ruta por una rampa
local suave. Comparación centro/periferia en `approach-profiles.png/pdf`.

La calibración posterior en mar abierto (run759f03c7) midió marcha1=neutra1,
RPM700 y hélice0 incluso con throttle0.75, salud intacta y0.30m en85s. Conservar
INCONCLUSO. Segundo discriminador: `plans/boat-control-calibration.md`, addon
aislado que aplica entradas en OnInput conforme al contrato transport.c:251–262.
No excavar más ni modificar física de vanilla para compensar un control fallido.

Último run propio cerrado por MCP (forced_kill; métricas de salida inválidas),
lease liberado y caja libre al cierre. Refrescar estado antes del siguiente uso.

TB no confirmó Abrir en la copia `tb/narva_navigation_v3`; no hay importación
persistida. Un reset del control recuperó escritura en una ocasión, pero ni
botón ni Return confirmaron apertura. Tras refrescar ventana y usar Alt+n,
el foco tampoco cambió. No continuar una cadena de inputs sobre estado supuesto.

La copia WRP derivada conserva el baseline y está marcada como tal. No sustituye
el gate nativo. No iniciar más variantes regionales de terreno hasta calibrar
el piloto o definir un discriminador que resuelva esta incertidumbre.
