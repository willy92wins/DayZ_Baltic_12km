# Adjudicación B4A2R1 y corrección de streams

Fable5.1 nativo51.578s SOUND-with-fixes. Confirmó nombres/campos reales y fixture independiente; no existe relajación. Aplicar al nuevo recuperador antes de ejecutar: testconv1 validado con cero llamadas al runner; outputdir y receipts/conversion_2 fijados en contrato externo, marcador exclusivo antes de lanzamiento que impida relanzar con otro nombre tras un fallo. No reintento ni nueva conversión1.

El código B4A2 corregido valida *_sha del runner y presenta *_sha256 en su informe enriquecido; no confundir ambos formatos. La unidad nueva verificará además input_sha/executable contra los pins, con negativos. Un birthnull por hijo demasiado rápido es rechazo conservador conocido, no corrupción probada; no se repetirá por esa causa.

El hallazgo de ausencia de testconv1 no acusa al código viejo de incumplir una recuperación que no implementaba: es requisito del NUEVO código, aún ausente. Los39tests pertenecen al probe corregido; no se atribuyen a B4A2R1. Revisión consumida, fase REVISADO_PARA_IMPLEMENTAR_RECUPERACION_GUARDADA. Sin parser de cierre ni aceptación del mapa.
