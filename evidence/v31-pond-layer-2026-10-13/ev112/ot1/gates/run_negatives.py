"""Run the negative controls of the EV112 kit gates against a validated run: the EV110 modes that apply unchanged to the
v9 gates (negative_controls.py) and the EV112 modes (negative_controls_v9.py). Every mode seeds its own folder under <base>.
Usage: run_negatives.py <validated_run> <base_dir>"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
run, base = sys.argv[1:3]
old_modes = ["g1-no-output", "wide", "stray", "frozen", "steep", "envelope", "probe-coordinates", "dry-expect-test", "old-bed-in-sheet",
             "g8-no-log", "g8-as-expected", "g8-lips-dry", "g8-control-wet", "g8-relabel-dry-all-wet", "g8-dry-depth-nan", "g8-ground-nan"]
passed = True
for script, modes, sub in (("negative_controls.py", old_modes, "ev110-modes"), ("negative_controls_v9.py", [], "ev112-modes")):
    pr = subprocess.run([sys.executable, "-I", os.path.join(HERE, script), run, os.path.join(base, sub)] + modes, capture_output=True, text=True)
    print(pr.stdout[-6000:]); print(pr.stderr[-2000:])
    passed &= pr.returncode == 0
print("NEGATIVES", "PASS" if passed else "FAIL")
sys.exit(0 if passed else 1)
