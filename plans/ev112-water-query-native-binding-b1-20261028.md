# B1: enlace nativo y ciclo de ejecución (28-10-2026)

Estado: REVISADO_POR_CODEX_PARA_IMPLEMENTAR; despliegue/admisión pendientes de revisión independiente.
Asientos vigentes: Codex ejecutor/integrador; Fable5.1 CLI revisor solo lectura.
Complementa el plan B1 ya congelado; no cambia productor, consumidor, selección ni tolerancias.

## Alcance e hipótesis
Obtener una captura B1 íntegra y atribuible al paquete experimental ya medido.
La identidad íntegra no resuelve H3 ni valida el producto. Original2658 permanece FAIL.
No nueva geometría ni calibración Bullet: B1 no ejecuta rayos. No repetir2658.
Se reutilizan exactamente producer3654693e, CSV1f75d141, sourceA14be579b y original e717a124.

## Diseño revisado
[EXACT] capture_owned_server_identity.ps1:1-45 verifica PID/creación, misión, opciones
de proceso, ejecutable, config y enumera PBO de los directorios -mod.
dayz_mcp/server.py:5482-5493 ejecuta preflight sin lease/admisión.
server.py:5868-5890 expone dayz_test_close(run_id,graceful_timeout_s) con lease.
dayz_test_request.py:254-268 exige ruta Windows absoluta canónica; no convertir a /.
ConsumerB1 separa pure consume de identidad, como explica su cabecera.

[DESIGN] Nuevo binder water_query_native_b1_ev112.py:
- gate: verificar SHA externo del accepted.json, manifiesto completo y hashes actuales,
  fuentes/copies/init/CSV/engine/4PBO; prohibir launch/result existentes.
- Identidad: run propio único entre admisión/host/MCP/cierre; server único; PID y fecha
  de creación idénticos; bridge BOUND/version ok/poll<10; ningún cliente iniciado.
- Misión/CSV y paquetes exactos por ruta normalizada, no sólo basename; engine exacto.
  Capturar host antes y después de log; config/commandline/identidad estables.
- Log dentro del perfil del propio PID, mtime >= creación, bytes copiados iguales,
  header/END345 y parser completo. CSV regenerado desde A y original antes de consumo.
- Resultado sólo después de cierre oficial confirmado, session self none, sin run propio,
  cero comandos pendientes y cleanup_degraded vacío. Si falla, conservar evidencia inválida.
- No escribir tokens/credenciales, commandline cruda ni salida completa de MCP en disco.
  Sólo recibos seleccionados; el token vive en memoria del coordinador.

[DESIGN] Preparador de una ejecución, con directorio nuevo de misión y mod:
revalidar final-offline/report.inputs, sus CSV/points; copiar tresPBO exactos del despliegue
anterior a nuevo mod exclusivo. Bridge externo cuartoPBO, engine fijado.
Crear input manifest, ejecutar tests y guardar recibos. Desplegar sólo después de
adjudicación Fable. Preflight oficial fresco y gate inmediatamente antes de FIFO.
Seal accepted incluye la aprobación, tests, manifiesto, código/helper/coordinador y preflight.
Gate revalida bytes desplegados y fuentes tanto antes como después del run.

[DESIGN] Lifecycle: dayz_test_run server/no_base_mods/no_file_patching/build=false/
navmesh_data_server=true/on_busy=queue/takeover=false, misión canónica de manifiesto.
Admisión propia seguida de acquire_wait que debe adoptar exactamente el run devuelto.
Bridge ready acotado300s; capture180s desde readiness. Heartbeat cada<=20s durante trabajo.
Captura comprueba PID/creation en cada iteración y no repite ni sustituye una captura.
finally: close propio; si stop_required, liberar y dayz_test_stop exacto. Si falla adopción,
no mutación alternativa; registrar y resolver oficialmente el run propio sin takeover.
Release y session_status terminal. Ninguna ocupación ajena se sondea antes del lanzamiento.

## Validación y presupuesto
Una unidad de implementación; tests <=120s; preparación <=120s/2GiB;
revisión independiente <=600s, corrección sólo por contraejemplo ejecutable.
FIFO <=600s total por activación, sin repetir rechazo sin cambio que lo justifique.
No mantener lease durante revisión/análisis/publicación.
Positivos: fixture analítico completo345 con recibos válidos, ruta canónica y cierre.
Negativos independientes: otro run/PID/creation, bridge stale/mismatch, cliente iniciado,
mtime vieja, logfile de otro perfil, falta/extraPBO, misión/CSV/engine/A alterados,
seal modificado, gate consumido, cierre incompleto, tokens no persistidos.
Mocks coordinador: éxito, adopción errónea, identidad cambiada, captura fallida,
close fallido y fallbackstop. Ningún mock cuenta como ejecución del motor.
Criterio integridad PASS sólo si todas las puertas anteriores; resultados diagnósticos
conservan INCONCLUSIVE/REFERENCE_MISMATCH y todas las observaciones.
Compilación motor sólo si llega log propio completo; lint1archivo no la sustituye.
Sin rechazo humano nuevo: autorizaciones y protecciones existentes permanecen.
