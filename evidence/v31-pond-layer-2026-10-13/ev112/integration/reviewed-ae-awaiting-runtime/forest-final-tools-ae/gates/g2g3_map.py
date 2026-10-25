"""G2 (density, spacing, species mix per context) and G3 (forest edges) per 1 km window over the whole map.

Usage: python -I g2g3_map.py <records.json> <gate-rasters dir> <livonia-ev112-bands.json> <out.json>
         [--windows x0,z0;x0,z0...]
Per window: the EV111 r2 metrics, bands and judge (gate_common.metric_table / judge, strict: every judged metric inside
the [min, max] envelope of the 256 comparable Livonia windows; tvd only <= max, agreement only >= min), over the
window minus the bog and its 25 m margin; canopy, contexts and nearest neighbours from the instances within 100 m
around the window (glib.py). A window is judged when it is comparable as Livonia's are (land >= 0.9, canopy >= 0.5).
Map verdict, fixed before the first map run (EV112): a Livonia window judged against the envelope of the other 255
fails G2 in 20.3 % and G3 in 16.0 % of the cases (livonia_bands.py); the map passes a gate when
  a) the share of judged windows with >= 1 failed metric is <= that Livonia leave-one-out share, and
  b) per metric, the share of judged windows failing it is <= the Clopper-Pearson upper bound, at confidence
     1 - 0.05 / m (Bonferroni over the m metrics the gate judges on the map), of that metric's own Livonia
     leave-one-out failure rate (k of n Livonia windows): a metric fails the map when it leaves its envelope more
     often than Livonia's own windows would, statistically, family-wise at 5 %. (Development: the uncorrected 95 %
     bound failed some metric on every development map with 2-7 windows of ~150-380 each, both tails, moving between
     seeds; the correction was set on development seeds 1-4, before the production and hold-out runs.)
Rule b) compares a metric only with itself (Codex review 2 of EV111 rejected a global tolerance taken from another
metric); rule a) alone would be such a tolerance. Reported, not judged: each failure's excess next to Livonia's largest
leave-one-out excess of the same metric, and a composition diagnostic for density.edge.trees and
density.riparian.trees: the share of the context's cells on forest texture f and the density Livonia would show at
that mix (Livonia on / off its surface: edge 202.5 / 83.3, riparian 231.8 / 59.4 trees/ha, whole enoch map).
The two EV111 pilot squares keep their own strict contract (0 failed metrics), judged with the unchanged r2 scripts on
the records inside them (run_gates.py)."""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glib  # noqa: E402

GC = glib.GC
ap = argparse.ArgumentParser()
ap.add_argument("records")
ap.add_argument("rasters")
ap.add_argument("bands")
ap.add_argument("out")
ap.add_argument("--windows")
a = ap.parse_args()
t0 = time.time()
MR = glib.MapRecords(a.records)
R = glib.Rasters(a.rasters)
LB = json.loads(Path(a.bands).read_text(encoding="utf-8"))
ref = MR.ref
wins = [tuple(float(v) for v in w.split(",")) for w in a.windows.split(";")] if a.windows else [(x, z) for z in glib.WIN_X0 for x in glib.WIN_X0]
res, verdict = [], {}
for (x0, z0) in wins:
    m, comp, info = glib.window_measure(R, MR, x0, z0)
    vals = GC.metric_table(m, ref)
    row = dict(info, comparable=comp, values=vals)
    for gate, pref in GC.PREFIXES.items():
        _, rows = GC.judge(vals, ref, pref)
        failed = [(r_[0], float(r_[1]), GC.excess(r_[1], r_[2], r_[3], ref["bands"][r_[0]]["max"] - ref["bands"][r_[0]]["min"]))
                  for r_ in rows if r_[4].startswith("FAIL")]
        row[gate] = {"judged": sum(1 for r_ in rows if r_[4] != "NO_BAND"), "failed": failed}
    res.append(row)
judged = [r for r in res if r["comparable"] and r["unknown_models"] == 0]
summary = {"windows": len(res), "judged_windows": len(judged), "seconds": round(time.time() - t0, 1)}
ok_all = True
for gate in ("G2", "G3"):
    lo = LB["loo"][gate]
    nfail = sum(1 for r in judged if r[gate]["failed"])
    share = nfail / max(1, len(judged))
    over = []
    for r in judged:
        for k, v, ex in r[gate]["failed"]:
            allow = lo["metrics"].get(k, {}).get("loo_max_excess", 0.0)
            if ex > allow + 1e-12:
                over.append({"window": [r["x0"], r["z0"]], "metric": k, "value": round(v, 4), "excess": round(ex, 4), "livonia_loo_max_excess": allow})
    by_metric = {}
    for r in judged:
        for k, _, _ in r[gate]["failed"]:
            by_metric[k] = by_metric.get(k, 0) + 1
    from scipy.stats import beta
    rule_b = {}
    m_metrics = len({k for r in judged for k in r["values"] if k.startswith(GC.PREFIXES[gate])})
    conf = 1.0 - 0.05 / max(m_metrics, 1)
    for k, nf in sorted(by_metric.items(), key=lambda t: -t[1]):
        lm = lo["metrics"].get(k, {"n_windows": 256, "loo_fail": 0})
        kk, nn = lm["loo_fail"], max(lm["n_windows"], 1)
        upper = float(beta.ppf(conf, kk + 1, nn - kk)) if kk < nn else 1.0
        nj = sum(1 for r in judged if k in r["values"])
        sh = nf / max(nj, 1)
        rule_b[k] = {"failed_windows": nf, "windows_with_metric": nj, "share": round(sh, 4), "livonia_loo": [kk, nn],
                     "cp95_upper": round(upper, 4), "ok": sh <= upper}
    ok = share <= lo["fail_share"] + 1e-12 and all(v["ok"] for v in rule_b.values()) and len(judged) > 0
    ok_all &= ok
    summary[gate] = {"failed_windows": nfail, "failed_share": round(share, 4), "livonia_loo_fail_share": round(lo["fail_share"], 4),
                     "rule_a": share <= lo["fail_share"] + 1e-12, "excess_beyond_livonia": over[:50], "n_excess_beyond_livonia": len(over),
                     "rule_b": all(v["ok"] for v in rule_b.values()), "rule_b_metrics_judged": m_metrics, "rule_b_confidence": round(conf, 6),
                     "rule_b_per_metric": rule_b,
                     "failed_by_metric": dict(sorted(by_metric.items(), key=lambda t: -t[1])), "verdict": "PASS" if ok else "FAIL"}
comp_diag = {}
for key, ctxk, on, off in (("density.edge.trees", 1, 202.5, 83.3), ("density.riparian.trees", 2, 231.8, 59.4)):
    rows_ = [r for r in judged if key in r["values"] and r.get("ctx_on_texture") and r["ctx_on_texture"][str(ctxk)] is not None]
    fails_ = [r for r in rows_ if any(k == key for k, _, _ in r["G2"]["failed"])]
    comp_diag[key] = {"windows": len(rows_), "failed": len(fails_),
                      "failed_obs_over_livonia_at_mix": [round(r["values"][key] / (r["ctx_on_texture"][str(ctxk)] * on + (1 - r["ctx_on_texture"][str(ctxk)]) * off), 3) for r in fails_][:60],
                      "failed_on_texture_share": [round(r["ctx_on_texture"][str(ctxk)], 3) for r in fails_][:60],
                      "all_obs_over_livonia_at_mix_p50_p90_max": [round(float(np.percentile([r["values"][key] / (r["ctx_on_texture"][str(ctxk)] * on + (1 - r["ctx_on_texture"][str(ctxk)]) * off) for r in rows_], q)), 3) for q in (50, 90, 100)] if rows_ else None}
summary["composition_diagnostic"] = comp_diag
Path(a.out).write_text(json.dumps({"summary": summary, "windows": res}, indent=1) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=1))
for g in ("G2", "G3"):
    print(f"{g}-map {summary[g]['verdict']} ({summary[g]['failed_windows']}/{len(judged)} windows fail, Livonia LOO share "
          f"{summary[g]['livonia_loo_fail_share']}; {summary[g]['n_excess_beyond_livonia']} excesses beyond Livonia's own)")
sys.exit(0 if ok_all else 1)
