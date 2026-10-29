**Verdict: REJECT for integration (fail-closed is intact, but the positive path cannot run against the real R0 report, and the only end-to-end tests exercise the same wrong field).**

**Blocking bugs**

- `tools/quality/road_installed_material_probe_ev112.py:158` reads `m.get('normalized')` from each R0 models row. The actual R0 report row has top-level `model` and `entry`; `normalized` exists only inside the `build` sub-dict. `_norm(None)` yields the string `none`, so every derived model key is `('none', entry)`, `derived != want`, and line 165 raises `selected_not_bound_to_r0` on real data. Fix: use `m.get('model')`. The test fixture at `tests/test_road_installed_material_probe_ev112.py:42` also writes `model`, not `normalized`, so `test_positive_end_to_end_and_consume` and `test_helper_ast_require_and_immutable_same_fixture` fail today. Treat the suite as red.

- `road_installed_material_probe_ev112.py:252`: `_require(out.resolve() in dest.resolve().parents or True, 'x')` is a dead check. The `or True` makes the output-ownership assertion unconditionally pass. Safety currently rests only on `_validate_raw_virtual`. Remove `or True` and give it a real message.

**Linkage against actual sources (checked, OK)**

- Lines 138 to 148 match the real schemas: r0_manifest and r0_report carry `tool_sha256`, b4a1_report carries `helper_sha256`, `r0_tool_sha256`, `r0_report_sha256`, `r0_manifest_sha256`, `r0_contract_sha256`, and `contract_sha256` equal to approval's `0559c7...`. No `b4.tool_sha256` is required. Pinned helper `2053b3c8...` equals R0 tool hash. References rows: top-level `normalized`, `entry`, `expected_sha256 == pbo_sha256`, and the external row lacks `entry`/`pbo_sha256`, satisfying lines 159 to 163.

**Unverified schema assumptions (likely to fail-close on real inputs, need confirmation before run)**

- Line 126 requires entries.json to be exactly `{"entries": [...]}` with no other top-level keys. Line 170 requires each entry to carry `name`, `normalized_name`, `size`, `mime`, `sha256` and at most `category`. Line 310 then requires every catalog entry to exist in the live roads table with equal size and mime. Any extra key or catalog subset mismatch aborts.
- Lines 176 to 179 and 184 require models.jsonl rows with `name` equal to the full virtual path (`dz/structures/roads/parts/...`), `status == READ_STRICT`, and `measurement.lods[].textures/materials` or `sections[].texture_raw/material_raw`. If `name` is the PBO entry name or the LOD reference fields differ, line 184 or 196 aborts. The plan's F3 correction (refs come from models.jsonl, table from entries.json) is honored structurally, but the field names are guessed.
- Line 115 pins every `.py`/`.pyd` under `psutil_root/psutil` recursively. A standard psutil package ships `psutil/tests/*.py`. The actual contract pins 11 files. If a tests folder exists, line 118 raises `missing_pin`. Line 117 also admits any pin whose key starts with `psutil_root` without verifying it exists, a small loosening of "every pin verified".

**Stream bounds and PBO identity (OK)**

- Extraction at lines 263 to 273 is chunked, bounded per resource and total, guards truncation. `pbo_table` already bounds `offset + size <= length`. Whole-file hashing before and after (lines 281, 287) reads roughly 1.1 GB total across three PBOs, well within 120 s. Same-handle identity via `fstat` vs `lstat` before and after is sound. Double close via `ExitStack` plus `_finish_pbo` is harmless.

**Provider matching (OK)**

- Line 334 compares `norm(prefix) + '/' + entry` to `norm(ext)` literally; no basename matching. Missing prefix or missing PBO yields `INCONCLUSIVE_PREFIX_UNKNOWN`, two matches yield `AMBIGUOUS_PROVIDER`, zero yields `UNRESOLVED_EXTERNAL`. Correct per contract. Roads is never a candidate for the external, which is fine for `dz/surfaces/...`.

**Conversions, PID birth, closures**

- Line 226 argv `[CfgConvert, -txt, -dst, decoded, original]` matches the anchored invocation. Receipt checks at lines 229 to 238 correctly handle JSON stringified PID keys and compare birth to `running.json`. Runner falls back to `birth=None` when psutil misses the child, and line 232 fails closed. Good.
- Line 356 calls `conv_factory()` per RAP asset, so `_verify_runner_import` re-executes the runner module and re-hashes psutil twice. Not a correctness bug, but wasteful and it re-runs `sys.path.insert`. Build the converter once.
- Line 238 compares `rc`/`reason` between completion.json and the returned dict, but the stdout/stderr hashes in the receipt are never cross-checked or recorded in the report. Minor.
- Nothing exercises `_default_converter_factory`. Every RAP test injects `converter=`, so PID birth, receipt presence, pinned runner import, and psutil rooting have zero coverage.

**Saved consumer**

- Lines 384 to 399 verify manifest hash, contract linkage, report hash, status, closure flags, and each artifact's size and hash. Artifact count is derived from `EXTRACTED` plus `DECODED_SAMPLE_ONLY`, which works because report and manifest share the same asset dicts (lines 319, 344). It does not check that the manifest `assets` list has exactly 7 roads entries plus the external, nor that each asset's `sha256` equals the artifact entry. Acceptable for initial discovery, but note it as not independent.

**Negative fixtures present vs missing**

- Present: traversal, duplicate entry, duplicate catalog model, unsupported MIME (selected and external), wrong path with known prefix, missing prefix, ambiguous provider, text/RAP/UNKNOWN material, bad rc, timeout, empty exit 0, converter mutating input, post-extraction artifact mutation, fake closed status, size range, strict JSON, bool limit, extra contract field.
- Missing: reference only in a non-visual LOD, same basename under a different provider prefix that must stay `UNRESOLVED_EXTERNAL`, catalog entry absent from live table, psutil pin or runner pin drift, real factory receipt validation (bad birth, missing completion), `CONVERSION_BUDGET_EXHAUSTED` with a third material, and `total_output_bytes` exhaustion. Procedural textures, nested nodes, macros, cycles, and depth belong to the later closure phase and are correctly absent.

**Smaller items**

- Line 324 reports a missing surfaces PBO as `MISSING` without `_no_reparse`, acceptable since no read occurs.
- Line 295 only rejects drive `P:`; a junction into P: under `out` is caught later by `_no_reparse` in `_safe_local`, but only after `out.mkdir` at line 298.
- Line 299 `all_lod_refs` dumps every reference of the three models into the report, which is fine since paths are not geometry.

**Summary**

Fix line 158 to `model`, fix line 252, consolidate the converter factory, confirm models.jsonl and entries.json field names and the psutil directory listing against the real files, then add the missing negatives. Contract and status labels are unchanged and not loosened.
