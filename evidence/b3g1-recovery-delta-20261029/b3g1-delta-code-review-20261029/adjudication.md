# B3G1 delta — adjudicación de código

Fable5.1 nativo56.625s, SOUND-with-fixes, completo, entradas intactas; sin tools
ni denials/escrituras externas. No ejecución nativa autorizada por esta revisión.
F1 UTC aware y offsetcero exigidos, naive/nonUTC rechazados con ValueError.
F2 ventana ligada a run_id/PID del host; no emparejar reloj ajeno.
F3 positivos/delegación y seis negativos nuevos cubren todas las guardas.
F4 claves faltantes se rechazan explícitamente en el delta. Las guardas antiguas
conservan sus excepciones; no se reescriben funciones selladas.
F5 definidos script_log_checked_utc dentro ready..start y pinSHA256. Esto NO
prueba por sí solo lectura fresca: coordinador/consumidor nuevos aún deben leer,
fijar contenido y comprobar error exacto/pid/mtime antes de invocar identity.
MisiónR0/R1: comparación simbólica de nueve campos y prefijo/sufijo exactos.
Rawlaunch no mutado y númeroexacto600 sólo en copia; fixture no prueba Enforce.

Correcciones locales con repro; suite final pendiente. No segundo juicio sobre
las partes intactas. Preparador/coordinador y su revisión siguen pendientes.

Corrección tras repro final: instant real water_query_native_b1_ev112.py:25-28 YA rechaza timezone naive con naive_time. La premisa del revisor era falsa en ese punto; no hubo falso PASS naive. El wrapper ahora traduce ese ValueError a clock_not_utc para diagnóstico uniforme, y conserva guarda nueva de offsetUTCcero. Primer suite47casos:46OK/1FAIL por mensaje esperado,2.984s; preservado. Suite final nueva sobre esta postimagen justificada por ese repro;120s/2GiB sin aumento.
