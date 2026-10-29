## Verdict: SOUND-with-fixes

The split is functional and materially breaks the R0/R1 loop: one new reader module plus one test slice, producer/consumer semantics deferred to separately authorized cuts, the wrong-proxy repro explicitly carried as cut-2 debt rather than claimed fixed, and the green state honestly capped at `READER_FIXTURE_VERIFIED_ONLY`. Original constraints are preserved by pin (contract R1 `e967…`, oracles `b4ba…`, universe 5509+6, 201 pilots, `(n,12)`, 43 ambiguous, epoch `3d9550bf`, caps). Budgets are real: 120s author / 90s review / 60s·256MiB suite, one 120s correction only against an executable repro from the closed set, suite re-run only after a delta. This review does not authorize cut 2, cut 3, or any real capture.

## Concrete defects to fix before coding

1. **NPY2 root cause not pinned explicitly.** The plan says "pre-read header length" but never states the version-dependent width: NPY 1.0 uses a 2-byte `<H` length, NPY 2.0 a 4-byte `<I` length. That omission is exactly repro 2 (`unpack requires a buffer of 4 bytes`). Write the width-per-version rule and the exact magic/version acceptance (major 1/2, minor 0 only) into the plan, not just "NPY1.0 and 2.0."

2. **`max_header_size=16384` boundary is ambiguous.** "Header 16384 valid / 16385 rejected" does not say whether 16384 counts the header-dict bytes alone or the full header including the 10/12-byte prefix. NumPy's own accounting differs by version. Fix the counting convention, or the boundary positive/negative pair is untestable as written.

3. **`inspect_npz(bytes, …)` contradicts reserve-before-allocate.** By the time a caller hands over `bytes`, allocation already happened, so the global budget cannot be reserved "ANTES de leer" on that path. Either restrict `inspect_npz` to bytes already charged by `load_verified_npz`/`read_snapshot`, or state it is a pure validator with no budget guarantee. Also, `load_verified_npz(...)` is still fictional; the plan's own "close API against real definitions first" gate must freeze who owns the budget (the `cap` argument vs `limits`) — one owner, not both.

4. **Limits lack per-scope units.** "16MiB almacenado, 128MiB archivo expandido, 262434599 total" does not say per-member vs aggregate, nor what 262434599 counts (bytes? elements?). Likewise "comprimido no admitido" never names the admitted compression set (stored only, or deflate too). The historical NPZ format decision hides here; pin both before coding or cut 3 will discover the mismatch.

5. **No closed error-code table.** Failure states are well separated (`OSError → INCONCLUSIVE_SOURCE_IO`, identity change → `INCONCLUSIVE_SOURCE_CHANGED`, internal bugs not laundered into `SOURCE_IO` — correct, and no inode/OneDrive speculation). But "each negative reaches a precise code" has no enumerated code list (header-too-large, unsupported version, trailing bytes, duplicate member, …). Without the table fixed pre-code, tests will invent codes ad hoc and the "precise code" requirement is unenforceable.

6. **Oracle independence is asserted, not enforced.** The literal external oracle (NPY1/2 headers, `float64[-0,1]`, 2×12 matrix, META35 bytes) is the right design, but the plan doesn't state it is authored and pinned by someone other than the executor before code exists. If the same executor writes oracle and reader, the oracle is self-consistent, not external. Pin its author and hash.

7. **`descriptor_json` needs its construction rule.** Repro 1 truncated `<i4` to `<`. Saying "report dtype as complete field list" doesn't forbid the slicing bug. Require building from `dtype.fields`/`dtype.descr` verbatim (name, format, offset, itemsize) and add the structured `<i4` case as a named positive, plus exact META itemsize/offsets — "35 bytes complete" alone doesn't fix field layout.

## What needs no change

Deferring the proxy to cut 2 with the debt stated openly; snapshot identity checked before/after with SHA of the parsed bytes; no NPZ mmap, no pickle, no fallback; ZIP duplicate/directory/path/encryption and pre-allocation shape-product guards; the stop rule via gates-ledger and the refusal to re-audit the R1 postimage.

Fix items 1–6 in the plan text (item 7 is one line), then the slice is executable as scoped.