# V30 navigation and visual continuation

Live assignment: Guillermo asked Codex to review Claude's handoff and resume on
2026-10-02. This continues the approved water-ground-rebuild-v1 plan, phase 5.
No new terrain or product decisions are introduced.

1. Confirm the deployed preview 6 PBO identities and inspect the compiled WRP,
   configuration and stale navigation. Review Claude's fixes and gate results.
2. Generate the complete navigation with NavMeshGenerator from that exact deployed
   WRP. Save a new file on E:, capture generator completion and inspect its header.
3. Replace only the navigation entry in a new PBO with the existing
   tools/playtest/attach_navmesh.py. Its FileBank path preserves every other entry
   byte-for-byte. This is the packaging refinement over attach_navmesh_v30.ps1,
   whose AddonBuilder pass rebuilds the world again after navigation generation.
4. Deploy after preserving the previous PBO and checking content parity. Run the
   game with V30 only. Verify loading, native AI paths and dry/wet surface samples.
   Inspect player-view screenshots at the handoff sites; do not use camera_set.
5. Record results, unresolved visual/product choices and lifecycle cleanup. Do not
   close visual bugs on offline results or call this a complete map release.

Acceptance: complete generation saved; compiled WRP unchanged; new NM loaded;
path queries succeed on land with a relevant negative control; actual game images
reviewed separately from numerical samples. A failed or missing capture remains
inconclusive. AI paths alone do not prove actor traversal or multiplayer capacity.

Preserve V10/V33/V29 and historical evidence. Load test BALTIC-008 remains postponed
until a mapped sector, as Guillermo decided. Keep Narva and the four surfaces in
the approved V30 while collecting visual evidence; defer optional product changes.
No deletions. Computer Use only for grouped UI operations and released afterwards.
If two UI attempts with different strategies fail, preserve the evidence and
continue independent work instead of repeating blind clicks.

Continuation after native paths passed (02-10): prepare a separate visual mission
with eight fixed, recorded player positions near the requested review sites.
One player only; move that player at 45 s intervals, log requested/settled poses
and nearby water/land samples, then stop after eight sites. No camera_set,
camera entity, population or terrain edit. Capture each view after verifying the
current stage and player position; discard frames belonging to another window.
The mission is a temporary inspection fixture, not part of the delivered mod.

Visual follow-up after the complete 8-site tour: preserve V30 unchanged and use a separate 2-site temporary mission, 90 s per site, with a stable observation and server weather reading at 60 s. Repeat the lagoon at identical coordinates/weather to check the observed dark hillside; observe the previously sampled hill summit facing north because the uphill view was obscured by grass. No camera API or terrain edits. A repeated artifact remains a candidate until isolated.

Offline continuation requested by Guillermo after stopping Computer Use (02-10):
verify the retained V3 fairway corridors against every intersected native terrain
triangle. Freeze the existing 24 m useful width and 3 m nominal depth (1 cm
comparison tolerance), sea minimum 0.5 m and the prior 24 m endpoint / 620 m Narva
exclusions. Report excluded short pieces and the new delta separately; no global
navigability claim. Use polygon/triangle intersection vertices, where the extrema
of affine terrain height occur, rather than only the earlier 2 m point samples.

If a local bed defect is confirmed, prepare one separate offline candidate: lower
only existing water vertices outside road platforms and protected Narva, by at
most 1 m, to achieve 3.05 m on the failing triangles. Preserve all masks, shores,
water levels and the deployed PBO/WRP/NM. Require the corridor check, the existing
terrain and road gates, and a shallow-obstacle negative control. One audit and at
most one candidate solve; an infeasible or failed candidate stays unpromoted.
Any terrain deployment would require a new navigation generation and runtime
checks, so this session without Computer Use does not replace the working map.

Review after that bounded attempt: its 1 m candidate was infeasible and remains
rejected. Exact inspection isolated four insufficient constraints, all in Luga;
the worst has 42.80994% dry-bank weight and 57.19006% mutable-bed weight. Its
computed equal-lowering bound is 1.49875 m for the unchanged 3.05 m repair target.
This is new evidence for one focused follow-up candidate, with an explicit 1.55 m
cap and fresh output/evidence paths. The 3 m acceptance criterion and all fixed
vertices stay unchanged. Preserve the original audit and failed attempt; no
further solve if this follow-up or its existing terrain/road gates fails.
