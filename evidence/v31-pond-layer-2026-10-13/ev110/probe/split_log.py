"""Split the BalticBridgeProbeV2 server log of the combined EV110 points into one log per family (ids mapped back to the
family files, header kept, BEGIN/END with the family count). Fails when the log does not frame exactly the combined set: one P row per expected id, no unknown or duplicate ids,
per-family counts equal to families.json.
Usage: split_log.py <baltic_bridge_probe_v2.log> <dir with points.json/families.json> [<out_dir>]"""
import json, os, sys

log, d = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(d, "split")
pts = {p["id"]: p for p in json.load(open(os.path.join(d, "points.json")))}
fams = json.load(open(os.path.join(d, "families.json")))["families"]
head, begin, end, rows, seen = None, None, None, {f: [] for f in fams}, set()
for line in open(log, encoding="utf-8", errors="replace"):
    a = line.strip().split(";")
    if a[0].startswith("BALTIC_"):
        head = line.strip()
    elif a[0] == "BEGIN":
        begin = int(a[1])
    elif a[0] == "END":
        end = int(a[1])
    elif a[0] == "P":
        i = int(a[1])
        assert i in pts, ("unknown id", i)
        assert i not in seen, ("duplicate id", i)
        seen.add(i)
        p = pts[i]
        rows[p["family"]].append(";".join(["P", str(p["family_id"])] + a[2:]))
assert head and begin == end == len(pts), (head, begin, end, len(pts))
missing = sorted(set(pts) - seen)
assert not missing, ("missing ids", len(missing), missing[:10])
for f in fams:
    assert len(rows[f]) == fams[f]["n"], ("family count", f, len(rows[f]), fams[f]["n"])
os.makedirs(out, exist_ok=False)
for f, r in rows.items():
    with open(os.path.join(out, f"{f}-baltic_bridge_probe_v2.log"), "w", newline="\n") as fh:
        fh.write("\n".join([head, f"BEGIN;{fams[f]['n']}"] + r + [f"END;{fams[f]['n']}"]) + "\n")
    print(f, len(r), "of", fams[f]["n"])
