**Verdict: SOUND-with-fixes. CONVERGE.** The separation hypothesis is correctly scoped, preserved guards are kept, and no consumed receipt is touched. Five contract-level gaps must be pinned before the contract freezes and before any code. None requires retracting the plan.

## Blocking fixes before contract freeze

**1. Root-level inventory is not closed.** Plan line 57 forbids extras only under work/tools/fixed. The prepared root also holds marker, report and journals, and nothing forbids an unenumerated sibling. The consumed probe allowed `output/`, `logs/`, `process/`, `profile/` at root (`probe_road_compile_c1c1.py:232-243`). A future B mistakenly pointed at the A root would leave such siblings undetected. The contract must enumerate every allowed root entry, including the exact metadata filenames, and the consumer must reject any other entry.
Counterexample N13: valid A output plus an empty `output/` directory at root. Expected: REJECTED with path. Current plan: VERIFIED.

**2. Terminal states and the INCONCLUSIVE versus REJECTED split are undefined.** Lines 95 to 98 name both outcomes but give no decision table. The consumed observer had an implicit one (`observe_road_compile_c1c1.py:140-148`: prerequisite errors become findings, phase incomplete becomes INCONCLUSIVE, pin mismatch becomes rejection). The contract must fix: producer statuses (IN_PROGRESS, PREPARED_PAIR_BYTES_ONLY, PREPARATION_STOPPED with phase and reason), consumer statuses, and the mapping. Minimum: budget or cap stop with internally consistent journals gives INCONCLUSIVE; any hash, identity, inventory, order, binding or cap violation gives REJECTED. The consumer must also check report.contract_sha256 equals the pinned contract, as the observer did (`observe_road_compile_c1c1.py:152`, BINDING), and must require report.status to be the PREPARED value before emitting VERIFIED (mirror of `observe_road_compile_c1c1.py:147`, REPORT_STATUS).
Counterexample N14: report with status PREPARED but phase 3 journal missing DONE. Expected: REJECTED, not INCONCLUSIVE.

**3. Journal binding and ordering are underspecified.** Line 90 freezes only the report SHA externally. Journals are therefore trusted only if the report carries each journal's SHA and the consumer rehashes them. Ordering (N09) needs a defined clock: wall time can step backwards, so each STARTED and DONE record should carry both wall time and a monotonic counter, and the consumer checks strict order on the counter. State who freezes the report SHA (the Codex executor, outside the producer process, from a fresh read of the file).
Counterexample: swap the DONE timestamps of phases 2 and 3 in the journals and leave the report untouched. Expected: REJECTED via journal SHA mismatch. If journals are not bound by SHA, this passes.

**4. Envelope enforcement and finalization time.** Lines 82 to 84 sum to exactly 360 seconds with no reserve for the final report write after phase 3 DONE. Either shrink the subphase sum or define the final report write as part of phase 3 before DONE. Also, the 512 MiB RSS and 360 second wall envelope cannot be enforced by the producer alone: a blocked `open()` never reaches the self-deadline check that caught C1C1 (`probe_road_compile_c1c1.py:25`). The contract must name the external supervisor (executor with kill) and state that a killed run leaves marker plus STARTED and is read as INCONCLUSIVE by the consumer. The marker must be created atomically with exclusive semantics, not check-then-create as in `probe_road_compile_c1c1.py:211`.

**5. Disk and preflight-copy pins.** Line 86 says disk 2 GiB "según límites heredados", but the inherited contract cap was 2 GiB (`contract.json:178`) while the code demanded over 3 GiB free (`probe_road_compile_c1c1.py:211`). State whether 2 GiB is free-space precondition or output size cap, and pick one. Line 56 adds `preflight-local.py` as a destination but no directory is enumerated for it. Pin its location and that B executes that copy with SHA 812e68aa, not the author path.

## Budgets: measured versus inferred

| Phase | Plan cap | Basis | Status |
|---|---|---|---|
| SOURCE_CHECK | 120 s | C1C1 source_checked 70.3 s | measured, same work |
| COPY | 150 s | C1C1 copy interval 103.25 s | measured, same work |
| FIXED_AND_VERIFY | 90 s | observer 85 s for four trees, so about 43 s for two | inferred, different process, likely warm cache |
| Consumer | 180 s | observer 85 s internal for four trees | measured, close analogue |

Phase 3 is the only cap with no same-work measurement. The plan already states that times do not prove sufficiency, so this is acceptable as a declared bet, but the contract should label it inferred so a BUDGET stop there is read as new evidence, not as a regression.

## Oracle notes

- N06 (source changes during read) is not deterministically testable through the real CLI without a pause hook, and a hook would weaken guards. Split it: in-flight identity detection tested at function level on the extracted read-and-hash routine, and post-DONE source mutation tested through the real consumer CLI against the C1B manifest. Record this split in the oracle list.
- N03 is already covered by the inherited directory derivation (`probe_road_compile_c1c1.py:167`, `observe_road_compile_c1c1.py:35-39`): no empty directory is allowed unless listed. The contract should state explicitly that the allowed-empty list is empty for this pair.
- N11 (false green on declared hash) needs a fixture where report and all journals are internally consistent but one destination byte is flipped after DONE. Expected: REJECTED from the consumer's own rehash.

## Preserved checks

Second full read of work, path and handle identity before and after, reparse rejection along ancestors, canonical alias and ancestor pins, logger original bytes, profile before and after, no hash cache, no native launch in A: all present in the plan and consistent with the consumed source. The baseline for B is the C1B manifest SHA b7d33588 plus the A consumer output, which the plan implies but should state.

Nothing here requires product permission already granted, map access, or rerunning consumed scripts.