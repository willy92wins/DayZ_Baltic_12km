"""How strict are G2 and G3, and how many failed metrics does Livonia itself show? Apply the judge to every comparable
Livonia window, in sample (bands from all windows) and leave-one-out (envelope rebuilt without the window), and write
the G2/G3 tolerance: the leave-one-out p90 of the number of failed metrics per window, and the largest leave-one-out
excess outside the envelope in band widths (v3, EV111 review 1).
Usage: python -I livonia_selfcheck.py <livonia-windows.json> [--write <livonia-tolerance.json>]"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate_common as GC  # noqa: E402

ref = json.loads(GC.REFERENCE.read_text(encoding="utf-8"))
wins = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
comp = [w for w in wins if w["land_frac"] >= 0.9 and (w["canopy_frac"] or 0) >= 0.5]
tabs = [GC.metric_table(w, ref) for w in comp]
res = {"windows": len(comp), "reference_sha256": GC.sha256(GC.REFERENCE)}
for gate, pref in GC.PREFIXES.items():
    n_fail, fails = [], {}
    for t in tabs:
        _, rows = GC.judge(t, ref, pref)
        bad = [r[0] for r in rows if r[4].startswith("FAIL")]
        n_fail.append(len(bad))
        for k in bad:
            fails[k] = fails.get(k, 0) + 1
    keys = sorted({k for t in tabs for k in t if k.startswith(pref)})
    vals = {k: np.array([np.nan if t.get(k) is None else t[k] for t in tabs], float) for k in keys}
    loo, excess = [], []
    for i in range(len(tabs)):
        n = 0
        for k in keys:
            v = vals[k][i]
            if not np.isfinite(v) or ref["bands"].get(k, {}).get("n", 0) < 10:
                continue
            o = np.delete(vals[k], i)
            o = o[np.isfinite(o)]
            lo, hi = (-np.inf if k.startswith("tvd.") else o.min()), (np.inf if k.startswith("agreement.") else o.max())
            if not (lo <= v <= hi):
                n += 1
                excess.append(GC.excess(v, lo, hi, o.max() - o.min()))
        loo.append(n)
    res[gate] = {"in_sample_pass_share": round(float(np.mean(np.array(n_fail) == 0)), 3),
                 "in_sample_failed_p50_p90_max": [float(a) for a in np.percentile(n_fail, [50, 90, 100])],
                 "loo_pass_share": round(float(np.mean(np.array(loo) == 0)), 3),
                 "loo_failed_p50_p90_p95_max": [float(a) for a in np.percentile(loo, [50, 90, 95, 100])],
                 "max_failed": int(np.floor(np.percentile(loo, 90))),
                 "loo_excess_n_p50_p90_max": [len(excess)] + [round(float(a), 4) for a in np.percentile(excess, [50, 90, 100])],
                 "max_excess": round(float(np.max(excess)), 4),
                 "most_failed_in_sample": sorted(fails.items(), key=lambda t: -t[1])[:6]}
print(json.dumps(res, indent=1))
if "--write" in sys.argv:
    Path(sys.argv[sys.argv.index("--write") + 1]).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
