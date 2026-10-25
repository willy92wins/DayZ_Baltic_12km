"""Stage the V30 world source from the accepted V29 package, without Terrain Builder.

The editable WRP (0WZD) keeps V29's header, material grid and the nine Narva bridge records byte for byte; heights
become terrain V30 and the 10,152 V29 water records are replaced by the V30 pieces. A piece's WRP translation is its
authored origin plus the centre of the box spanned by its outline and the origin: the rule Terrain Builder applied
to every V29 edge piece (6,186 checked, max 0.5 mm). A pose with a full 'matrix' (vanilla channel pieces,
tools/water/fit_channel_pieces_v30.py) is written with that matrix and model path, without the box rule.
config.cpp requires Baltic_Water_V30 instead of Baltic_Water and sets the sea of class BalticTrial: the engine sea is a
12.5 s swell, MaxTide/2 + MaxWave*sin (inherited from CAWorld, DZ\\data\\config.cpp:1667-1668: 0.75 +- 0.25 m); MaxTide
1.5 keeps the mean at the 0.75 m the terrain is built for and MaxWave 0.10 halves the swing (decision of 04-10;
evidence/v30-tide-swell-2026-10-04).
With --outside-terrain the world also gets the OutsideTerrain class of Chernarus
(DZ\\worlds\\chernarusplus\\world\\config.cpp:210-222) with the terrain synthesis off: beyond the map the engine
continues the terrain from its edge, and without that class an edge above the sea is drawn flat and untextured (the
land borders since v4, BALTIC-020). A trial: in v7b/v7c it drew lines at a distance that may have been texture
loading (evidence/v30-v7-candidate-2026-10-05/border-fix). Without synthesis (v8b) the land borders stayed flat;
--outside-synth turns it on, as Chernarus has it.
Layers (satellite, mask, 4,775 materials) and the navmesh are still V29's: phase 4 and a new navmesh replace them.
Usage: derive_world_v30.py <terrain_v30.npz> <pieces.json> <stage_dir> [--outside-terrain] [--outside-synth]
       (stage_dir must not exist; --outside-synth implies --outside-terrain)
"""
import hashlib
import json
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrp0wzd import object_record, read, write  # noqa: E402

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
BASE = os.path.join(R, "packages", "baltic-road-v29", "source", "BalticTrialWorld")
BASE_WRP_SHA = "e9325dff8b2e"
FIRST_ID = 16777216 + 20000
SEA = {"MaxTide": "1.5", "MaxWave": "0.1"}
OUTSIDE = """
		class OutsideTerrain
		{
			satellite="DZ\\worlds\\chernarusplus\\data\\outside_sat_co.paa";
			enableTerrainSynth={synth};
			class Layers
			{
				class Layer0
				{
					nopx="DZ\\surfaces\\data\\terrain\\cp_grass_nopx.paa";
					texture="DZ\\surfaces\\data\\terrain\\cp_grass_ca.paa";
				};
			};
		};"""


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    terrain, pieces_path, stage = sys.argv[1:4]
    synth = "--outside-synth" in sys.argv[4:]
    outside = synth or "--outside-terrain" in sys.argv[4:]
    assert not os.path.exists(stage), "fresh stage required"
    base_wrp = os.path.join(BASE, "baltic_trial.wrp")
    assert sha(base_wrp).startswith(BASE_WRP_SHA)
    base = read(base_wrp)
    heights = np.load(terrain)["heights"].astype("<f4")[::-1, :]
    keep = [o for o in base["objects"] if not o["name"].startswith("baltic_water")]
    assert len(keep) == 9 and all(o["name"].endswith("bridge_metal_25.p3d") for o in keep), [o["name"] for o in keep]
    pieces = json.load(open(pieces_path, encoding="utf-8"))
    models = {m["name"]: m for m in pieces["model_list"]}
    records = [o["bytes"] for o in keep]
    for k, p in enumerate(pieces["poses"]):
        if "matrix" in p:
            records.append(object_record(p["matrix"], FIRST_ID + k, p["model"].encode("ascii")))
            continue
        b = models[p["model"].split("\\")[-1][:-4]]["bounds_rel"]
        cx = (min(b[0], 0.0) + max(b[2], 0.0)) / 2
        cz = (min(b[1], 0.0) + max(b[3], 0.0)) / 2
        x, y, z = p["origin"]
        records.append(object_record([1, 0, 0, 0, 1, 0, 0, 0, 1, x + cx, y, z + cz], FIRST_ID + k, p["model"].encode("ascii")))

    shutil.copytree(BASE, stage, ignore=shutil.ignore_patterns("baltic_trial.wrp"))
    out_wrp = os.path.join(stage, "baltic_trial.wrp")
    write(out_wrp, base["header"], heights, base["materials"], records, base["terminator"])
    config = open(os.path.join(stage, "config.cpp"), encoding="utf-8").read()
    assert config.count('"Baltic_Water"') == 1 and config.count('description="Baltic 12km - Narva test";') == 1
    assert "MaxTide" not in config and "MaxWave" not in config and "OutsideTerrain" not in config
    sea = "".join(f"\n\t\t{k}={v};" for k, v in SEA.items())
    config = config.replace('"Baltic_Water"', '"Baltic_Water_V30"').replace(
        'description="Baltic 12km - Narva test";', 'description="Baltic 12km - V30";' + sea + (OUTSIDE.replace("{synth}", "1" if synth else "0") if outside else ""))
    with open(os.path.join(stage, "config.cpp"), "w", encoding="utf-8", newline="\n") as f:
        f.write(config)

    back = read(out_wrp)
    checks = {
        "heights_exact": bool(np.array_equal(back["heights"], heights)),
        "materials_bytes_identical": back["materials"] == base["materials"],
        "header_identical": back["header"] == base["header"],
        "bridges_identical": [o["bytes"] for o in back["objects"][:9]] == [o["bytes"] for o in keep],
        "object_count": len(back["objects"]) == 9 + len(pieces["poses"]),
        "ids_unique": len({o["id"] for o in back["objects"]}) == len(back["objects"]),
    }
    receipt = {"status": "STAGED_V30_WORLD_SOURCE" if all(checks.values()) else "FAIL", "checks": checks,
               "base_wrp_sha256": sha(base_wrp), "wrp_sha256": sha(out_wrp), "terrain_npz_sha256": sha(terrain),
               "pieces_sha256": sha(pieces_path), "water_objects": len(pieces["poses"]), "bridges": 9, "sea": SEA, "outside_terrain": outside, "outside_synth": synth,
               "limits": ["Layers and navmesh are V29's (stale for V30 water and relief).",
                          "Derived without Terrain Builder: no native save/reopen provenance."]}
    with open(os.path.join(stage, "..", "stage-receipt.json"), "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=1)
    print(json.dumps(receipt, indent=1))
    assert all(checks.values())


if __name__ == "__main__":
    main()
