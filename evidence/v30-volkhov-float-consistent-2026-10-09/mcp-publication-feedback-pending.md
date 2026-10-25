# Incidencia de entorno pendiente de enviar

No es un ticket enviado. `pipeline_feedback` no está publicado en este chat.

Título: DayZ MCP conectado en la UI de Codex sin herramientas disponibles en el chat tras reconexión.

Observación: inicialmente ambas conexiones `dayz-mcp` y `dayz-mcp-130` devolvían Transport closed en session_status. La recuperación pública server_reload devolvió el mismo error. El usuario aclaró que había reiniciado el servidor externo; después reabrió la conexión cliente en Codex. Desde entonces ALL_TOOLS no incluye ninguna herramienta dayz_mcp. Intentar session_status por el nombre anterior devuelve TypeError, herramienta no disponible. El usuario confirma que la UI muestra conectado, sin errores. Ambas entradas siguen enabled=true en la configuración local. Los procesos externos existen; esto no prueba handshake correcto de este chat. Los logs locales disponibles no registran el intento actual.

Impacto: impide lectura de ocupación/lease y ejecución de las pruebas preparadas EV67/68. No se ha lanzado ningún run nuevo ni usado HTTP/CLI como bypass. No hay prueba de la causa interna ni atribución a la generación del daemon.

Esperado: herramientas tipadas accesibles tras conectar, o error explícito de handshake/registro en la UI. Recuperación pendiente: una sesión cliente con catálogo publicado. Mantener aparte del ticket de foco existente fb-20261008-233507-8b1c; no duplicarlo.
