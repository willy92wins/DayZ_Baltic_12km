## 0. Crítica del encuadre

**El encuadre mezcla coherencia de niveles, representación geométrica y apariencia. Recomiendo resolverlos en ese orden; el candidato v2 debe servir como referencia de comparación, no como compromiso de conservar sus cotas.** El producto permite rediseñar alturas, pero exige conservar agua, conexiones y navegación; además, declara expresamente que los niveles no están cerrados. (`product-spec.md:8,15,18,23`).

Hay cinco correcciones necesarias antes de elegir rumbo:

1. **El censo detecta desniveles respecto al entorno final; no demuestra una discrepancia con el terreno natural original.** Carga `heights` del candidato y compara sus bancos con tierra situada a más de 12 y hasta 36 m. No consulta una superficie anterior a excavaciones, carreteras o acondicionamientos. Sus 631 unidades son componentes conectadas por nivel redondeado al centímetro, con al menos cuatro vértices; no necesariamente 631 entidades GIS independientes. Es un buen inventario de candidatos, pero no un cálculo de cotas hidrológicas. (`tools/water/census_perched_water_v30.py:59-95,117-164,325-335`).

   Además, **aproximadamente el 94 % de los 7,0 km² señalados corresponde a los dos lagos mayores** —cálculo sobre `top` y `totals`—. La superficie afectada no expresa por sí sola la gravedad visual ni justifica bajar ambos lagos. (`evidence/v30-polish-candidate-2026-10-04/census/census.json`).

2. **H3 acredita un exceso enorme de solape, pero todavía no aísla la causa de las costuras.** La medida compara huellas completas proyectadas, sin recortarlas por terreno visible. Además, el comparador calcula el ángulo con `he[cand] - he[i]`: compara las orientaciones de **salida** de ambas piezas, aunque también obtiene sus entradas. Ese estadístico no mide correctamente la continuidad salida→entrada de una curva. (`tools/water/compare_channel_joints_v30.py:147-168,185-243`).

   La documentación contiene tanto una prueba contraria a la hipótesis del solape como una reinterpretación posterior favorable, sin experimento que separe solape y profundidad. Mantendría ambas causas como **[SUPUESTO]** hasta una comparación controlada. (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:172-194`).

3. **Todavía no se ha probado el encadenado propuesto con curvas.** El colocador filtra `turn_deg == 0`; su cabecera describe curvas, pero la implementación selecciona únicamente rectas. El piloto documenta expresamente esa sustitución. Por tanto, el resultado actual no demuestra que las piezas curvas fracasen en R2/R3. (`tools/water/fit_channel_pieces_v30.py:9-12,205-213`; `evidence/v30-vanilla-channel-pilot-2026-10-04/README.md:124-130`).

4. **Las puertas no equivalen a aceptación del producto.** El verificador excluye la zona de Narva en varios controles y solo limita a 35° los triángulos íntegramente terrestres. El candidato conserva seis incidencias de calado y 35 del comprobador de planos; algunas requieren interpretar qué agua existe realmente después de sustituir planos por piezas. Incluso el comprobador específico registra un vértice mojado sin pieza y otro con profundidad negativa respecto a su superficie visual. No procede llamarlo PASS global. (`tools/terrain/verify_terrain_v30.py:3-13,44-89`; `evidence/v30-polish-candidate-2026-10-04/README.md:47`; `evidence/v30-polish-candidate-2026-10-04/reports/channel-reaches.json`).

5. **La falsa dicotomía es “escalera o transparencia” como imposibilidad general.** Está demostrada para las variantes ensayadas, no para todas las combinaciones de lecho, materiales y geometría. La regla de planos por celda está implementada en vuestro generador; esa función, por sí sola, no demuestra una limitación universal del motor. (`tools/terrain/v30_common.py:88-104`; `evidence/v30-shore-crossing-candidate-2026-10-04/README.md:148-171`).

## 1. Agua colgada

**Recomiendo una mezcla: revisar las cotas por sistema conectado, bajar agua donde resulte compatible y remodelar localmente lecho y márgenes. Conservar diques únicamente como excepciones de diseño explícitas.**

I1 es plausible: los niveles de lago proceden de `contour-v2`, mientras el relieve admite rediseño. Pero la causa histórica “V29 contra V30” sigue siendo **[SUPUESTO]** sin comparación anterior/posterior por lago. Sí está verificado el mecanismo que conserva esas cotas y eleva márgenes. La afirmación “sube toda la tierra cercana a nivel +0,35” necesita matiz: esa rama excluye las orillas ya perfiladas, que tienen otra regla. (`tools/terrain/build_v30_water.py:44-51`; `tools/terrain/build_v30.py:432-450`).

Aplicaría este criterio:

| Situación | Decisión propuesta |
|---|---|
| Lago aislado con terraplén artificial confirmado | Bajar su nivel y reconstruir orilla y lecho conservando su identidad y contorno aceptado. |
| Lago conectado a río o canal | Resolver conjuntamente nivel del lago, entrada, salida y perfil longitudinal; nunca bajar el lago aisladamente. |
| Lago cuyo descenso rompe P9, islas o conexiones | Mantener total o parcialmente la cota y rediseñar la transición terrestre con intervención acotada. |
| Dique deliberado, funcional y visualmente aceptado | Conservarlo identificado; no perseguir un censo artificialmente igual a cero. |

La mediana del anillo sería una **señal de revisión**, no la nueva cota. Exigiría perfiles por sectores del perímetro y comprobación de salidas y pasos bajos. El estadístico actual resume medianas y no comprueba esos desagües. (`tools/water/census_perched_water_v30.py:120-164`).

Rebajar solo el terreno exterior aumentaría el desnivel relativo; rebajar solo el fondo no eliminaría el agua elevada. Al bajar agua habrá que recuperar el calado necesario donde corresponda, porque el verificador lo calcula como nivel menos terreno. (`tools/water/census_perched_water_v30.py:138-142`; `tools/terrain/verify_terrain_v30.py:45-49`).

**Priorizaría dependencias y jugabilidad antes que visibilidad:** Luga–lake_014 y sistemas conectados, grandes lagos, después masas aisladas. El nuevo canal tiene 20 m de anchura declarada, pero su calado mínimo informado es 0,35 m: eso no acredita por sí mismo P9. (`evidence/v30-polish-candidate-2026-10-04/reports/polish-report.json`; `product-spec.md:15`).

También revisaría la vecindad hidráulica: el tope actual permite que cualquier vecino mojado más bajo reduzca agua fluyente, sin comprobar en ese bucle que exista una conexión de diseño. No resolvería ese problema ajustando únicamente el parámetro de 0,25 m. (`tools/terrain/build_v30_water.py:207-235`).

## 2. Cauces y piezas

**Sí al encadenado inspirado en Chernarus; no a extender piezas por el mero hecho de que un río sea ancho.** Las reservaría para pendientes donde los planos causen discontinuidad y donde quepan una cadena coherente y sus transiciones.

Mantendría los planos en tramos suficientemente horizontales. La selección sería por necesidad longitudinal, anchura útil, curvatura y geometría del lecho, no exclusivamente por etiqueta río/arroyo.

Para resolver curvas propongo:

- Encadenar marcos de entrada y salida medidos, resolviendo posición, orientación, cota y escala conjuntamente.
- Introducir el giro dentro de piezas curvas; permitir desplazamiento lateral dentro de un corredor aprobado.
- Comprobar los bordes completos y la superficie cubierta, no solo centros y ejes.
- Admitir pequeños solapes de tolerancia; prohibir el solape sistemático de un par de faldones como solución general.

La biblioteca contiene curvas medidas cuyos ángulos efectivos no coinciden necesariamente con los nombres `10` y `30`; deben usarse sus marcos reales. Chernarus tampoco presenta solape exactamente cero: los grupos medidos tienen aproximadamente 0,33 % y 0,49 %. (`evidence/v30-vanilla-channel-pilot-2026-10-04/library.json`; `evidence/v30-polish-candidate-2026-10-04/joints/joints.json`, bloque `groups`).

**Umbral operativo propuesto: 18 m de anchura mojada mínima**, acompañado de al menos una hilera continua de vértices interiores que permita trabajar el lecho sin mover inmediatamente ambas orillas. **[SUPUESTO DE DISEÑO]** Es un filtro conservador para esta malla, no un límite demostrado del motor. Por debajo usaría planos por defecto; por encima tampoco garantizaría viabilidad.

No impondría cero solape geométrico absoluto. Propondría inicialmente **≤1 % de huella múltiple por tramo**, sin concentración de solapes visibles, y cero huecos detectados en el corredor funcional. **[SUPUESTO DE DISEÑO]** Ese 1 % es un objetivo inspirado en el referente, pendiente de validación visual.

El ensayo de lancha debe acompañarse de lectura del agua: el diagnóstico anterior documenta que una lancha atravesó un hueco porque allí el motor encontraba el mar inferior. Un recorrido exitoso aislado puede dar una falsa sensación de continuidad. (`evidence/v30-vanilla-channel-pilot-2026-10-04/README.md:80-82`).

## 3. Arroyos estrechos

**Para 1.0 elegiría agua somera continua y orilla suave, con tratamiento legible del lecho, antes que generalizar piezas solapadas.** No prometería que el tratamiento visual resuelva la transparencia.

La tercera vía de menor alcance es conservar agua real y mejorar su lectura mediante contraste moderado del fondo y transición húmeda de la orilla. El proyecto ya dispone de opciones de tono del fondo y anillo superficial, aunque la superficie nueva sigue sin verse en motor. (`evidence/v30-polish-candidate-2026-10-04/README.md:30,52-54`).

**[SUPUESTO]** Esa combinación puede hacer reconocible un arroyo somero sin profundizarlo. Requiere una comparación a altura de jugador; no debe aceptarse solo desde vista aérea. Cambiar textura tampoco elimina discontinuidades geométricas del agua.

Otras vías:

- **Ensanchamiento o remodelado local:** posible propuesta para casos críticos, sujeto a aprobación si altera el contorno protegido por P2/P12. (`product-spec.md:8,18`).
- **Malla global de 3 m:** cuadruplicaría aproximadamente el número de muestras para el mismo recorte —cálculo frente a P1—; su viabilidad en esta cadena no está verificada. La dejaría fuera. (`product-spec.md:7`).
- **Objetos de orilla o láminas específicas:** **[SUPUESTO]** pueden mejorar la silueta, pero falta demostrar concordancia visual, física y navegación. No los convertiría en dependencia de 1.0.

No eliminaría arroyos ni los sustituiría silenciosamente por texturas secas: conservar agua funcional forma parte de P2. (`product-spec.md:8`).

## 4. Rumbo fijo

Propongo **siete pasos**. Sus umbrales nuevos son propuestas de aceptación, no resultados ya obtenidos. Un FAIL vuelve al paso responsable; un resultado INCONCLUSO no permite congelarlo.

1. **Fijar el contrato y registrar v2.**  
   Ver el candidato en las cámaras previstas y definir qué tramos cumplen P9, qué embarcación es el consumidor y qué envolvente representa el margen para barcos medianos. El candidato sigue pendiente de vista y aceptación. (`HANDOFF.md:7,20`; `product-spec.md:15`).  
   **Salida:** todos los criterios con medida o cámara identificada; cero requisitos de navegación con consumidor indefinido.  
   **Congelar:** recorte, conexiones protegidas, corredores, criterios visuales y tolerancias.

2. **Resolver la red de niveles.**  
   Asociar las componentes censadas a identidades de diseño; distinguir contactos accidentales, conexiones reales y masas aisladas. Elegir cotas y transiciones conjuntamente. El constructor actual separa ciertas aguas estancadas y rebaja fluyentes por vecindad. (`tools/terrain/build_v30_water.py:207-235`).  
   **Salida:** 100 % de las componentes censadas clasificadas; todas las conexiones con niveles compatibles o transición explícita; cada dique conservado justificado.  
   **Congelar:** niveles, conexiones, desembocaduras y excepciones de relieve.

3. **Cerrar la política de representación con pruebas acotadas.**  
   Construir una cadena representativa con curvas reales y comparar dos estados del arroyo estrecho: referencia actual y surco somero con tratamiento superficial. Los ensayos anteriores no usaron curvas en el ajuste. (`tools/water/fit_channel_pieces_v30.py:205-213`).  
   **Salida:** cada representación satisface cobertura, calado, orilla y lectura visual; presupuesto de dos variantes y una ronda correctiva por representación. Si ninguna cumple, declarar incompatible el criterio concreto y elevar esa decisión, sin abrir otra serie indefinida.  
   **Congelar:** representación por tramo, límites de anchura y política de juntas.

4. **Reconstruir conjuntamente agua, lechos y orillas.**  
   Aplicar las decisiones a todo el mapa y medir por clase y por sector. El p90 global de orillas oculta diferencias: el candidato documenta 0,666 m en lagos y 3,892 m en navegables. (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:44-54`).  
   **Salida:** cero fallos no explicados en controles aplicables al agua realmente presente; incidencias localizadas, resueltas o convertidas en excepciones aprobadas. Sin pérdida de conexiones ni regresión de carreteras.  
   **Congelar:** candidato geométrico y manifiesto de sus entradas y artefactos.

5. **Aceptar visual y físicamente ese candidato.**  
   Comprobar cámaras comparables, bajamar, pleamar y margen de oleaje; recorrer conexiones navegables en ambos sentidos y verificar agua presente, profundidad y gálibo. P9/P14 exigen consumidores y observación, además de geometría. (`product-spec.md:15,20`).  
   **Salida:** todos los casos obligatorios ejecutados; cero discontinuidades funcionales y cero defectos visuales bloqueantes pendientes.  
   **Congelar:** geometría aceptada. Cualquier modificación posterior invalida las pruebas afectadas.

6. **Cerrar Terrain Builder y el paquete de distribución.**  
   Completar máscara y capas, todavía pendientes según el estado, y comprobar el resultado exportado contra la geometría aceptada. (`HANDOFF.md:13-14`).  
   **Salida:** diferencias de alturas, agua y objetos explicadas; materiales verificados; paquete identificado por hash y comprobado en motor.  
   **Congelar:** artefacto de distribución, manteniendo su trazabilidad a las fuentes.

7. **Generar navegación y cerrar base 1.0 sobre ese artefacto.**  
   Completar navmesh, grafo y pruebas físicas de IA, incluyendo orillas modificadas. El estado actual solo registra 4/12 casos físicos PASS y casos pendientes. (`HANDOFF.md:11`).  
   **Salida:** todos los casos obligatorios PASS, sin pendientes encubiertos por resultados históricos; aceptación expresa de Guillermo.  
   **Congelar:** base 1.0, hashes y evidencia. La futura colocación de objetos requerirá regenerar y validar navegación según P10. (`product-spec.md:16`).

## 5. Fuera de 1.0

Dejaría fuera:

- Refinamiento global de resolución, nuevos sistemas de agua y objetos personalizados para ocultar todas las limitaciones: viabilidad no demostrada y alcance innecesario para cerrar esta base.
- Fidelidad hidrológica absoluta: el producto permite relieve selectivo. (`product-spec.md:18`).
- Decoración, vegetación colocada, edificios, carreteras físicas y ferrocarril: están pospuestos expresamente. (`product-spec.md:16,21`).
- Afirmar capacidad para 80–100 jugadores: continúa sin verificar. (`HANDOFF.md:18`).

**No dejaría fuera** conexiones rotas, navegación sin acreditar, agua indeseada ni diques artificiales sin decisión. Son asuntos de aceptación del terreno, no decoración pendiente. (`product-spec.md:8,15,20`).

## 6. Discrepancias con el orquestador

- **I1:** acepto el mecanismo plausible, pero no doy por demostrada la causalidad histórica V29→V30.
- **I2(a):** coincido en abandonar el solape sistemático; discrepo de convertir “solo ríos anchos” en regla suficiente o considerar agotadas las curvas en arroyos.
- **I2(b):** no bajaría lagos automáticamente al entorno ni empezaría solo por los visibles. Resolvería componentes conectadas y restricciones de navegación.
- **I2(c):** congelaría primero geometría, completaría Terrain Builder y cerraría la navegación sobre el paquete final.
- **I3:** acepto el compromiso observado; rechazo presentarlo como imposibilidad general. La legibilidad del agua somera admite una prueba separada, sin garantía anticipada.

## LO_NO_VERIFICADO

- No ejecuté scripts, pruebas ni DayZ; tampoco usé red, modifiqué archivos o leí fuera del repositorio. Los resultados históricos citados proceden de sus informes.
- No comparé lago a lago V29 con una superficie V30 anterior al acondicionamiento.
- No inspeccioné visualmente las capturas ni verifiqué los binarios desplegados.
- No quedó aislada la causa de las costuras ni de las manchas oscuras.
- Los umbrales propuestos de 18 m y 1 % no son límites demostrados del motor.
- No están demostradas la mejora visual mediante materiales, las alternativas con objetos ni la viabilidad de aumentar resolución.
- No doy por acreditadas P9, navmesh o IA del candidato v2.

FIN-DICTAMEN