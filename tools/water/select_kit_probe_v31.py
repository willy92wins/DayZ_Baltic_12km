"""Deterministic runtime sample; exhaustive points remain the offline oracle.

Keep each reach's first/middle/last piece, every model kind, largest absolute
pitch, first/middle/last joint and two old-bed controls when available. Preserve
point-reference closure. Refuse a budget too small for these strata.
"""
from collections import defaultdict
import math


def select(points, records, limit=3000):
    by_id = {p["id"]: p for p in points}
    if len(by_id) != len(points):
        raise ValueError("duplicate point ids")
    axis, sides, joints, old, baseline = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for p in points:
        k = p["kind"]
        if k == "kit_axis":
            axis[(p["site"], p["piece"])].append(p)
        elif k in ("kit_side", "kit_joint_side", "kit_confluence"):
            sides[p["of"]].append(p)
        elif k == "kit_joint":
            joints[p["site"]].append(p)
        elif k == "old_bed":
            old[p["site"]].append(p)
        elif not k.startswith("kit_"):
            baseline[k].append(p)
    selected = set()
    def keep(p):
        if p["id"] in selected:
            return
        selected.add(p["id"])
        for ref in p.get("lips", []):
            keep(by_id[ref])
        if "of" in p:
            keep(by_id[p["of"]])
        for s in sides.get(p["id"], []):
            keep(s)
    def positions(items):
        return [items[i] for i in sorted({0, len(items)//2, len(items)-1})] if items else []
    by_site = defaultdict(list)
    for r in records:
        if r["piece"] != "stones":
            by_site[r["site"]].append(r)
    strata = {}; extra_axes = {}
    for sid, rs in sorted(by_site.items()):
        rs.sort(key=lambda r:(r["station"][0], str(r["piece"])))
        chosen = {r["piece"]: r for r in positions(rs)}
        kinds = defaultdict(list)
        for r in rs:
            kinds[r["model"]].append(r)
        for model, members in sorted(kinds.items()):
            r = members[len(members)//2]; chosen[r["piece"]] = r
        r = max(rs, key=lambda r: abs(r["matrix"][7])/max(math.sqrt(sum(v*v for v in r["matrix"][6:9])),1e-12))
        chosen[r["piece"]] = r
        extra_axes[sid] = []
        for pc in chosen:
            if not axis.get((sid,pc)):
                raise ValueError(f"missing axis coverage: {sid}/{pc}")
            samples = sorted(axis[(sid,pc)],key=lambda p:p["id"])
            keep(samples[len(samples)//2])  # Centre + both sides form the mandatory runtime stratum.
            extra_axes[sid].extend(p for p in samples if p["id"] not in selected)
        js = sorted(joints.get(sid,[]),key=lambda p:p["id"])
        for p in positions(js):
            keep(p)
        ob = sorted(old.get(sid,[]),key=lambda p:p["id"])
        for p in ([ob[0],ob[-1]] if ob else []):
            keep(p)
        strata[sid] = dict(records=len(rs), selected_pieces=sorted(chosen,key=str), model_kinds=len(kinds),
                           available_joints=len(js), selected_joints=[p["id"] for p in positions(js)], old_bed_available=len(ob))
    for _, group in sorted(baseline.items()):
        for p in positions(group):
            keep(p)
    confluences = defaultdict(list)
    for p in points:
        if p["kind"] == "kit_confluence":
            confluences[tuple(sorted((p["site"],p["other_site"])))].append(p)
    for pair, group in sorted(confluences.items()):
        keep(sorted(group,key=lambda p:p["id"])[len(group)//2])
    mandatory = len(selected)
    if mandatory > limit:
        raise ValueError(f"mandatory reach strata need {mandatory} points; budget is {limit}")
    # Preserve the full baseline when it fits, then add quarter/three-quarter
    # points round-robin across reaches rather than consuming the budget on the first one.
    for _, group in sorted(baseline.items()):
        for p in group:
            if len(selected) >= limit:
                break
            keep(p)
    for i in range(max((len(v) for v in extra_axes.values()),default=0)):
        for sid, group in sorted(extra_axes.items()):
            if len(selected) >= limit:
                break
            if i < len(group):
                keep(group[i])
    out = [p for p in points if p["id"] in selected]
    return out, dict(schema="kit-probe-sampling-v31.v2", limit=limit, exhaustive_points=len(points),
                     mandatory_points=mandatory, runtime_points=len(out), per_site=strata,
                     confluence_pairs=[list(pair) for pair in sorted(confluences)])
