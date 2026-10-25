# Reparación de publicación MCP

El parserhost_config rechazaba enabled=true en el bloqueCodexdayz-mcp. Comparación canónica enmemoria confirmó conflicto por esa clave únicamente. Se retiró solo ese metadato redundante del servidor principal mediante comprobaciónCAS; codex mcp get antes/después idéntico y enabledtrue por defecto. CódigoMCP/guardas y servidor experimental intactos. Tras reiniciarChatGPT reaparecen herramientas; EV73/74 lanzados y cerrados por MCP.

Ticket presentado: fb-20261009-213708-1d4d. La procedencia de quien escribió enabled no se ha aislado. Este workaround no sustituye una corrección del parser con pruebas de compatibilidad y seguridad. Ticket de focoWindows anterior fb-20261008-233507-8b1c sigue abierto; no duplicado.
