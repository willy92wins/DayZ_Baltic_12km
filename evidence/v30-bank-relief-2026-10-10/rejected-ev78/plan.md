# EV78 — taludes ribereños y crestas facetadas

Petición viva10-10: avanzar mapa y suavizar las elevaciones de borde de río que parecen pirámides. Traza P12/P14 y BALTIC-007; plano aprobado plans/v30-rumbo-agua-1.0, pasos4/7. Alcance de esta unidad: suavizar el relieve SECO ribereño que admite movimiento sin cambiar geometría mojada. No afirmar corrección de finales, calado, lámina gris ni toda la base.

## Descubrimiento y mecanismo leído

`tools/terrain/smooth_dry_relief_v30.py:smooth` deja fija la banda36m del agua. EV25 `author_hinges.py:prepare` deja fijas todas las esquinas de celdas P. EV70/71 libera esquinas totalmente secas pero solo a36m de los objetivos bajos y sin bajar alturas (`author.py:minimum=original`). Estas políticas conservan crestas secas fuera de esa selección; no son prohibiciones universales de producto. Luna localiza los pliegues actuales antes de atribuir una captura a una coordenada.

## Candidato único acotado

- Fuente EV71/72 b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36. Campos P/F768e8e58/f446a216 exactos. Metadata completa exacta. Capa delta reversible; no sobrescribir base.
- Dominio ribereño: vértices secos a≤96m de clases3/5/6. Mantener protecciones heredadas EV71 (`other_fixed`, grandeslagos), más soporte de triángulos realmente mojados frente P,F y mar máximo0.85; y halo3x3 de reserva/plataforma para conservar caras que las tocan. Borde66m, costa/playa y cuerpos protegidos intactos. Narva solo donde el dominio heredado permite: no liberar protecciones por comodidad.
- Optimizar saltos de gradiente entre los triángulos NW-SE reales mediante K/build_groups ya verificados en EV25, regularización1/16. Permitir bajar crestas y subir depresiones hasta2m, presupuesto ya usado por ese método. Transición quintic0→1 en18m desde el dominio fijo. Nunca bajar de min(altura fuente,1.8). La lámina y las caras mojadas quedan exactas: calado/corredores conservados por construcción y comprobados por consumidor.
- Restricción de cada cara durante actualización: pendiente≤max(35°,pendiente fuente). Salida float32 se juzga con consumidor histórico1e-4°; no cambiar tolerancia después del resultado.
- Un cálculo,60barridos o600s, sin ajuste de parámetros. Una corrección mecánica permitida si el consumidor identifica una incompatibilidad concreta de precisión/conservación; conservar el rechazo. No barrido de variantes.

## Consumidor y aceptación

Luna calcula normales desde productos vectoriales de triángulos, independiente del objetivo K. Recorrido completo del mapa: datos finitos, metadata/P/F exactos; soporte mojado, ingeniería+halo, protecciones y fuera dominio idénticos; cota seca no baja bajo su mínimo; desplazamiento≤cap local y2m; ninguna nueva cara sobre max(35°,fuente)+1e-4°. Consumidor de carreteras actual.

Exigir reducción de energía angular de aristas incidentes≥5%, p99 y cantidad>30 no peores en banco e interior; CERO aristas nuevas>30° desde≤30° (tolerancia angular1e-4). Registrar todos los sectores y cualquier regresión local, aunque global pase. Máximo de los sectores modificados no debe subir más de1e-4°. Para afirmar eliminadas pirámides, además exige descenso cuantificado de los máximos localizados y comparación visual válida posterior; no basta energía global.

Positivos: plano inclinado sin pliegue, pliegue conocido y fuente sin cambios. Negativos en consumidor real: alterar vértice mojado, ingeniería, suelo mínimo y pico seco. No PASS por contar checks o porque candidato coincida con su propia transformación.

Solo tras consumidor PASS, revisar exposición de objetos compilados, generar paquete aislado desde EV72, decodificar WRP y comprobar PBO real; son gates distintos de motor. No regenerar satélites si el consumidor demuestra exactas sus entradas semánticas; si pendiente afecta paleta/textura, regenerarlas y verificarlas. Vista de motor pendiente si no carga; censo de alturas se puede ejecutar solo en servidor. Sin push, ni promociónEV68, ni aceptación base1.0.
