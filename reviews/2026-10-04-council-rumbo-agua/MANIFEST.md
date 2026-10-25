tipo: COMPARABLE

# Consejo «rumbo del agua» — DayZ Baltic 12km — 04-10-2026

- run_id: council-rumbo-agua-2026-10-04
- pedido por: Guillermo, «pide una segunda opinión a astra, grok y gemini porfa, vamos a nutrirnos para poner un rumbo fijo»
- pregunta: rumbo fijo del sistema de agua y orillas hasta la base 1.0 (agua colgada, cauces con piezas vanilla, arroyos estrechos, secuencia de trabajo)
- decision_de_producto (C2, 3 lanes): niveles de lago (re-derivar o diques), encadenado de piezas vanilla y alcance de R2/R3, orden de trabajo hasta 1.0; no se puede decidir leyendo el árbol porque son decisiones de diseño con riesgo visual
- brief_path: E:\DayZ-Baltic-Build\council-rumbo-2026-10-04\brief\BRIEF.md
- brief_sha256: 02e48c1b355577d1364dd5e56f98051e00b56db10233ec7e9f0386d4596869c9 (10.134 bytes, UTF-8 sin BOM, LF)
- arbitro: Claude (orquestador; no es lane)
- ceguera: lanes en paralelo; salidas en `lanes\<id>\`, fuera de las carpetas que el brief manda leer

## Universo de cifras del brief

| Cifra | Fuente |
|---|---|
| desvío p50/p90 0,517/2,441 → 0,082/1,591 m | evidence/v30-shore-crossing-candidate-2026-10-04/README.md (todas las aristas agua-tierra con signo coherente) |
| 26–30 % de la mejora con calado ≥ 0,25 m | bugs.md:19 (BALTIC-007) |
| 0,33/0,49 % frente a 58/73/75 % de doble lámina; −0,044 m; 0,44°, 8,8° y 11,4° | evidence/v30-polish-candidate-2026-10-04/joints/joints.json, bloque groups (660 + 389 piezas de Chernarus; 8 + 44 + 47 nuestras) |
| 631 masas, 111 lagos, 7,0 km², 190 con dique | evidence/v30-polish-candidate-2026-10-04/census/census.json (agua estancada, clases 2 y 7, ≥ 4 vértices) |
| ~4,15 m sobre ~3,0 m, diques ~1,4 m | censo (cuerpos 499 y 508) y figures/luga-head-heights-before.png |
| 141 vértices hasta 2,10 m | evidence/v30-polish-candidate-2026-10-04/reports/polish-report.json |
| 5,0/3,8/1,2/1,0/2,7 ha | bugs.md:28 (BALTIC-016) |

## Lanes

| id | proveedor | binario | modelo_pin | tools | puede_leer_arbol | cuota_pre | invocacion | output_path |
|---|---|---|---|---|---|---|---|---|
| astra | OpenAI (suscripción pro) | codex-cli 0.160.0 | gpt-6-astra, effort xhigh | sandbox read-only | sí | ventana semanal 34 % usada (rollout 2026-10-04T04:51Z), créditos sí | `codex exec -m gpt-6-astra -s read-only -c model_reasoning_effort="xhigh" -o lanes\astra\out.md - < brief\BRIEF.md` (cwd = repo) | lanes\astra\out.md |
| gemini | Google (suscripción Antigravity) | agy 1.2.16 | gemini-3.1-pro-high | lectura de ficheros; sin shell | sí (--add-dir repo y brief) | sin contador legible; sonda 2026-10-04 OK (9,8 s, lee fichero, denied_actions nulo) | `agy --model gemini-3.1-pro-high --add-dir <repo> --add-dir <brief> --disable-slash-commands --output-format json --print-timeout 60m -p "<puntero al brief>"` | lanes\gemini\out.json → out.md |
| grok | xAI | — | — | — | — | SIN CELDA VIVA hoy (tabla C3b) | — | — |
| glm (SUBSTITUTED: grok → glm-gx10, decisión de Guillermo 04-10) | Zhipu GLM, local GX10 | gx10_lane.py (API directa :8001, streaming) | GLM-5.3-Flash-EXL3, effort medium, max_tokens 60000 | ninguna (sin herramientas) | no: NO-HARNESS con fuentes en línea | GX10 2/3 ocupado, caché KV 10,3 % | `GX10_EFFORT=medium python gx10_lane.py lanes\glm\input.sent.md lanes\glm 60000` | lanes\glm\content.md |

Entrada de glm: los bytes de BRIEF.md (prefijo intacto, sha 02e48c1b…) seguidos de un anexo con el contenido literal
de las fuentes obligatorias, numerado por línea (`lanes\glm\input.sent.md`, 81.218 bytes, sha256
12c125c84b0a00a0ac699fb63f226f131fed8cbb9ec384f33c40b4b026c1f3e0). Por eso no es comparable byte a byte con las
otras dos: cuenta como opinión, no como medida de precisión entre proveedores. Recuento por puerta tras la
sustitución (LL-449): codex exec 1, agy 1, API del GX10 1; ninguna puerta lleva más de la mitad.

Fallback declarado: gemini → gemini-3.8-flash-high (misma familia) si Pro devuelve 503 o cuota; astra → sin fallback.
Entrada efectiva: astra recibe BRIEF.md por stdin; gemini recibe un puntero corto y lee BRIEF.md con su herramienta
(mismos bytes; el puntero es transporte). Grok, si vuelve a tener celda, recibiría BRIEF.md por `--prompt-file`.

## Sondas del día por familia (C3b) — xAI (Grok)

| Peldaño | Celda | Sonda (2026-10-04) | Resultado |
|---|---|---|---|
| pago | grok-4.7 × grok-cli 1.0.46 | un turno, leer el cwd | `402 Payment Required: Grok Build usage balance exhausted` |
| suscripción | grok-4.7-xhigh × cursor-agent 2026.09.26 | un turno, leer product-spec.md | `ActionRequiredError: Named models unavailable. Free plans can only use Auto` |
| gratis | grok-code × OpenCode Zen | un turno | el modelo ya no está en el catálogo (`opencode models`: grok-4.5/4.6/4.7, grok-build-0.1) |
| pago | opencode/grok-4.7 × OpenCode Zen | un turno | `Upstream request failed: Insufficient account funds` |
| pago | ~x-ai/grok-latest × OpenRouter | un turno | `requires more credits … can only afford 7403` tokens |

Sondas de las otras dos familias (mismo día): astra × codex exec → lista el cwd, `model: gpt-6-astra` en el log, RC=0;
gemini-3.1-pro-high × agy → primera vez con shell denegada (`denied_actions: command`); segunda, con «usa tu
herramienta de ficheros», copia la primera línea de product-spec.md, `denied_actions` nulo.

## Relanzamiento (04-10, 18:11)

| id | proveedor | binario | modelo_pin | tools | puede_leer_arbol | invocacion | output_path |
|---|---|---|---|---|---|---|---|
| gemini38 | Google (suscripción Antigravity) | agy 1.2.16 | gemini-3.8-flash-high (sonda `agy models` del día: versión más alta) | lectura de ficheros; sin shell | sí: `snapshot-5125f35`, un `git archive` del commit que leyeron las otras lanes | `agy --model gemini-3.8-flash-high --add-dir <snapshot> --add-dir <brief> --disable-slash-commands --output-format json --print-timeout 60m -p "<puntero>"`, cwd = instantánea | lanes\gemini38\out.json → out.md |

Desviación declarada: el puntero (`lanes\gemini38\input.sent.md`, sha256 a84f87aa…) añade una frase de transporte que
lleva la raíz del repo a la instantánea, porque el repo vivo ya contiene los dictámenes, el arbitraje y el plan. El
brief es el mismo (sha 02e48c1b).
