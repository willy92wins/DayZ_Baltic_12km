```json
{
  "reviewer": "claude-fable-5-1 (seat: independent read-only, Anthropic family)",
  "date": "2026-10-26",
  "subject": "plans/ev112-kit7-navigation-consumer-20261026.md (pre-implementation plan review)",
  "verdict": "SOUND-with-fixes",
  "summary": "The plan is coherent: 558 proposals (278 piece + 276 seam + 4 natural_end) in proposals.json plus 4 cap_to_land legs in geometry.json give the stated 562 local queries; 45 regressions retained; routes fixed before FindPath; all old gates (header, END count, exact coverage, sequential indices, finite vectors, requested positions <0.01 m, endpoints <=2.1 m, terrain 0.011 m, surface 0.801 m) remain in verify_v30_acceptance.py / verify_continuity_nav_v30.py. The new corridor/footprint check closes the known detour hole. Three items must be fixed before coding so the single budgeted run does not produce a false FAIL or an unimplementable step; none of them is a false-PASS path.",
  "findings": [
    {
      "id": "F1",
      "severity": "medium",
      "type": "plan-underspecified / tool incompatibility",
      "source": "plan §5 (line 20); tools/navigation/verify_patch_nav_coverage_ev112.py:13-14, 23, 27-33",
      "mechanism": "Plan §5 says to keep the eight F local checks 'contra E' plus the 45 regressions. The existing tool hard-codes E_SHA/F_SHA, raises 'Expected frozen F reference' unless reference.side=='F' and terrain_sha256==F_SHA, requires exactly 8 local_query_names == LOCAL_NAMES, and requires the geometric screen status 'PREPARED_GEOMETRIC_SCREEN_NOT_NATIVE_ACCEPTANCE' with exactly 8 queries. The new reference necessarily carries the kit7 buried terrain (815ef8b7..., asserted in discover_kit7_nav_routes.py:16) and 607 queries, so the tool cannot run on the new evidence and the old reference cannot consume a log ending 'END;607' (verify_v30_acceptance.py:21).",
      "impact": "Step 5 as written is not executable; an implementer may silently drop it or fork the tool ad hoc. Either way the handoff claim 'ocho comprobaciones F conservadas' would be unsupported.",
      "fix": "State explicitly in the plan which terrain pair the 8 local F legs are compared against (E vs new G, or E vs F using F only as a frozen source for the names/XZ), and that a parametrised successor of verify_patch_nav_coverage_ev112 (terrain SHAs and local names from the reference, not constants) is part of this unit, with its own negative control (wrong terrain SHA / wrong local set). If the delta E->G on those 8 legs is not >=0.05 m, publish INCONCLUSIVE for that sub-check instead of relaxing 0.05."
    },
    {
      "id": "F2",
      "severity": "medium",
      "type": "false-FAIL risk on fixed routes (not false-PASS)",
      "source": "plan §4 (line 19) 'El resto de casos no permite salida al terreno'; discover_kit7_nav_routes.py:47-48 (natural_end starts at station[0] / ends at station[-1]); discover_kit7_packed_nav.py:75-82 (cap legs: land -> natural edge -> inside)",
      "mechanism": "The 4 natural_end routes start exactly at the model's outer edge (bed[0]/bed[-1]). SampleNavmeshPosition uses radius 2 (init.c:41-42) and the consumer accepts snapped endpoints up to 2.1 m away. The snapped endpoint and first/last waypoint may legitimately lie up to ~2 m outside the packed dry footprint, which under 'covered by dry union, tolerance 0.01 m, no terrain exit except transitions' is a FAIL. The cap legs correctly get the exterior allowance; natural_end does not.",
      "impact": "Up to 4 guaranteed-or-likely false FAILs on an all-or-nothing gate ('no acepta el conjunto si no pasan todas las rutas'), burning the single budgeted run without informing about the graph.",
      "fix": "Specify in §4 that natural_end routes receive the same exterior allowance as transitions but only for the sub-segment within 2.1 m of the requested edge endpoint and outside the full model projection, with the remaining >=0.5 m intersection requirement unchanged. Do not re-select routes after FindPath; this is a consumer rule fixed now."
    },
    {
      "id": "F3",
      "severity": "medium",
      "type": "false-green guard missing as a precondition",
      "source": "plan §4 corridor definition (line 19); discover_kit7_nav_routes.py:19 (columns at q=±6), :18 (dry columns -18..18 and water at ±2.25); discover_kit7_packed_nav.py:63-66 (dry = dry_faces minus water_faces)",
      "mechanism": "The corridor (screen line at |q|=6, radius 2.1 m) spans |q| in [3.9, 8.1]. The plan relies on this corridor being wholly inside the packed dry footprint and wholly outside the packed water footprint, but nothing in the plan asserts it per route from the frozen geometry. If a piece's packed water_ext faces extend past |q|=3.9 or dry faces end before |q|=8.1 (poses are identity-rotation translations only, discover_kit7_packed_nav.py:48, so this is checkable offline), then the 'does not cross water' and 'covered by dry union' tests would rely on the engine path, not on the fixture.",
      "impact": "Without the precondition, a corridor that already overlaps water would make 'no water crossing' pass trivially for any path hugging the inner edge, i.e. a structural false-green for that route; conversely a corridor exceeding the dry footprint invites false FAIL.",
      "fix": "Add to §1 (preparation, before FindPath): for every local route compute corridor ∩ packed water (must be empty) and corridor \\ dry_union(required models) (must be empty except the declared exterior part for transitions and, per F2, natural_end). Record per-route margins in the reference; any violation blocks the run rather than being adjusted after results."
    },
    {
      "id": "F4",
      "severity": "low",
      "type": "negative-control completeness",
      "source": "plan §Puertas (line 31)",
      "mechanism": "Listed controls: remove piece/seam/end, terrain detour, water crossing, pose change, partial path, NaN, duplicate, truncation, altered regression contract. Not listed: (a) a path whose waypoint Y sits on the buried terrain layer under the roof (max_roof_ground_separation 1.33-1.57 m in proposals.json screen) to prove the 0.801 m surface gate rejects a terrain-layer path; (b) a path that only grazes a required piece (<0.5 m) and a seam path covering only one of the two pieces; (c) a correctly-shaped path on the opposite bank (left route evaluated against right corridor) to prove side binding.",
      "impact": "These are the exact mechanisms the new consumer claims to close; without a failing control each, 'controls pass' does not evidence that the gate is live.",
      "fix": "Add the three controls; each must produce FAIL (not INCONCLUSIVE) and be published with the checkpoint."
    },
    {
      "id": "F5",
      "severity": "low",
      "type": "producer hygiene",
      "source": "missions/BalticV30ContinuityNavV1.BalticTrial/init.c:19-21, :36, :38-39, :20",
      "mechanism": "(a) Missing input/output handles return silently -> no log -> consumer INCONCLUSIVE; acceptable but plan should name the log file with the probe UUID so the historical baltic_v30_continuity_nav_v1.log cannot be mistaken for new evidence. (b) 'FAIL;SCHEMA' then END;count<607 -> verify_v30_acceptance raises on the malformed row and on END count: correct, no false green. (c) NONE filter is keyed on the literal name 'negative'; any new negative-filter case must reuse that name or the producer must gain a kind column. (d) Plan §2 adds GetObjectsAtPosition warm-up and 1 query per 0.1 s tick; ensure the END row is written only after the last query's P rows and that m_Done semantics do not drop a tick mid-path.",
      "impact": "Evidence identity and schema strictness; none opens a false PASS.",
      "fix": "Unique log name with UUID in header; document the 'negative' name convention or add a 3rd CSV column consumed by schema check; END written in the final tick after the last P row."
    },
    {
      "id": "F6",
      "severity": "info",
      "type": "coherence checks that pass",
      "source": "proposals.json:13119-13120; geometry.json:93138-95396; patch-nav-f45/reference.json:378-386; plan lines 8-10",
      "mechanism": "558 + 4 caps = 562 local; 0 proposals with wet samples (grep for non-empty wet_indices: 0 hits); cap max slopes 9.21/9.76/11.46/11.46 deg match plan's 11.47; all four caps have land_endpoint_outside_model=true; changed_bank_13 old Ys 8.061/9.302 vs new terrain 5.242 (roadway 5.897) / 8.993 justify a Y-only retarget since the old Y lies >2 m from the new surface and SampleNavmeshPosition radius is 2; XZ unchanged. Budget: 607 queries at 0.1 s/tick ~ 61 s + 5 s arm, inside 900 s probe and 300 s boot. Corridor radius 2.1 m vs engine string-pulled chords: route lengths ~4-5 m (pieces ~8.7 m long over ~1.2 km) so chord deviation on bends is far below 2.1 m.",
      "impact": "No action.",
      "fix": "None."
    }
  ],
  "false_green_assessment": "The old height gates already reject a terrain-layer path under the roof (surface error would be ~1.3-1.6 m > 0.801) and a wrong-world log (header, END count). The corridor+footprint rule closes terrain detours and bank switching provided F3's precondition is asserted from the fixture. No reviewed mechanism lets a path avoiding a required model pass.",
  "scope_respected": "Plan does not claim locomotion, segment heights, or global EV112; limits list is accurate. No request to enumerate all paths; 562 fixed local routes plus 45 regressions is proportionate.",
  "required_before_implementation": ["F1", "F2", "F3"],
  "recommended": ["F4", "F5"],
  "no_side_effects": "Read-only review; no commands, writes, MCP, or subagents; active nav generation untouched."
}
```

Veredicto: SOUND-with-fixes. Las tres correcciones obligatorias son definir la herramienta y el par de terrenos para las ocho comprobaciones F (el tool actual está fijado a F_SHA y 8 nombres), dar a los cuatro natural_end la misma holgura exterior de 2,1 m que a las transiciones para evitar FAIL falsos, y asegurar antes de FindPath que cada corredor fijado queda dentro del seco y fuera del agua empaquetados. El resto son controles negativos adicionales e higiene del productor; ningún mecanismo revisado permite un PASS esquivando piezas.
