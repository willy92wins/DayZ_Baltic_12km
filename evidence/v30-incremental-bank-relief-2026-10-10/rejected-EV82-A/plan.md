# EV82 — preservar el terreno vigente al suavizar

EV81 queda rechazado y no se vuelve a variar. El consumidor aisló un error de referencia: sus límites contra EV79 permitían perder seis aristas ya corregidas por EV80. Este plan cambia ese mecanismo, no las tolerancias. Petición viva: seguir autónomamente corrigiendo los taludes y toda la base; raíces numéricas, agua, reservas y resto de contrato continúan.

Separar tres papeles explícitos:
- EV79: metadatos, selector original de4329 nodos, protecciones y presupuesto TOTAL altura±2m. Hash dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c.
- EV80 desplegado: alturas iniciales y referencia de todas las pendientes, bisagras, p99 y límites por sector. Hash0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b. Ninguna mejora ya aceptada se usa como presupuesto para empeorar.
- EV82: solo alturas propuestas; P/F y metadatos exactos, fuera de selector y fixed exactos respecto a ambas referencias.

[DESIGN] Reutilizar solve_node de EV81, añadiendo referencia angular separada y conservando los validadores float32 0/1/2ULP. El intervalo inferior debe incluir EV79altura−2−alturaactual, no un −2m acumulativo; superior EV79altura+2−alturaactual. Piso original EV79. Normales/pendientes/umbrales para p99/nuevo>30/sectores se leen únicamente de EV80. Orden estable,4329 nodos a lo sumo una vez, máximo180s, abortar sin salida si no completo. Registrar alturas antes/EV79/EV80/propuesta/fallback por nodo. No ejecutar antes de review root del diff.

Fixtures nuevas necesarias antes de autoría: presupuesto ya agotado en+2m no puede crecer; altura original−2m no puede bajar; referencia angular EV80 más restrictiva que EV79 rechaza una propuesta que el modo antiguo permitiría; identidad como opción válida; fallbackreal/no-beneficio conservan gates. Las APIs son internas leídas en EV81author.py, no nuevas llamadas de motor.

Consumidor independiente conserva toda la reconstrucción EV79 de máscaras, selector, suelo y presupuesto y añade íntegros los criterios de EV81 frente a EV80: cero nuevos>30, p99/cuentas no peores, máximos de sectores incidentes a cambios no peores, energía incidente baja>=5%, pliegues mixtos <3384. La referencia nativa desplegada se verifica por PBO/hash. Además identidad fuera del selector respecto a EV80, soporte mojado/ingeniería exactos. No confiar en los checks de autoría para aceptar geometría. El log incremental debe distinguir nodos editados en esta pasada y total acumulado respecto a EV79.

Una autoría bajo este contrato. Si falla, no combinar parcialmente ni relajar puertas; preservar EV80 y diagnóstico, sin otra autoría bajo este plan. Solo tras PASS: exposición compilada, superficie afectada/padding/solapes/mips, nuevo PBO íntegro, censo nativo completo y cierre orderly. EV81 no se incorpora. No renderclaim ni base1.0 aceptada; no push.

## Aclaración previa al cálculo

«Únicamente EV80» se refiere a los límites locales del autor. El consumidor mantiene también todos los gates finales EV79 que tenía EV81, incluida compatibilidad angular, y exige además los de EV80; no se elimina ninguna puerta tras el FAIL anterior. Añadir explícitamente pendiente nativa <=max(35°,EV80) además de la prueba heredada contra EV79. El consumidor puede ser conservador respecto al autor: un resultado que falla cualquiera se rechaza. El baseline EV80 como fixture de identidad pasa invariantes, no la puerta de mejora material, que requiere cambios.
