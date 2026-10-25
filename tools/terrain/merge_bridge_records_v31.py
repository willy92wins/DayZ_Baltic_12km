"""BALTIC-015: the object records a stage_bridges_v31.py run appends = the pilot bridge 015-15 (bridges/records.json, staged
since EV107/EV108: the terrain carries its cut, so without its record that channel has no bridge) + the streambed kit's
records of the same chain + a bridges_v31.py run's bridge-records.json, in that order (as records-ev110.json of EV110).
Review of 18-10: the EV112 recipe 'kit + bridge-records' dropped the pilot and stage_bridges_v31.py still passed every
check, so the list is built and checked here, and gates_v6.py G14 checks it and the staged WRP again.
Refused: an existing output; a part that is not a non-empty list of records {site, model, matrix (12 finite numbers)};
a pilot or bridge record repeated (same site, span, role), a kit record repeated, or two records at the same model +
matrix; a pilot site that is also a bridge site of --sites; a bridge site of --sites with a missing record (one upper
record per span, and one stack-lower per span where stack is set) or any bridge record of a site not in --sites.
Usage: merge_bridge_records_v31.py --pilot records.json --kit kit-records.json --bridges bridge-records.json
                                   --sites sites.json --out merged.json"""
import argparse, collections, json, math, os, struct, sys


def refuse(msg):
    raise SystemExit(f"merge_bridge_records_v31: refused: {msg}")


def load(path, name):
    try:
        recs = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        refuse(f"{name}: {e}")
    if not isinstance(recs, list) or not recs:
        refuse(f"{name}: not a non-empty list")
    for r in recs:
        M = r.get("matrix") if isinstance(r, dict) else None
        if not isinstance(r, dict) or not r.get("site") or not isinstance(r.get("model"), str) or not isinstance(M, list) or len(M) != 12 \
                or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in M):
            refuse(f"{name}: invalid record {str(r)[:120]}")
        try:
            pose = struct.unpack("<12f", struct.pack("<12f", *M))
        except (OverflowError, struct.error):
            refuse(f"{name}: matrix is outside finite float32")
        if not all(math.isfinite(v) for v in pose):
            refuse(f"{name}: matrix is outside finite float32")
    return recs


def main():
    ap = argparse.ArgumentParser()
    for k in ("pilot", "kit", "bridges", "sites", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        refuse(f"{a.out} exists")
    pilot, kit, br = load(a.pilot, "pilot"), load(a.kit, "kit"), load(a.bridges, "bridges")
    sites = json.load(open(a.sites, encoding="utf-8"))
    sid = {s["id"]: s for s in sites}
    out = pilot + kit + br
    keys = collections.Counter((r["site"], r.get("span"), r.get("role")) for r in pilot + br)   # kit pieces repeat ('stones')
    keys.update(json.dumps(r, sort_keys=True) for r in kit)
    dup = [k for k, n in keys.items() if n > 1]
    if dup:
        refuse(f"repeated records {dup[:5]}")
    poses = collections.Counter((r["model"], struct.unpack("<12f", struct.pack("<12f", *r["matrix"]))) for r in out)
    if any(n > 1 for n in poses.values()):
        refuse("two records at the same model and float32 matrix consumed by WRP")
    clash = sorted({r["site"] for r in pilot} & set(sid))
    if clash:
        refuse(f"pilot sites {clash} are also bridge sites")
    for s in sites:
        n = int(s.get("spans", 1)); mine = [r for r in br if r["site"] == s["id"]]
        up = sorted(r.get("span") for r in mine if not r.get("role")); lo = sorted(r.get("span") for r in mine if r.get("role") == "stack-lower")
        if up != list(range(n)) or lo != (list(range(n)) if s.get("stack") else []) or len(mine) != len(up) + len(lo):
            refuse(f"{s['id']}: bridge records {len(up)} upper / {len(lo)} stack-lower, expected {n} / {n if s.get('stack') else 0}")
    stray = sorted({r["site"] for r in br} - set(sid))
    if stray:
        refuse(f"bridge records of sites not in --sites: {stray}")
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(dict(out=a.out, total=len(out), pilot=len(pilot), pilot_sites=sorted({r["site"] for r in pilot}), kit=len(kit),
                          bridges=len(br), stack_lower=sum(1 for r in br if r.get("role") == "stack-lower")), indent=1))


if __name__ == "__main__":
    main()
