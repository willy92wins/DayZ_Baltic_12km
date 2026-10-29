**Verdict: not acceptable yet.** Beyond the two issues the parent already flagged (mixed-root join at lines 218/224 and pinned JSON re-opened at line 426 without matching the hashed bytes), there are further concrete blockers.

**Blockers**

1. **Timeout path asserts `r0_unchanged: True` unverified (line 472).** On budget exhaustion the final pin re-check (lines 457-461) never ran, yet report.json still claims R0 unchanged. That is a fail-closed weakening. Emit `r0_unchanged: "NOT_VERIFIED"` or omit it.

2. **OS `TimeoutError` is conflated with the budget deadline.** `TimeoutError` subclasses `OSError`. A network/OneDrive read timing out inside `hash_file` or `capture_file` is caught at line 470 as a budget timeout and produces a DISCOVERY_ONLY report instead of raising. Use a private exception subclass for the deadline.

3. **Deadline not bounded by the runner.** `deadline = start + contract["seconds"]` accepts any positive value. If the contract says more than roughly 25s the runner kills the process at 30s and no report.json is written at all. Reject or clamp `seconds` to under the runner limit.

4. **OneDrive files-on-demand not handled.** The root is under OneDrive. Dehydrated placeholders carry reparse tag 0x9000001A and `RECALL_ON_DATA_ACCESS` attributes. Depending on the helper's `is_link`, every file either becomes `UNRESOLVED_LINK` or hydrates during `open`, changing attributes/ctime between `lstat` and `fstat` and tripping `SOURCE_UNSTABLE`. Record the tag and attribute bits explicitly and give cloud placeholders a distinct status so the run is diagnosable.

5. **Alias form vs QueryDosDevice.** `alias` may be `X:/` per the regex at line 76, but `QueryDosDeviceW` needs `X:` with no slash. Unless the helper strips it, both mapping predicates fail for every file. Normalize before calling, and record the raw full buffer rather than only the first NUL-terminated string (line 240 discards the rest).

**Non-blocking but concrete**

- `detect_format` receives 16 bytes (line 330) where the original sampled 8192. Expect spurious `UNKNOWN` formats. Pass the 8192-byte sample or record that only 16 bytes were examined.
- `name` validation (line 103) does not reject a drive-relative name like `C:foo`, which `os.path.join` would treat as resetting the drive. Add an `ntpath.splitdrive` check.
- `pins_after` is populated from `pin_actual` (the before values). Equality is enforced so it is correct, but label it as re-verified rather than re-measured.
- `write_partial` fsyncs on every progress call. Keep `--out` off OneDrive or the 30s budget will be consumed by sync I/O.

**What is correct**

- The five original predicates (lines 357-361) match `_capture_file` line 131 exactly, including ctime only within the same API.
- read1/read2 hash, count, and prefix equality (lines 366-371) are enforced, and both reads are counted against `fstat` sizes.
- All seven files are captured regardless of individual status, `all_stable` requires exactly seven, and any error or false predicate yields `SOURCE_UNSTABLE`.
- Raw `_stat_dict` output preserves ctime_ns, attributes, and reparse tag for every observation, including ancestors.
- No `INPUTS_MATCH`, `build_ready` is always false, external references stay `UNRESOLVED_EXTERNAL`.

Fix items 1-5 together with the two parent-identified issues before this counts as a delivery.