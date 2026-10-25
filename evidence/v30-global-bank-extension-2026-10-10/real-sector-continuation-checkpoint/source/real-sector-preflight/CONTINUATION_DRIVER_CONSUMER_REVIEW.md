# Continuation driver and independent consumer

Prepared only; no real continuation, candidate, or terrain write was run.

- Driver `solve_real_sector_continuation.py`: SHA-256 `7a8625a43f1610322f1f32bc1d20bbb5b7fcace1e3259bec7577c0c27660e9cb`.
- Consumer `verify_real_sector_continuation.py`: SHA-256 `5952de0210215275cf8ed67d644dd4a9bd0325b95c1dfda07751510ad9ad821f`.
- Consumer lineage fixture `test_continuation_consumer_lineage.py`: SHA-256 `529ec25138d02aea11aee9ba21f24fb4224b5fdff7eff3cd038019baa2f375dd`.
- Cached source driver remains SHA `5e75e0e1d3e3c6938679cd31e87f4f317353e64ff919c471d79d1a04d50f98f9`; cached consumer remains SHA `3e7a6996f5e4b637ba7d94ad20dd3add6643f52db31d7098c6baa32e238d4799`.
- Frozen original ADMM solver remains SHA `7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149`; continuation helper pin is `b852af714667e8b07944a97fbdbaba97fe0c2b90c3a555ff9821ef11fe6791d2`.

The continuation driver extends the readset from 30 to 37 pinned paths, verifies all 19 prepared arrays against attempt 02 bit-for-bit, validates the exact nonconverged parent and state, and permits only the fixed `solve-run-03-continuation` output. It restores the global iteration/cg counters and unscaled y duals at rho=2, with rho adaptation still frozen after global iteration 2,000. The consumer independently pins the parent result and validates the same prepared arrays, iteration/rho/update lineage, and 300-second additional / 600-second cumulative resource limits as an explicit gate.

GIS Python checks:

- `py_compile` passed for driver, consumer, and lineage fixture.
- Driver pin contract and `verify_parent_checkpoint(parent_prepared)` passed: 37 pinned inputs, 19 arrays exact, parent iteration 10,000, no candidate.
- Consumer readset passed for 47 paths; driver identity matched its consumer pin.
- Consumer lineage fixture passed valid synthetic continuation metadata and rejected an off-by-one starting iteration.
- Existing consumer self-fixtures passed.

The reports above validate the implementation and pinned parent artifacts only. Root must still review, run the new preflight, and decide whether to launch the one continuation.
