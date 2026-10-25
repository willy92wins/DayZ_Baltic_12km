# EV95 global dry rollback from the single unconstrained screen

## Decision and scope

This is one deterministic post-processing path for the already completed,
unaccepted global PCG diagnostic. It does not rerun PCG, ADMM, or optimize a
new objective. It starts from that exact continuous vector, clips once to the
existing inward float32 boxes, then monotonically rolls changed vertices back
to EV95 whenever their incident constraints fail. Every rollback is a direct
replacement with the pinned EV95 float32 value; no interpolation, retries,
parameter sweep, or nextafter repair is allowed.

No real map data may be processed until the parent reviews this plan, source,
and fixtures. The source must create an exclusive run directory only after
all input pins and resource admission pass. A later output is always
`PENDING_INDEPENDENT_CONSUMER`, never a map PASS or buildable package by itself.

## Frozen source data

- Base: EV95 terrain `build-wide-slope/candidate/terrain.npz`, SHA
  `40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a`.
- Continuous vector: original reviewed screen `run-01/unaccepted-continuous-vector.npz`,
  SHA `f7412e6f14fc8b5e4fdee4230991927fe912ea87febb242caf3447bee89b8fb1`;
  its source receipt SHA is `f66d7d49cfee0d6bb0844210177e5be7810e1d07970d4a404ecbe9f4c257828d`.
- Physical boxes, variable order, and per-triangle radii: prepared EV95
  `global-dry-solve/prepared-01/bounds.npz`, SHA
  `b0c4499776148b080049a528807e31a62d5fd11ba90fcaae5a7881124cde81fb`.
- The frozen objective and fused-action implementations remain pinned to
  `structured_operator.py` SHA
  `d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a` and
  `fused_normal.py` SHA
  `19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa`.
- Native hinge formulas and source are reanchored to
  `review-independent/verify_ev87.py`, SHA to be checked at execution.

All variables and all non-height arrays remain tied to the prepared EV95
domain. The only possible height changes are the 2,712,136 prepared variables;
everything outside that exact row-major list remains bit-identical to EV95.

## Deterministic algorithm

1. Verify exact hashes and cross-links of base, original screen receipt/vector,
   prepared bounds, operator sources, EV87 hinge source, plan, and fixture
   report. Verify the vector's variable coordinates exactly match
   `bounds.npz`, and `base[variables]` is exactly the prepared baseline.
2. Set each variable to `float32(clip(solution_float64, lower_float32,
   upper_float32))`. Require the resulting float32 value to be inside the
   exact inward float32 bounds. Initialize all other nodes from EV95 unchanged.
3. On the full 2048² grid, identify in chunks every violation against the
   prepared face-radius bound, every failed EV95 non-strict D8 witness order,
   and every newly introduced native hinge angle strictly greater than 30°
   where the same EV95 hinge was at most 30°. The hinge normals/angles use the
   exact EV87 triangle orientation, geometry, and float64 promotion. Chunk
   boundaries include the adjacent cell row needed for horizontal hinges.
4. For every failed face, D8 pair, or new-over-30 hinge, mark all changed
   variable vertices incident to that constraint. Roll the marked values
   back to their EV95 float32 values simultaneously. Never roll a node away
   from EV95 later. Re-evaluate every constraint family over the entire map.
   Each nonterminal round must reduce the changed-node count; a failed row
   with no changed incident vertex is an implementation/source error, not a
   geometric rejection.
5. Stop only when no local failures remain, or terminate INCOMPLETE on the
   600-second deadline, 3-GiB process peak, 6-GiB available-physical-memory
   floor, source drift, or another explicit error. The finite rollback
   sequence has at most one removal per variable, but the runtime budget is
   the practical bound. The watchdog must cover chunk scans and check at every
   chunk boundary.
6. Recompute the original A-objective from the final float32 variable values.
   Emit an unaccepted terrain only if the cost is strictly lower than EV95;
   otherwise record `NO_OBJECTIVE_IMPROVEMENT` and emit no candidate.

The A-only implementation is used for objective accounting; no C/G matrices
are built. D8 witnesses are derived once from EV95 and retained only for the
rollback check. The script does not create a second optimized vector or change
the objective. Face checks use every prepared per-triangle radius. New local
strict minima are prevented by retaining each EV95 non-strict center's
baseline minimum-neighbor witness order; pre-existing strict minima are not
reclassified as newly introduced.

## Independent acceptance remains separate

The author output is not accepted until a separate consumer verifies at least:

- strict objective improvement against EV95 and the intended p99
  non-regression on the declared bank/interior populations;
- protections, prior 499 retained windows/foci, and all metadata/frozen arrays;
- P/F sign topology, compiled physical/visible support and coverage, and the
  existing independent water and corridor contracts;
- full-domain native D8, face-cone, hinge-angle, and other existing global
  shape gates on the actual float32 terrain.

There is no post-quantization repair step here, so the unrelated `OC 1e-7`
micro-repair threshold is not used or claimed. A failed independent gate
rejects this output; this unit does not authorize a second attempt.

## Resources and output

One invocation only: 600 seconds total, process working-set peak at most
3 GiB, and at least 6 GiB free physical memory throughout. Reject admission
before creating the run directory if available RAM is below 6 GiB plus the
3-GiB cap. Use bounded row chunks for all face/hinge scans; do not materialize
the three full hinge-angle families simultaneously. Progress records include
round, chunk, elapsed time, changed count, per-family failure counts, peak
working set, and available RAM.

Only after review and resource admission, a fresh run may write a terminal
receipt and, if objective improvement remains, `candidate-terrain.npz` plus
explicit source hashes and `PENDING_INDEPENDENT_CONSUMER`. No output can be
packaged or deployed from this status.
