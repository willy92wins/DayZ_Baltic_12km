# Carreteras B0 — geometría local medida, consumidor aún desconocido

Extraídas dos rectas instaladas (asf1_25, asf2_25) y una curva (asf1_10 100),
con todos sus LOD Visual/Roadway, caras, asignaciones de material/textura y
proyecciones completas o marcadas explícitamente como parciales. Config binaria
instalada1c7aad19 decodificada con CfgConvert fijado. PBO34c1cabe intacto.
Las caras y máscaras locales quedan privadas, fuera del repositorio público.

INCONCLUSIVE_DISCOVERY: clases de config y caras locales no prueban consumidor
WRP/RoadNetwork, pivote nativo, ancho útil, arcén transitable ni cruces/accesos.
No hay poses nuevas, pavimento colocado, puentes ni conducción probada.
El referente de agua independiente sigue pendiente; un catálogo de puentes
no sirve de oráculo de los cruces que faltan.

23tests R1PASS0.922s. PlanFable77.828s/código102.390s y revisión de corrección propia
adjudicadas. Primer intento preservado: prefijoDZ real frente a guarddz; abortó
antes de decodificar/extractar. R1 exige literal real y conserva hash del PBO.
También se corrigió el driver: run_tree lanza RuntimeError en rc2 aunque guarde
recibo; se acepta sólo INCONCLUSIVE sinerror,3modelos y recursos cumplidos.
Timeout, error, falta de reporte o retorno contradictorio siguen rechazados.
Ni datos del mapa ni tolerancias cambiaron por esta corrección del instrumento.

Límites y mediciones exactas en report.json y discovery/report.json.
No repetir extractores/revisiones/suites consumidos. Siguiente descubrimiento:
consumidor efectivo y transformaciones en WRP instalado con identidad propia;
después reservas que cubran huella y accesos completos, conservando P9/P10.
C1, RAM, las nueve regresiones y la calidad global permanecen abiertos.
