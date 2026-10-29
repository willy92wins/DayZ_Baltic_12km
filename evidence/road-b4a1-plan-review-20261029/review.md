**Verdict: SOUND-with-fixes.** The design is read-only, keeps every existing guard, and correctly refuses to extrapolate the asf1_25 observation. The fixes below close false-green gaps in the new predicate and in test coverage.

**What holds up**

- Reading twice from the same handle with fstat before, between and after isolates "changed over time" from "two APIs disagree". The discriminator already shows the existing predicate is not tripped by the handle/path ctime gap, since ident_tuple drops ctime and stat_tuple is only compared within the handle. So the plan's refusal to reclassify R0 is correct, not just cautious.
- Excluding asphalt_ext from the seven and hard-blocking INPUTS_MATCH while an external reference is uncovered is the right shape, provided it is enforced in the report builder, not only documented.
- Pin checks before parsing R0 and the receipt, immutable inputs, no run_discovery call: all fine.

**Concrete false-green risks to fix**

- **Byte count never compared to st_size.** Line 131 accepts stable=True even if the loop ended early with fewer bytes than fstat reports. A short read ending on an empty chunk looks like EOF. Require n equal to fb.st_size and fa.st_size for both reads. This adds a guard, it does not loosen one.
- **QueryDosDeviceW returns a MULTI_SZ list; buf.value keeps only the first entry.** A second mapping entry would be invisible, and the plan explicitly cares about historical junctions and a double-slash alias. Parse the full buffer, require exactly one entry, and apply the same normcase to both the returned string and expected_mapping. Currently win_norm normcases but expected_mapping does not.
- **Which root is "the exact path".** The discriminator ran against the OneDrive real path, while inspect_build joins root plus the normalized relative path. If R0 recorded alias-rooted paths, the new capture must use the same root string and also record the resolved target. Otherwise you certify a path R0 never read.
- **Timeouts.** With no internal retries, a 30s overrun on a cloud-backed file must still emit INCONCLUSIVE_SOURCE_STABILITY with all raw values captured so far. Make that an explicit test, since OneDrive hydration stalls are the most likely way to hit the budget.
- **Test honesty.** "Predicado EXACTO de R0 más hash2" can only exercise the code path, because R0 lost the metadata that triggered SOURCE_UNSTABLE. State that the tests validate the predicate, not reproduction of the historical failure.
- **Component guard is mtime-based.** Lines 186-189 compare directory ident_tuple including mtime. Any sibling write, including OneDrive sync of an unrelated file, flips it. That is not a false green, but it is a chronic INCONCLUSIVE source. Record which component changed and both tuples, per the plan's "razones por igualdad".

**Observations to record without causal claims**

- The handle ctime on asf1_25 sits near the capture timestamp, while the path ctime equals mtime. On Python 3.12 Windows, st_ctime is creation time from GetFileInformationByHandle. The gap is worth logging per file as a raw field. Do not fold it into any predicate or verdict.
- Attributes 32 and 49 show no reparse tags today. That says nothing about the state at R0 time, which the plan already scopes correctly as temporal.

**Accepted limit to state in the output**

A byte change between read one and read two that is fully reverted before read two, with mtime restored, is undetectable by this design. The listed negative fixture covers the persisting case only. Say so in the report schema.

With the size check, full MULTI_SZ parsing, explicit root choice, and the timeout test added, the plan is sound to implement within the stated budgets.