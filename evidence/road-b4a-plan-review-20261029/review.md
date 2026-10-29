**Verdict: SOUND-with-fixes.** The scope is right (read-only resolution of the three pieces' build inputs, no build, no re-census), but five concrete points would produce a false result or a budget breach as written.

**Fixes required**

1. **1GiB cap is incompatible with the pinned PBO reader.** Step 3 names "parser ya fijado", and both pinned consumers use `read_pbo` from attach_navmesh, which returns the whole image plus a payload dict. The catalog and B0 runs needed a 2GiB budget for exactly this reason. With a 675MB archive, raw plus entries exceeds 1GiB before the three pieces are even hashed. Either use the streaming `pbo_table` helper (already pinned, used at catalog line 118 with a file handle) to seek and read only the three entry ranges while hashing the whole file in chunks, or raise the cap to 2GiB and say so. As written, the planned run will end in RESOURCE_FAIL on the first attempt.

2. **No aggregation rule for the three statuses, so INPUTS_MATCH can be a false PASS.** Step 5 defines per-entry states and three overall statuses but not how they combine. Define it explicitly: INPUTS_MATCH only if every entry is MATCH; any UNRESOLVED_EXTERNAL, missing file, missing include.lst, or unreadable link metadata forces INCONCLUSIVE_DISCOVERY; any hash drift forces INPUTS_DIFFER. Without this, a report with external rvmat references could still print INPUTS_MATCH.

3. **Text-vs-binarized assets on P: will be reported as drift.** Step 2 compares P: files by SHA against PBO entries. P: trees commonly hold unbinarized rvmat and tga/png textures where the PBO holds binarized rvmat and paa. A byte mismatch there is a format difference, not necessarily a content difference. Add a FORMAT_DIFFERS state keyed on magic bytes or extension, and keep it out of both MATCH and DIFFER. Do not attempt to normalize or convert.

4. **Material and texture coverage from B0 is partial.** The local-faces files only contain Visual and Roadway LODs (consumer discovery line 96 skips the rest). Geometry, Memory and other LODs are not covered, so step 2's "referencias Ãºnicas" is not the full reference set. The catalog's existing per-LOD `textures` and `materials` lists in models.jsonl already cover every LOD without re-running anything. Use that file, pinned by hash, as the reference source and cite local-faces only for the Visual/Roadway subset.

5. **The premise is unpinned.** The intro states the installed catalog and P: differed in asf1_25, but no [EXACT] source backs it. Cite the measurement (path, hash, line) or mark the premise as a hypothesis the discovery will test. Otherwise the report's framing rests on an unverified claim.

**Smaller issues**

- Step 1 reads link metadata from the historical kit7 stage, but the compile helper creates fresh junctions at build time (lines 18-22). State that the resolution target for a future build is P:\DZ directly, and that stage links are only historical evidence.
- Step 4 pins the compile helper while the sources section calls it "NO entrypoint a repetir". Clarify that it is pinned as evidence of the resolution mechanism, not as the future runner.
- The include.lst path in the helper points at a OneDrive worktree. Expect absence; the plan already allows recording it without bootstrap, which is correct.
- For "escape por enlace", specify that the junction target is read once via reparse data and must resolve under P:\ with no further reparse points; Python's `Path.resolve` follows chains silently on Windows.

**What is correct**

- Reusing B0/B3 receipts and SELECTED hashes instead of re-cataloguing 265 or 5509 models.
- UNRESOLVED_EXTERNAL rather than nearest-name satisfaction, and no transitive RVMAT closure claim.
- Fixture list covers the right failure classes, including repinned receipts and byte changes behind matching names.
- Explicitly no pivot/width interpretation, no acceptance of water/terrain/roads.

Apply fixes 1 and 2 before implementation; 3, 4 and 5 can be folded into the same revision.