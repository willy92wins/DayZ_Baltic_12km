# Unknown-F static geometry precheck

This is a preservation record of the already reported one-off audit, not a rerun. The exact temporary script and exact numeric per-intersection minima were not present in the available review directory/session artifacts. Accordingly, no replacement is presented as the exact original, and minima are explicitly marked `NOT_RECORDED` in the JSON.

The recorded result was 24,847 changed F-unknown triangles (all all-NaN; 447,246 m²). Of these, 18,468 had no visible-LOD XZ footprint and 6,379 did. For those 6,379, each projected visible face intersection was reported buried in both B and H with `min(ground-face) > 2e-5 m`; possible exposure/contact counts were 0 for B only, H only, or both. Union footprint area was 2.1917286106459573 m². These are static heightfield-vs-visible-LOD geometry results, not an engine/render proof and not inferred F/sea state.

The 122 differences versus the older WRP inventory were reported as Y-translation-only; names, rotation, and X/Z translation were unchanged. The spatial broadphase was then recalculated with current B WRP transforms. Full old-inventory WRP digest and exact per-piece minima were not retained in this audit context.

Input hashes and the complete recorded counts are in `unknown-domain-precheck.json`. The receipt explicitly records that no script was rerun and no candidate or policy was modified.
