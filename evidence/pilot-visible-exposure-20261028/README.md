# Exposición geométrica de los lechos: censo continuo verificado

201modelos,185744caras de lecho y299567intersecciones con caras nativas.
El consumidor independiente verifica18métricas en TODASlas caras mediante
semiplanos GEOS, alturas fuente y corredor formado por buffers independientes.
No importa SAT ni clipping del productor. Máximo residual3.22e-12m² y9.98e-13m,
por debajo de los mismos límites aritméticos1e-7m²/1e-9m; producto sin cambios.
37fixtures fuente (12refinamiento,15integración,10incidencia exacta), cuatro
controles analíticos del consumidor y pruebas exportadas antes del commit.

La revisión detecta y reproduce dos vías de falso resultado: restar float32 antes
de promover, y clasificar como agua contactos que sólo comparten borde/punto.
SATentero y fallback racional conservan área pequeña verdadera sin descartarla
por tolerancia. La pertenencia exacta se conserva incluso si los vértices float
colapsan. El consumidor GEOS verifica primero las huellas originales.
Se eliminaron75falsos contactos en34modelos, sin alterar alturas (byteexactas).
Los fallos y experimentos pareados permanecen en la evidencia; r1 no se acepta.

Kit118:13.478894m² de cuerpo y10.477772m² de CAPestán sobre el terreno fuente
dentro de rectángulos del corredor±4m, y no bajo agua Visual del piloto. Sólo
un modelo del conjunto presenta ese solape. Los discos de junta/extremo se
separan: inscrito, circunscrito y anillo incierto; no se declara libre el anillo.
La anchura es reserva de control, no pavimento medido ni comprobación de conducción.

El área sobre terreno NO es toda defectuosa: incluye lecho bajo agua y orillas
diseñadas. Campo agua nominal difiere de lámina Visual; ambos se conservan.
“Bajo agua” no significa invisible. Máximos B-H tampoco son desplazamientos de
generación ni identifican automáticamente las capturas de Guillermo.
Uniones/componentes son por modelo; áreas por cara pueden contar capas.
La diferencia de winding fuente/ODOL permanece documentada en Visual201.

Producciónr2:210.282s/401MB. Consumidor154s/392MB. Preflight y rondas consumidos.
Reproducir sólo en output NUEVO con PythonGIS -I; entrada root/worktree explícita.
Matrices/carpetas externas, mallas y NPZ grandes quedan por hash; no se publican
recursos de terceros ni historial privado.

Siguiente: medir también extensión lateral y altura relativa al agua de sección,
atribuir áreas a las restricciones efectivamente aprobadas, comparar candidato
seco1e85 sólo en139kit7 y planificar reparación de todos los casos equivalentes.
No materializar automáticamente una candidata que no cubre kit118/65.
Mapa sin cambios; nueve regresiones, C1sinrevisar, RAM y calidad global abiertas.
