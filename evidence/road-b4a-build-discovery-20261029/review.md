**Verdict: SOUND-with-fixes.** The extractor is read-only, streams the PBO, enumerates all LODs, and never emits build-ready. Four defects can misclassify the real run, and one path silently follows the SUBST alias the plan forbids.

**Blocking fixes**

1. **Binarized RVMAT signature is wrong, so format and identity get conflated** (`road_build_discovery_ev112.py:64`, `:69-72`). The raP magic is `\x00raP`, not `rap\x00`. A binarized RVMAT inside the installed PBO falls through to the text branch, decodes as UTF-8 (NULs are valid), and matches `stage`/`pix`/`texture` tokens, so it is labelled RVMAT_TEXT. A text RVMAT on P: is also RVMAT_TEXT. Result: DIFFER and aggregate INPUTS_DIFFER for what is a representation difference. Counterexample sample: `b'\x00raP\x00\x00\x00\x00\x08\x00\x00\x00Stage1\x00...'`. Minimum fix: test `s[:4]==b'\x00raP'` first, and reject the text branch when `b'\x00' in s`. The suite has no RVMAT_RAP fixture.

2. **FORMAT_DIFFERS is treated as demonstrated drift** (`:308-310`). Plan §2 reserves INPUTS_DIFFER for comparable drift and §3 says different bytes are not different content. MLOD source on P: versus ODOL in the PBO is the expected state for every real model, so the real run will report INPUTS_DIFFER on format alone. Minimum fix: `drift={'DIFFER'}`; FORMAT_DIFFERS stays in incomplete_coverage and yields INCONCLUSIVE_DISCOVERY. No test asserts the aggregate for this case, so the change breaks nothing.

3. **Alias resolution silently follows the SUBST** (`:192`, `:195`). BUILD_ALIAS_MAP is empty in production, so `P:/` falls back to `os.path.realpath`, which is exactly the uncontrolled resolution plan §6 forbids. The lstat at line 195 is on the realpath result, not on `P:/`, so the PowerShell ReparsePoint/blank-target observation is never recorded or reconciled with the Python attrs 0x31/tag 0 observation. Tests always populate the map, so the fallback is untested. Minimum fix: with no map entry, add comparison `build_alias UNRESOLVED_LINK` and set trusted False; record `link_info` for the raw alias and for the canonical root separately.

4. **Parsed bytes are not bound to the hash that was verified** (`:166-168`, `:92-95`). The contract is hashed, then re-read; equality relies on stat tuples, and mtime/size can be preserved across a rewrite. The catalog data is read after both hash passes and never hashed itself. Counterexample: rewrite models.jsonl between line 92 and line 95 with `os.utime` restored; pins report MATCH while references come from other content. Minimum fix: read once, `h1=sha_bytes(data)`, or `require(sha_bytes(data)==h1,'reparse_mismatch')` after each read.

**False-green gap**

5. **A catalog row with no LODs or an unexpected schema yields INPUTS_MATCH** (`:228-241`). If the real models.jsonl keys differ from the invented fixture keys (`measurement.lods`, `sections[].material_raw`), refs is empty, no reference comparison exists, and the aggregate can be MATCH on three model hashes alone. Minimum fix: require `lods` non-empty per selected row and add a `model_lods` comparison with status UNREADABLE otherwise; write `reference_count` into the report. The catalog schema is pinned by hash but was not shown here, so this is unverified, not refuted.

**Should-fix**

- `is_link` flags any reparse attribute (`:53`). OneDrive placeholders under the build root carry the cloud reparse tag, so dehydrated files become UNRESOLVED_LINK. Not a false green, but coverage collapse on a OneDrive-backed build_root. Check name-surrogate tags only (`tag & 0x20000000`) or the symlink/mount-point tags explicitly, and record the raw tag either way.
- `link_info` only reads the target for S_ISLNK (`:56`). Junctions in the stage return `readlink=None`, so the stage evidence plan §1 asks for is not captured. Attempt `os.readlink` whenever the reparse bit is set.
- `find_catalog` suffix fallback (`:219-220`) matches by name proximity, which §2 of the design forbids. Keep the exact `entry` lookup only.
- Prefix comparison is exact-string (`:261`). If the installed property is lower-case, you get PREFIX_MISMATCH and INCONCLUSIVE rather than a false green. Acceptable, but record both values.
- Pin DIFFER lands in the drift set, so a tampered receipt reads as "P: differs from installed". Use a distinct PIN_MISMATCH status outside drift, or abort.
- `open` after `os.path.exists` (`:247-248`) raises uncaught on a locked PBO instead of UNREADABLE.
- All 5509 catalog rows are parsed into memory (`:201-210`). Budget is fine, but the plan said no mass read. Streaming lines and keeping only selected rows is a small change.

**Test coverage**

- `test_linkescape` skips when symlinks are unavailable, which is the normal state on this Windows host without Developer Mode. Fall back to `_winapi.CreateJunction` so the escape case actually runs here.
- Missing negatives: RVMAT_RAP in PBO versus text on P:, FORMAT_DIFFERS aggregate, empty alias map, pin MISSING, zero-LOD row, root alias being a link.
- `test_FORMAT_DIFFERS` and `test_MIME` assert only membership in comparisons, not the aggregate.
- `test_reportcorruption` is good. `test_contract_hash_before_parse` is good.

**Confirmed sound**

- All LODs are walked, including `materials` lists on non-Visual LODs; `test_allLODextraReference` covers it.
- External references are UNRESOLVED_EXTERNAL and never satisfied by a neighbour (`:299`).
- PBO path safety, duplicate rejection, entry budget, and output non-overwrite all fail before the output directory is created.
- The report fixes `build_ready=False` and the UNKNOWN pivot/width fields unconditionally.

Nothing here authorizes a build. Apply fixes 1 to 5, add the listed negatives, then the real run is worth executing.