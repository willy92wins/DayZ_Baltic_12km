"""Run the EV112 kit gates in order and print one PASS/FAIL/NOT_RUN line per gate, then write <out>/gates-summary.txt.
G1 runs the EV112 step-1 command (chain-ev112-step1.json) into <out>; G2-G5 and G9-G10 are offline on its outputs; G6 runs
HANDOFF step 2 (bury_edges) on them; G7 the probe points; G11 needs G6's footprint; G8 is the engine acceptance from a server
probe log (NOT_RUN until it exists). The regression against EV110 (component mode = v8) runs first as G0.
Usage: run_gates.py <out_dir> [--skip-g1] [--tools dir]   (--skip-g1: <out_dir> already holds a run of the same command;
--tools: folder with probe_points_kit.py for G7 and streambed_kit_v31.py for G0; default the worktree)"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gatelib as G
args = sys.argv[1:]
skip1 = "--skip-g1" in args; args = [a for a in args if a != "--skip-g1"]
tools = G.WT + "/tools/water"
if "--tools" in args:
    i = args.index("--tools"); tools = args[i + 1]; args = args[:i] + args[i + 2:]
out = args[0]
lines, status = [], {}
gates = [("G0", [os.path.join(HERE, "regression_ev110.py"), tools + "/streambed_kit_v31.py", out + "/regression-ev110"])]
if not skip1:
    gates.append(("G1", [os.path.join(HERE, "gate_g1_cli.py"), out]))
for g, f in (("G2", "gate_g2_width.py"), ("G3", "gate_g3_continuity.py"), ("G4", "gate_g4_engine_margin.py"), ("G5", "gate_g5_slopes.py"),
             ("G6", "gate_g6_pond_layer.py"), ("G7", "gate_g7_probe.py"), ("G8", "gate_g8_engine_probe.py"), ("G9", "gate_g9_mounds.py"),
             ("G10", "gate_g10_stones.py"), ("G11", "gate_g11_junctions.py")):
    gates.append((g, [os.path.join(HERE, f), out] + (["--tools", tools] if g == "G7" else [])))
for g, cmd in gates:
    pr = subprocess.run([sys.executable, "-I"] + cmd, capture_output=True, text=True)
    open(os.path.join(out, f"gate-{g.lower()}.log"), "w", newline="\n").write(pr.stdout + "\n--- stderr\n" + pr.stderr)
    last = (pr.stdout.strip().splitlines() or ["(no output)"])[-1]
    toks = last.split()
    status[g] = toks[1] if len(toks) > 1 and toks[0].startswith(("G", "REGRESSION")) else "ERROR"
    if status[g] == "PASS" and pr.returncode != 0:
        status[g] = "ERROR"
    lines.append(f"{g}: {last} (exit {pr.returncode})")
    print(lines[-1], flush=True)
    if pr.returncode not in (0, 3):
        print(pr.stderr[-1500:])
offline = all(v == "PASS" for k, v in status.items() if k != "G8")
lines.append(("OFFLINE PASS (G8 excluded)" if offline else "OFFLINE FAIL") + "; G8 engine " + status.get("G8", "?"))
print(lines[-1])
open(os.path.join(out, "gates-summary.txt"), "w", newline="\n").write("\n".join(lines) + "\n")
sys.exit(0 if offline else 1)
