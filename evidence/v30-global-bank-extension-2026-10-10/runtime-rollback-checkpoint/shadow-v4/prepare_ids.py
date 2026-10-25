#!/usr/bin/env python3
"""Turn a successful read_diag_registry.py JSON into the mission's six-line ID file."""
import argparse
import json
from pathlib import Path

EXPECTED_SHA = "34f6377be4fd065d104e67263e0c96ac2cb2e348119a4838eba08d2e61b7a69a"
EXPECTED_IMAGE = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\DayZDiag_x64.exe"
TARGETS = ("Shadows", "Terrain shadows")
EXPECTED_CONTROLS = {"Render debug mode": 131, "Water": 276}

def stop(message):
    raise SystemExit("STOP: " + message)

parser = argparse.ArgumentParser()
parser.add_argument("--crosswalk", required=True, type=Path)
parser.add_argument("--out", required=True, type=Path)
args = parser.parse_args()
try:
    data = json.loads(args.crosswalk.read_text(encoding="utf-8"))
except Exception as exc:
    stop(f"cannot read crosswalk JSON: {exc}")
if data.get("status") != "READ_ONLY_REGISTRY_CROSSWALK_OK": stop("crosswalk status is not exact success")
if data.get("sha256") != EXPECTED_SHA: stop("executable SHA mismatch")
if str(data.get("image_path", "")).casefold() != EXPECTED_IMAGE.casefold(): stop("exact DayZDiag image path mismatch")
if type(data.get("pid")) is not int or data["pid"] <= 0: stop("crosswalk PID is absent/invalid")
if not isinstance(data.get("module_base"), str) or not data["module_base"].startswith("0x"): stop("module base evidence missing")
if data.get("mapped_text_matches") is not True: stop("mapped .text proof missing")
targets = data.get("targets")
if not isinstance(targets, dict) or set(targets) != set(TARGETS): stop("target labels are missing or unexpected")
ids = {}
for label in TARGETS:
    record = targets[label]
    if not isinstance(record, dict) or record.get("backlink_slot_matches") is not True: stop(f"backlink proof missing for {label}")
    value = record.get("id")
    if type(value) is not int or not 0 <= value < 4096: stop(f"invalid ID for {label}")
    ids[label] = value
if ids[TARGETS[0]] == ids[TARGETS[1]]: stop("target IDs are not distinct")
controls = data.get("controls")
if not isinstance(controls, dict): stop("control crosschecks missing")
for label, expected_id in EXPECTED_CONTROLS.items():
    record = controls.get(label)
    if not isinstance(record, dict) or record.get("id") != expected_id or record.get("backlink_slot_matches") is not True:
        stop(f"control crosscheck failed for {label}")
text = "\n".join((EXPECTED_SHA, "READ_ONLY_REGISTRY_CROSSWALK_OK", str(ids["Shadows"]), "Shadows", str(ids["Terrain shadows"]), "Terrain shadows")) + "\n"
args.out.parent.mkdir(parents=True, exist_ok=True)
with args.out.open("x", encoding="ascii", newline="") as handle:
    handle.write(text)
print(json.dumps({"status": "MISSION_ID_INPUT_WRITTEN_FROM_VALID_CROSSWALK", "path": str(args.out), "sha256": EXPECTED_SHA, "targets": ids}, indent=2))
