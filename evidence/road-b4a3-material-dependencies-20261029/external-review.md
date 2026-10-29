**Verdict: SOUND-with-fixes.** Nothing I read produces a passing report on bad input in production code. The weaknesses are in test rigor, one unused stat snapshot, and consumer checks that are narrower than they could be. Scope: this offline unit only. Nothing here approves the native engine, build, or the 5509 models.

**Verified findings (from reading the code as pasted)**

1. **Test fixture opener looks wrong.** `tests/test_road_material_dependencies_ev112.py:32` builds the stage class as `f"class {name}\""`, which emits `class Stage1"` with no `{`. The producer lexer would then read a string token spanning into the texture line and fail on the first backslash. If this is the real source and not a paste artifact, every positive test fails and every `assertRaises(Exception)` test passes vacuously. Fix: `f"class {name}{{"`, and add a one-line sanity assert at the top of each negative test that `prod.parse_rvmat(make_text())` succeeds.

2. **Negative tests accept any exception.** All negative cases use bare `assertRaises(Exception)` (lines 73, 78, 82, 103, 109, 121, 136, 151, 169, 185, 200, 207). A `NameError`, `KeyError`, or `TypeError` from a broken fixture satisfies them. This is the main false-PASS shape in the unit. Fix: `assertRaisesRegex(prod.RvmatError, "unknown_assignment")` and similar for each case, and `ValueError` with the reason string for range, stat, and leaf-set checks.

3. **Unused handle snapshot during table read.** `tools/quality/road_material_dependencies_ev112.py:480` captures `sh_table` from the handle used for `pbo_table` and never compares it. The hash-before, extract, and hash-after handles are compared, but the table-reading handle is not. Fix: `compare_stat_snapshots(sp_b, sh_b, sp_b, sh_table)` immediately after line 480. Same file, `hash_pbo` returns a path-after snapshot that `run` discards at line 476 (`sp_mid`) and `main` discards at 556. Compare them or drop them.

4. **Consumer range check has no upper bound.** `verify_road_material_dependencies_ev112.py:192-206` checks mime, size, and offset sign, but not `offset + size <= 318217469` even though the consumer already pins that size at line 255. Fix: add `file_size` parameter and the bound check, mirroring the producer. Test line 159-163 only exercises the mime case on the consumer side.

5. **Consumer does not tie leaf entry name to virtual path.** `verify_road_material_dependencies_ev112.py:299` compares sha, size, offset, and mime between report and contract leaves, but ignores `entry.name`. The producer checks it at lines 486-491, so a co-mutation of `entry.name` in contract and report is invisible to the consumer. Fix: require `normalize(lr.entry.name) == normalize(lc.entry.name)` and that the virtual path ends with that relative name after the prefix.

6. **Missing-field defaults in the source-table compare.** `road_material_dependencies_ev112.py:324` defaults `mime`, `size`, and `offset` to 0 when absent. A source table entry missing `mime` silently equals a live mime of 0. The brief says `source_table.json` has 501 entries, and `entries.json` has no offsets. If the pinned source table also lacks offsets, every run fails closed at line 345, which is safe but will need a contract decision. Fix: raise on missing keys instead of defaulting.

7. **Catalog membership check is loose.** `road_material_dependencies_ev112.py:360-364` treats any 64-hex string anywhere in the catalog as a sha. A leaf sha appearing in an unrelated field would satisfy line 431. This cannot produce a false pass on its own because leaf bytes are still hashed against the contract, but the check proves less than its name suggests. Fix: restrict to values under `sha256`, `sha`, or `hash` keys.

8. **Consumer does not check `report.pbo.sha256` or `catalog_pins`.** Lines 255 and 251 check `sha256_before`, `sha256_after`, models, and catalog, but not the plain `pbo.sha256` field or the `catalog_pins.source_table_sha256` field. These are stale-field risks, not false-pass risks. Fix: compare them to the contract.

9. **Consumer accepts any `eof_state`.** `compare_parsed` only requires report and reconstruction to agree. If the frozen brief fixes EOF newline, pin it in the consumer alongside `EXPECTED_INVENTORY`.

**Verified as correct**

- Report key set at producer line 571-586 matches `REPORT_KEYS` at consumer line 20 exactly, 19 keys each.
- Token dict shape, assignment dict shape, and `texture_refs` shape round-trip through JSON and match between producer and consumer, so `compare_parsed` on `tokens` and `texture_refs` is a real equality, not a trivially-true one.
- Inventory arithmetic for the frozen shape is 20/4/6/8/5/1/24 under both parsers.
- Both number lexers reject `1.`, `.5`, `1e5`, `-1`, `+1`, and both treat backslashes inside strings as literal bytes.
- Capture count 51 at consumer line 128 is right for the anchored pattern.
- Failure path in producer `main` can only write `INCONCLUSIVE_DEPENDENCIES`, and both output and marker use exclusive creation.
- Consumer never opens the PBO path, as required.

**Hypotheses (not verifiable without the helper)**

- The producer assumes `helper.pbo_table` returns entries with keys `name`, `mime`, `size`, `offset` (lines 492, 540). Other key names produce `KeyError` and a fail-closed result, never a false pass, but the unit cannot pass at all until confirmed.
- `read_payload(f, entry, digest)` is assumed to raise on mismatch. The producer re-checks the hash at line 542 anyway, so a silent helper would still be caught.

**Missing integration tests**

- No test drives `prod.main` end to end with a synthetic contract, a stub helper module exposing `pbo_table` and `read_payload`, and the `build_pbo` fixture. The fixture at test line 43 exists but nothing exercises the contract-to-report wiring.
- No test calls `cons.verify` against a producer-written report. The co-mutation requirement in the brief is only covered at the `validate_leaf_set` level, not at the contract-plus-report level.
- No test exercises `test_output_exists_exclusive` for the attempt marker or for the consumer `--output` path.

**Recommended order of fixes:** test fixture opener, replace bare `assertRaises(Exception)`, compare `sh_table`, add the consumer bound check and entry-name check, then add one end-to-end test with a stub helper before any real extraction.