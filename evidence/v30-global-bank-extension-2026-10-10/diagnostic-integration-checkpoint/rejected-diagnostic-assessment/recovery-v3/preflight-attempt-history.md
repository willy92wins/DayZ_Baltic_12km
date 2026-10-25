# Preflight-only attempts (transparent history)

These were harness checks only; no geometry API ran and no assessment report was written until attempt 03.

| Attempt | Result | Cause |
|---|---|---|
| 01 | `ERROR_BEFORE_PREFLIGHT` | The recovery-v3 driver still pointed at the original helper, so the four-argument call reached the unmodified three-argument `verify_preflight`. |
| 02 | `ERROR_BEFORE_PREFLIGHT` | After switching to the copied helper, source-key validation assumed `PATHS` and `EXPECTED` had identical key sets. The real producer intentionally omits dynamic `retained_selection` from `EXPECTED`; the pinned preparation receipt supplies its digest. |
| 03 | `PREFLIGHT_ONLY_PASS_NO_GEOMETRY` | Source aliases resolved through the pinned producer; retained-unit entries were independently rehashed as absolute paths. Structural, identity, lineage, and readset checks passed. |

The first two tool errors were observed in the session output; no original JSON error report was produced. The v2 `FileNotFoundError` transcript remains separately preserved in `run-02-error-note.json` and points to the parent-reported transcript copy.
