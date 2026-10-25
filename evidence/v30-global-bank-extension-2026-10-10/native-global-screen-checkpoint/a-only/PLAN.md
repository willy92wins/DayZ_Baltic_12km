# A-only memory diagnostic preparation

## Scope

This is an isolated preparation for one later, reviewed measurement: build the
EV95 objective operator using only A, evaluate one fused `A.T @ A @ x0`, and
record peak working set/free RAM. It is not a solver run, terrain candidate,
acceptance result, or replacement for the frozen `screen.py`. The benchmark
must not run until the parent reviews this preparation. It has a 120 s budget,
1 GiB process-peak cap, and an unchanged 6 GiB free-physical-memory floor.

## Exact operation contract

- Inputs stay pinned to the existing EV95 terrain, `bounds.npz`, frozen full
  operator, fused-normal implementation, memory sampler, screen, and screen
  review. The existing 6 GiB floor is not lowered.
- `AOnlyOperators` retains only `base`, sorted `variables`, `xx_rc`, `zz_rc`,
  `xz_rc`, `rhs_a`, and `diag_a`. Its A and A-adjoint formulas retain the
  original row/tap order. `FusedNormalAction.a_normal` is used unchanged.
- D8 arrays, C rows/offsets/diagonal, G face offsets/diagonal are absent from
  this build. If a later diagnostic needs D8, it must compute its witnesses
  after the A action; no D8 result is implied by this measurement.
- RHS rows are written into one preallocated array. The full operator's
  `rhs_parts` plus `np.concatenate` temporarily keep two A-row-sized buffers.
- No global input is loaded by fixtures. The one-build benchmark is a separate
  entry point and creates an exclusive output only after pins and resource
  admission pass.

## Memory estimate from frozen dimensions

For `n=2,712,136` and a 2047x2047 cell grid, the full object retains:

| Omitted from A-only | Shape / dtype | Bytes |
|---|---:|---:|
| `k_g` | 2047 x 2047 x 4, float64 | 134,086,688 |
| `d_c` | 4,182,435, float64 | 33,459,480 |
| `diag_c` | n, float64 | 21,697,088 |
| `diag_g` | n, float64 | 21,697,088 |
| **Total retained-state reduction** | | **210,940,344 (201.2 MiB)** |

This is a retained-array estimate, not a constructor peak estimate. An A-only
builder also avoids the full `k_grid` and G diagonal construction transients;
the exact peak remains unmeasured until the authorized benchmark. Other live
construction arrays include the 2048x2048 base (33.55 MB), variable list
(21.70 MB), a possible int32 index grid (16.78 MB), active/fixed grids,
anchor coordinate arrays, RHS and anchor temporaries, and D8 data is not built
here. The benchmark enforces the 1 GiB cap and 6 GiB floor rather than
assuming the estimate proves fit.

At the reported 7,563,341,824 bytes available, the unchanged 6 GiB floor
leaves 1,120,890,880 bytes (about 1.044 GiB) for this process and other
concurrent changes. The benchmark admission check also requires floor plus its
1 GiB cap, so the reported snapshot has only about 45 MiB admission headroom;
the check is intentionally fail-closed if that snapshot worsens.

## Verification

`test_a_only_operator.py` compares exact A anchors, RHS, diagonal, `A`, and
`A.T` against the pinned full operator across edge and interior shapes, then
compares the unchanged fused normal action. It includes invalid-domain
controls. These are implementation fixtures only; they do not measure global
memory or prove global timing.
