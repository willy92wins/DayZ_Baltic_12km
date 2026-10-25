COBERTURA

run_id: 2026-10-24-council-terrain-quality
decision_de_producto: reforzar deteccion de defectos visibles/jugables del mapa antes de aceptar o extender los candidatos actuales.
justificacion_n: usuario exige todas las familias distintas accesibles, incluyendo Opus5.5/Grok4.7/Muse/Gemini4. No ranking de modelos; lectura real y contrapropuestas matematicas complementarias. Solo rutas existentes, sin compras ni instalaciones.
arbitro: Codex sesion principal; verificacion propia de cada hallazgo y repro. Codex no abre subagentes.
scope: checks terreno/rios/bosque/carreteras/empaquetado/performance. No modificar fuentes originales, agua protegida o criterios aprobados; no publicar.
inputs: BRIEF-source.md para rutas nativas Anthropic/xAI/Google; BRIEF-abstract.md sin codigo privado/vault para rutas gratuitas o contributor. Hashes en inputs.json antes de primera lane de contenido. PONG preflights en probes/.
budget: una ronda de cobertura por familia con timeout20min; una ronda de revision independiente de implementaciones. Cada bug necesita repro/positivo/negativo y consumidor real. Errores de transporte permiten un reintento corregido y evidenciado, sin hacer pasar una ausencia por aprobacion.
green: controles nuevos detectan contrajemplos cerrados y conservan positivos; ejecucion real contra R con hashes; cero fallos reparables introducidos por el lote; limites visual/motor siguen abiertos hasta evidencia propia. Cuatro asientos obligatorios vigentes: Fable5.1, Grok4.7, Gemini4ArgonHigh, MuseWonder1.0 CLI.
privacy: Muse contributor y familias gratuitas reciben solo problema abstracto, sin codigo ni vault. Fuentes solo en nativas expresamente solicitadas. Sin credenciales en prompts/logs.
lanes: fable/claude-fable-5-1 native; grok/grok-4.7 native; gemini/gemini-4-argon-high agy; wonder/muse-wonder-1.0 native (contributor off). Extras completadas GLM5.3FlashEXL3 y Qwen3.8:98k locales. MuseGlimmer30B NIM solo informe suplementario de la misma familia.
quota_pre: 2026-10-24T14:13Z Opus weekly429 reset25oct22Madrid,0tokens; grokPONGmodelUsage4.7-build0.050008USD; GeminiPONGsuccess (modelo se verifica con metadata local); MuseOpenCode error servidor. Cline requiere reauth; Cursor requiereauth. Catalogos no equivalen a corrida.
steering: Guillermo sustituye expresamente Opus por Fable5.1. Corrige Muse a CLI nativo y Wonder1.0: autenticacion verificada PONG y contenido completado, run.usage identifica muse-wonder-1.0,15 llamadas completadas. Gemini primer intento vacio por read_file denegado, reintento con raices autorizadas produce informe completo. Cuatro asientos completos.
fallback: ningun fallo de una celda excluye una familia. OpenCode/Cline/Cursor no autenticados en esas rutas, sin implicar falta de login del CLI Muse. NIM DeepSeek timeout, Nemotron500, MiniMax504, Mistral404, Kimi404, StepFun504, Poolside503; no aportaron informe valido. No compras ni cambios de cuenta.
