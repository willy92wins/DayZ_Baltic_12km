# Council ampliado y siguiente plan de calidad

Encargo autorizado por Guillermo el 27-10-2026: terminar primero el trabajo
vigente, reunir después un council ampliado, proponer mejoras del mapa, las
herramientas de generación y validación y el resultado final; incorporar al
plan las propuestas aprobadas y ejecutarlas. Esta orden amplía la cola de
trabajo. No da por cerrado EV112 ni aprueba propuestas aún inexistentes.

## Secuencia y condición de inicio

1. Continuar el paquete vigente según HANDOFF.md y sus planes aprobados.
   Preservar los 607 PASS de Nav8 y resolver la puerta de memoria pendiente;
   mantener visibles los demás fallos, límites y comprobaciones pendientes.
   No usar el contraste con Chernarus como exención de altura ni rebajar
   tolerancias. No reiniciar coordinadores o preparadores ya consumidos.
2. Al cerrar el trabajo previo, congelar el commit, inventario de artefactos,
   validadores, resultados, limitaciones y decisiones del usuario. Registrar
   el cierre de cada pendiente; ninguno desaparece por cambiar de fase.
   Si una dependencia humana impide cerrar, conservarla como pendiente y
   avanzar solo en trabajo independiente; no fingir que se cumplió el inicio.
3. Ejecutar el council ampliado sobre esa base. Su decisión de producto es
   qué mejoras incorporar a la siguiente fase y con qué prioridades,
   manteniendo la visión del mapa y sus restricciones aprobadas.
4. Consolidar las propuestas, verificar sus fundamentos, resolver duplicados
   y contradicciones, y registrar aprobación o rechazo con motivo.
5. Añadir al plan ejecutable todas las propuestas aprobadas, ordenadas por
   dependencias; implementar, validar y corregir hasta cumplir sus criterios.
   Hacer commit y push de unidades validadas mediante el checkout público
   saneado. No publicar historial privado ni afirmar aceptación global con
   puertas abiertas.

## Composición y ejecución del council

Aplicar las skills `delegar` y `council-orchestration`. La petición actual
asigna a Codex la coordinación e integración; el asiento ChatGPT puede ser
esta sesión. No abrir subagentes Codex adicionales por rutina.

Núcleo obligatorio: Claude/Fable (sustitución de Opus ya autorizada), ChatGPT,
Grok, Muse Wonder por CLI nativo y Gemini/Argon. Sondar el día de la corrida
modelo real, esfuerzo, disponibilidad y ruta de cada miembro. No sustituir
Muse por otro modelo o relé en silencio.

Ampliación: buscar aportaciones independientes de GLM, Qwen, DeepSeek, Kimi,
Nemotron y otras familias accesibles que aporten cobertura. La lista es de
candidatos, no de participantes confirmados. Usar las rutas autorizadas y
sondas vivas de `delegar`; registrar ausencias, errores, cuotas y límites.
Un nombre comercial o una respuesta vacía no cuenta como familia participante.
No cargar ni cambiar modelos en recursos compartidos congelados.

Primera fase: COBERTURA amplia con un núcleo común de fuentes y restricciones,
y encargos por dominio declarados. Cada miembro puede cuestionar el encuadre
y proponer alternativas fuera del menú inicial. Segunda fase: contraste de
propuestas concretas con brief común congelado, diferenciando revisión ciega
de reconciliación. No comparar como equivalentes entregas con fuentes o
herramientas diferentes. Archivar inputs efectivos, hashes, modelos reales,
salida completa y cierre de cada proceso; rechazar entregas truncadas.

El arbitraje conserva la regla vigente del núcleo de cinco: mayoría 3/5 para
las decisiones que requieran votación, sin vencer evidencia re-verificada ni
ocultar DISENSO-FUERTE. Los miembros adicionales aportan cobertura; no cambian
silenciosamente el denominador. Una mayoría de opiniones no aprueba una API,
un cambio de datos ni un resultado de pruebas.

## Cobertura mínima de propuestas

| Dominio | Preguntas que deben quedar examinadas |
| --- | --- |
| Validadores | Falsos PASS/FAIL, cero cobertura, NaN/Inf, referencias independientes, negativos, límites entre muestras, cobertura espacial, severidad y trazabilidad hasta el consumidor real. |
| Relieve | Pirámides, pozos, rectángulos, escalones, cambios de pendiente, artefactos de triangulación y repetición; evaluación desde suelo y a media/alta altura; acceso y jugabilidad. |
| Ríos y costas | Codos, rectas artificiales, juntas, extremos invisibles, confluencias, islas, Narva y desembocaduras; continuidad visual, física e hidrológica, agua, lecho, navegación y puentes. |
| Bosques y biomas | Soporte continuo, árboles flotantes/hundidos, distribución, repetición, límites de la reserva, variedad, legibilidad, colisión, navegación y coste. |
| Carreteras y ferrocarril | Posición y conectividad, rasantes, peraltes, empalmes, cruces y puentes, conducción real; distinguir reservas del terreno de vías físicas y respetar las fases P10/P15. |
| Generación | Reproducibilidad, determinismo, deltas, dependencias, incrementalidad, precisión, tiempo/coste, diagnóstico de fallos, recuperación y coherencia fuente/WRP/PBO/despliegue. |
| Rendimiento | RAM y CPU de servidor, FPS/frame times/tirones y VRAM de cliente, LOD, densidad y carga de sectores; comparación equivalente con Chernarus y ensayos de jugadores/IA/loot aparte. |
| Experiencia final | Orientación, líneas de visión, accesos, diversidad de recorridos, navegación, ambientación real, Narva y San Petersburgo, identidad Este/Oeste y loot como propuesta de producto, presentación y revisión visual. |
| Pruebas integradas | Actores, vehículos y embarcaciones, colisiones, navmesh, recorridos completos, escenarios adversos, regresiones, pruebas humanas necesarias y coste de mantener cada control. |

La cobertura es un mínimo, no una lista cerrada. Se busca una exploración
amplia y útil; no afirmar que se enumeró literalmente toda mejora posible.

## Registro y aprobación de cada idea

Cada propuesta necesita ID, dominio, problema observable, fuente/evidencia,
beneficio esperado, alternativa mínima, riesgos, coste, dependencias, cambios
concretos y consumidor independiente para validarla. Separar hechos,
hipótesis y preferencias estéticas. Citar APIs reales antes de recomendar
código ejecutable. Las cifras deben declarar universo y método de medición.

Estados: PROPUESTA, INVESTIGAR, APROBADA_TECNICA, DECISION_USUARIO,
RECHAZADA, IMPLEMENTADA, VALIDADA. Conservar disensos y motivo de descarte;
no perder ideas por falta de prioridad inmediata.

Codex puede aprobar y ejecutar mejoras técnicas justificadas dentro del
alcance autorizado, con revisión independiente y evidencia. Cambios que
contradigan decisiones del picker, recorte, protecciones, producto o fases
vigentes se presentan juntos para decisión de Guillermo antes de aplicarlos.
No pedir de nuevo permiso para correcciones ya autorizadas.

Cada idea aprobada entra al plan con prioridad, archivos/componentes,
dependencias, criterios PASS/FAIL/INCONCLUSO, baseline, pruebas positivas y
negativas pertinentes, rollback y evidencia esperada. Antes del primer bucle
fijar criterio mecánico y presupuesto conforme a `gates-ledger`; no aprobar
por número de rondas, modelos o tests. Si falla, corregir la causa sin
relajar tolerancias ni retirar casos incómodos. Si no hay progreso, revisar
la hipótesis y dejar el estado real, nunca fabricar un PASS.

## Entregables

- Manifiesto de la corrida, disponibilidad y cobertura por familia y dominio.
- Informes independientes completos y registro consolidado de propuestas.
- Adjudicación trazable, desacuerdos y decisiones de producto pendientes.
- Plan actualizado con todas las ideas aprobadas y orden de implementación.
- Cambios, pruebas, regresiones, evidencia de motor/visual cuando corresponda,
  commits y publicación de las unidades validadas.

Estado inicial: EN_COLA_TRAS_TRABAJO_VIGENTE. Council no ejecutado; ninguna
idea futura se considera aprobada todavía. El seguimiento debe continuar
el trabajo previo y activar esta fase cuando se cumpla su condición de inicio.
