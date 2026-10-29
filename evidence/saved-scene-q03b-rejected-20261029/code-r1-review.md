**Verdict: SOUND-with-fixes. CONVERGE.** Static read of the four new images only. The twelve R0 findings and the Codex guard list are addressed in both producer and consumer against the real saved schemas shown. Remaining defects are one test that cannot pass as written, one path-binding loophole, dead code, and missing negative tests. None reopens the R0 families.

## R0 items verified closed

- **Pin schema (R0-1).** `saved_scene_io_q03b.py:76` now tolerates the three array-only keys, and every caller passes a projected sub-pin (`saved_scene_binding_q03b.py:207,243,337`; consumer `:58,97,200`). Fixture arrays no longer trip REJECTED_PIN_SCHEMA.
- **Surface inputs (R0-2, F2 refutation honored).** Five keys required at `saved_scene_binding_q03b.py:213`. The value is compared to the discovery manifest source_pin at line 66, derived from the surface_manifest pin path suffix. On the real path this yields the exact worktree key shown in the saved JSON. Fixture mirrors the real shape.
- **Instance counts (R0-3).** The `or True` is gone. Nonvegetation rows are compared exactly at line 281 and in the consumer at line 136. Vegetation is excluded, as the adjudication requires.
- **Epoch literals (R0-4).** Compiled, editable, and PBO keys are built from source_root and a constant at lines 57 to 61. The editable key equals the real stage-kit7 path with no substring match. The consumer checks all three independently at line 74.
- **Pilot links required (R0-5).** Lines 80 to 83 require manifest literal, surface inputs path, and instances path as dict keys. List-shaped pins reject with a clear message at line 76.
- **Archive resolution (R0-6).** Exact `PILOTD/spec.file` lookup at lines 333 to 334, no basename fallback. Consumer line 197 same.
- **Ambiguous/degenerate (R0-7).** Derived from flag bits 2 and 4 at line 291 and compared to expected and to the saved surface report.
- **Proxy routing (R0-8).** Kind 2 rows bound to route root/source at lines 142 to 146. Routes traverse saved proxies by literal slot. Consumer re-derives at lines 146 to 165.
- **NOT_SAVED set (R0-9), spec/site cross-check (R0-10), reparse (R0-12).** Lines 286, 322, 329 and `saved_scene_io_q03b.py:46-49` close these.
- **Memory (R0-11).** Per-archive `expanded_bound` and archive cap enforced before any payload read at `saved_scene_io_q03b.py:164-170`. Pilot arrays are released at line 346. The global total is checked after each archive loads rather than before, but each archive is already bounded to 128 MiB, so the 512 MiB cap is not threatened by the real sizes.
- **dtype matching.** `dtype.str` is used throughout, so `<f8` comparisons are correct. `descr_json` emits lists on both sides, so JSON roundtrip and in-memory rebuild compare equal under `strict_equal`.

## Defects to fix (code only, same four paths)

1. **`test_pilot_two_instances` fails with the wrong code.** `tests/test_saved_scene_binding_q03b.py:117-124` raises instance count to three but leaves the fixture surface report at `instances: 2`. The producer checks the saved surface report at `saved_scene_binding_q03b.py:297-299` before any pilot, so the run rejects REJECTED_COVERAGE, not REJECTED_PILOT_TWO_INSTANCES. Fix: also set the fixture report instances to 3 and repin.

2. **Array path not bound to relative.** `saved_scene_binding_q03b.py:237` accepts `path == join(root, relative) OR path.startswith(root)`. An entry can read file Y under root while being reported as relative X. Drop the `or`. The consumer at line 92 has no path check at all. Add the exact join equality there.

3. **Dead loop with real cost.** Lines 139 to 141 build a set of 539009 tuples and discard it. Delete. Also `tests/...:107` ends in a no-op assertion. Replace with reading the written `failure.json` and asserting the code.

4. **Consumer guard gaps.** The consumer lacks catalog duplicate index/name detection (producer lines 220 to 221), pilot uniqueness (line 324), the core-plus-pilot array kind count (line 240), and the surface-inputs discovery_artifacts key schema check (line 73). Each is a divergence where the producer rejects and the consumer would not. Add them; no producer import needed.

5. **read_snapshot identity on Windows.** `saved_scene_io_q03b.py:40-41` compares `st_dev`/`st_ino` from `lstat` against `fstat`. If the interpreter's lstat fast path reports zero inode, every real read becomes INCONCLUSIVE_SOURCE_CHANGED. This is fail-closed, not a false PASS, and the fixture positive test exercises it on the real interpreter. Treat a positive test pass as proof. If it fails, compare only `st_size` and `st_mtime_ns` plus handle-to-handle `fstat` before and after.

## Real-data risks that cannot be confirmed from the excerpt

- Real pilot pins must contain the instances.npz absolute path as a key. The saved excerpt shows only the first four pairs. If absent, the run rejects REJECTED_EPOCH_LINK at line 82. That is correct fail-closed behavior, not a bug, but it blocks until confirmed.
- Catalog name normalization uniqueness at line 221 over 5509 real names is unverified. A collision rejects REJECTED_CATALOG_DUPLICATE, again fail-closed.

## Missing tests from the R0 list

Still absent: inflated member (central-directory size under cap, stream larger), NPY header length 16385, NPY 3.0 magic, Fortran order, object dtype, directory entry, grid `n*m = 3B+1`, triangle index equal to `n*m`, kind 2 row with mismatched route, and a CLI consumer run against a hand-edited report. The inflated case will reject via CRC failure inside standard `ZipFile` and surface as REJECTED_ZIP_SIZE through `saved_scene_io_q03b.py:210`. The test should assert that code and must not fabricate the exception.

Fix items 1 to 3 and add the consumer guards before the single real run. Items 4 and 5 and the missing negatives can follow in the same correction round within budget.