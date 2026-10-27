# Nav8: viabilidad de reducir coste sin perder geometría

Estado: EJECUTADO_INCONCLUSIVE_FORMAT_CONTRACT. Consumidor: Codex, ejecutor e integrador del
encargo vigente; juicio independiente Fable por CLI nativo. Continúa P7/P10,
sin iniciar el council ampliado. No sustituye la aceptación de EV112.

## Hechos y pregunta

[EXACT] Nav8 conserva 607 PASS y falla su bloque RAM completo. Nav12 tiene
tres fallos de altura. El diagnóstico publicado en 486e8df demuestra localmente
interpolación de polígonos en seis puntos, sin verificar el algoritmo generador.
Nav8 mejora cuatro y empeora dos de esos puntos: no hay monotonía.
El bloque Load1 posterior quedó incompleto y no se reabre.

[EXACT] tools/navigation/inspect_navmesh_v9_ev112.py y el censo publicado
validan TESM9/VAND12, prefijos y longitudes; no validan el formato completo.
No hay teselas sin polígonos en los cuatro archivos censados. Detour upstream
usa versión7, mientras DayZ usa12. Sus definiciones sirven como comparación,
no como contrato de compatibilidad del consumidor DayZ.

[HIPÓTESIS H1] Una parte relevante del payload Nav8 corresponde a estructuras
por tesela/enlaces que podrían ser independientes de su geometría. Hay que
medir su correspondencia antes de considerar cualquier reducción.
[HIPÓTESIS H2] Reagrupar polígonos Nav8 en teselas mayores podría preservar sus
superficies, pero exige conocer referencias, vecinos, portales, BV y enlaces.
Una semejanza con Detour no autoriza escribir un NM.

## Alcance y ejecución

Una ronda de lectura local de hasta 25 minutos tras la revisión; cero partidas,
cero generaciones, cero escrituras NM/PBO/config/WRP. No ejecutar NMG ni
consultar ocupación MCP. Fuentes binarias inmutables, hashes antes/después.

1. Leer definiciones upstream primarias de dtMeshHeader/dtPoly/dtLink y del
   serializador; fijar URL/revisión/hash en evidencia. Enumerar diferencias
   conocidas con DayZ, sin trasplantar nombres a campos no verificados.
2. Muestreo determinista limitado de los cuatro archivos previamente censados:
   principio/medio/final y casos locales conocidos. Leer únicamente cabeceras
   y prefijos ya contrastados. Comparar el tamaño de la cola contra fórmulas
   candidatas upstream; no declarar semántica por mera igualdad de bytes.
3. Limitar la búsqueda adicional a documentación primaria BI y código upstream
   fijado. No analizar ejecutables propietarios. Reutilizar el censo completo
   existente de los campos9:12 en Nav8/Nav12; no repetirlo. Ampliar únicamente
   la muestra de cabeceras8:14 de los cuatro archivos, sin convertirla en censo.
4. Decidir si H1/H2 tienen anclas suficientes para un experimento siguiente,
   o descartarlas por contrato desconocido. No construir escritor ni
   cambiar parámetros en esta fase. Identificar la vía más simple verificable.

## Criterios y parada

VERDE del diagnóstico: fuentes atribuidas, muestra y fórmula reproducibles,
diferencias/contraejemplos preservados, hashes intactos, conclusión acotada.
Este VERDE no es PASS de mapa, altura, RAM ni formato completo.
Negativos cerrados: versión distinta, longitud que no cierra, campos o secciones
no explicados, referencias/portales desconocidos. Cualquiera impide autorizar
un escritor. Si una fórmula encaja, sigue siendo observación, no especificación.
Si no hay contrato suficiente: INCONCLUSIVE_FORMAT_CONTRACT y siguiente paso
solo con plan nuevo; no otra ronda de conjeturas o prueba ciega de tileWidth.
Presupuesto: una revisión del plan, una ejecución de descubrimiento25min,
una revisión de los hallazgos; ninguna ronda N+1 automática.

Se mantienen 0.801/0.011/2.1, RAM1.10 y dispersión5%. No modificar DayZ MCP,
fuentes de otras sesiones ni evidencia histórica. Publicar únicamente evidencia
y código comprobados mediante public-repo; nunca historial privado o binarios.

## Adjudicación de la revisión independiente

Fable5.1, nav8-storage-plan-review-20261027, terminó sin error y con fuentes
intactas. Se aceptan delimitación de fuentes y tabla de decisión. H2 solo evalúa
requisitos: un escritor queda fuera incluso si parece viable. No repetir el censo
9:12 ya publicado para Nav8/Nav12. No se acepta inferir que todo coste de RAM
proviene de fragmentación ni que ceros prueban por sí solos ausencia de detalle
en todo el formato. El propio censo explicita esos límites. Tampoco se acepta la
corrección del recuento: de seis comparaciones, cuatro mejoran y dos empeoran;
tres de las cuatro mejoras son los antiguos FAIL, la cuarta era PASS.

| Hallazgo | Decisión |
| --- | --- |
| No cierra alguna fórmula o faltan contratos | INCONCLUSIVE_FORMAT_CONTRACT; ningún escritor |
| Fórmula encaja pero versión/semántica DayZ siguen desconocidas | Observación local, mismo rechazo de escritor |
| Campos de detalle distintos de cero | Buscar control documentado; no asumir semántica por índice |
| Campos de detalle cero | Preservar observación; no afirmar algoritmo ni crear control inexistente |

Nav8 permanece rechazado por su RAM medida. Una conclusión negativa de esta
lectura no clausura el proyecto ni autoriza otro tileWidth a ciegas. Inicio del
presupuesto de descubrimiento: 2026-10-27T14:13Z; fin máximo14:38Z.

Resultado: evidence/navigation/nav8-storage-feasibility-20261027. Una muestra1035,7controlesPASS,0runs/0generaciones/0escriturasNM. Fable revisó y las adjudicaciones están preservadas. Sin candidato nuevo.
