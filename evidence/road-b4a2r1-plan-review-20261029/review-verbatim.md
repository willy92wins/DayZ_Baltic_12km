**Verdict: SOUND-with-fixes.** The literal fix matches the real runner contract, and the plan keeps one pending conversion. Two gaps need closing before the recovery runs.

**What checks out**

- **Field/filename fix is literal and correct.** The runner writes `stdout`/`stderr` (no extension) and emits `stdout_sha`/`stderr_sha` in both completion.json and its return dict. The diff reads exactly those. The saved receipt hashes are the empty-input SHA-256, consistent with the empty stream files the fixture test writes.
- **Stricter, not looser.** The old `in (None, hash)` tolerance on the result dict became strict equality. Good: a runner that omits stream hashes is now rejected rather than waved through.
- **PID/birth linkage holds against the actual receipt.** running.json pid 72168 and birth appear in completion identities with the same float. The second identity (82756) is a descendant and is correctly ignored by the check. JSON stringifies the int keys; the probe tolerates both forms.
- **Mock-vs-reality failure is now covered.** The new test loads the real receipt JSON rather than the mock's schema, which is the regression that caused the INCONCLUSIVE. That is the right fixture.
- **Separation of facts is preserved.** Parent failure at 2.375s and child rc0 at 0.344s stay distinct. No retroactive INITIAL_DISCOVERY_ONLY, no report repair, no promotion on partial failure.
- **Runner prevents output-dir reuse.** `mkdir(exist_ok=False)` on the receipt dir makes rewriting conversion_1 receipts in place physically fail.

**Findings requiring fixes**

1. **No test proves conversion 1 is verified without launching.** The diff and all tests exercise the run path. The plan says conv1 is receipt-verification only, but nothing asserts that the runner is never invoked for RVMAT1 (for example `runner.calls == 0` when receipts/conversion_1 already exists and validates). Without that, a reviewer cannot distinguish recovery from a quiet second run of conv1. Add a fixture test: pre-existing conv1 receipts, consumer accepts, runner call count zero.
2. **"At most one new CfgConvert" is a policy, not a mechanism.** The runner only blocks reuse of the same directory. A retry under a new directory name is still possible. Pin the second conversion's receipt dir to a fixed name such as `receipts/conversion_2`, so a repeat attempt hits the existing `exist_ok=False` guard and fails rather than silently producing conversion_3. Add the corresponding negative test.

**Smaller items**

- The fixed probe does not check `running['input_sha']` against the RVMAT1 hash or `running['executable']` against the pinned CfgConvert. The plan assigns these to the new unit. Make sure they land there with fixture tests, since the current 39 passing tests do not cover them.
- Naming drift: the consumer emits `stdout_sha256` while embedding the raw `completion_receipt` with `stdout_sha`. Both are correct, but document that the enriched keys are consumer-normalised to avoid a repeat of this exact mismatch downstream.
- Runner race: if CfgConvert exits before `psutil.Process(child.pid)`, birth is null and the probe rejects with `conversion_birth_receipt_missing`. That is a false reject, not a false accept. Acceptable under the no-retry rule, but note it as a known failure mode so it is not misread as a corrupt receipt.
- The fixture test mocks `_verify_runner_import`, so the psutil pin check is bypassed there. Fine, since the pin test exists separately, but the recovery unit itself must not mock it.

**Scope confirmation**

- Only RVMAT2 is pending. RVMAT1 text exists, is non-empty, and is correctly treated as unparsed bytes with no transitive-closure claims.
- Output state MATERIAL_SAMPLES_RECOVERED_ONLY with build_ready=false and dependency_closure=NOT_EVALUATED is appropriate for two literal samples.
- Budgets (30s/256MiB per conversion, 90s/512MiB per unit) are consistent with the 0.344s observed run.

Proceed to the 120s implementation window once findings 1 and 2 have tests written.
