# EV93 compound selector

`selector.py` implements the selector from `crest-extension/EXECUTION_PLAN_V2.md` (plan SHA `8a4afc1e26dc0d816ade9454ee4f4e31c185b03a56c8a9ef5005f468d0cff9b0`). It consumes the finalized quarantined pool of 340 legacy accepted deltas and 228 crest target references. It keeps local classifications separate from the author’s source rows: legacy rows use the pinned layer consumer, while crest rows use `verify_selected_composite.py`'s independent local verifier and are cross-checked against the author artifact reader. It then scans the pinned ODOL face index once for P/F XZ support and restores whole locally valid units in deterministic order while recomputing every incident cell.

The selector has no solver or map-build path. It writes a candidate NPZ only when both support-hole sums are strictly below `1e-7 m²` and at least one nontrivial crest remains. The NPZ copies every metadata array from B unchanged. Failure states write a selection receipt without a candidate. A nonempty output directory is rejected.

The selector receipt is `ev93.compound-selection.v1`. `units` is the exhaustive 568-row classification; identity is `unit_id=origin:queue_id`, so equal qids from the two origins remain distinct. A local or policy rejection is `local_status=FAIL`, `selection_status=excluded_local`; an original source result is never rewritten. Support removals are whole-unit `excluded_support` rows. The receipt pins the pool, exact attempt-04 FAIL report, B, both author sources and their ledgers, helper sources, index manifest/builder, models, shards, per-row artifacts, selector source and plan.

Synthetic selection fixtures:

```powershell
& 'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe' 'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/compound-selection/selector.py' --self-test
```

The bounded real-artifact integration check follows the local row path for one legacy accepted row, one derived crest, and one policy-rejected crest. It does not scan support, run a solver, or write a terrain candidate:

```powershell
& 'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe' 'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/compound-selection/integration_real_rows.py'
```

The full selector remains an explicit, separate command and has not been run in this preparation:

```powershell
& 'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe' 'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/compound-selection/selector.py' --execute --pool 'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/crest-extension/quarantine-pool-v3/compound-pool.json' --output-dir 'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/compound-selection/output' --progress-jsonl 'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/compound-selection/output/progress.jsonl'
```

Do not run the command until the independent review accepts this source and the actual pool contract.
