# Adjudicación de preparación vial

75.937s, Claude Fable5.1 nativo; entrega completa, entradas intactas, sin herramientas.
Se aceptan denominador íntegro, pinlector, ausencia de puentes acotada, ancho útil
indeterminado, agregados sin mallas, trazabilidad P9 y recibos separados.

F1: los tres hashes ya existen y se verificaron; se fijan en el plan. No duplicar
un lector externo gobernado ni cambiarlo. F4: definición leída, read_pbo rechaza
compresión. Se añade contraste de tabla/bounds/trailer con otro parser existente
y SHA256 externo integral. No inventar algoritmo para trailer: wiki BI ambiguo;
eso no impide identidad byte a byte del PBO fijado ni lectura estricta de entradas.
F5 rechazado parcialmente: fixture analítico del CONSUMIDOR no necesita escritor
ODOL. Se usan objetos de datos y struct sobre bytes float32 independientes.
FTT/P: no es identidad instalada por nombre; no imponer bbox12x25 si hash cambió.
F8: decision.json citado falta en ambos checkouts, P9/README sí existen; recuperar
recibo antes de futura fase nativa. F9:11secciones enlazadas,24m² sólo contexto
no usado como guard hasta recuperar recibo. No abrir fases B/C todavía.

REVISADO_PARA_IMPLEMENTAR_A. Una revisión de código y suite antes de un catálogo;
120s/2GiB sin build, modificación del PBO, despliegue, DayZ ni lease.
