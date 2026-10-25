"""Shoreline gates with v3 semantics for the v31 pond-layer pilot: base EV103 and the v31 envelope as cover.

eval_shore_v3.evaluate() (lines 226-256) refuses any base or cover but EV99 / cover-level-ev98; this copy takes the
context from pe_check.ctx_v3 (eval_shore_v3.base_context lines 104-128 with base and cover as arguments) and keeps the
v1, v2 and v3 gate code untouched by importing the frozen harness modules read-only (hash-checked in pe_common).
Usage: eval_p1_v31.py <candidate.npz> <out.json>
"""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'E:/DayZ-Baltic-Build/v31-pond-layer-20261013/p1-builder')
import json, time
import numpy as np
import pe_common as C
import pe_check as PC

V3, V2 = C.V3, C.V2


def main():
    cand, out = sys.argv[1:3]
    x = PC.ctx_v3(C.BASE, C.COVER)
    t0 = time.time()
    stem = out[:-5] if out.endswith('.json') else out
    r2 = V2.evaluate(x, cand, stem + '.v2.json')
    H1 = np.load(cand)['heights']
    g3, det = V3.v3_part(x, H1)
    gates = dict(r2['gates_violations']); gates.update(g3)
    groups = dict(r2['gate_groups_pass'])
    for g, ks in V3.V3_GROUPS.items():
        groups[g] = all(gates[k] == 0 for k in ks)
    res = dict(schema='shore-eval.v3-params', base=C.BASE, base_sha256=r2['base_sha256'], cover=C.COVER,
               cover_sha256=r2['cover_sha256'], candidate=cand, candidate_sha256=r2['candidate_sha256'],
               gates_violations=gates, gates_pass=all(v == 0 for v in gates.values()), gate_groups_pass=groups,
               changed_vertices=r2['changed_vertices'], max_abs_change_m=r2['max_abs_change_m'], details_v3=det,
               summary_base_cand=r2['summary_base_cand'], v2=r2, runtime_s=round(time.time() - t0, 1))
    if res['base_sha256'] != C.BASE_SHA or res['cover_sha256'] != C.COVER_SHA:
        raise SystemExit('base or cover hash changed during the run')
    with open(out, 'w') as fh:
        fh.write(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res[k] for k in ('gates_violations', 'gates_pass', 'gate_groups_pass', 'runtime_s')}, indent=1))


if __name__ == '__main__':
    main()
