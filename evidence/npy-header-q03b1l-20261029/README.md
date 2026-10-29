# Q03B1L — cabecera NPY verificada con fixtures

NPY_HEADER_FIXTURE_VERIFIED_ONLY. Dos archivos funcionales nuevos, sin abrir NPZ históricos. El inspector consume sólo MAGIC/versión/longitud/cabecera, exige NPY1.0/2.0 y comprueba16384 antes de solicitar header. Conserva descriptores completos; las fixtures cubren META35, offsets, matriz2x12 y signo de cero. member_bytes es longitud atestada por el llamador: no se mide ni lee payload.

Ejecución local Codex asignada explícitamente tras noentregas previas:187.177s dentro360s; entrega directa, sin rescatar parciales. Esto no aísla la causa de los timeouts anteriores. Delta Muse16.250s revisado. Primera revisión de código Muse90.110s no entregó dictamen; recuperación Fable74.938s SOUND-with-fixes sí entregada con identidad. Ningún consenso ficticio ni suite atribuida al revisor.

Único hallazgo: un schema con dtypeobjeto/subarray se atribuía a NPY_DTYPE antes de leer fuente. Repro separado confirmó ambos; corrección31.480s traduce sólo esa validación de expectativa a MEMBER_SCHEMA. NPY_DTYPE permanece para datos de cabecera inválidos. Extensión externa177d117f congelada antes de corrección; contrato de2afee0 y oráculo79b946 no se alteran. No se amplió la tabla histórica26 para forzar pruebas. El integrador comprobó el delta propuesto y sus tests; Fable no volvió a leer la postimagen corregida.

Validación privada final:7métodos unittest PASS, tabla cerrada26negativos y2casos schema adicionales, sin skips;0.469s/50.92MB del proceso. El tiempo interno unittest y tiempo del launcher son medidas distintas. Positivos usan bytes literales externos y lectura NumPy estándar sólo en tests; negativos comprueban códigos independientes. NumPy2.5.3 fijado. R0seis métodos verdes se conserva; no equivale a ausencia de errores.

Guardas de ZIP, snapshot de archivo/identidad, reservas globales, proxy y consumidor de escena siguen pendientes. No archivo de mapa modificado, construcción, DayZ, ni reparación humana. C1NOT_REVIEWED, nueve casos0resueltos. Esta función es una dependencia para el lector futuro; no lo sustituye.

Validación pública de los mismos bytes:7métodos PASS0.531s/53.02MB, con oráculos/contrato/extensión leídos desde la copia pública. Sin repetir autoría ni lectura histórica. Identidades observadas propias retiradas26; no operación/run/lease.
