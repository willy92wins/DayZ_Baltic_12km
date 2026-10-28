# B1: contrato de diagnóstico de consultas de agua

**Validado offline; todavía no preparado para lanzar en DayZ.**
La sonda anterior2658 conserva FAIL. Esta unidad no repara ni acepta el mapa.

Incluye un productor nuevo de servidor y un consumidor estricto para115 puntos
ya fijados:47 fallidos,21 inciertos y47 controles positivos; tres rondas previstas,
345 registros. Consulta profundidad a tres alturas y superficie con/sin fake wave,
con referencias marinas y una instantánea de objetos. No cambia terreno, modelos,
jugadores, cámaras, tolerancias físicas ni expectativas del informe original.

La revisión independiente Fable5.1 del plan duró173.110s y la de código262.578s.
Las copias de entrada revisadas se conservan por hash. La adjudicación está en el
plan. Una corrección cerró dos huecos del consumidor: instantáneas vacías sin aviso
y desplazamientos de5mm aceptados como identidad de consulta. El segundo se
reprodujo después de la revisión, por Codex; no se atribuye al revisor externo.

Validación final con Python GIS -I en el worktree indicado por report.json:

-26 tests analíticos y negativos; lint de1archivo sin errores ni avisos.
-Formato de10632 vectores de la sonda nativa anterior comprobado.
-230 coordenadas reales sobreviven al roundtrip decimal→float32 exacto.
-1725 casos de redondeo Y con NumPy independiente y tres valores float32
 adyacentes por altura de entrada; no son nuevas mediciones del motor.

Las bandas físicas permanecen: Ground0.01m y Roadway0.03m. La identidad XZ
requiere el mismo float32; Y permite sólo el error documentado de serialización
y aritmética. Las20 referencias Roadway inciertas de A siguen inciertas.
Un valor parecido a B/W/H no identifica una superficie: H3 sigue INCONCLUSO.
El referente independiente de producto también sigue pendiente.

**Pendiente antes del motor:** binder de procedencia de run/misión/CSV/engine/4PBO,
despliegue sellado, revisión del lifecycle, preflight y admisión FIFO oficial.
No usar directamente el CSV para dar por autorizada una ejecución. Los scripts
de preparación y validación de esta evidencia ya fueron consumidos.
No hay run ni lease propios activos. RAM, C1, nueve regresiones visuales y council
ampliado siguen abiertos; el piloto completo de orilla seca sigue sólo offline.
