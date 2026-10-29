**Verdict: NEEDS-WORK.** Static read only, no tools run. Two defects make the producer and consumer reject the real (and the fixture) data outright, one check is disabled with a literal `or True`, and several contract-mandated links are either substring-matched or never asserted. The test suite as written cannot pass, so no passing run should be believed until these are fixed.

## Blocking bugs

1. **Every NPZ array is rejected by pin schema.** `saved_scene_io_q03b.py:66` requires pin keys to be exactly path/sha256/bytes with no optional set. The producer calls it with the whole array entry at `saved_scene_binding_q03b.py:163`, and the consumer at `verify_saved_scene_binding_q03b.py:68`. Array entries carry relative/kind/expanded_bound, so `req_keys` raises REJECTED_PIN_SCHEMA before any array is loaded. The fixture arrays carry the same six keys, so `test_positive_literal_oracle` and every pilot negative test fail at the first array rather than on the intended condition. Fix: pass a projected dict or add `optional=("relative","kind","expanded_bound")`.

2. **Real surface inputs.json is rejected.** The saved file has five top-level keys including `artifact_manifest_sha256`. The producer at `saved_scene_binding_q03b.py:146` and the consumer at `verify_saved_scene_binding_q03b.py:54` require exactly four keys, so the real run yields REJECTED_METADATA_FIELD. The fixture omits that key, which is why the tests cannot detect this. The contract also says the original surface artifact manifest SHA must be preserved, so this key should be required and compared against `pins.surface_manifest.sha256`, not rejected.

3. **Catalog instance counts are not verified.** `saved_scene_binding_q03b.py:195` ends in `or True`, so REJECTED_INSTANCE_COUNT can never fire. The catalog row for index 0 declares 11240 instances and the contract requires the per-model instance census. The consumer never checks this either, so a mismatch produces a false PASS on both sides.

## False PASS and fail-closed gaps

4. **Editable WRP epoch is never checked on real data.** `saved_scene_binding_q03b.py:46` fires only if the pin path contains the substring "editable". The real editable path is `stage-kit7-fc-20261026\root\...\baltic_trial.wrp` and contains no such word, so the check silently passes. The consumer at `verify_saved_scene_binding_q03b.py:62` does not check editable at all. The contract says exact named pins, not substrings. Fix: match the three epoch paths literally against the contract and require all three to be present.

5. **Pilot pin links are optional instead of required.** Lines 53 to 56 only verify pins that happen to collide with contract paths. If the real pilot pins omit the instances archive or surface inputs path, nothing fails. Contract epoch_binding requires `pins[surface inputs path]` and `pins[instances path]` to exist and match. Also the real pilot inputs excerpt renders pins as a list of pairs; if the saved key is a list, line 52 rejects with the misleading code REJECTED_EPOCH_LINK. Confirm the real shape before relying on the dict path.

6. **Basename fallback for pilot archives.** `saved_scene_binding_q03b.py:249` and `verify_saved_scene_binding_q03b.py:117` resolve the archive by `endswith(basename)`. The contract forbids basename fallback. Resolve by exact `pilot-visible-surface-extraction-20261028/` + `spec.file` and reject otherwise.

7. **Ambiguous and degenerate counts are not derived or compared.** Coverage `ambiguous` sums pilot spec fields, which are all zero, while the contract expects 43 from the prototype flags. Line 255 deliberately excludes `ambiguous` and `degenerate` from the expected comparison, so the report states 0 against an expected 43. Either derive from `meta.flags` with a declared bit and compare, or record NOT_EVALUATED explicitly; never emit a contradicting integer.

8. **Kind 2 proxy routing is not bound to faces.** `validate_meta` only bounds `proxy` to 0..6. Nothing checks that each kind 2 row's (model, source_model, proxy) resolves to a proxy-paths route with root_model and source_model matching, nor that route `source_model` exists in model-sections. Contract identities.proxy requires this.

9. **NOT_SAVED is not restricted to vegetation.** Lines 200 to 202 only compare the count 72. A nonvegetation model with zero saved faces would offset a vegetation model and pass. Assert `group == "vegetation_not_inspected"` for every NOT_SAVED row and the converse.

10. **Spec model name and index not cross-checked.** Pilot rows copy `spec.model` and `spec.model_index` without asserting the catalog row at that index normalizes to the same name, and without asserting `spec.site` equals the catalog `site`. Site counts 139/26/9/27 are not verified.

11. **Expanded-memory bound is not enforced and per-pilot release is absent.** `limits.total_expanded_bytes` is never read. `load_npz` sums member sizes only after reading them all (`saved_scene_io_q03b.py:151`), and the producer retains all 201 pilot array sets in `pilot_arrays` plus `tobytes` copies, contrary to "release per-pilot before next". Rough footprint is prototypes plus 201 pilots plus digests, close to the 512 MiB RSS cap. Enforce the running total before each `zf.read` and drop each pilot after its digests are recorded.

12. **Reparse detection is incomplete on Windows.** `Path.is_symlink` is false for junctions and other reparse points. Use `os.lstat` and test `st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT`.

## Independence and consumer

The consumer is a near-verbatim copy of the producer's semantic walk, including the same basename lookup, the same four-key schema, and the same models builder. It is nominally separate but shares every bug above, so it provides no independent detection. It also drops checks the producer has: META descr, kind ≤ 2, vertices 3..4, proxy 0..6 for kind 2, category sum equals B, pilot `_n`/`_flags`/`_source_ids` dtype and shape, grid dtype, scalar dtype, `bed_source_face`, and the editable epoch. Any defect in those areas that the producer misses is therefore undetectable by the consumer. The `strict_equal` walker is fine and does enforce int-vs-bool.

Dead code to delete: `saved_scene_binding_q03b.py:22` (`if False else True`), line 130 (reads and discards surface inputs, then line 135 overwrites it).

## Test suite problems

- All negative tests assert on a substring of code plus message, so "PILOT" and "CAPS" match many codes. `test_pilot_two_instances` sets an unknown id, exercising zero rows, not two. Assert exact codes.
- Fixture `source_pins` uses the literal key `wrp_compiled` rather than a path, so epoch matching by substring is never exercised against real naming. No `test_epoch_wrong_pbo`, which the contract mandates.
- `test_negative_zero_and_winding_preserved_by_digest` only checks a key exists. Build twice, once with +0.0 and once with -0.0, and assert the digest differs.
- No consumer negative test: mutate one report field and assert REJECTED_REPORT_MISMATCH, add a key and assert REJECTED_UNKNOWN_KEY.

## Independent tests to add

1. Real-shape surface inputs fixture with `artifact_manifest_sha256` and real-looking WRP paths; assert PASS, then flip the editable SHA and assert REJECTED_EPOCH_WRONG.
2. Catalog row instances 5 against 1 pose row; assert REJECTED_INSTANCE_COUNT.
3. Remove the instances path from pilot pins; assert rejection.
4. Pilot archive renamed to `other/cs_kit_118_0000.npz` with spec file unchanged; assert REJECTED_PILOT_ARCHIVE.
5. Kind 2 row with proxy 0 while proxy_paths is empty or root_model differs; assert REJECTED_LOST_PROXY_ROUTE.
6. Nonvegetation catalog row absent from meta while a vegetation row is present; assert rejection.
7. NPY header length 16385 in a crafted member; NPY 3.0 magic; Fortran order; trailing bytes; `allow_pickle` object dtype; duplicate ZIP member; directory entry; each must reject with the named code and before `np.load`.
8. Member whose central-directory `file_size` is under cap but decompresses larger; assert REJECTED_ZIP_SIZE, not an exception path.
9. Duplicate JSON key and `NaN` constant in a pinned JSON; assert REJECTED_JSON_*.
10. Output directory pre-existing; assert REJECTED_OUTPUT_EXISTS with no partial write.
11. Pilot `source_grid` with n·m = 3B+1; assert REJECTED_PILOT_GRID_BOUND. Triangle index equal to n·m; assert REJECTED_PILOT_TRIANGLE_RANGE.
12. Consumer run against a hand-edited report (one coverage integer changed, one `historical_checks` bool changed); assert mismatch.

Summary: fix items 1 to 3 before any run, then add literal epoch and link requirements, exact archive resolution, proxy route binding, and the memory bound. Re-run the suite after making negative assertions exact, and treat the current consumer as a duplicate rather than an independent check until it carries at least the producer's full guard set.