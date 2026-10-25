# Continuación del mapa — 08-10

Base congelada: 71131f52e2ea48550f3d6e9d5e59fc22692c3db4. Petición viva: «Continua», tras presentar el resultado y la revisión externa pendiente.

1. Revisión cruzada de Claude, solo lectura y limitada a la lista de review-brief del commit. Ruta de suscripción nativa, default vivo, safe-mode, sin MCP, herramientas ni persistencia de sesión; fuentes incorporadas como texto numerado. Codex contrasta cada hallazgo. Una revisión y una respuesta correctiva; no aceptar por mayoría ni ampliar el alcance.
2. Inspección visual del paquete desplegado b363b79d/1d311b00 en los sectores pendientes: reserva, San Petersburgo, Luga y bajos. Capturas con cámara y jugador próximos, hora fija y lecturas de posición. No cerrar tiles por la heurística de color. Máximo una repetición por vista si la carga impide evaluarla; conservar INCONCLUSO si no discrimina.
3. Corregir hallazgos reproducibles dentro de los requisitos aprobados. La excepción de fondo de BALTIC-012 permanece pendiente: continuar no elige entre sus dos alternativas de producto. Mantener separados los prototipos no aceptados.
4. Evidencia, estado por bug, cierre ordenado de runs propios y commit local, sin push. Terrain Builder y navmesh final siguen a la aceptación de geometría.

Sonda de Claude 08-10: CLI 2.1.285, default claude-opus-5-5 firstParty, PONG, sin tools. No supone validación del commit. El usuario ha indicado continuar después de la solicitud explícita de revisión de esa lista; no se amplía la lista a logs, credenciales, vault ni otros archivos.

## Correcciones concretas descubiertas

- Calado: la propuesta anterior altera 483 vértices de reserva **vial**, ninguno de reserva natural. El generador conserva ahora la reserva vial; el solve pasa a INFEASIBLE. La propuesta anterior queda rechazada, sin despliegue. Decidir solo la excepción de 88 fondos altos ya no basta.
- Controles: el 693 era un positivo alto seco. Nuevo gate por rol, conservación de la evidencia vieja y ensayo V3 de 18 puntos con el positivo alto 2001 fijado contra las caras actuales antes del lanzamiento.
- Unión R1: hueco subcelda de 1,813 m² que escapaba al gate de vértices. Una variante y una corrección como máximo. Añadir área a pilot_00001 al mismo nivel 1,45 m, conservar terreno y posiciones físicas, compensar su centro al recompilar el WRP. Comprobar 698 caras mojadas, ODOL empaquetado y mismo observador en baseline/candidato. R1 corrigió el interior pero dejó la diagonal: corrección R2 con solape de 1 cm sobre terreno sumergido. Conservar los dos fallos previos; no mover puntos ni relajar el gate para aprobar.
- Capturas: spawn y reserva siguen sin texturas y con cielo magenta tras una repetición. Cerrar el bloque como INCONCLUSO y conservar BALTIC-019 abierto; no tocar materiales por ese único síntoma.
