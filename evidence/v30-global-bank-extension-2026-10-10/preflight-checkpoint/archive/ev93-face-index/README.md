# EV93 global ODOL face-range index

Status: source and synthetic fixtures prepared for review. The global index build has **not** been run. This folder contains no terrain candidate and does not invoke a solver, DayZ process, MCP, or build tool.

`build_face_index.py --build` is the only build entry point. It reads B's staged `0WZD`, deployed PBO and extracted ODOL sources, verifies their existing manifests/pins, and writes a new timestamped run under `ev93-face-index/runs/`. It refuses output roots outside this folder, caps shard output at 2 GiB, and uses a 10-minute deadline. An interrupted/error run is labeled incomplete and is never queryable as complete. Source objects, models, P/F, and terrain are read-only.

## Frozen anchors

- EV87 source: `v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py`, SHA256 `964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27`. Its `compiled_objects`/`compiled_exposure` path supplies the exact water-object name filter, identity translation requirement, `float32(3e15)` physical and `1.0` visible LOD selection, triangular faces, translated XYZ, and XZ area behavior.
- EV90 preflight source: `v30-wide-bank-fairing-pilot-20261010/next-method-preflight/ev90_preflight.py`, SHA256 `5892e917335ca2d8caa427f04f48ba8acbd8e16a5e1b400be596d5dd636afb7f`. The builder calls its frozen `check_linkage_and_load()` to verify B, source WRP, PBO linkage, deployed artifacts, bounds manifest, and read-only readers. It also checks the object-ID/model/transform/bounds linkage used by EV90's compiled-face scan.
- Approved EV93 plan: SHA256 `ccc018a9e1cc8a51b075a91905b1cbe7d3cdaf72040e51992f2ac55db8ad7e82`.

The staged WRP, OPRW payload extracted from the deployed world PBO, and bounds manifest remain separate identities in the manifest. The object transforms come from the staged `0WZD`; the model files come from the pinned staged model directory and must match the per-model SHA in `compiled-instance-bounds.json`. The builder does not claim that it extracts object transforms from the OPRW.

## Shard schema and query API

`manifest.json` uses schema `ev93.face-range-index.v1`. `models` is sorted by basename and assigns stable `model_id` values. `water_object_ids_sha256` hashes sorted unique WRP IDs serialized as little-endian int32. `input_hashes` covers EV90's complete pinned read set, EV87/EV90/EV93 source, the staged WRP, deployed world/water PBOs, bounds manifest, parser/readers, and every ODOL file read. Every shard has a relative path, SHA256, byte size, and row count.

Each `shards/faces-NNNNNN.npz` stores row-aligned arrays:

| Array | dtype and shape | Meaning |
|---|---|---|
| `kind` | `uint8[n]` | `0` physical, `1` visible |
| `object_id` | `int32[n]` | WRP object identity |
| `model_id` | `uint32[n]` | key into manifest `models` |
| `face_id` | `uint32[n]` | face index inside the selected LOD |
| `xyz` | `float64[n,3,3]` | world-space face vertices; columns X,Y,Z |
| `plane_y_xz` | `float64[n,3]` | coefficients `Y=aX+bZ+c` |
| `area_xz` | `float64[n]` | projected triangle area |
| `cell_range_rc` | `int32[n,4]` | inclusive conservative `[r_min,r_max,c_min,c_max]`; all `-1` means off-map |
| `degenerate` | `uint8[n]` | `1` iff projected area `<= 0`; zero plane coefficients are a finite sentinel for these records |

All faces are retained, including zero-area and tiny positive-area faces. Positive-area planes are computed by EV87's `affine_coeff` and cross-checked against EV90's affine solver. Degenerate triangles have no unique plane; they remain queryable and are labeled. The index does not apply EV87's downstream exposure cutoff or EV90's clipping; consumers apply the frozen rule appropriate to their comparison.

`FaceRangeIndex(run_dir)` requires a `COMPLETE` manifest, verifies every shard once, and loads the arrays into memory. `.query_window(r0,r1,c0,c1,kind=None)` and `.query_cell(r,c,kind=None)` return the arrays for faces whose conservative ranges can touch the requested cells. This is a candidate query only: callers must perform exact intersection/clipping before making exposure claims. Call `.reverify()` after a batch to re-hash the manifest and all shards. There is no option to disable shard verification.

## Validation boundary

`test_face_range_index.py` covers a large face crossing a query window, exact closed-boundary contact, off-map and empty queries, retention of degenerate/tiny faces, the EV87 NW-SE native split, row/ID return shape, shard lifecycle re-verification, and an altered source-pin rejection. The fixtures are synthetic and do not establish that a global build fits the time/output budget. The first actual build is bounded by the plan's 10-minute/2-GiB stop and must be reviewed before any consumer compares full-map representation or exposure.

ODOL header gate accepts only versions 54 and 55. This is not a claim that every parser path for those versions is generally safe: the pinned debinarizer notes a v55 animation-record desynchronization case. A global build must therefore fail closed on parser/LOD inconsistency; the current fixtures prove record handling for supplied face arrays, not a full-corpus parse.
