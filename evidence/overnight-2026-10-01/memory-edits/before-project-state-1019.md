# Estado de proyectos — snapshot 2026-08-27

> Vista de pÃ¡jaro de todos los proyectos activos, reconstruida del barrido
> completo del historial de sesiones de Cowork (77 sesiones). Pensada para
> que una sesiÃ³n futura se oriente leyendo un solo archivo. **Es un
> snapshot fechado** â€” el estado vivo de cada proyecto estÃ¡ en su repo
> (`CLAUDE.md`, `plans/`) y en sus handoffs `HANDOFF_*.md`.
>
> **Regla de lectura:** este archivo orienta y conserva historia; ante cualquier
> discrepancia gana el bloque `LIVE-STATE` del `*_dev\HANDOFF.md`. Si no hay un
> `LIVE-STATE` fresco, el bloque se marca **STALE**.

## LIVE 2026-08-28 noche (Asistente; Luna 10_Projects #2)

Fuente de verdad = bloque `LIVE-STATE` del `HANDOFF.md` de cada repo `_dev`. Este snapshot no lo pisa. Verificado leyendo los tres HANDOFF, no el ranking de Luna.

- **LFPowerGrid** LIVE 2026-08-28 noche. `C:\Users\guill\OneDrive\Documentos\DayZ Projects\LFPowerGrid_dev\HANDOFF.md`. Checkout `release/lfpg-footprint-rc` @ `5a1ef09`, main intacto @ `d61705e`. Frente A: sorter V4 TEST (vuelo F, fuentes). Frente B: F7 smoke del dueño. El bloque de abajo (julio / 13-ago) es historia.
- **LF-COM** HANDOFF LIVE-STATE **2026-08-29**. Harness F0: G1–G5 MET, G6 ABANDON, R21 Codex+Claude SOUND. Próxima: tanda A-solo con operador. `C:\Users\guill\OneDrive\Documentos\DayZ Projects\LFCOM_dev\HANDOFF.md`. El snapshot 15-ago queda como historia debajo del LIVE-STATE.
- **DayZ-MCP no esta cerrado.** Bloques 1-2 cerrados/merged (PR #15, tip `d5e179f`); **Bloque 3 en curso** tip `6de5d98` (tablero 2026-09-11). El header CERRADO 2026-06-11 era el cierre de las 5 fases, no del proyecto. Estado vivo: `C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_MCP_dev\HANDOFF.md`.
- **AI_Pipeline** no tiene HANDOFF de repo. Canónico: `C:\Users\guill\.claude\skills\delegar` (`routing.md`). `gates-ledger` v2 sigue **NO instalar**. La foto 26-ago de abajo queda STALE.

Luna #1 (cerrar o abandonar gates-ledger, techo 2-3 días) y el o/o #3 F0 LF-COM vs #4 G0 DayZ-MCP son GO de producto, no de este archivo.

## LFDucati — moto 1.30 heredando de la vanilla **NEW 2026-09-19**

Mod DayZ nuevo para 1.30 Experimental: Ducati Desmosedici GP16 importada de un OBJ de SketchUp, hereda de `MotorbikeScript`
(`simulation = "motorbike"`) y solo cambia masa, CdG, geometría, motor y modelo. Destino Workshop. Contrato en **borrador v0**
(`P:\LFDucati_dev\product-spec.md`, 7 decisiones cerradas, DA-4…DA-8 abiertas). Hallazgo del arranque: 1.30 binariza en **ODOL v56**
(1.29 = v54) y el desbinarizador necesitaba parche; anatomía P3D vanilla delegada a GX10. Estado vivo: `P:\LFDucati_dev\HANDOFF.md`.
Handoff: `30_Sessions/2026-09-19-lfducati-arranque-contrato-research.md`.

## LFSecure — kit → puerta → sala segura a 3900 m **NEW 2026-09-07**

Mod DayZ nuevo (La Frontera): un kit (caja de LFPowerGrid) coloca una puerta exterior pegada a una pared de
edificio; la puerta genera una sala segura a `RoomHeight` (JSON, 4000 m por defecto) y teletransporta al jugador
(mantener F) entre ambas. Contrato V1 **cerrado el 2026-09-07** con 8 decisiones del usuario (D-01 revisada vía picker a HouseNoDestruct; 3900 m; 9°)
(`P:\LFSecure_dev\product-spec.md`; `10_Projects/LFSecure/decisions/decision-log.md`). Plan pendiente
(Astra + Claude) tras compactar; implementación delegada a Astra (`gpt-6-astra`), revisión Claude.

- **Estado 2026-09-07 (18:50)**: **CODIGO V1 COMPLETO** (L0 assets, L1a nucleo servidor, L1b kit/holograma, L2 acciones/luces)
  entregado por Astra en 4 lotes (puertas ejecutables, recepcion y R-2 de Claude con 2 defectos reales corregidos) y desplegado en
  `P:/Mods/@LFSecure/Addons/LFSecure.pbo` (185 entradas, 16 scripts). Pendientes: revision final de L2 (tras compactar) y
  pruebas en motor B-4/B-5, I-0..I-10 en sesion nueva (`P:/LFSecure_dev/NEXT-SESSION.md`; MCP desarmado en la sesion del plan).
- **Proximo**: revision final L2 -> sesion nueva con MCP: `dayz_test_run(project=LFPowerGrid, extra_mods=[@LFSecure])`, I-0..I-10; rojo -> L3 a Astra.
- Handoff: [`30_Sessions/2026-09-07-lfsecure-contrato.md`](../30_Sessions/2026-09-07-lfsecure-contrato.md);
  estado vivo: `P:\LFSecure_dev\HANDOFF.md`; sesion de plan: [`30_Sessions/2026-09-07-lfsecure-plan-y-lotes.md`](../30_Sessions/2026-09-07-lfsecure-plan-y-lotes.md).

- **Estado 2026-09-08 (00:10): V1 LOGRADA.** Guillermo verifico in-game holograma/colocacion/entrar/salir/texturas (PBO L7). Post-V1 en `P:/LFSecure_dev/NEXT-SESSION.md`.
- **Update 2026-09-10 — V2/V3**: V2 probada in-game; contrato V3 cerrado (armero + cocina de gas con sonda L0). Handoff: [`30_Sessions/2026-09-10-lfsecure-v3-contrato-l0.md`](../30_Sessions/2026-09-10-lfsecure-v3-contrato-l0.md). Brief: [`LFSecure/project-brief.md`](LFSecure/project-brief.md). Estado vivo: `P:\LFSecure_dev\HANDOFF.md`.

## DayZ_Baltic_12km — base nativa0.2 y navegación propia comprobadas

Recorte aprobado, base propia 12,288 × 12,288 km y assets vanilla primero. Agua,
San Petersburgo íntegro, Narva/frontera y territorio occidental son prioritarios.
Objetivo: 80–100 jugadores, rendimiento sin demostrar.

Repo: `P:\DayZ_Baltic_12km_dev`; estado vivo: [HANDOFF](<C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/HANDOFF.md>).
Base0.2 activa fd2c7023:1242 ediciones nativas/tres puentes persistidos, navmesh propia60025teselas, carga cliente/servidor e IA real ida/vuelta por Narva. Carga100 infectados activos medida; no demuestra80–100 jugadores. Relieve selectivo por jugabilidad aprobado (P12), sustituye elección×1/×3; propuesta por zonas preparada, sin editar terreno. Terreno e hidrografía regional antes del mapeado, cotas finales pendientes. Rollback y checkpoint8945archivos guardados. Sin concurrencia con Exta; estado vivo en HANDOFF.
[Último handoff: relieve selectivo](../30_Sessions/2026-09-30-dayz-baltic-relieve-selectivo.md). [Base nativa y pruebas](../30_Sessions/2026-09-30-dayz-baltic-native-navmesh-performance.md). Proyecto hermano: [[IberiaMap|IberiaMap]].

## SUB_BRZ — Subaru BRZ FE 2022 widebody (Forza -> DayZ) **VIVO 2026-09-10**

Pipeline reproducible Forza -> DayZ. Memoria: [`SUB_BRZ/project-brief.md`](SUB_BRZ/project-brief.md).
Mod: `P:\SUB_BRZ`; dev: `P:\SUB_BRZ_dev`; pipeline: `C:\Users\guill\ForzaDayZ`; PBO: `P:\Mods\@SUB_BRZ\Addons\SUB_BRZ.pbo`.
- **Hitos 2026-09**: GPS completado en **s76** (desplegado, sin prueba visual cliente); sonda **s90** (tablero slug `sub-brz` snapshot 2026-09-10a; via (c) muerta).
- **Estado vivo**: `P:\SUB_BRZ_dev\HANDOFF.md` (gana ante este indice).
- Excepcion de memoria declarada en `_memory-exceptions.json`.

## A6_SR2M — SMG SR-2M Veresk; grip de mano de apoyo **UPDATED 2026-06-23**

Mod DayZ: SMG rusa 9x19 SR-2M Veresk (malla del usuario → `.p3d` → config heredando del pack A6). Foco de
las últimas semanas: el AGARRE de la mano de apoyo (caía plana encima del cañón, no cerrada en el foregrip).
Memoria en el repo (`…\A6_SR2M_dev\`: product-spec, HANDOFF.md, research/, reviews/).

- **Estado 2026-06-23**: **IDLE RESUELTO + shippeado a producción.** Determinante = GEOMETRÍA, no anim: el
  bore estaba 2.4 cm más bajo que el de una ref que funciona → la mano caía encima. Fix = subir el modelo
  +Y0.024 (`sr2m_body_raised.p3d`) + `RegisterFireArms`+`pm73_ik` (ikpose vanilla). Validado in-game (idle
  perfecto). Lo destrabó la RE empírica del pack KarmaKrew (workshop 2864245850) + diagnóstico de geometría
  (debinarizado KK `SR2.p3d` vs el del proyecto). Doc: `research\2026-06-22-karmakrew-vikhr-RE-grip-mechanism.md`.
- **Pendiente**: el APUNTADO abre la mano (aim-space comparte ikpose con idle). Plan: gate que fuerce el
  apuntado (`OverrideRaise`, `human.c:249`) + tune de ikposes; fallback = override `.asi` de aim/ADS (V1).
  Clon de comparación iter34 (KK SR-2M geo vs producción en ADS) en preparación en `@A6_AnimRTTest`.
- **Aprendizajes durables**: LL-153 (juzgar visual por full-res, no RMS/miniatura); refuerzo en
  `dayz-animation-pipeline\weapon-in-hands.md` (parity-raise como fix del grip). Handoff:
  [`30_Sessions/2026-06-23-A6_SR2M-grip-RE-geometry.md`](../30_Sessions/2026-06-23-A6_SR2M-grip-RE-geometry.md); estado vivo: `A6_SR2M_dev/HANDOFF.md`.

## kt_roadkill_armed — coche armado con torreta M2 (Phase 2) **UPDATED 2026-06-07**

Mod DayZ: coche "roadkill" con M2 en torreta; copiloto artillero, 1ª persona apuntando por el cañón.
**Memoria de proyecto EN EL REPO** (`…\DayZ Projects\kt_roadkill_armed_dev\`: product-spec, decisions/019, bug-ledger, reviews/), no en 10_Projects.

- **Estado 2026-06-07**: Phase A OK in-game (modelo base). Phase 2 por sprints: A, B, eye_gunner y
  **G' (convergencia de mira + recoil server-owned) cerrados OFFLINE** tras ciclo R22→R21×2
  (2 bugs + 1 regresión cazados y corregidos: bug-014/015). `.p3d` en `_dev/model-rig/phase2_build/`
  **verificado correcto** (py3d-direct; la alarma de selecciones fue falsa — LL-111); SIN copiar a `data/`.
- **Próximo**: Sprint C (prompt entregado: 7 clamp-sites + config + model.cfg angles) → D/E/H/I →
  gate bundle → rebuild → sesión in-game única. Handoff:
  [`30_Sessions/2026-06-07-kt-roadkill-armed-phase2-sprint-g-prime.md`](../30_Sessions/2026-06-07-kt-roadkill-armed-phase2-sprint-g-prime.md); estado vivo: `kt_roadkill_armed_dev/HANDOFF.md`.

## LFGungame — modo GunGame para DayZ **⏸️ CONGELADO 2026-06-16**

> **CONGELADO 2026-06-16** (decisión del usuario): proyecto pausado en el estado 06-10. No retomar hasta descongelar; el resto de proyectos continúa. Al reanudar, arrancar por la sesión de fix (GG-01 raíz + GG-10 deploy). Ver [`90_Archive/2026/50_Weekly-Pending/2026-06-15-pendientes.md`](../90_Archive/2026/50_Weekly-Pending/2026-06-15-pendientes.md).

Mod de scripts puros: GunGame activado por comando de chat LBmaster `!gungame` (solo
Admins). Progresion por tiers de armas; cuchillo de un golpe que sube al asesino y baja
a la victima; scoreboard (tecla L), contador de tier + corona; config JSON no-lazy.

- **Memoria**: `AI/10_Projects/LFGungame/` (6-tupla + research/).
- **Repo**: `…\DayZ Projects\LFGungame\` (compilable, scaffold) + `LFGungame_dev\` (contrato + dev).
- **Deps DURAS (verificadas vs source montado)**: `LBmaster_Groups` (comando `LBChatHandler`),
  `LBmaster_Core` (presets `LB_PresetLoader`/`LB_PresetBase`). Ver `verified-apis.md`.
- **Estado 2026-05-27**: **scaffold + contrato cerrados** via Grill de producto (4 rondas con
  usuario). Sin implementacion. Contrato: `LFGungame_dev/product-spec.md` (criterios A–I, R26).
  Gotcha clave: `SpawnPresets` aplica chances → presets del gungame deben ser chance 1/100%.
- **Pendientes (hasta 2026-05-27)**: research dual (fase 0) → plan fase 1 → grill de plan → R22 Codex → implementar.
  Decision GUI (vanilla/Dabs/Expansion) diferida a fase 1.
- **Estado 2026-05-31 (supersede lo anterior)**: **S0–S5 implementados y revisados** (arranque +
  tiers + kills/cuchillo/muerte/stats/assists/respawn; núcleo de combate completo offline).
  Cadena de compile errors resuelta: BUG-002 (truncado de `LFGungame_Constants.c`), BUG-003
  (violación de capa `LB_PresetLoader` 3→4 en `Config.c` + colisión de nombre `LogManager`→`LogRound`
  en `RoundManager.c`). **Bloqueante actual: BUG-004** — crash al entrar (`CreateWidgets` sobre
  layouts inexistentes: HUD + JoinMenu); nunca se había entrado in-game. UI (S6/S7) sin adoptar:
  4 layouts en `LFGungame_dev/_kit/Gungame/gui/layouts/` pendientes de adoptar al mod.
- **Próximo**: sesión de UI completa (prompt en `LFGungame_dev/reviews/2026-05-31-prompt-sesion-ui-completa.md`)
  → resolver BUG-004 → primer ciclo de test in-game S1-S5. Handoffs:
  [`30_Sessions/2026-05-31-LFGungame-constants-truncation-fix.md`](../30_Sessions/2026-05-31-LFGungame-constants-truncation-fix.md) +
  [`30_Sessions/2026-05-31-LFGungame-compile-chain-y-crash-ui.md`](../30_Sessions/2026-05-31-LFGungame-compile-chain-y-crash-ui.md).
- **Estado 2026-06-10 (supersede lo anterior)**: **mod terminado OFFLINE + remediación de auditoría aplicada en fuentes**
  (UI adoptada, fin de ronda I1-I4, scoreboard G3-G5, HUD corona H1-H2, clusters 1-4 de la auditoría preprod 06-07,
  WARN-1/3 Codex arreglados). Auditoría pre-test 2026-06-10 (Claude/Fable): **GG-01 bloqueante** — respawn cableado
  al personaje VIEJO (`OnClientRespawnEvent`); el nuevo nace en `OnClientNewEvent`, NO hookeado → F1/F2/I4-muertos
  rotos en cada muerte real. + GG-02..GG-09, F-25 huérfano del plan, **GG-10**: PBOs desfasados (06-05/06-02) sin
  los fixes. Última verificación in-game real: RPT 06-02 (ciclo completo limpio). Estado vivo: `LFGungame_dev/HANDOFF.md`.
- **Próximo (2026-06-10)**: sesión de fix (prompt en `LFGungame_dev/reviews/2026-06-10-prompt-sesion-fix.md`:
  R1=GG-01+02+03 → R2=GG-04+05) → rebuild `-packonly`+sign+deploy → test in-game ciclo 1. Fuente única de findings:
  `LFGungame_dev/_review_flags/audit-pretest/2026-06-10-REPORTE-AUDITORIA-PRETEST.md` + handoff
  [`30_Sessions/2026-06-10-LFGungame-auditoria-pretest.md`](../30_Sessions/2026-06-10-LFGungame-auditoria-pretest.md).


## LF_RollingStone â€” piedra fÃ­sica que rueda (PhysX nativo) **NEW 2026-05-21**

Mod DayZ standalone: piedra esfÃ©rica que rueda con fÃ­sica PhysX nativa (gravedad,
fricciÃ³n baja, rebote, daÃ±o + empuje a jugadores). AcciÃ³n "Empujar" = impulso.

- **Memoria**: `AI/10_Projects/LF_RollingStone/` (6-tupla + ADR 001 + research/).
- **Repo**: `â€¦\DayZ Projects\LF_RollingStone\` (compilable, scaffold) + `LF_RollingStone_dev\`.
- **DecisiÃ³n central (ADR 001)**: API rigid body nativa (`dBody*`) sobre `LFRS_RollingStone
  extends ItemBase`. Descartados CarScript y simulaciÃ³n scripted.
- **Estado 2026-05-21**: Sprint 1 implementado por Codex en `LF_RollingStone/` con validacion estatica limpia (readback + anti-sync grep + syntax-risk grep). Plan canonico:
  `LF_RollingStone_dev/plans/2026-05-21-sprint1-skeleton.md`; handoff de implementacion:
  `LF_RollingStone_dev/plans/2026-05-21-sprint1-impl-handoff-codex.md`. Prior art `ScriptModel`; veredicto sync pendiente de server real.
  Params fisicos: R=1.0 m, M=200, damping bajo-no-nulo (0.02/0.03).
- **Review S1 + modelo 2026-05-21 (Claude R21)**: revision independiente OK, fidelidad alta. Finding P2 cerrado: revert de `dBodySetSleepingTreshold`+`dBodyEnableCCD` (estaban fuera del Step 3 del plan; CCD ademas sin verificar). Modelo del artista integrado visual-only: `data/RollingStone.p3d` (texturizado via py3d con `pelota.rvmat`+`pelotatext.paa`), `config.cpp:63` actualizado; colision sigue programatica. Riesgo abierto: Geometry LOD full-res del modelo puede competir con el body (bug-ledger 2026-05-21). Handoff: [`30_Sessions/2026-05-21-lf-rollingstone-sprint1-review-modelo.md`](../30_Sessions/2026-05-21-lf-rollingstone-sprint1-review-modelo.md).
- **Pendientes**: build/PBO + server dedicado POS-1/NEG-1/NEG-2 para veredicto sync SI/NO/INCONCLUSO;
  si NO -> Sprint 1.5 (sync manual). Accion "Empujar" (S2) debe derivar de `ActionPushObject` vanilla.

## magic-standard-brewing â€” Brewing MTG Standard Bo1 ranked (Arena) **NEW 2026-05-19**

Proyecto NO-cÃ³digo. Brewing de Grixis Artifacts (UBR) en Standard 2026 con
objetivo top 1200 Mythic. **Camino brewing genuino sobre baseline competitiva**.

- **Memoria**: `AI/10_Projects/magic-standard-brewing/` â€” 6-tupla adaptada
  (verified-cards, assumptions, matchup-matrix, deck-ledger, decisions/, reviews/).
- **Estado 2026-05-19**: vault setup completo. VerificaciÃ³n Scryfall API directa
  de 18 cartas core. Cadenas de interacciÃ³n mapeadas (3 engines: spam-tokens,
  Geardrake-Ooze sacrifice, Munition reach). AnÃ¡lisis cuantitativo Monte Carlo
  re-derivado (los scripts originales se perdieron). Replanteo de arquetipo
  consolidado.
- **Hallazgo crÃ­tico**: 3 asunciones del handoff anterior eran errÃ³neas â€”
  Tezzeret CMC = 3 colorless (no 4 UB); Pactdoll es artifact creature (no
  solo enchant-drain); Weapons Manufacturing existe y completa una cadena
  de reach (Munitions = 2 dmg al salir). v1.2 propuesta con WM + Worldwalker
  Helm subido + FIX_D 23L. v1.3 Izzet+splash B tambiÃ©n propuesta como brazo C.
- **Pendientes**: verificar 6 SB cards (Pyroclasm, Fire Magic, Diversion Unit,
  Ghost Vacuum, Spectral Restitching, Soul-Guide Lantern), discutir D9-D12
  con usuario, craftear, jugar bloque 30 partidas.
- **Decisiones pendientes**: D9 (FIX_D 23L), D11 (Lista 3 Izzet+splash), D12
  (A/B/C plan), D13 (Magic/ tracking on-demand).

## LF_VStorage â€” mod de virtual storage

Mod DayZ que virtualiza el contenido de containers (barriles, etc.) a
disco para aliviar la persistencia del server.

- **Rutas**: proyecto en `â€¦\Claude\Projects\Virtual Storage\LF_VStorage\`;
  cÃ³digo referenciado desde `P:\`; GameFiles CF en `P:\GameFiles`.
- **DecisiÃ³n de arquitectura central**: los items restaurados se guardan
  como **PERSISTENT**, NO con `ECE_NOPERSISTENCY_WORLD`. Tras restaurar se
  borra el archivo `.lfv`. Verificado contra Expansion y ToFu vStorage 2
  (ninguno usa NOPERSISTENCY). AcompaÃ±ado del fix de reconciliaciÃ³n
  (`ClearPhantomItems` **despuÃ©s** de un load exitoso, nunca antes; borrar
  `.lfv` stale).
- **Otra decisiÃ³n clave**: la clase base `LFV_Module.c` no lleva NINGÃšN
  `#ifdef SERVER`; todo lo server va en `LFV_Module_Server.c` como
  `modded class` dentro de `#ifdef SERVER`. Ver
  [`AI/20_Knowledge/dayz-modded-class-server-stub-pattern.md`](../20_Knowledge/dayz-modded-class-server-stub-pattern.md).
- **Estado**: Sprint 2 cerrado (~76 %â†’100 % en disco tras Bundle 6+7).
  Sprint 5.4 con el fix crÃ­tico C1 (`data.m_State = VIRTUALIZED` en
  `BuildContainerFile`) **aplicado en cÃ³digo pero el PBO no rebuildeado** â†’
  el bug de pÃ©rdida total por restart podrÃ­a seguir vivo en producciÃ³n si
  no se completÃ³ el deploy. Pendiente de verificar.
- **Pendiente recurrente**: el fallo de workflow del proyecto fue trabajar
  "en papel" muchos sprints sin compilar ni probar en server real.
- **Handoffs**: varios en `AI/30_Sessions/2026-05-1*-lf-vstorage-*.md`.
- **Estado 2026-06-11**: auditoría de producción consolidada (Claude Fase A completa
  + Codex): 4 cadenas P0 (bridges de lock, identidad sid, .lfv-delete window,
  IdMap flush) + P1-10 (trigger ciego a attachments). El aviso previo de "PBO no
  rebuildeado" se confirmó: PBO 28-may sin el bridge del 01-jun (interior sondeado).
  Informe: `LF_VStorage_dev\AUDIT_PROD_TRIAGE_2026-06-11.md`. Siguiente sesión:
  plan+fix por pipeline normal (LIVE-STATE creado en `LF_VStorage_dev\HANDOFF.md`).
- **Estado 2026-07-08**: ironing pre-1.5.0 aplicado y verificado offline tras revision
  completa + 4 subagentes. Fixes: `SYNC_SETTINGS` client-only, `EECargoOut`, sidecars
  fail-closed, `RequestRestore` bool, reset/migrate-all monotono, legacy tmp filtrado,
  `PhantomDrop.FinalizeSuccess` durable, version `1.5.0`. Gates verdes:
  `verify_ironing_contracts: OK` y `enforce_compile_risk_sweep: OK (57 file(s))`.
  **No release-safe aun**: falta rebuild/sign/deploy PBO + Fase B in-game completa
  (10 escenarios). Handoff: [`AI/30_Sessions/2026-07-08-LF_VStorage-ironing-fixes.md`](../30_Sessions/2026-07-08-LF_VStorage-ironing-fixes.md);
  estado vivo: `LF_VStorage_dev/HANDOFF.md`.
- **Estado 2026-07-11**: F-01..F-14, F-16 y F-18 verdes; seis regresiones adicionales
  RED->GREEN (fallback canonicalization, checkpoint identity, stages, cancel intent,
  same-SID y reset con writer abierto). Candidato R-01 reproducible 66/66, SHA-256
  `AF823C562A3866427DE52FAACF528E6AEF6FFFE29183A431BFE931149329C0D2`, sin firma
  ni deploy. `NEEDS-WORK - NO PUBLICAR`: siguen abiertos D2 node-level, C4 doble
  `RestartMission`, límites binarios, hot paths síncronos, Fase B y auditoría SOUND.
  Handoff: [`AI/30_Sessions/2026-07-11-lfvstorage-f15-f18-r01-audit-closure.md`](../30_Sessions/2026-07-11-lfvstorage-f15-f18-r01-audit-closure.md).
- **Estado 2026-07-13**: executor y Track B del correctivo V-B están GREEN offline
  (`70/70`, compile-risk 65, verifiers 20/20 y 4/4), pero SC-001 falló dos veces
  en DayZDiag real: el move positivo preservó el subárbol y ambos destinos
  inválidos devolvieron `true`. `BLOCKED-STOP`: producto intacto, V-B/V-A
  integradas no ejecutadas y nuevo plan de arquitectura obligatorio. Handoff:
  [`AI/30_Sessions/2026-07-13-lf-vstorage-d2-vb-sc001-blocked-stop.md`](../30_Sessions/2026-07-13-lf-vstorage-d2-vb-sc001-blocked-stop.md).

## LF_PowerGrid â€” mod elÃ©ctrico + web de documentaciÃ³n

- **Mod**: en `P:\LFPowerGrid` (carpeta de **pruebas** â€” el repo es
  intocable, ver regla repo/pruebas abajo). Sistema de proxies para el
  battery adapter, registries de dispositivos/balance, save por validaciÃ³n
  de rango (no magic-prefix dual-format, porque el save de DayZ es stream
  binario secuencial sin headers).
- **Web**: en `C:\Users\guill\LFPowerGrid-Web` (fuera de OneDrive a
  propÃ³sito). Stack **Astro 5 + Vite 6.4.1** (forzado: Node 24 es
  incompatible con Vite 7/Rolldown) + Tailwind v3 + React + Three.js. 34
  pÃ¡ginas de docs = 100 % del sidebar. i18n con bloques `data-lang="en/es/ru"`.
  Modelos `.p3d`â†’`.glb` con la skill `dayz-3d-viewer`. Deploy: `npm run build`
  â†’ `dist.zip` â†’ descomprimir en `C:\web\lfpowergrid` del server.
- **Bugs web abiertos**: Solar Panel sale tumbado (rotaciÃ³n correcta
  `[90,0,0]`); Logic Gate con triÃ¡ngulo gris gigante (proxy geometry sin
  filtrar).
- **Pendiente**: spec de remediaciÃ³n v2 de la auditorÃ­a lista para aplicar.
- **Estado (2026-07-30)**: T5/AUTH siguen cerrados en `11bad048`. El carril
  server-footprint ha reducido el peor World−E desde `1522 kB` hasta
  `1250 kB`; reducción causal acumulada `272 kB`, gap `494 kB`. A10-D59 sigue
  parent experimental inmutable (`48a3bef...b524`, PBO
  `DDA30458...59A5`). A14 cerró child `LoadScript` como `NO_GO` bajo Intent K.
  K2/M1 normal Mission está redactado/revisado y congelado por cuatro SHA, pero
  `BLOCKED_PRODUCT_APPROVAL`; Task 0 exige además cero consumers externos en
  todos los scripts del stack. No está integrado; Task 11/12, publicación y
  eliminación siguen cerrados. Estado vivo: `LFPowerGrid_dev/HANDOFF.md`.
- **Estado (2026-08-13)**: BUGFIXING Phase A de la 1.2.3 en ejecución por tandas:
  **17 de 27 filas cerradas en offline** (A0..A3C + **A4a sustrato economía** con
  sus correctivas A4aC/A4aC2 — anti-replay BTC, durabilidad propagada, rango
  acotado). Ciclo completo por tanda: Codex implementa → receptor propio → gate
  de compile (sellado `33AA139C` custodiado) → Grok R21 con repreguntas → fan-out
  DZ-R9 → arbitraje. Veredicto final A4a: SOUND-CON-FIXES, 0 crítico/mayor
  abierto. **Nada probado in-game** (sesión agrupada de fin de fase pendiente).
  SIGUIENTE: montar A4b (9 filas + migración BalanceData v2 de BTC-034, decisión
  C+A+E en `decisions/002`). Directriz de modelos: subagentes Codex/Grok/Opus,
  nunca Fable salvo petición. Estado vivo: `LFPowerGrid_dev/HANDOFF.md`; log:
  `LFPowerGrid_dev/reviews/2026-08-13-phase-a-a4a-sustrato/EXECUTION-LOG.md`.
  Handoff:
  [A14 child NO_GO y propuesta K2/M1](../30_Sessions/2026-07-30-lfpowergrid-a14-childmodule-no-go-k2-proposal.md).

- **Estado (2026-08-17)**: **B3 (suelo WithdrawOnly) CERRADO con A/B in-game
  real** — con el flag a 1 la compra en cuenta devuelve `err=9` (el gate del servidor) y con el
  flag a 0 la misma sonda devuelve `err=2`, lo que hace el resultado atribuible; las guardas de
  cliente de los dos Deposit quedan probadas por ausencia de respuesta. Era la primera cobertura
  in-game del proyecto desde el 24 de julio. Lo que lo bloqueaba estaba fuera del mod: `ui_click`
  del MCP no podía pulsar **ninguna** UI de Dabs (4 vistas de producto del mod son
  `extends ScriptView`, más 3 duplicados TEST);
  parcheado, desplegado y verificado in-game. Existe ya una celda reutilizable (`atm_b3_cell.py`)
  que corre la cadena entera sin manos. SIGUIENTE: convertir el guión in-game pendiente (Phase A
  494 líneas + Bloque D 182) en celdas, que hasta hoy no era posible. Sigue pendiente **subir la
  1.2.2 al Workshop** (carpeta lista desde el 20/07; arregla un crash en producción de dos admins
  externos sin tocar código). Estado vivo: `LFPowerGrid_dev/HANDOFF.md`. Handoff:
  [B3 cerrado y ui_click para Dabs](../30_Sessions/2026-08-17-lfpowergrid-b3-cerrado-y-uiclick-dabs.md).

- **Estado (2026-08-19)**: **Hito 1 CERRADO — A-1/A-2/A-3 PASS in-game con evidencia cruzada**
  (`LFPowerGrid_dev/reviews/2026-08-19-a-final/`); el mod validado por la campaña A sin tocarse.
  CORRECCIÓN al estado anterior: **la 1.2.2 se publicó en el Workshop el mismo 20-jul**
  (ACF+SHA verificados) — el «sigue pendiente subir» era un fantasma heredado un mes (LL-327).
  Ciclo **1.2.3 ABIERTO**: fixes `err=11/14` aplicados al working tree del mod **SIN commit**
  (validar antes de commitear), celda B2 híbrida lista (`--assume-wired`; el cableado no es
  automatable por `action_use` v1), guión de la sentada única de validación de agosto en
  `LFPowerGrid_dev/plans/2026-08-20-guion-sentada-validacion-agosto.md` (~1-1.5h, una caja).
  Sell-quema cerrado como diseño. Drainfix de `logs_since` integrado en DayZ_MCP_dev (activo al
  próximo reinicio del daemon). SIGUIENTE: la sentada única → commit → build → firmar → Publisher
  3696475622. Estado vivo: `LFPowerGrid_dev/HANDOFF.md`. Handoff:
  [Sentada A completa, tres Grok y el Workshop fantasma](../30_Sessions/2026-08-19-lfpowergrid-sentada-A-completa-tres-grok-y-workshop-fantasma.md).

- **Estado (2026-08-26, `LIVE-STATE` vigente)**: la RC del recorte está aterrizada y
  auditada. **World retail con LBmaster = 588 kB** (objetivo `<=628 kB`). El checkout
  vivo está limpio en `release/lfpg-footprint-rc` @ `5a1ef09`; **`main` permanece
  intacto** @ `d61705e`.
- **Siguiente gate**: falta **F7 smoke in-game** (persistencia tras reinicio,
  flujos ATM/claims y sonda del fixture); solo si pasa se ejecuta F8
  (fast-forward de `main`, tag, canary y changelog). Fuente autoritativa:
  `C:\Users\guill\OneDrive\Documentos\DayZ Projects\LFPowerGrid_dev\HANDOFF.md`.
- **Estado (2026-09-15)**: **release 1.2.5 publicada en la carpeta de subida del item
  principal**.
  - Contenido: PBO firmado `DAA6155C`, bisign `0AD2EE3D` y `Extra/LFPGtypes.xml` con los
    kits T2. Solo falta la subida al Workshop, que hace el usuario.
  - Git: `main` = `origin/main` = `3e5ab8a`, tag `v1.2.5`.
  - Gate in-game G1–G4 en verde:
    - kits T2, con persistencia tras reiniciar;
    - mejora de bomba y solar;
    - PTZ tras reiniciar;
    - saldo tras la muerte;
    - E02 sin efectivo por la interfaz;
    - puertas lógicas y cableado por RPC.
  - Sin ejecutar: x36-b/c (análisis aceptado).
  - Backlog:
    - arnés GS-02 (timeouts, `dst_*`/`tgt_*`, carrete);
    - rechazo intermitente del storage de pruebas.
  - Estado vivo en `LFPowerGrid_dev/HANDOFF.md`; evidencia en
    `LFPowerGrid_dev/reviews/2026-09-15-sentada-g2g3/`.

## DayZ_UI_Research â€” visor de `.layout` de Enfusion

Herramienta para renderizar interfaces de DayZ (`.layout`) a HTML/CSS **sin
lanzar el juego**, con emulaciÃ³n de estados (widgets `visible 0`, pestaÃ±a activa,
hover, valores de binding, listas pobladas). Fin: acortar el loop de diseÃ±o de UIs.

- **Rutas**: repo en `â€¦\OneDrive\Documentos\Claude\DayZ_UI_Research\`; memoria de
  proyecto en `AI/10_Projects/DayZ_UI_Research/`. Artefacto de prueba canÃ³nico:
  `P:\LFPowerGrid\gui\layouts\LFPG_Sorter.layout` (+ hijos).
- **Estado**: existe renderer v1 funcional (`renderer/dayz_layout_render.py`) pero
  con 15 bugs catalogados y hardcodeado a LFPG. Plan v2 de **reescritura +
  generalizaciÃ³n** redactado (`plans/2026-05-14-renderer-v2-reescritura.md`) y
  revisado por Codex (handoff convergente).
- **DecisiÃ³n abierta**: arquitectura del renderer A/B/C (Pythonâ†’HTML estÃ¡tico /
  Pythonâ†’JSONâ†’visor / JSON+resolver en JS). Bloquea Fase 0.
- **Bug crÃ­tico v1**: `visible 0` se ignora â†’ todos los overlays/paneles ocultos
  se renderizan superpuestos. MÃ¡s el hardcoding de LFPG en un tool "genÃ©rico".
- **Canal de comentarios Claudeâ†”Codex**: [`reviews/ui-renderer-plan-comments.md`](DayZ_UI_Research/reviews/ui-renderer-plan-comments.md)
  (formato `[CODEX|CLAUDE] [P0-P3] [agree/disagree/question] archivo:linea â€” â€¦`).
- **Incorporado al pipeline** 2026-05-14 (CLAUDE.md + memoria + plan + review inbox).

## GPS â€” mod de rutas (`LBGroups_GPS` + SDK `RoadGraph_Core`)

- **Rutas**: `â€¦\Claude\Projects\GPS\`. Handoff vigente
  `HANDOFF_2026-04-28_v4.md`, spec `WRP_V29_FORMAT.md`.
- **Estado**: mod V1 feature-complete (M1â€“M5, D9â€“D11). 9 mapas extraÃ­dos
  (chernarusplus, enoch, banov, deerisle, deadfall, namalsk + chernarus2035, onforin, iztek) con calidad
  84â€“98 % de conectividad. Pendiente de test in-game completo.
- **Estado (2026-07-19)**: V2 object-roads CERRADO. +Takistan (v28) y TakistanPlus (v29) por objetos = 11 mapas soportados y desplegados. Modo ROAD arreglado (artefacto de Y en el subgrafo pavimentado, `_apply_road_connect`). Pipeline V2 multi-mapa. Publicado por el usuario. Detalle: `30_Sessions/2026-07-19-gps-roadgraph-takistan-takistanplus.md` + auto-memoria `gps-roadgraph-project`. LL-205/206/207.
- **Estado (2026-09-04)**: **18 mapas**, lista cerrada para el release. +antoria (2026-09-03), +valning y +takistansequel (2026-09-04). Valning: V1 Roadnet, OPRW v28, 163,6 km, top-1 98,4%. **Takistan Sequel NO es un mapa nuevo**: es un override de terreno que declara la misma clase `CfgWorlds` que TakistanPlus, y sus redes difieren (84,2% compartido, 40,3% de la suya es nueva), asi que se sirven los dos desambiguando por `FileExist` del prefijo del override. Arreglado un fallo SILENCIOSO del localizador de objetos del V2 (devolvia 1 objeto para un terreno de 87 MB), con gate de regresion contra los dos mapas V2 ya publicados. **Bloqueado por la firma**: los dos `.bisign` son del 19-jul. Nada probado in-game. Detalle: `30_Sessions/2026-09-04-gps-valning-y-takistan-sequel.md`. LL-435 rev.
- **Proceso de extracciÃ³n**: documentado en
  [`AI/20_Runbooks/dayz-wrp-road-graph-extraction.md`](../20_Runbooks/dayz-wrp-road-graph-extraction.md).
- **En curso**: una sesiÃ³n paralela estÃ¡ reconstruyendo los scripts de los
  pases de conectividad (`fase2_5_road_connector.py` y el parser de la
  Object section) que se reconstruyeron el 2026-05-14 (`apply_connectivity_passes.py` + `wrp_object_parser.py`, en `extractor/`) y se empaquetaron en la skill `dayz-roadgraph-extraction`.
- **LimitaciÃ³n V1**: el parser solo lee la secciÃ³n Roadnet; vÃ­as de tren y
  puentes custom (Object section) son el bloque de V2.

## LF-COM â€” mod de "red social de fotos" in-game

- **Memoria**: [`project-brief.md`](LF-COM/project-brief.md).
- **Rutas**: planning en `â€¦\DayZ Projects\_LFCOM_Planning\`
  (`LFCOM_HANDOFF_SESION_1.md`, spikes de validaciÃ³n).
- **Veredicto cerrado**: NO se pueden capturar pÃ­xeles desde un mod puro de
  DayZ. Ver [`AI/20_Knowledge/dayz-capacidades-verificadas.md`](../20_Knowledge/dayz-capacidades-verificadas.md).
- **Arquitectura final**: PBO + launcher companion `.exe` + backend web.
  El launcher convierte PNGâ†’EDDS y el mod los carga con `LoadImageFile`.

- **Estado (2026-08-26; evidencia posterior al `LIVE-STATE`)**: el `LIVE-STATE` del
  `HANDOFF.md` sigue anclado al 15-ago y queda marcado **STALE** frente a la evidencia
  del 26-ago. La corrida F0 **A-SOLO** de las 12:08 Madrid terminó
  **SETUP-FAILED**; el verificador inicial devolvió `3` y no se emitió ningún
  `F0_GATE` terminal. **No es `F0-A-SOLO-DONE`.**
- **Detalle del fallo**: M0.4 no produjo shutter (`raised_samples = 0`) y el run 2
  registró AV `0xc0000005` en `M01_FALLBACK`. El gate sigue siendo repetir F0 con
  el setup corregido; **no iniciar Phase J**. Fuentes:
  `C:\Users\guill\OneDrive\Documentos\DayZ Projects\LFCOM_dev\HANDOFF.md` y
  `C:\Users\guill\OneDrive\Documentos\DayZ Projects\_LFCOM_Planning\evidence\slice2-f0-20260826-112241\f0-verdict.md`.

## Crate â€” mod de caja destructible

- **Rutas**: mod en `DayZ Projects\Crate\`; artefactos (handoffs, patches
  de skills, viewers 3D, renders) en `DayZ Projects\CrateFiles\`.
  ConvenciÃ³n: no mezclar archivos de proyecto con assets vanilla del juego.
- **Estado**: feasibility resuelta; gotchas de fÃ­sica documentados en
  [`AI/20_Knowledge/dayz-capacidades-verificadas.md`](../20_Knowledge/dayz-capacidades-verificadas.md) (`ECE_CREATEPHYSICS`
  vs `ThrowPhysically`, regla 0.5 m, FireGeo necesario para recibir balas).

## LF_Transfer / Maplink â€” orquestador de clusters + mod de transferencia

- **Rutas**: `â€¦\Claude\Projects\Maplink\` (mod `LF_Transfer/` + servidor
  `lf-orchestrator/`).
- **Stack**: backend Python con **Pydantic v2** + admin UI HTML; mod
  Enforce Script. El orquestador es opcional: el mod debe funcionar
  plug-and-play con el orquestador caÃ­do (pre-load de cache en `OnInit`).
- `start_orchestrator.bat` autosuficiente (verifica Python 3.10+, crea
  venv, instala `requirements.txt`, lanza `app.py`).
- **Estado (2026-05-16)**: Phase 1 review loop CERRADO con convergencia
  iter 3. Plan C1 L5c admin bypass shipped por Codex. Plan C2 L5b shipped
  (cost-only V1.0): schema currency/cost, server-authoritative validation,
  wire-safe debit y mod-side UI/RPC/REST integrados. `test_e2e.py` 33/33
  PASS. Fase 1
  invariantes 12/12 PRESENT, MapLink M1-M7 7/7 HOLDS, 0 regresiones.
  BASELINE.md vivo en `Projects/Maplink/BASELINE.md` con Â§6 Resolved.
- **Memoria de proyecto en pipeline**: `AI/10_Projects/Maplink/` con
  skeleton completo (project-brief, verified-apis, assumptions,
  validation-matrix, bug-ledger, decision-log).
- **Plans listos / estado Codex (2026-05-16)**:
  - [`plans/2026-05-16-plan-a-orchestrator-quality.md`](Maplink/plans/2026-05-16-plan-a-orchestrator-quality.md) (N4, NF2-Â§2-5,
    NF2-Â§4-N9, OBS2)
  - [`plans/2026-05-16-plan-b-mod-completeness.md`](Maplink/plans/2026-05-16-plan-b-mod-completeness.md) (L1, L2, L4,
    NF2-Â§1-3, NF2-Â§1-6)
  - [`plans/2026-05-16-plan-c1-l5c-admin-bypass.md`](Maplink/plans/2026-05-16-plan-c1-l5c-admin-bypass.md) (L5c) - shipped
  - [`plans/2026-05-16-plan-c2-l5b-currency.md`](Maplink/plans/2026-05-16-plan-c2-l5b-currency.md) (L5b) - shipped
    cost-only V1.0; action-on-object parked a V1.1
  - [`plans/2026-05-16-plan-c3-l5a-cooldown.md`](Maplink/plans/2026-05-16-plan-c3-l5a-cooldown.md) (L5a)
- **Prioridad acordada**: Admin > Currency > Cooldown (L5c â†’ L5b â†’ L5a),
  Plan A y Plan B en paralelo cuando los L5 estÃ©n planeados.

## ContribuciÃ³n a Agentic-Z (skills de la comunidad)

- 3 PRs pusheados a `willy92wins/Agentic-Z`, **pendientes de mergear**.
- MCP `dayz-rag`: plugin `agentic-z@dayz-n-chill`. Requiere Voyage AI key
  en `.env` e Ã­ndice prefab (`/dayz-search-download`, ~200 MB).

## Wrapper de agente IA descentralizado (proyecto de diseÃ±o)

- **Killer domain elegido**: refactoring Python multi-archivo, benchmark
  **RefactorBench** (gap LLM 22 % vs humano 87 % â€” el mayor documentado).
- Arquitectura acordada: IRA con sub-templates, "anillo verde" de 6
  verificadores, KG schema "RefactorPattern". Synthesis Engine rechazado;
  ConductLearner a fase 2.
- **Estado**: diseÃ±o sÃ³lido; las specs concretas de tareas se validan en
  Sprint 0 (un agente delegado confabulÃ³ nombres de tareas â€” verificar).

## Server DayZ (operaciÃ³n)

- Server en `C:\Agent\deployments\DeerIsle\`, gestionado con **CFTools
  Architect**. DayZ `1.29.x`. Mods: Expansion, LBmaster.
- Herramientas de reinicio en `â€¦\DayZ Projects\CrateFiles\DayZRestartTools\`
  (scheduled tasks como SYSTEM, force-kill + reinicio cada 3 h).
- **Gotcha Windows Server**: `/SC ONDEMAND` falla en muchos Windows Server
  â†’ usar `/SC ONCE /ST 00:00 /SD 01/01/2099` (disparable con `schtasks /run`).

## DayZ_Tooling â€” linter pre-PBO y herramientas cross-mod

Proyecto cross-mod (no encaja en LF_PowerGrid ni LF_VStorage). Primer
entregable: linter pre-PBO de "backpressure mecÃ¡nica" inspirado en
harness engineering.

- **Rutas**: memoria en `AI/10_Projects/DayZ_Tooling/`. CÃ³digo del piloto
  vivirÃ¡ en `DayZ_Tooling/scripts/` (a definir cuando se cree el repo).
- **Stack**: Python 3.x stdlib, sin dependencias externas.
- **Estado (2026-05-17)**: fase 0 (research dual) cerrada; ADR 001
  aceptado (contribuciÃ³n a `dayz-pbo-build` con `script_validator.py`
  nuevo, piloto en `DayZ_Tooling/scripts/`, promociÃ³n explÃ­cita al
  cerrar piloto); plan fase 1 v2 cerrado en
  [`plans/2026-05-17-linter-pre-pbo.md`](DayZ_Tooling/plans/2026-05-17-linter-pre-pbo.md) tras **R22 cerrada** (revisiÃ³n
  vÃ­a ChatGPT, 11/11 hallazgos aplicados, cero P0). Listo para fase
  de implementaciÃ³n. Top-5 cerrado: `RVMAT-NO-NORMALMAPMACRO`,
  `ES-CTX-READ-UNCHECKED` (severidad mixta), `ES-SYNCVAR-CONTRACT`,
  `ES-NO-DELETE`, `ES-EMPTY-IFDEF`.
- **Hallazgo clave (CONFLICT-3)**: `dayz-pbo-build` no tiene `.py`
  runnables; los 4 validators viven embebidos en
  `references/validation-scripts.md`. Cobertura runnable real = 0%
  documental â‰  ejecutable. Anexado a `verified-apis.md`.
- **BUG-001** (drift entre copias de skills DayZ â€” ruta Cowork vs ruta
  Codex) abierto, va por carril separado (deuda de pipeline). El plan
  del linter convive con el drift sin sufrirlo (fuente Ãºnica = ruta
  Cowork para fase 1).
- **BUG-002** (drift en `dayz-p3d-audit/audit_p3d.py` con `GeoPhys` y
  `FireGeo`) abierto, no afecta fase 1 (no se invoca `audit_p3d.py`).
- **Handoff vivo**: [`30_Sessions/2026-05-17-DayZ_Tooling-linter-fase-1.md`](../30_Sessions/2026-05-17-DayZ_Tooling-linter-fase-1.md).

- **Estado (2026-06-06, py3d fork)**: segundo entregable cerrado en codigo: fork local de
  py3d **1.2.0** (S1 46/46 + S2 115/115; guards anti-corrupcion, helpers F2, validate()
  v1.2.0, CLI `python -m py3d`, gates INTEG PASS). Entregado en
  `LF_RollingStone_dev/_tools/py3d/` (arbol+bundle+wheel+rollout). PENDIENTE host:
  aplicar `rollout/` a los 2 roots de skills (BUG-001) + refrescar `P:\py3d`.
  Handoffs `30_Sessions/2026-06-06-DayZ_Tooling-py3d-fork-s{1,2}.md`; STATUS.md seccion nueva.
## Expansion_Study â€” estudio de DayZ Expansion para enriquecer skills **NEW 2026-05-20**

Research dual (fase 0, R24) sobre el mod mÃ¡s grande de DayZ para nutrir
`enforce-script-reference`, `dayz-ui-development` y notas de "trucos". Entregable
acordado: **knowledge-notes-first, luego parches**.

- **Memoria/research**: `AI/10_Projects/Expansion_Study/research/`. Empezar por
  [`_synthesis-claude-arm.md`](Expansion_Study/research/_synthesis-claude-arm.md) + [`_module-map.md`](Expansion_Study/research/_module-map.md).
- **Fuente**: clon open-source `salutesh/DayZ-Expansion-Scripts`, rama `release`,
  commit `8f75d554`. âš ï¸ Puede divergir de la versiÃ³n instalada en el server.
- **Estado 2026-05-20 (research dual CERRADO)**: ambos brazos completos y reconciliados
  para los 6 mÃ³dulos. Empezar por [`_synthesis-final.md`](Expansion_Study/research/_synthesis-final.md). VerificaciÃ³n anti-confabulaciÃ³n
  acumulada: **69/69 citas muestreadas OK, 0 confabulaciones** (19 Claude + 18 auditorÃ­a
  mÃ­a de los consolidados de Codex + 32 codex-only de los agentes). El cap 8â€“15 + excerpt
  verbatim + clon grepeable validado en ambos brazos.
- **Por mÃ³dulo** (patrones / solape R24 / skill): Core 21/60%/no Â· AI 20/33%/**sÃ­
  `dayz-ai-patterns`** Â· Vehicles ~15/n-d/no Â· BaseBuilding ~12/60%/no Â· Market 18/66.7%/no
  (+reference file) Â· Quests 14/n-d/no. Solapes 33â€“66.7% â‰ª 90% â†’ mantener dual (R24).
- **Reparto de parches**: ~57+ â†’ enforce-script-reference (capa RPC propia, SyncVars,
  CF_ModStorage+versioning, bit-packing, server-authoritative, EXTrace, + perf de AI:
  scheduler/backoff/throttling FPS/rolling-average); ~13â€“18 â†’ dayz-ui-development (MVC
  propio + reference `expansion-market-menu-pattern.md`).
- **"El de muebles" = BaseBuilding** (confirmado).
- **Skill nueva**: Ãºnica candidata real = **`dayz-ai-patterns`** (arquitectura IA
  irreductible: FSM, pathfinding, grupos, threat, LOS; la perf va a enforce, es
  transversal). **DecisiÃ³n del usuario pendiente** (sÃ­/no crear).
- **Gotcha de sesiÃ³n**: Codex guardÃ³ `Market-codex.md` en `DayZ_UI_Research/research/`
  (proyecto equivocado) â†’ reubicado. Y no calculÃ³ solape R24 en Vehicles/Quests.
- **Skills ENTREGADAS (2026-05-20)**: las 3 empaquetadas con el gestor (validadas <1024
  chars de description) en `Expansion_Study/skill-packages/`:
  - [`dayz-ai-patterns.skill`](Expansion_Study/skill-packages/dayz-ai-patterns.skill) (NUEVA â€” FSM, pathfinding, grupos, threat, LOS; perf fue a enforce).
  - [`dayz-ui-development.skill`](Expansion_Study/skill-packages/dayz-ui-development.skill) (ampliada: `references/expansion-mvc-patterns.md` +
    `expansion-market-menu-pattern.md`).
  - [`enforce-script-reference.skill`](Expansion_Study/skill-packages/enforce-script-reference.skill) (ampliada: `references/expansion-framework-patterns.md` +
    `expansion-server-performance.md`).
  - Ediciones aditivas (R20): solo se aÃ±adieron references + puntero + description; sin reescribir.
  - **Pendiente de INSTALAR por el usuario** (copiar los `.skill` a la carpeta de skills).
- **Vehicles enrutado**: consolidado copiado a [`DayZ_Vehicle_Skill/research/2026-05-20-expansion-vehicles-patterns.md`](DayZ_Vehicle_Skill/research/2026-05-20-expansion-vehicles-patterns.md)
  + nota [`_expansion-study-import.md`](DayZ_Vehicle_Skill/research/_expansion-study-import.md). Lo transversal quedÃ³ en enforce; lo vehÃ­culo-especÃ­fico, ahÃ­.
- **Handoffs**: [`30_Sessions/2026-05-20-expansion-study-research-dual-claude-arm.md`](../30_Sessions/2026-05-20-expansion-study-research-dual-claude-arm.md)
  (sesiÃ³n 1) + `...-reconciliacion.md` (sesiÃ³n 2) + `...-skills-empaquetado.md` (sesiÃ³n 3).

## BRDK_BRDM_2 - PBO recovery and KGB deobfuscation

Recuperacion legitima de fuente de mod DayZ propio a partir de PBOs sin source
disponible.

- **Memoria**: `AI/10_Projects/BRDK_BRDM_2/`.
- **Estado 2026-05-19**: primera capa PBO/JAPM cubierta por
  `japm-pbo-recovery`; segundo layer KGB_DF v2 documentado en ADR-002 con
  10,713/11,354 bloques resueltos y 641 residuales. Skill
  `kgb-deobfuscator` promoted to plugin package:
  `C:\tmp\kgb-deobfuscator.skill` y copia en
  `C:\tmp\outputs\kgb-deobfuscator.skill`.
- **Pendiente**: instalacion manual del `.skill` en la carpeta de skills y
  backlog separado para renombrado de identificadores `BRDK_BRDM_2_*`.

## Skills propias y reglas de Claude

- **`C:\Users\guill\.claude\CLAUDE.md`** â€” reglas globales R1â€“R28+,
  construidas incrementalmente vÃ­a sesiones de "Introspection". Cubren
  severidad, no confabular APIs, no usar muletillas, alternativa simple
  primero, usar AskUserQuestion para aprobaciones (R28), etc.
- **`LFPG_WORKFLOW_RULES.md`** (`.claude/skills/`) â€” regla de oro: NUNCA
  tocar el repo. Los cambios van a `P:\LFPowerGrid` (pruebas), el usuario
  prueba y solo Ã©l pasa al repo. Outputs en `â€¦\Claude\LFPowerGrid`.
- **Skills propias creadas**: `secrets-handling` (raÃ­z: un PAT de GitHub
  pegado en un chat), `japm-pbo-recovery`, `dayz-p3d-inspector`,
  `rigorous-data-audit`.
- **`dayz-animation-pipeline` (DRAFT, en curso 2026-05-20)**: pipeline de
  animaciÃ³n DayZ espectro completo (config-driven + skeletal RTM/`.anm`).
  Draft + 6 references + 2 scripts (self-test PASS) en
  `AI/20_Knowledge/skills-drafts/dayz-animation-pipeline/`. Falta evals +
  empaquetado `.skill`. Feasibility en [`dayz-capacidades-verificadas.md`](../20_Knowledge/dayz-capacidades-verificadas.md).
  Handoff: [`30_Sessions/2026-05-20-dayz-animation-pipeline-skill-draft.md`](../30_Sessions/2026-05-20-dayz-animation-pipeline-skill-draft.md).
- âš ï¸ **El audit de skills DayZ del ~2026-05-10 saliÃ³ ~55 % confabulado**
  (evento PASADO, no defecto de la skill): un pipeline de 4 agentes produjo
  un `index.md` con ~248 "hechos"; al re-verificar a mano los 11 hallazgos
  crÃ­ticos eran 6 confabulados / 2 reales / 3 exagerados. **No confundir con
  la skill `rigorous-data-audit`**: la skill se creÃ³/endureciÃ³ *a raÃ­z* de ese
  postmortem y es el remedio, no la causa â€” su Step 3 (3a cita literal, 3b
  verificador independiente sin contexto compartido, 3c muestreo 20 %) existe
  precisamente para prevenir esa clase de fallo. AcciÃ³n vigente: si una sesiÃ³n
  futura cita un hallazgo de *aquel audit de 2026-05-10*, verificar contra
  archivo real antes de actuar. Doctrina:
  [`AI/20_Knowledge/verificacion-outputs-multi-agente.md`](../20_Knowledge/verificacion-outputs-multi-agente.md); postmortem de origen:
  `â€¦\LF_VStorage_dev\skills\rigorous-data-audit\postmortem.md`.

## Otros (no DayZ)

- **Agente de consultas agrÃ­colas**: entregable
  `base_conocimiento_agente_agricola.md` (proyecto cliente separado).
- **Mazos de Magic (MTG)**: hobby personal, no se consolida salvo peticiÃ³n.

## Relacionado

- [`AI/20_Runbooks/dayz-wrp-road-graph-extraction.md`](../20_Runbooks/dayz-wrp-road-graph-extraction.md)
- [`AI/20_Knowledge/cowork-entorno-y-tooling-gotchas.md`](../20_Knowledge/cowork-entorno-y-tooling-gotchas.md)
- [`AI/20_Knowledge/dayz-capacidades-verificadas.md`](../20_Knowledge/dayz-capacidades-verificadas.md)
- [`AI/20_Knowledge/dayz-modded-class-server-stub-pattern.md`](../20_Knowledge/dayz-modded-class-server-stub-pattern.md)
- [`AI/00_System/workflow.md`](../00_System/workflow.md)


## LFQuad (added 2026-05-23)
Quad DayZ: cuerpo Yamaha Banshee (mod LMs/llama) + suspensión carácter FC_Brabus + ruedas desmontables tipo Croco + stats conducción mejorados.
**Estado**: modelo + color rojo/negro + acabado PBR **cerrados y validados offline** (3 `.p3d` + 14 `.rvmat` en `P:\LFQuad`; visor + editor de encaje en `P:\LFQuad_dev`). **Pendiente**: integración (config.cpp / model.cfg / proxies de rueda / colisión / LOD1-3) → test in-game.
**Memoria**: `P:\LFQuad_dev\HANDOFF.md` (detalle) + [`30_Sessions/2026-05-23-LFQuad-modelo-color-acabado.md`](../30_Sessions/2026-05-23-LFQuad-modelo-color-acabado.md). Lecciones: LL-020/021/022.
**2026-05-23 (cont.)**: p3d rotados a -Z front (match Croco); crew/pos horneados en Memory LOD; anim soft-dep resuelta (driver pose = ConfigIsExisting SurvivorAnims ? 22 : V3S). Vault 6-tupla creado en `AI/10_Projects/LFQuad/`. Plan `LFQuad_dev/plans/2026-05-23-lfquad-integration.md`; handoff [`30_Sessions/2026-05-23-LFQuad-integracion-anim-softdep.md`](../30_Sessions/2026-05-23-LFQuad-integracion-anim-softdep.md). Lección LL-023. Pendiente Fases B-F (proxies/LODs/Geometry/config.cpp/model.cfg/test).
**Próximo**: debinarizar Croco `quadbike.p3d` → crewDriver/pos_driver reales → fit editor → hornear → integración.
**2026-05-23 (cont. 2)**: Fases **B+C+C.5 hechas y verificadas** (verify_c5.py 169/169). .p3d integrado: 4 proxies path-fix (proxy:LFQuad\LFQuad_wheel_front/rear.p3d.NNN) miembros de rotación+damper+turn, 12 memory axes 2pt + seat_con_1_1/2_1, Geometry convex (290/576), selección "color"=B_WHITE. Matriz contrato `LFQuad_dev/plans/2026-05-23-faseC5-p3d-modelcfg-matrix.md`; R22 de Codex + respuesta en `LFQuad_dev/reviews/codex-review-inbox.md`. Decisiones D9-D15; lecciones LL-024/025; SP-008. **Pendiente**: Fase D/E (Codex, config.cpp+scripts/4_world+model.cfg) usando la matriz; esquemas de color de variantes; Fase F (audit+pbo-build+test in-game R5).
**2026-05-24 (cont. 3)**: Gate post-C.9 resuelto con RPT `02:58:32`: **C.9 confirmado in-game** (wheel-geo + create blockers fuera; el quad se crea). **F1.B descartada** (sin fallo de attach de rueda). Blocker nuevo = crew proxies (`crewdriver`/`crewcodriver`) faltan en un ViewGeometry LOD (config los pide como proxyPos; LFQuad solo los tiene como memory points). **F2 Parity Audit (mitad Claude)** hecha: [`research/2026-05-24-parity-audit-civiliansedan-claude.md`](LFQuad/research/2026-05-24-parity-audit-civiliansedan-claude.md) con checklist maestro de gaps (A ViewGeo+crew=blocker, B FireGeo, C luces, D dano+wreck, E anim-sources; sedan **sin LandContact**). D18, LL-031. **Pendiente**: Codex hace su mitad del research dual F2 (`-codex.md`) -> consolidar -> F3 (ViewGeometry LOD + crew proxies).
**2026-05-25**: get-in C.11 ✅. **Luces faro delantero** (cono + lente emisiva) implementado+build+firmado (pendiente deploy+in-game). **Repostaje** arreglado (causa real: `refill` debía ser selección en ViewGeometry, no solo memory point; +`GetActionDistanceFuel`+`OnDebugSpawn`) — portado a `P:\LFQuad` (modelo `36aa31e5`). **CRASH P1 hallado** (RPT): sin `DamageSystem` → `No DamageSystemData`. **Auditoría exhaustiva vs contrato** → `reviews/2026-05-25-auditoria-contrato-completa-sprint.md`, segmentada en 4 sprints; **Sprint 0 (estabilizar) spec listo para Codex** `reviews/2026-05-25-sprint0-estabilizar-codex.md`. Handoffs [`30_Sessions/2026-05-25-LFQuad-luces-faro-delantero.md`](../30_Sessions/2026-05-25-LFQuad-luces-faro-delantero.md) + `...-repostaje-damagesystem-audit-sprint.md`. Lecciones LL-039/040/041; R31; SP-010. **Pendiente**: Sprint 0 (Codex, mata crash) → Sprint 1 (luces completas) → Sprint 2 (daño+FireGeometry, el grande, sesión nueva) → Sprint 3 (paridad+tuning). El "bote/desync" sin causa probada (RPT limpio de física).
**2026-05-26**: **Sprint 2 (daño+FireGeo) verificado offline** — R21 PASS por reproducible-build (body `0fd7d790…`), DamageZones 7 zonas + FireGeo daño; decisiones D21-D24 (zonas mín / wreck diferido S3 / efectos 2 básicos / healthLevels `{}`); Paso 4 HideDestroyed dropeado (NO-OP). Prep offline S1 luces + Paso 5 partículas. **GATE IN-GAME**: gasolina/encendido/escape ✅ (refill confirmado); **P1 BLOCKER N2**: quad enterrado + no se mueve + ruedas no giran. **RCA**: FireGeometry **sin proxies de slot de rueda** (= criterio **N2.1**, gated y nunca implementado; F1.B descartada prematuramente en D18 porque el fallo solo aparece al CONDUCIR). Fix-spec listo: [`research/2026-05-26-fix-firegeo-wheel-proxies-claude.md`](LFQuad/research/2026-05-26-fix-firegeo-wheel-proxies-claude.md) (replicar los 4 wheel-proxies de VIS0 en la FireGeo). Notas research: [`2026-05-26-parity-damage-firegeo-claude.md`](LFQuad/research/2026-05-26-parity-damage-firegeo-claude.md), `-parity-lights-claude.md`, `-paso5-particles-prep-claude.md`, `-fix-firegeo-wheel-proxies-claude.md`. Handoff [`30_Sessions/2026-05-26-LFQuad-sprint2-R21-gate-rca-wheelproxy.md`](../30_Sessions/2026-05-26-LFQuad-sprint2-R21-gate-rca-wheelproxy.md). Lecciones **LL-039** (RPT multi-mod red herring) + **LL-040** (no descartar gated por ausencia de error no testeado). **Pendiente**: sesión correctiva N2.1 (bake proxies → R21 → gate in-game) ANTES de retomar S1/S5. ⚠️ Drift de numeración: la línea 2026-05-25 referencia "LL-039/040/041" que nunca se escribieron; LL-039/040 ahora usadas para ESTA sesión (contador lessons-learned = autoridad). Reconciliar (PB-007).
**2026-05-29/30**: arc bounce/`contact=0` → **reframe doc-grounded**. Refutados in-game: T1-D wheel-Memory, `class=vehicle`, D4H, suspensión blanda, ride-height ROUND-1 (insuficiente). **Causa raíz (doc-grounded, VIVO):** la Geometry es 1 componente monolítico (`component01`, ~90% de la masa) en vez del compuesto multi-convexo de un coche real (Croco 23+4) → impulso de depenetración PhysX (trigger) + inercia baja Izz 128.5 = 37% Croco (amplificador). Doc-research (Bohemia LOD/Vehicle_Configuration/Validating_Geometries + NVIDIA PhysX "Overlapping objects explode") + parse del tutorial paso-a-paso **Tyson89/Landrover** (wiki+repo). **Encodeado:** `dayz-model-pipeline` Addendum 2026-05-30 (canon de construcción + wiki Landrover citada como referencia) + `dayz-p3d-audit` Killer #13; `.skill` reempaquetados en outputs; patches `LFQuad_dev/skill_patches/2026-05-30-landrover/`; research [`research/2026-05-30-landrover-car-build-reference.md`](LFQuad/research/2026-05-30-landrover-car-build-reference.md); LL-062/063. Handoffs [`30_Sessions/2026-05-29-lfquad-contact0-decision-rideheight-skillencode.md`](../30_Sessions/2026-05-29-lfquad-contact0-decision-rideheight-skillencode.md) + [`2026-05-30-lfquad-landrover-canon-carbuild-reframe.md`](../30_Sessions/2026-05-30-lfquad-landrover-canon-carbuild-reframe.md). **Pendiente**: (a) spec ROUND-2 (geometry multi-componente + masa repartida + `autocenter=0`/comp + revert D4H + ride-height ROUND-1, R26 vs Croco/sedán); (b) sub-tarea aparte: skill de coches end-to-end (gap-fill completo `dayz-model-pipeline`), prompt de arranque entregado 2026-05-30. Causal con el bote `[verify in-game]` (R31); divergencia de construcción verificada a 3 referentes.
**2026-05-30 (cont.)**: **spec ROUND-2 escrito** (`outputs/2026-05-30-LFQuad-ROUND2-multicomponent-geometry-codex.md` → destino `LFQuad_dev/plans/`): SOLO la Geometry LOD del body — `component01` monolítico → varios convexos cerrados + masa repartida + wheel-wells + revert D4H (X±0.175→±0.275) + `autocenter=0`/comp + CoM.z corregido + Izz↑ + ride-height ROUND-1; todo lo demás byte-idéntico (R20). R26 A-F (Killer #13 + inercia + holgura + no-regresión + toolchain + gate in-game). **Bifurcaciones (grill):** py3d Geometry-LOD-only espejando el Croco extraído / corregir CoM.z / **gate duro Izz≥300**. **Veredicto: NO mejorar el debinarizer** — la Geometry del Croco ya está extraída y usable (`croco_extracted/quadbike_mlod.p3d`, SP-013/014/015 applied 2026-05-27); gap residual solo en LODs visuales (verificado, subagente Opus). Handoff [`30_Sessions/2026-05-30-LFQuad-round2-spec-y-debinarizer-verdict.md`](../30_Sessions/2026-05-30-LFQuad-round2-spec-y-debinarizer-verdict.md); LL-064; patch staged de skill (`outputs/2026-05-30-vehicle-structural-parity-debinarizer-correction-PATCH.md`). **Pendiente**: sesión de REVISIÓN en limpio (spec ↔ skill ↔ wiki Landrover; R22 previa) → Codex implementa (R20).

**2026-08-24 (`LIVE-STATE`)**: gate UV humano ejecutado; los 16 atlas fueron
rechazados, incluido el de baja deformación. El carril vigente separa atlas A
(pintura) y B (mecánica) y usa proyección ortográfica por vista dominante, con
recuento objetivo de 11-15 islas solo para A. Fuente autoritativa:
`C:\Users\guill\OneDrive\Documentos\DayZ Projects\LFQuad_dev\HANDOFF.md`.

**2026-08-27 (nota posterior al LIVE)**: entregado el primer `_nohq` por modelo del
cuerpo: `LFQuad_body_nohq_DX.png`, **4096², 16 bit, tangent-space DirectX (Y−)**,
con copia GL y el blend del atlas A. También quedó el selector autónomo
`LFQuad_selector.html`, con **544 piezas clicables**. El alcance sigue siendo solo
`B_WHITE` (carrocería + muelles, 18,85 % de los polígonos del quad); faltan los demás
grupos, con ruedas aparte, verificar DirectX in-game y pintar el atlas. Fuente:
`C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-08-27-LFQuad-nohq-bake-y-selector.md`.

**2026-09-02 (`LIVE-STATE`)**: cerrado el blocker de destino que arrastraba desde
el 27-ago. Los **dos LOD visuales de la malla que se envia** (`LFQuad_body.p3d`,
38.831 + 15.422 caras) desplegados sobre **una sola hoja de 4096 en zonas
disjuntas**, reparto 75/25: **0,00 % de caras colapsadas y 0 pares SAT** en cada
uno, 0 cruzados entre ellos, a 349 y 204 px/m. Cambio **solo de UV** — puntos,
topologia, materiales y selecciones identicos en los seis LOD. `_nohq` horneado
de los dos LOD, `_smdi` desde intencion PBR por material y **13 `.rvmat` al
shader `Super`** muestreando el atlas 1:1 (se acabo el tileado x4). **8 de 10
puertas selladas**; quedan **G9** (reempaquetar: falta el `include.lst` y la
clave de firma, y el mod tiene dos PBO divergentes con el viejo desplegado) y
**G10** in-game. Nada esta pintado todavia. Sin PBR nativo: MatPBR es namespace
de Reforger, confirmado por dos lanes independientes. Fuente: `C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-09-02-LFQuad-atlas-compartido-multi-lod.md`.

## LFQuad2 -> **Arma2Quad** (renombrado 2026-09-09; carpeta vault sigue `LFQuad2/` hasta migracion) (added 2026-08-29)
**Update 2026-09-09/11**: renombrado operativo a **Arma2Quad** (ex LFQuad2). Tablero slug `lfquad2` -> LIVE-STATE `Arma2Quad (ex LFQuad2) 2026-09-11 16:40`. Carpeta `10_Projects/LFQuad2/` y `P:\LFQuad2_dev` conservan nombre viejo (NO renombrar aqui). Handoff: [`30_Sessions/2026-09-09-arma2quad-renombrado-y-hundimiento.md`](../30_Sessions/2026-09-09-arma2quad-renombrado-y-hundimiento.md).
Segundo quad DayZ: port del **ATV de Arma 2: Operation Arrowhead**. Nace porque LFQuad lleva bloqueado en el UV desde julio y este asset **ya trae UV y texturas hechas**. Licencia **DPL** (atribucion + no comercial, sin share-alike).
**Estado**: **el vehículo NACE in-game** (2026-08-29 15:30): `CreateObjectEx` devuelve el objeto con 4 ruedas y depósito lleno. El bloqueo eran los cuatro `wheel_N_M_damper_land` en el LOD LandContact en vez de Geometry — y `G15` medía el LOD equivocado. Cirugía H01–H07 aplicada, PBO reconstruido (29 entradas, crudo). **15 de 17 puertas**; `G19`/`G23`/`G24` rojas **por alcance** (los 15 cosméticos H08–H22 quedan fuera). **Pendiente**: G13 apariencia y G14 tacto, ambas manuales y en curso; primer sospechoso si la suspensión falla es el tamaño del buje (la rueda entera, 0,60 m, contra 0,22 m del referente). La firma sigue siendo deuda separada.
**Memoria**: `P:\LFQuad2_dev\HANDOFF.md` (estado vivo) + `P:\LFQuad2_dev\GATES.md` (criterio de terminado, ejecutable) + [`30_Sessions/2026-08-29-LFQuad2-cadena-delegada-por-etapas.md`](../30_Sessions/2026-08-29-LFQuad2-cadena-delegada-por-etapas.md) + [`30_Sessions/2026-08-29-LFQuad2-cirugia-y-primer-arranque.md`](../30_Sessions/2026-08-29-LFQuad2-cirugia-y-primer-arranque.md). Informes de la sesión: `LFQuad2_dev\_chain\PARITY-AUDIT-20260829.md` y `CIRUGIA-20260829.md`. Capa de proyecto completa en `LFQuad2/`.

**2026-08-28**: Council de 7 lanes sobre como importar. **Cuello de botella roto**: el `.p3d` era ODOL v49 y el debinarizador moria en `Skeleton.read` por 5 bytes de desfase (3 campos DayZ-only sin guardia de version); diagnostico dado **en paralelo y a ciegas** por Grok y Fable. Parche en la herramienta compartida con regresion 54/54. Licencia resuelta a DPL (la desatasco el usuario). Materiales decididos por medicion: DayZ shippea **3.074 `_smdi` contra 31 `_sm`**. Ronda 1 de integracion RECHAZADA por Codex con 6 P1, tres causados por el brief. Plan publicado como artefacto.

**2026-08-29**: Cadena delegada por etapas (Grok implementa, Codex revisa, puerta entre etapas) hasta el PBO. **E1** censo y paridad en 5 rondas: instrumento MLOD **sin py3d**, 15 clases de defecto, certificado de automorfismo para el residuo irreducible. **F3** adelantada por delante de la cirugia tras una pregunta del usuario: **el MLOD binariza**. **E2a** en 5 rondas: recupera la membresia visual invirtiendo `vertex_bone_ref` (no estaba perdida, se hornea al binarizar); **promovido a la herramienta compartida** con dos regresiones limpias (54 ODOL del revisor + 60 de 8.163 vanilla mios). **E2b** cirugia: 6 puertas de golpe. **E4/E4b** config, `model.cfg`, subclase Enforce y luces emisivas. Masa copiada del LFQuad (1500 kg) porque **en DayZ la masa vive en el TAGG `#Mass#` del p3d, no en el config**. Empaquetado **en crudo** porque AddonBuilder no mete los `.rvmat` que solo referencia el config. Ledger de puertas ejecutables como criterio de terminado. **Patron de la sesion**: **seis gates mios con la misma firma** — el gate se satisface con algo que no llegue a nombrar — y **los seis los cazo la familia contraria**. Coste Grok $8,35 en 15 encargos.

**2026-09-06** (trabajo del 09-04): **cuadro con textura dedicada, en el PBO y SIN confirmar en juego.** Las dos esferas pasan de islas de 80 px del atlas del cuerpo a una textura propia de 1024x512 con rvmat de normal y especular planos, fuera de `camo1`, y copiadas al LOD de piloto (1100/1200). El arte oficial del cuentavueltas **venia con los numeros fuera de su propia rejilla** —el "4" y el "5" un mayor corridos, el de 89,88 sin numerar, sin mayor del cero— y se corrigio moviendo los glifos originales; la sesion de LFQuad3 la instalo byte a byte en `_shared_parts`. **La regla de giro sacada de vanilla sale AL REVES en este modelo**: las dos agujas descansaban en -13,1 km/h y +903 rpm, a lados opuestos, que es la firma de un signo y no de un desplazamiento; angulos negados y pendientes de confirmar. Tres hallazgos que ahorran ciclos: el LOD de piloto es una vista **curada** y su censo se hace **contra la LOD0** (la tercera bombilla del manillar NO es comprobable desde el asiento, `light_dashboard` 12 -> 0); **sin `@SurvivorAnims` una prueba de postura o camara no vale** (`LFQuad2.c:22-31` cae a la pose de camion, y la observacion del asiento se hizo asi); y el `storage_1` compartido se corrompe porque unas corridas llevan `@CF` y otras no, con el sintoma disfrazado de `server_poll_stale`. PBO `12.162.069 B` verificado por contenido. **Proximo**: un solo ciclo in-game con `@CF` y `@SurvivorAnims` y storage ciclado — agujas en el 0, esferas visibles sentado, y la punta. Handoff [`30_Sessions/2026-09-06-lfquad2-textura-dedicada-y-signo-de-agujas.md`](../30_Sessions/2026-09-06-lfquad2-textura-dedicada-y-signo-de-agujas.md).
**2026-09-07**: cuadro **confirmado en juego** -- esferas sin espejo y legibles (R_DIAL 0.038), discos girando con el manillar, y **panel de gasolina nuevo encima de los relojes** (debajo no cabe: el bombin de la llave ocupa el centro), con prueba de CABLEADO y no solo de dibujo (aguja construida a 90 grados, en juego en la F = 48.5, o sea +41.5 = `angle1` con `fuel=1.0`). Eje del manillar puesto vertical: *"mejor ahora el eje"*. PBO 12.633.390 B, p3d `3670fe455648c1ac`, model.cfg `3be9df1813a6f72a`, verificados por contenido. **Sin confirmar**: la postura (conductor 80 mm adelante y 30 mm abajo; alcance 623 mm contra los 589 de LFQuad3) y el barrido a +-15, que no esta justificado por medida. **Abierto**: dos caras huerfanas de 2.25 m en los LOD 1100/1200 que se ven como una raya a la espalda, y la textura del pod con techo de 2.2 mm/texel (repintado a mano). Handoff: [`30_Sessions/2026-09-07-lfquad2-gasolina-postura-y-manillar.md`](../30_Sessions/2026-09-07-lfquad2-gasolina-postura-y-manillar.md).
**2026-09-07 (madrugada, 2a mitad)**: PBO `bea1b889b3ecedae` desplegado y verificado por contenido, con el conductor 125 mm adelante del original, el barrido a `+-22.5` y las dos caras huerfanas de los LOD 1100/1200 fuera. **Sin mirar**: la sesion de Windows estaba bloqueada y toda captura sale negra. El tema del manillar quedo **reencuadrado y traspasado**: la pose del conductor es la anim instance 22 (`QuadBike` de @SurvivorAnims), las manos van por IK con DOS poses que conmutan en los topes, y hay contrato escrito (`LL-handlebar-rotation-sync`) que dice que el barrido se IGUALA al `steerMax` de la pose. La comparativa contra LFQuad3 quedo anulada porque van en la instancia 12 (**LL-472**). La medida esta disponible en frio: clips extraidos, parser de SEAnim con control de bytes exacto y tabla de padres del esqueleto (148 huesos), todo en `LFQuad2_dev\_chain\anm_quadbike\`. **Guillermo puso a LFQuad3 al mando** de esa sincronia; LFQuad2 apoya y no elige barrido. Bug del build: `fb-20260907-001715-af59`.
**2026-09-07 (tarde)**: PBO `ec50a6b861de47fe` desplegado y verificado por contenido, **sin mirar**. Lleva conductor 30 mm mas adelante, copiloto centrado y +10 mm, barrido a `+-25` (interino, lo decide LFQuad3) y el **cuadro rediseñado**: panel unico plano de 172 x 86 mm, negro, con reborde, esferas arriba y gasolina abajo. Se logro **sin crear geometria** — py3d no modela — agrandando la unica cara que llevaba la gasolina, remapeandola a UV 0..1 y poniendola 1,5 mm por detras de los dos discos, mas un repintado de su textura a 11,907 x 9,410 px/mm por el escorzo de 50,8 grados. Dentro va tambien la sonda **v2** de LFQuad3. Medido en juego: **`anim=22` confirmado** y **X y Z negadas** entre py3d y `GetMemoryPointPos` (dos modelos, cuatro puntos, con LFQuad3). Fricciones: los `base_mods` de `DayZ_MCP` no traen `@SurvivorAnims`, asi que **ninguna corrida previa pudo juzgar la postura**; y el cliente lanzado por el daemon muere en bootstrap 5 de 5 con la clave de Steam sana — receta valida: servidor por el daemon, cliente a mano. Leccion **LL-474**. Fichas `fb-20260907-130618-a2c0`, `fb-20260907-132025-0155`, `fb-20260907-143740-6665`.




## LFVehicleUI — UI de navegación soft-coupled **MEMORIA COMPLETA 2026-08-29**

**Estado:** source↔PBO reconciliado offline (soft-dep 11/11 y contenido 9/9),
pero compile/runtime del SHA actual **UNKNOWN** y sin firma. La decisión vigente
descarta RT dinámico como GPS vivo y conserva HUD genérico; el source mantiene RT
incondicional, conflicto pendiente de adjudicar antes del próximo build.
**Memoria:** [brief](LFVehicleUI/project-brief.md),
[matriz](LFVehicleUI/validation-matrix.md),
[bugs](LFVehicleUI/bug-ledger.md). Autoridad viva: `P:\LFVehicleUI_dev\HANDOFF.md`.

## LFThermalCore — core térmico standalone **F0 CERRADO CON MOTOR 2026-08-31**

**Estado:** spec v1 `Draft`; plan v2 **RATIFICADO**. Esqueleto F1 construido, firmado
y desplegado en `P:\Mods\@LFThermalCore\`. **F0 PASS con motor**: G9 (carga limpia, cero
runtime en dedicated), G10 (la humedad no repinta prendas; control positivo emparejado) y
G11 (`defines[]` exporta el token entre mods → **FC-0 resuelto**, rama consumidora de
LFHeliCore autorizada). Hallazgo que condiciona F3: **`healthLevels[]` es un writer nativo
de material sobre prendas** y `SetObjectMaterial` hay que **re-afirmarlo**, no llamarlo una
vez. A3–A6 siguen UNKNOWN.
**Próximo:** diseñar F3 decidiendo **cuándo** se re-afirma el material (evento vs tick).
**Memoria:** [brief](LFThermalCore/project-brief.md),
[matriz](LFThermalCore/validation-matrix.md),
[supuestos](LFThermalCore/assumptions.md). Autoridad viva: `P:\LFThermalCore_dev\HANDOFF.md`.

## LFSlidingFloor — suelo sin fricción para jugador a pie **POC TERMINADO 2026-06-10**

Asset DayZ: zona que, al pisarla un jugador a pie, le quita el control y conserva
velocidad+dirección (patinar) hasta chocar; al frenar recupera.
**POC cerrado con veredicto POC-V confirmado: el enfoque A (scripted erguido) va a producto**
(A1/A3/A4 ✓ in-game; A2 owner ✓, observador [verify]; B descartado: simula solo server-side,
desync con el owner client — handoff [`30_Sessions/2026-06-10-LFSlidingFloor-R21-tests-spikes-veredicto.md`](../30_Sessions/2026-06-10-LFSlidingFloor-R21-tests-spikes-veredicto.md)).
Siguiente fase: producto sobre el Spike A (Grill de producto pendiente).

- **Memoria**: `AI/10_Projects/LFSlidingFloor/` (6-tupla + research/ con source-inventory,
  conflict-log e informes de los 2 agentes — estrena las 2 plantillas nuevas).
- **Repo**: `…\DayZ Projects\LFSlidingFloor\` (scaffold compilable) + `LFSlidingFloor_dev\`
  (CLAUDE.md, AGENTS.md, product-spec.md, HANDOFF.md).
- **Enfoques a probar**: A (scripted erguido: overrides input + HumanCommandScript/
  PrePhys_SetTranslation desde CommandHandler) y B (ragdoll consciente: PhysicsSetRagdoll
  sobre jugador vivo + cámara unconscious 1PP anti-jitter + suprimir PPE blackout).
- **Estado 2026-05-26**: creado. APIs de ambos enfoques verificadas a nivel de línea en P:\.
  Sin código de feature (R26). 2 desconocidos empíricos abiertos: (B) ¿ragdoll simula en
  jugador vivo? — riesgo nº1; (A) ¿fluido en MP? — SP engaña.
- **Pendientes**: cerrar product-spec con Grill (Modo A); plan del Spike B; R22 de Codex.

## dayz-weapon-ingest — skill para importar armas DayZ en masa **NEW 2026-05-30**

Herramienta (skill) que importa modelos de armas (OBJ/FBX/glTF) y los convierte en
`.p3d` riggeados + `CfgWeapons` + economy, en batch. 6 fases.

- **Memoria**: `AI/10_Projects/dayz-weapon-ingest/` (weapon-anatomy.md, plans/, reviews/, gold fixture).
- **Estado 2026-05-30**: Fase 1 ✓ (anatomía del arma verificada debinarizando el AKM vanilla;
  memory points `usti hlavne`/`konec hlavne`/`eye`/`*_axis`…; arma sin anims embebidas en el p3d)
  + Fase 2 ✓ (importador universal OBJ/FBX/glTF en Blender headless, por Codex, aceptado en review).
  Gold fixture [`akm_mlod_goldfixture.p3d`](dayz-weapon-ingest/akm_mlod_goldfixture.p3d).
- **Decisiones**: una skill end-to-end de armas (no 2 modulares); 3 formatos vía Blender; entrada
  mixta nombre+heurística; v1 = core rig automático + proxies de attachment manuales; Codex implementa código.
- **Pendiente**: Fase 3 (auto-rigger, la core) — prompt next-session lista en
  [`reviews/2026-05-30-prompt-next-session-fase3.md`](dayz-weapon-ingest/reviews/2026-05-30-prompt-next-session-fase3.md); Fases 4-6 después. Finding WI-F1
  (longest_axis = dims AABB, no eje) en `reviews/codex-review-inbox.md`.
- **Handoff**: [`30_Sessions/2026-05-30-dayz-weapon-ingest-fase1-2.md`](../30_Sessions/2026-05-30-dayz-weapon-ingest-fase1-2.md).

## DayZ-MCP — servidor MCP que controla DayZ (DayZDiag) **VIVO 2026-09-11 · Bloque 3** (tip `6de5d98`; el CERRADO 2026-06-11 era el cierre de las 5 fases, no del proyecto)

Servidor MCP que expone DayZ como tools tipadas (server-authoritative, sin teclas SO ni OCR). Control + datos engine-native; captura visual por window-grab.

- **Memoria**: `AI/10_Projects/DayZ_MCP/` (6-tupla + research/). **Repo**: `…\DayZ Projects\DayZ_MCP\` (bridge compilable) + `DayZ_MCP_dev\` (contrato + server Python + tools). Estado vivo: `DayZ_MCP_dev/HANDOFF.md`.
- **Update 2026-09-11 (indice)**: Bloque 1 cerrado; Bloque 2 completado/merged (PR #15, tip `d5e179f`); **Bloque 3 en curso** tip `6de5d98` (tablero LIVE-STATE 18:05 Madrid). Fuente: `_tablero.md` slug mcp + recap 2026-09-11.
- **Estado 2026-06-11 — PROYECTO CERRADO (con R21 estructural F4 + X.5 procesadas)**: las 5 fases (0 transporte / 1 control / 2 observación / 3 visual / 4 MCP stdio) PASS in-game; E1-E4 ✓. Las 12 tools responden desde un cliente MCP real. Pipeline completo en cada fase. Fase 4: gates 4A+4B PASS (4 bugs cazados, BUG-013..016). **R21 estructural F4 (2026-06-11, doble independiente Claude+Codex)**: consolidado 3 P1 + 4 P2 + 8 P3 → **X.5 completa verificada** (5 fixes Python/install-only, cero rebuild; suite 38/38+20/20, smoke MCP 9/9, regresión fase3 GATE=PASS) → BUG-017..023 fixed, BUG-024..031 backlog. Handoffs: [`30_Sessions/2026-06-10-DayZ_MCP-fase4-plan.md`](../30_Sessions/2026-06-10-DayZ_MCP-fase4-plan.md) + [`30_Sessions/2026-06-11-DayZ_MCP-r21-fase4-x5.md`](../30_Sessions/2026-06-11-DayZ_MCP-r21-fase4-x5.md).
- **Update 2026-07-16 (auditoría + reaper)**: [broker D-14 + coordinación multiagente H1-H8 + fase 5 drivability posteriores al cierre 2026-06-11; el header "CERRADO" está stale]. Auditoría adversarial completa de todo el MCP = `SOUND-with-fixes` ([`DayZ_MCP_dev/reviews/2026-07-16-fable-full-audit.md`]). Incidente ghost-run (crash de DayZ bloqueaba la caja permanente) cerrado con **dead-run reaper** (auto-heal ≤30 s + reap no-TTY, D-18, 533/533 + R9 doble + desplegado en vivo). Único P1 abierto: **F-01/BUG-044** (embedded reclaim puede matar un daemon sano, fix 1 línea). Handoff: [`30_Sessions/2026-07-16-DayZ_MCP-audit-and-reaper.md`](../30_Sessions/2026-07-16-DayZ_MCP-audit-and-reaper.md); LL-346.
- **Update 2026-07-22 (BUG-046/H9)**: la cola es request-bound FIFO y no concede leases a callers ausentes; cerrada la carrera release-WAL/persistencia que producía `audit_failed`. Launcher nativo `dayz-test-v1` instalado, token/identidad sólo en entorno interno sellado; timeout host 7 días efectivo tras sesión nueva/restart. Queue/WAL/E2E 106/106, launcher 67/67 y adversarial final 63/63 sin High/Critical. Pendiente únicamente gate real 2 Claude + 2 Codex, ejecución PE/DayZ y bootstrap V24/H10 global. Handoff: [`30_Sessions/2026-07-22-DayZ_MCP-bug046-h9.md`](../30_Sessions/2026-07-22-DayZ_MCP-bug046-h9.md).
- **Update 2026-08-16 (preparación del repo público)**: cerrada la deuda que bloqueaba publicar — dependencias declaradas en `tools/pyproject.toml` con test que las ata a `requirements-mcp.txt`, `test_registry_lock` desacoplado del lock canónico del árbol, y **la cartera de proyectos fuera del builder y del `launcher.cpp`** (política externalizada a `%LOCALAPPDATA%\DayZ_MCP\launcher-policy.json`, 10 proyectos; paridad re-medida por el orquestador sobre bytes canónicos: `35.202 == 35.202` y `6.183 == 6.183`, con control negativo que pone el gate en rojo). Suite del árbol **1381 / 0 fallos / 4 skips**; PE reproducible entre máquinas. **El gate que decide sigue ROJO y no es esa suite, sino la corrida DESDE EL EXPORT** (1241 tests, 19 fallos + 37 errores): hasta que pase, no hay `git init`. D-35 (el subsistema del launcher se publica) + BUG-072 (la cadena del registro se rompe si algo lo reescribe en sitio sin recibo). Handoff: [`30_Sessions/2026-08-16-dayz-mcp-publicacion-y-pack-routing.md`](../30_Sessions/2026-08-16-dayz-mcp-publicacion-y-pack-routing.md).
- **Update 2026-08-17 (noche)**: hoja de ruta de 8 ciclos RATIFICADA (D-48); ciclo 1 gateado in-game (run `28f2e26f`), ciclos 2/3b por Grok + revision ciega + promocion; suite real 1507 OK; clon 1344/0/0 ×3; repo publico `willy92wins/dayz-mcp` en `c5bf220`; sonda qwen3.5 PASS (gate ciclo 2). D-49 (PID gone/foreign). Siguiente: ciclos 4-5 offline; ciclo 6 = PBO. Detalle: `30_Sessions/2026-08-17-DayZ_MCP-ciclo1-gate-y-lanes-B-C.md`.
- **Update 2026-08-18 (cierre 19)**: ciclos 0-5 CERRADOS en Python (D-50 cable `dialog`; D-51 pin local). Lanes D/E por Grok + revision ciega 0 P1 + r2 + promocion; suite real 1566 OK; pin local hecho; export 207 sin JSON de seguridad; clon 1403/0/0/29; checkout 1403/0/0/29; repo publico `willy92wins/dayz-mcp` en `2bbb4b4` (push con OK). Ciclo 6 = PBO. Detalle: `30_Sessions/2026-08-18-DayZ_MCP-ciclos-4-5-lanes-D-E.md`.
- **Update 2026-08-18 (cierre 20)**: ciclos 0-7 CERRADOS en codigo (D-52 bump v8 aplazado; D-53 `SetUserData` para `ui_click`). Gate in-game `ui_dialog` **11/13** (caso 11 «busy» abierto, BUG-094). Suite real 1590 OK; clon/checkout 1427/0/0/29; repo publico `willy92wins/dayz-mcp` en `992899e` (push `2bbb4b4..992899e`, OK). Pendiente: caso 11 ×3, P1-02 in-vivo, `wait_for` ATM, bump v8. Detalle: `30_Sessions/2026-08-18-DayZ_MCP-ciclos-6-7-gate-ui-dialog.md`.
- **Update 2026-08-18 (cierre 20b)**: gate in-game de pendientes: caso 11 «busy» ×3 PASA (flake del arnes, BUG-094 no reproducible); BUG-086 lookback confirmado in-game (0,155 s vs control 6,65 s); verbos UI `not_handled` (ATM sin corriente); dialogo no bloquea `camera_get` 0,30 s; `dayz_test_stop` con PID muerto 2,88 s PASA. Bump 7→8 INTENTADO Y ABORTADO (D-54; arbol sigue en 7). Suite real `Ran 1590 tests in 234.130s` / `OK (skipped=4)`. **Pendiente unico: PBO v8 + P1-02.** Detalle: `30_Sessions/2026-08-18-DayZ_MCP-ciclos-6-7-gate-ui-dialog.md` addendum 13:1x-13:3x.
- **Update 2026-08-18 (cierre 20c)**: ciclos 0-7 cerrados; v8 desplegado (`F070A6C8`); D-55 tomada (fencing primero; `instance` nuevo en el PBO, no reusar la key). Pendiente: movimiento 1 + fencing en el PBO siguiente + revisar/promocionar lane K (`%TEMP%\mcp-laneK-20260818`). Detalle: `30_Sessions/2026-08-18-DayZ_MCP-council-lease-cola.md`.
- **Hallazgos clave**: coches PHYSICS client-authoritative (B3 diferido a fase client-peer); cámara vía `Camera` entity (no indexado); captura por window-grab host-side (MakeScreenshot roto); el SDK MCP no serializa tool-calls (mutex obligatorio); `exec_enforce` ejecución = limitación engine headless (gating+audit sí verificados); el gate de versión debe vivir también en la ENTREGA del poll, no solo at-enqueue (R21 F4). Lecciones LL-115/116/117/118/139/140/141/142.
- **Backlog opcional (NO bloquea — proyecto entregado)**: re-registro `install-mcp.ps1 -Register` (activa `--require-version` en Claude Code); BUG-024..031 (P3 R21 F4); deuda G-4 (scene-freeze server-side, migrar [`MCPBridge.c`](../_tmp_dayz_mcp_step0/DayZ_MCP/scripts/5_Mission/MCPBridge.c)→`MCPJobRunner`); BUG-009 (cliente flaky, mitigado) + BUG-010/011/012 (hardening `telemetry_read`, P2).

## MercedesAMGLF — import Mercedes-AMG GT3 a DayZ (CarScript proxy-based) **NEW 2026-06-22**

Import de un coche deportivo GT3 recibido como v1 de un amigo (Codex). Objetivo: drivable de alta calidad,
cuerpo regenerado desde FBX y partido en PROXYS (fuente glTF 236k verts / 166 mallas) para esquivar el
límite de vértices por objeto.

- **Memoria**: `AI/10_Projects/MercedesAMGLF/` (project-brief, product-spec, plans/, research/2026-06-22-lfquad-carryover, verified-apis, assumptions, reviews/).
- **Repo**: hermanas `…\DayZ Projects\MERCEDES_AMGLF\` (compilable) + `MERCEDES_AMGLF_dev\` (dev); tooling reusable en `C:\Users\guill\DayZ_Tooling`.
- **Estado 2026-07-24**: plan integral R21 APPROVE; S0 cerrado **GREEN** sin tocar producto. Specs canónicas SHA `E67B7F39...F4F4`; baseline v6 nuevo 257 archivos; verificadores TDD `24 failed→25 passed`; PACKONLY de control con cierre semántico `E8B66685...1A7448`. Árbol de producto pre/post `E5E03127...60B86`.
- **Estado 2026-08-01**: S1 seguía RED por SC-015 → **DECISIÓN: desacoplar** (enmienda §1.1-1.2 pendiente; SC-015 → gate exclusivo de S9, carril DayZ_MCP). Review Fable+R22 aplicada (OUTPUT v2.1, R22F-001..009); defecto nuevo **R22F-003** (12 `mb_*_lod1/_lod2` sin rotar → LOD1/2 dibujan cabina 180°) con candidato gateado 12/12 y confirmado en visor: `MERCEDES_AMGLF_dev\_candidates\2026-08-01-lodvariants-yaw180\`. Próximo: sesión de enmienda (prompt en `reviews\2026-08-01-prompt-arranque-enmienda-s1.md`) → micro-rebuild R22F-003 pre-S3 → slices S2+.
- **Decisiones**: v6 es única fuente de composición; v64 solo control. Techo `<65535` resolved/LOD/proxy y `>=2` visuales. Cockpit v1.0 source-faithful = volante real animado + MoTeC real estático iluminado, sin agujas inventadas; telemetría viva v1.1. G8/AC8.1 separan preview/spawn frío, stale y warm. Sin CE en v1; nombre canónico `MERCEDES_AMGLF`; DamageZones espaciales v1.0 = 4 auditadas.
- **Skill de dominio**: `dayz-vehicles`; S0 también aplicó `dayz-preflight`, `dayz-pbo-build`,
  `dayz-p3d-audit` y `dayz-mod-workflow`. No se modificaron skills/runbooks en S0.
- **Próximo**: S1, únicamente caracterización baseline de rendimiento frío según el plan integral; S1 no se inició en S0. Handoff vigente [`30_Sessions/2026-07-24-mercedes-amglf-s0-cierre.md`](../30_Sessions/2026-07-24-mercedes-amglf-s0-cierre.md).

## LFHeli — helicóptero DayZ custom (CarScript-as-aviation) **NEW 2026-07-16**

Helicóptero propio construido tras diseccionar 5 mods de heli (SIB, RFFS, MH6, Expansion, LM_Planes). CarScript-as-aviation (la clase nativa `Helicopter` es stub); control kinemático + estabilizador envelope-protection + pipeline Pawn (owner predice bajo `NetworkMoveStrategy.PHYSICS`).

- **Memoria**: `AI/10_Projects/LFHeli/` (project-brief, verified-apis, assumptions, validation-matrix, bug-ledger, decisions/, reviews/) — creada 2026-07-16 consolidando ~30 sesiones. Estado vivo en `LFHeli_dev/HANDOFF.md` (bloque LIVE-STATE).
- **Repo**: `…\DayZ Projects\LFHeliCore\` (scripts) + `LFHeli_OH1/_SF8B` (assets) + `LFHeli_dev\` (plans/specs/reviews/tools). Plan vigente `plans/2026-08-06-d3-1-pawn-inerte.md` (v2, R22 Grok) + `BALANCE-2026-08-06.md` (el contrato de la construcción D.3: 14 filas CERRADO + 4 fases).
- **Estado 2026-08-17 14:40**: **LF-001 con fix MEDIDO** (Core desplegado `BD039747`, OH1 `4CB7BA8F`, JSON `e9178fea`): el proxy del ex-owner queda congelado en el último snapshot pre-posesión y no recibe transform (snap cliente y lift server INERTES); `RemoteObjectTreeDelete/Create` 500 ms tras `OnDriverExit` → exit3-10 3/3 reentradas, |Δ| 0,12/0,11 m. **LF-007 nuevo y arreglado**: el OWNER apagaba el motor por réplica sin bujía/batería (`CheckVitalItem` authority-only); la «regresión del build snap» era falsa. Guard DIAG de acciones de motor (input ajeno en la ventana del cliente) y settle por estado autoritativo en el guion. **LF-005 campaña AutoHover por celdas** hecha: MaxTilt es la palanca (Oopp = clamp + 0,13°): T7 −22 % contrabanco por +0,5 s de frenado, T5 −44 % por +0,7 s; KTilt DOMINADA (K10 peor en ambos ejes, K15 no baja el pico). LL-304..308; SP-285/286. **FLIR probado desatendido** (autotest F0 + cierre por software): cazo **LF-008** - el cliente leia el motor NATIVO de un proxy (`natEng=false syncEng=true`) y la camara termica se cerraba sola al instante; fix `LFHeliEngineOnReplicated()`, corrida 2 PASS con reposesion verificada. LL-309/310, SP-288.
- **Decisiones**: CarScript-as-aviation; vía D.3 = fuerzas simétricas owner/server (patrón Expansion, ForceSpike E = SÍ); latch del colectivo → caída pasiva 7,8/2 m/s² tunable; envelope stabilizer + recover. Ver `decisions/decision-log.md`.
- **Skill de dominio**: `dayz-vehicles` SP-188 (escalera Pawn + reglas duras, con veredicto runtime) — promovido 2026-08-06; `dayz-aviation` (roll/feel diferido).
- **Próximo**: (1) EL VUELO del piloto (uno): LF-001 por feel (posarse, salir 2-3 veces, reentrar) + A/B de los 2 candidatos AutoHover (T7 = AutoHoverMaxTiltDeg 7,0 (adaa153a) y T5 = 5,0 (04d941ad)) en la misma sesión (JSON se lee en EEInit: cambiar el fichero y spawnear otro OH1); selector por fila al recibir feedback; (2) limpieza del árbol (snap cliente inerte + sondas), `EXIT_REMOTE_RESYNC_DELAY_MS` 500→200 medido con exit3; (3) parser «rebote owner post-touchdown» para LF-004; (4) `-NoScript`, `-Retries`, runner lista DayZDiag ajenos; (5) LFThermalCore. Handoff [`30_Sessions/2026-08-17-lfheli-lf001-fix-lf007-tarde.md`](../30_Sessions/2026-08-17-lfheli-lf001-fix-lf007-tarde.md).

## Utopia_PC — recuperación de PBOs comprados **NEW 2026-07-20**

- **Memoria**: `AI/10_Projects/Utopia_PC/` (6-tupla, research y ledger UTOPIA-001..024).
- **Workspace**: `P:\Utopia_PC`, `P:\Utopia_PC_Core`, `P:\Utopia_PC_CCTV`,
  `P:\Utopia_PC_Server`, `P:\Utopia_CoreServer`.
- **Estado**: recuperación accesible y auditoría estática cerradas. 536.931 entradas
  actuales verificadas, 88 fuentes semánticas + 396 strings, PC_Server recuperado
  de Discord, CoreServer v1.4.4 preservado como referencia y 73 originales
  históricos exclusivos. Veredicto código: `NEEDS-WORK`; ningún fix/repack/runtime.
- **Bloqueos**: exactos CoreServer 2024 y ZIP sólo existen como metadata/hash;
  fuente Core duplicada/syntax; dependencias CF/topología; RPC Printer/CCTV no
  autoritativos; corrupción/pérdida en recipes/mining/transforms.
- **Próximo**: spec con fixtures → stub CoreServer + DAG de dependencias → compile
  limpio → fixes por autorización/pérdida/corrupción → repack/deployed hash →
  dedicated dos clientes/in-game. Handoff:
  [`30_Sessions/2026-07-20-Utopia_PC-pbo-recovery-audit.md`](../30_Sessions/2026-07-20-Utopia_PC-pbo-recovery-audit.md).

## ForzaDayZ — pipeline Forza → DayZ, piloto coche #2 (WRX STI '04) **NEW 2026-08-07**

Pipeline repetible para convertir coches rippeados de ForzaTech en vehículos DayZ conducibles
(`CarScript`). El coche #1 (`SUB_BRZ`) estrenó y endureció el pipeline y tiene su propia carpeta;
esta memoria es del **piloto CAMBIO-3**, `sub_wrxsti_04`, elegido para medir cuánto se ha abaratado
el proceso. Repo (git, NO OneDrive): `C:\Users\guill\ForzaDayZ`, rama `import-pipeline-redesign`.

- **Estado 2026-08-07**: T4 → T5a → T5b → T7 → T7b → **T6 cerradas**. El hito de T6 es que el rig de
  desmontables dejó de ser solo-puertas y acepta bisagras **horizontales**, así que capó y maletero
  salen como attachments de verdad — y eso lo hereda el coche #3. El coche #1 sigue siendo el
  control de no-regresión y salió byte-idéntico.
- **Bloqueos**: ninguno. El build sale exit 1 **por diseño** (dos pilotos traseros con winding
  irreparable por el método del pipeline, decisión de no absorberlos); desde esta sesión su firma
  está fijada para poder distinguir ese rojo del rojo nuevo.
- **Próximo**: T8 (config.cpp + model.cfg + PBO) → **test vivo #1**. El piloto reserva 2 pruebas
  in-game y no se ha gastado ninguna.
- **Memoria**: [`project-brief.md`](ForzaDayZ/project-brief.md), [`verified-apis`](ForzaDayZ/verified-apis.md), [`decision-log`](ForzaDayZ/decisions/decision-log.md). Estado vivo
  en `C:\Users\guill\ForzaDayZ\HANDOFF.md`. Handoff:
  [`30_Sessions/2026-08-07-forzadayz-piloto-wrx-T6-desmontables.md`](../30_Sessions/2026-08-07-forzadayz-piloto-wrx-T6-desmontables.md).

## IberiaMap — mapa DayZ de la Península Ibérica **NEW 2026-08-08**

Mapa DayZ con la silueta de Iberia reconocible, topografía derivada de datos reales, Baleares
(al menos Mallorca) y sur de Francia como zona lategame. **Análisis de viabilidad cerrado; sin
implementación, sin repo, sin un solo archivo tocado en `DayZ Projects\`.**

- **Estado 2026-08-08**: veredicto del council = la fase de terreno son **8-14 semanas**. No es
  «bajo trabajo» en absoluto (el gate que puso el usuario), pero sí es la parte barata y
  automatizable frente al kit de assets, que es el proyecto real: DayZ no tiene teja árabe,
  encalado, bloque de los 70 ni hórreo, y sin ese kit el mapa es Chernarus con carteles en español.
- **Decisiones (4 ADR)**: 1:1 descartada — el argumento no es el peso (>1,2 TB extrapolado del
  `.wrp` medido) sino que **el jugador no escala**. Lienzo 20×20 km → 167-202 km² de tierra, entre
  Livonia y Chernarus. Escala **anisótropa**: horizontal 1:54-1:60, vertical 1:6-1:7.
- **El hallazgo que reordenó el proyecto**: el agua de terreno del `.wrp` es un **plano global
  único** (lagos y ríos = heightmap hundido bajo esa cota). Con la meseta a 100-180 m, ni el Duero
  ni el Tajo ni el Ebro pueden llevar agua. Política híbrida: agua de motor solo en tramos
  conectados al mar, lecho seco en el interior, objetos-charco donde la pendiente lo permita.
  **Abarata** el paso que las dos lanes daban por más caro. Evidencia comunitaria convergente,
  **sin confirmar en doc oficial** — es la asunción A-01 y de ella cuelga la decisión entera.
- **El trilema del relieve**: a 1:60 se tienen dos de tres — planta fiel, montañas con presencia,
  laderas caminables. Un macizo de 600 m caminable necesita 4 km de base y hay 833 m.
- **Próximo**: decisión de arranque del usuario. Si arranca: fijar por escrito qué río va en qué
  modo **antes** de tocar herramienta alguna, y confirmar A-01 midiendo in-game la cota de un lago
  interior de Livonia.
- **Memoria**: `AI/10_Projects/IberiaMap/` (brief, verified-apis, assumptions, validation-matrix,
  decisions/, research/). Handoff:
  [`30_Sessions/2026-08-08-IberiaMap-council-viabilidad.md`](../30_Sessions/2026-08-08-IberiaMap-council-viabilidad.md).

## ControlPlane — plano de control programático + director de eventos **NUEVO 2026-08-15**

Mod DayZ server-side y **producto** para dueños de servidores: expone un catálogo de verbos con permisos a un
agente externo por HTTP saliente (el servidor pollea, no se abre puerto entrante), y encima un director de
eventos reactivo como primer caso de uso vendible.

Nació el 2026-08-15 de una exploración sobre filepatching que acabó descartando esa vía —el binario retail la
bloquea y en producción se desactiva— y encontrando el hueco real: **nadie expone el gameplay por una API**.
LBmaster tiene la tubería pero sus rutas son de infraestructura; VPPAdminTools y LBAdmin tienen los verbos pero
siempre con un humano pulsando botones.

**Decisiones cerradas**: producto = plano genérico + director encima · depender de CF y **reimplementar** el
director inspirado en Dabs (su cabecera prohíbe el repack, verificado) · **opción A**: el director decide en
local y el agente es overlay opcional, para que el mod funcione sin que nadie pague inferencia · PBO propio sin
depender de DayZ_MCP (que lleva `exec_enforce`) · el permiso lo impone el dispatcher, nunca el handler.

**Estado vivo:** el plan no fue revisado **antes** de implementar, pero la
implementación recibió R21 posterior: 9/9 hallazgos resueltos/medidos. PBO
`A9F2318C6192A691` (92.115 B), firmado; corridas 42/0/3 sin cliente, 38/0 y 7/0.
Guía de comprador existente (410 líneas) y BattlEye restaurado. Pendientes:
portabilidad del launcher de gate, metadata de producto, hipótesis de punteros a
`Object` destruidos y re-firma en cada redespliegue.

Memoria: [ControlPlane](ControlPlane/project-brief.md) · autoridad viva
`P:\ControlPlane_dev\HANDOFF.md`.

## SimpleGroup — grupos y territorio por bandera **UPDATED 2026-08-15**

Mod DayZ propio: grupos de jugadores con bandera como ancla de territorio (radio de proteccion,
cupo de deploy, raid bajando la bandera ajena). ~8.066 lineas de Enforce en 35 ficheros.
Repo `DayZ Projects\SimpleGroup\`; memoria en `AI/10_Projects/SimpleGroup/`.

- **Estado 2026-08-15**: auditoria de codigo multi-agente cerrada — 17 subagentes, **77 hallazgos,
  51 CONFIRMED**. Plan de **16 lotes** reconciliado entre dos lanes ciegas (Grok autor, Qwen
  auditor de citas). **Aplicados los lotes 2, 4, 5a y 5b + los 6 arreglos de la review R21**: todo
  el bloque de persistencia y arranque. Territorio, perf, UI y config siguen sin tocar.
- **Nada de esto ha corrido.** Enforce no compila fuera del juego; lo aplicado esta verificado solo
  por lectura de codigo y asserts de escritura. El unico gate real es levantar el servidor.
- **Dos P0 abiertos**: (a) el orden de arranque — `LFPG_ModdedMissionServer.c:8-21` hace `Create()`
  → `super.OnInit()` (el engine restaura entidades → `AfterStoreLoad`) → `Init()` (→ `LoadGroups`),
  de modo que toda bandera consultaba su grupo contra un mapa vacio y persistia `m_GroupID = ""`;
  **es inferencia de codigo, no observacion de runtime**. (b) **TERR-1**: `actiondiggardenplot.c:109`
  calcula la posicion y `:119` NO la pasa a `OnPlacementComplete`, asi que el override del mod
  recibe `(0,0,0)`, concluye «fuera de zona» y borra el huerto — todo huerto cavado con pala se
  autodestruye. El lote 10 lo cierra y va inmediatamente despues del gate in-game.
- **Invariantes cerradas por decision del usuario** (no re-abrir sin evidencia): bajar la bandera
  ajena **es** mecanica de raid intencional · `ActionDestroyPart` queda libre, se gatean Build y
  Dismantle · la bandera abandonada se queda bajada en el mundo **y sigue negando su radio** ·
  no se quita `JM_CF_Scripts`. ADR-2026-08-15-A a D en `decisions/decision-log.md`.
- **Proximo**: build del PBO + test in-game empezando por el **escenario 15** (borrar
  `groups.json` dejando el `.bak`, reiniciar, comprobar que los grupos vuelven). Ese escenario
  prueba el lote 2 y confirma o refuta el orden de arranque. En el RPT: parar si sale
  `BOOT SAFETY NET`. Handoff:
  [`30_Sessions/2026-08-15-simplegroup-auditoria-y-fixes-persistencia.md`](../30_Sessions/2026-08-15-simplegroup-auditoria-y-fixes-persistencia.md);
  estado vivo: `SimpleGroup_dev/HANDOFF.md`.

## LFLiveContent — motor de "contenido como datos" **NUEVO 2026-08-16**

Mod DayZ (sin código aún): intérprete que lee JSON y lo materializa en runtime — UI procedural sin `.layout`,
swap visual de objetos y composición de props — para sacar del ciclo rebuild+reconnect (3-10 min) todo cambio
que sea recombinación de assets ya cargados. Memoria en `AI/10_Projects/LFLiveContent/`; spec en
`DayZ Projects\LFLiveContent_dev\SPEC.md`.

- **Estado histórico 2026-08-16**: **spec en Draft, NO implementar.** Dos revisiones adversariales (Grok) declararon
  UNSOUND la v1 y la v2; 30 hallazgos aceptados, 0 rechazados, $0,571. Arbitraje en el scorecard §Corrida 30 y §32.
- **Estado vigente 2026-08-17**: Hito 0 quedó **CERRADO in-game**; ASSUMED-02, ASSUMED-07 y ASSUMED-10 fueron medidas. El siguiente objetivo es Hito 1 (UI declarativa); ASSUMED-08, ASSUMED-09 y ASSUMED-11 siguen abiertos para Hito 2. Autoridad: `AI/10_Projects/LFLiveContent/project-brief.md:3-5`; `assumptions.md:8,13-17`.
- **La tesis se sostiene**: no hay `ConfigSet*` y los `.p3d` son inmutables, pero `WorkspaceWidget.CreateWidget`
  levanta UI sin ningún `.layout` (`enwidgets.c:179`) y acepta handlers (`SetHandler` está en la clase base
  `Widget`, `enwidgets.c:172`). El vocabulario es fijo; la gramática puede ser texto.
- **El diseño ya existe en vanilla** y la v3 debe copiarlo, no inventarlo: `3_game\objectspawner.c` es el
  análogo (JSON→`CreateObjectEx`→`SetOrientation`→`SetScale` con whitelist y flags ECE), y el par
  `undergroundarealoader.c:175` + `undergroundtrigger.c:10,36,52` es el plano de los dos canales — documento
  tipado por RPC al conectar, índice `RegisterNetSyncVariableInt` **en la entidad afectada**, y guarda
  `m_JsonData && index != -1` que resuelve la carrera documento/índice.
- **Restricción dura**: no existe `RegisterNetSyncVariableString`; una ruta de material no viaja por netsync.
  Vanilla lo intentó y dejó el intento comentado y marcado como fallo de sincronización (`barrel_colorbase.c:610`).
- **Bloqueado por dos medidas in-game**, en una sola sesión: (1) si `SetObjectMaterial` replica solo — si
  replica, el canal 2 entero sobra; (2) qué ve un cliente que hace late-join con el índice ya aplicado.
- **Aprendizajes durables**: LL-281 (un "cero usos" desde salida paginada no es ausencia — costó excluir
  `SetScale` del alcance sobre un conteo falso) y LL-282 (al cambiar la arquitectura los criterios se
  re-derivan, no se heredan). Refuerzos aplicados: caso violador en `CLAUDE-reference.md` §R22 y checks
  CHK017/CHK018 de falsificabilidad en `dayz-feature-spec`.
- Handoff: [`30_Sessions/2026-08-16-LFLiveContent-spec-v1-v2-council.md`](../30_Sessions/2026-08-16-LFLiveContent-spec-v1-v2-council.md).

## AI_Pipeline — qué modelo ocupa cada asiento del pipeline

Proyecto de infraestructura de agentes, no de mod. Nace el 2026-08-24 de «¿hay un
modelo local gratis que orqueste `prime-agent` para hacer ciclos de desarrollo?».

- **Rutas**: memoria en [`AI_Pipeline/README.md`](AI_Pipeline/README.md) y [`project-brief.md`](AI_Pipeline/project-brief.md). Ledger canónico: [`gates-ledger-live`](AI_Pipeline/gates-ledger-live/SKILL.md). Sin repo de código propio;
  las herramientas viven en las skills (`delegar`, `opencode-handoff-template`,
  `qwen-handoff-template`) y en el clon de `unlazy`.
- **Tesis**: el asiento de orquestador es donde fallan TODOS los modelos —
  AgentFloor mide 0-16 % en horizonte largo para open-weight y 10 % para GPT-5 —
  así que el criterio de «terminado» sale de la cabeza del modelo a un fichero de
  puertas ejecutables. `prime-agent` ya trae `--autonomous --autonomous-gate`.
- **Estado (2026-08-24, sesión nocturna)**: el hueco grande **queda cerrado** —
  `--autonomous-gate` está MEDIDO con control positivo y negativo: la puerta se
  ejecuta, una que falla realimenta al modelo y dispara continuaciones (2 turnos →
  6), y con la puerta imposible el proceso sale **rc=1**: falla cerrado. También
  cierra **A5**: la lane local responde por el arnés (40 s), y NVIDIA estrena arnés
  (9 s). **BUG-9 resuelto**: el proveedor nuevo tumbaba `models.json` ENTERO y las
  dos lanes gratis llevaban horas caídas sin que nadie lo viera. **D7**:
  `gates-ledger` **NO se instala** — la review de Codex la declara NO SÓLIDA con dos
  PASS falsos reproducidos (typo en un atributo → puerta manual certificada;
  abandonar todas → `ALL MET` exit 0), los dos verificados también por mí con su
  control. **D8**: el criterio de terminado de un delegado lo pone una puerta
  calibrada, no el modelo. Procedimiento nuevo en
  `20_Runbooks/sesion-larga-delegada-por-el-arnes.md`. Prueba 2 (plan →
  implementación → revisión, todo gratis) **cerrada y limpia**: examen que rechaza
  al impostor 5/5, implementación 5/5 sin tocar el examen, y un revisor gratis que
  encontró el defecto sembrado que sobrevivía a las cinco puertas. Handoff:
  `30_Sessions/2026-08-24n-la-noche-del-arnes.md`.
- **Estado (2026-08-24)**: fase de selección. **D1** asiento local `qwen3.8:98k`
  (15,0 GB · 100 % GPU · 98k ctx; 3/3 en el test de cadena con 4 llamadas y 38,9 s
  — corrige la primera recomendación, que rankeaba a Qwen por los números de su
  predecesor). **D3** de `unlazy` se adopta el ledger de puertas, no el Depth Tree.
  **BUG-1 abierto**: `prime-agent --provider opencode` no sirve corrida (500 con
  Muse Spark, 0 bytes en 420 s con Ox Alpha) mientras `oc_run.py` sí — y sale con
  `rc=0`. Eso deja `--autonomous-gate` sin medir.
- **Segunda mitad del 24-ago**: lane **NVIDIA NIM** configurada y medida — 9 de 9
  modelos con tool-calling OBSERVADO, incluido `moonshotai/kimi-k3` (MCP-Atlas
  84,2, el mejor open-weight), latencias de 1-4 s. Skill **`gates-ledger`**
  escrita por Grok (17 ficheros, $0,31, suite verde) y **pendiente de revisión
  por Codex**. Y **BUG-6**: cuatro credenciales en el transcript, rotación
  pospuesta por decisión del usuario con la exposición medida.
- **Pendiente inmediato**: batería de aceptación (D4) antes de que
  `x-preview-f-free` deje de ser gratis (~5 días desde el 24-ago), y probar
  `--autonomous-gate` contra `--provider ollama`, que no depende de Zen.
- Handoff: [`30_Sessions/2026-08-24i-el-asiento-de-orquestador.md`](../30_Sessions/2026-08-24i-el-asiento-de-orquestador.md).

- **Estado (2026-08-26; sin `LIVE-STATE` fresco — STALE)**: la foto posterior
  registra **21 lanes** y `prime-agent 0.8.1`. `gates-ledger` v2 está empaquetado,
  pero **no tiene aún la revisión final de dos familias**, por lo que no se da por
  cerrado ni promovido. El Grill **JUICIO** quedó cerrado el 26-ago: Qwen filtra,
  Codex ocupa la revisión fuerte y el juez es Opus para trabajo normal o Fable
  para trabajo importante.
- **Fuente de orientación**:
  `C:\Users\guill\ObsidianVault\AI\20_Knowledge\ai-stack-destilado-20260825.md`.
  Al no haberse aportado un HANDOFF/LIVE más nuevo, esta entrada permanece **STALE**.

## BenchRE — recuperación y carga semántica **STALE 2026-08-27**

Bloque separado de `BRDK_BRDM_2`; se conserva aquel historial sin mezclarlo con
este frente.

- **Estado disponible**: 4 bloques de carga cerrados; inventario aproximado de
  **~86 errores semánticos**.
- **Autoridad**: no se aportó un `LIVE-STATE` o handoff fresco, por lo que este
  resumen queda explícitamente **STALE** y no se infiere avance adicional.
- **Scratch de trabajo citado**: `C:\Users\guill\dayz_re_scratch\`.

## LF_RusticTable — mesa estática DayZ **STALE 2026-08-11**

- Candidato MLOD reproducible y PBO construido; Object Builder abrió 864 puntos,
  1.456 caras, 22 secciones y 9 LOD.
- Gate visual 14/16; revisión técnica final e in-game pendientes. El path de
  texturas en Object Builder estaba vacío.
- Autoridad: [project brief](LF_RusticTable/project-brief.md). No se infiere
  avance posterior sin HANDOFF fresco.

## LocalVerifier — verificador local con abstención **UPDATED 2026-08-16**

- Pasos 0/1 hechos: Qwen3.8-27B 100 % GPU, 77 tok/s y P(True) con 0,984 de
  accuracy sobre ítems inequívocos; la banda de abstención enriquece ambiguos ~9×.
- Pendiente: etiquetado completo (paso 2) antes de que la métrica sea gold y
  cualquier QLoRA de calibración.
- Autoridad: [project brief](LocalVerifier/project-brief.md) y
  [validation matrix](LocalVerifier/validation-matrix.md).

## Stack3D — stack 3D local + harness **STALE 2026-06-10**

- Infraestructura procedural/AI local para Blender→py3d→P3D; caso activo
  histórico CMMG Mk47 y skill `hunyuan3d-local`.
- Sin HANDOFF fresco en esta auditoría; no se infiere estado actual del harness.
- Autoridad: [README](Stack3D/README.md), [bugs](Stack3D/bug-ledger.md) y
  [APIs](Stack3D/verified-apis.md).

## AssetLab — blockout 3D con jueces locales **UPDATED 2026-08-01**

Laboratorio de generación `bpy` (Blender 5.1.1 + Ollama/Luna). Working tree `E:\assetlab`; memoria en vault.

- **Estado 2026-08-01**: R1 auditada; matriz R2 `gpt-5.6-luna`/Codex-low 12/15 completed. Sin más inferencias autorizadas.
- **Autoridad**: [project-brief](AssetLab/project-brief.md).

## LFQuad3 (added 2026-09-02, rev. 2026-09-05)

**Estado (2026-09-05)**: lote grande CONSTRUIDO y DESPLEGADO, sin ver en juego. PBO
`7A58173E268384B2` en `Mods\@LFQuad3\Addons\`. Lleva: D5 cerrado con las dos mitades de
config (`AnimationSources` + animacion `hide`), gate del copiloto por `CrewCanGetThrough`,
mapeo UV de los relojes a `(+U,-V)` (criterio: determinante NEGATIVO del afin pantalla->UV),
angulos de las tres agujas rederivados enteros, 7 slots de carga y conductor/copiloto +5 cm.
Proximo paso: UN ciclo in-game — relojes sentado, proxys **desde fuera**, copiloto con mochila,
7 slots en inventario. Handoff de sesion
[`30_Sessions/2026-09-05-lfquad3-relojes-slots-y-modset.md`](../30_Sessions/2026-09-05-lfquad3-relojes-slots-y-modset.md).
**Abierto**: D2 (cuatro selecciones de luz a 0 caras en TODAS las LOD, heredado del ancestro
comun con LFQuad2; se modela DESPUES del ciclo) y el falso verde del LOD de piloto — ver
[`10_Projects/LFQuad3/bug-ledger.md`](LFQuad3/bug-ledger.md).
**Coordinacion**: la mision se comparte con LFQuad2 y ForzaDayZ WRX. Decision vigente: igualar
la infraestructura (`@CF, @VPPAdminTools, @DayZ_MCP, @SurvivorAnims`) **y** ciclar `storage_1`
antes de cada arranque — son una sola decision con dos mitades.

### Historico


**Estado**: tanda 4 (ciclo in-game 1, 2026-09-02) cerrada en ROJO: LFQuad3 carga pero sin ruedas (FireGeometry sin la cara del proxy en `wheel_x_y`), get-in/asientos rotos, huecos y reposo de agujas mal; D sin medir (rpmMax 6400). Tanda 5: heredar LODs no visuales de LFQuad2 + cuadro/agujas + backlog M01-M04; tanda 6 = ciclo 2. Informe `P:\LFQuad3_dev\reports\ciclo1.md`; nota [`30_Sessions/2026-09-02-lfquad3-ciclo1-ingame.md`](../30_Sessions/2026-09-02-lfquad3-ciclo1-ingame.md).
**Memoria**: `P:\LFQuad3_dev\HANDOFF.md` (estado vivo) + `P:\LFQuad3_dev\GATES.md` (32 puertas, 28 CHECK aprobados) + [`30_Sessions/2026-09-02-lfquad3-asset-a-pbo.md`](../30_Sessions/2026-09-02-lfquad3-asset-a-pbo.md) + [`10_Projects/LFQuad3/project-brief.md`](LFQuad3/project-brief.md).
**Producto**: workspace local `%LOCALAPPDATA%\Temp\claude\...\LFQuad3_ws\impl\ws\` (unidad `W:` por subst); promocion a `P:\LFQuad3\` tras el ciclo final.

## LFTurret — torreta sovietica (mod DayZ en curso; ya no "arte, no mod") (added 2026-09-08; refresh 2026-09-11)

Origen en modelado visual por revisiones (rev04 eyeccion aceptada 2026-09-08); desde 2026-09-09 es **mod funcional** con scripts Enforce, no solo arte Blender.
Prototipo **P0 in-game** (`@LFTurret_P0`), articulacion rev08, items/cartuchos, operator binding; cambio de admision Steam en [PR #5 borrador](https://github.com/willy92wins/dayz-mcp/pull/5). Brief vivo: [`LFTurret/project-brief.md`](LFTurret/project-brief.md).
- **Memoria**: `AI/10_Projects/LFTurret/` (solo brief; excepcion declarada 2026-09-08). Estado vivo: `P:/LFTurret/HANDOFF.md`.
- **Handoffs**: [rev04 eyeccion](../30_Sessions/2026-09-08-LFTurret-revision04-eyeccion.md), [operator binding](../30_Sessions/2026-09-09-LFTurret-operator-binding.md), [Steam admission](../30_Sessions/2026-09-10-LFTurret-Steam-launch-admission-implementation.md).

