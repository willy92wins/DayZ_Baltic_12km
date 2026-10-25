# EV80 compiled package review

**PASS_EV80_COMPILED_PACKAGE_REVIEW**

Independent read-only checks of EV80 source/deployed PBOs against the EV79 deployed baseline.

## Result

- Entries: 6827 total, 133 changed (1 WRP + 132 PAA), 6694 byte-identical.
- Surface: 459 tile coordinates regenerated; 918 PAA inputs evaluated, 786 were byte-identical to baseline; 66 tile coordinates contain at least one changed PAA.
- Stage raw WRP: 18033 objects; object byte streams, materials, header, and terminator match EV79 while heights match EV80.
- Water PBO is byte-identical to EV79: `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`.

## Checks

- PASS `deploy_manifest_status`
- PASS `source_deployed_world_sha_matches_manifest`
- PASS `baseline_world_identity`
- PASS `water_sha_is_baseline_ev79`
- PASS `world_entry_set_and_count`
- PASS `pbo_properties_exact`
- PASS `world_pbo_bytes_match_expected_replacements`
- PASS `deploy_changed_entry_list_exact`
- PASS `deploy_changed_texture_list_exact`
- PASS `only_wrp_and_texture_entries_changed`
- PASS `unchanged_entry_count_exact`
- PASS `regenerated_surface_tiles_match_manifest`
- PASS `stage_wrp_hashes_match`
- PASS `stage_heights_objects_materials_exact`
- PASS `compiled_wrp_embedded_hash_exact`
- PASS `surface_manifest_pass`
- PASS `reference_inventory_count`

## Limits

- Package readback and raw staged WRP identity only; no native engine SurfaceY, rendering, or navmesh acceptance.
- 459 regenerated tile coordinates yielded fewer byte-different PAA entries; PAA equality is measured entry-by-entry.
- Stage object/material equality is checked on raw WRP0WZD before AddonBuilder; compiled payload is verified by OPRW identity/hash and deployed byte equality.
