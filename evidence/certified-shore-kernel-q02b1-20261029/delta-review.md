**Verdict: SOUND-with-fixes** (conditional on the suite currently running on the final source passing; no result exists yet for the three new root tests, and no corpus run).

**Previously flagged blockers are closed in the diff**

- idiv log overwrite: producer `fdiv` now uses `logop` append (`certified_shore_kernel_ev112.py` hunk @-62). Consumer `idiv` emits once with `_emit=False` on the inner `imul`, so no double certificate.
- Ignored window expectation: `if kind=='window' and rec['state']!=obj['expected']: raise Bad('windowexpected')` is now unconditional.
- Empty or partial proof: exact set equality `req!=rep` → `Bad('proofset')` is applied to old, window, station and interval kinds, and only skipped when both sides are RESOURCE_INCONCLUSIVE. Extra valid-but-unrequired certificates are also rejected by set equality.
- Per-entry cap reset: `verify_transcript(rec,cap)` shares one `CapB` with the expected computation and all `cmp_*`/`encloses` calls. `cap.events=None` during transcript validation correctly suppresses emission, then `cap.events=[]` before the walk.
- Closed duplicate and h0: strip applied identically in producer `compute_window_core`, producer station branch, consumer `expected_window`, and consumer station branch, all after `pts=list(pts)` and before `is_degenerate`/`degenerate`. `center_index` bounds checked in both.
- Root precharge: producer `b.tick(16)` and consumer `cap.tick(16)` precede shift/isqrt; `verify_witness` charges 10 before any product. Test patches `isqrt` to assert no execution after exhaustion.

**Fixes (non-blocking)**

1. **VERIFIED can be emitted while a record is RESOURCE_INCONCLUSIVE.** In the window/station/interval branches, `Cap` inside `expected_window`/`walk_locate` is caught locally and becomes `exp['state']='RESOURCE_INCONCLUSIVE'`. If the contract's `expected` is also RESOURCE_INCONCLUSIVE, the record passes, the proofset check is skipped, and `resource_inconclusive` stays False, so the final status is `VERIFIED_NUMERIC_KERNEL_ONLY`. Not a forgery path (contract must declare it), but the top-level status overstates. Fix: set `resource_inconclusive=True` whenever `rec['state']=='RESOURCE_INCONCLUSIVE'`, or add an inconclusive record count to the output. Anchor: `verify_certified_shore_kernel_ev112.py` main loop, `except Cap: exp={...}` and `verified=not errors and not resource_inconclusive`.

2. **Bogus transcript that exhausts ops yields RESOURCE_INCONCLUSIVE, not REJECTED.** `except Cap: resource_inconclusive=True` in the record loop means a forged 4000-root transcript on a real record reports inconclusive rather than rejected. Never VERIFIED, so not a soundness hole, but `test_actual_query_operation_cap_before_root` hard-codes this as the expected status. Consider rejecting when Cap fires inside `verify_transcript` specifically (producer-side transcript size is the producer's fault) while keeping inconclusive for Cap in the expected computation.

3. **Unconfirmed test arithmetic.** That same test needs 4000 sqrt_interval entries to exceed 100000 ops inside `verify_transcript`. Per entry: `tick(10)` in `verify_witness` ×2, plus `ipair`/`pair`/`mk` ticks. If per-entry cost lands under 25, the loop finishes, `proofset` raises `Bad`, status is REJECTED, and the test fails. This is a test-correctness question, not a kernel issue; the running suite decides it.

4. **Redundancies, harmless:** `load_pin` re-checks length after `read_bounded`; `ce` re-checks witness bits already covered by `fl`; producer `sqrt_witnesses` witness check is always true for `isqrt(n//d)`.

**Set-equality caveat, accepted as designed**

`rep` is built from `json.dumps` of raw transcript entries, so a non-normalized fraction (e.g. `[2,2]`) would pass `ipair` validation but mismatch the canonical `enc_iv` string and be rejected. That is conservative (false reject, never false accept) and consistent with the stated set-not-multiset intent.

**Next:** confirm the suite result on the final source, then a real corpus run. Atan2 remains pending per the stated scope.