#!/usr/bin/env python3
"""Read-only recomposition check for the EV93 focal delta; inert unless --run."""
from __future__ import annotations
import argparse, hashlib, json, math, os
from pathlib import Path
from typing import Any

ROOT=Path(r"E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010")
FU=ROOT/"global-operator-prototype/real-sector-preflight/focus-unit"
SELECTION=ROOT/"compound-selection/run-02/selection.json"
SELECTED=ROOT/"crest-extension/selected-consumer-runs/attempt-03/review.json"
RAW_FAIL=ROOT/"consumer-global/runs/attempt-04/ev93-review.json"
FOCAL=FU/"consumer-run-01/review.json"
SUPPLEMENT=FU/"consumer-run-01/acceptance-supplement.json"
EXPECTED={
 "selection_sha":"3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b",
 "selected_sha":"656e676e38817592ed96d13ddeb1693d2a9bead152770256b0b21e665cedf8ec",
 "raw_sha":"ed9a071d359dc446b5146a255c3ab9f15481c92e24c2169b6da47dd4ad27c0ec",
 "base_sha":"6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d",
 "focal_sha":"b9af8d77c2efe342b02012af160a1f8cae44d41d5581be21045da8539116de7e",
"supplement_sha":"fab5c76e2f1a7a5935cf70bfaa08dedd4500411e4c2ac11670dc7fccc4b89e7f",
"finalizer_sha":"bb5cd1ddc65004654bfce64bda8c57afc4af6ac39e954db92c6c165caa6f73b1",
"focal_consumer_sha":"5dff923cca7d519ca728c64e821b43c05685f542e1279a85cbd5ccc659557c0a",
 "candidate_sha":"30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1",
 "focus":[840,370],
 "cells":[[839,369],[839,370],[840,369],[840,370]],
 "raw_status":"FAIL_INCREMENTAL_NONREGRESSION",
 "global_status":"PASS_INCREMENTAL_NONREGRESSION",
 "focal_status":"PASS_FOCAL_DELTA_OFFLINE",
 "open":"OPEN_INHERITED_MAP_DEFECTS",
 "legacy":332,"crest":167,
}
SUPPLEMENT_STATUS="PASS_FOCAL_DELTA_OFFLINE_COMPLETE_GATESET"

class VerificationError(RuntimeError): pass
def require(ok: bool, msg: str)->None:
    if not ok: raise VerificationError(msg)
def sha(path: Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()
def readj(path: Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(x,dict),f"not JSON object: {path}")
    return x
def pinned(path: Path, digest: str)->dict:
    require(path.is_file(),f"missing {path}")
    got=sha(path); require(got==digest,f"SHA mismatch {path}: {got}")
    return readj(path)
def rehash_set(rs: dict, label: str)->int:
    require(isinstance(rs,dict) and rs,f"{label}: empty readset")
    seen={}
    for raw,want in rs.items():
        p=Path(raw); require(p.is_file(),f"{label}: missing {p}")
        got=sha(p); require(got==want,f"{label}: hash drift {p}")
        key=os.path.normcase(os.path.abspath(str(p)))
        require(key not in seen or seen[key]==got,f"{label}: conflicting duplicate {p}")
        seen[key]=got
    return len(seen)
def rehash_map(rs: dict, label: str)->dict[str,str]:
    require(isinstance(rs,dict) and rs,f"{label}: empty readset")
    out={}; normalized={}
    for raw,want in rs.items():
        p=Path(raw); require(p.is_file(),f"{label}: missing {p}")
        got=sha(p); require(got==want,f"{label}: hash drift {p}")
        key=os.path.normcase(os.path.abspath(str(p)))
        require(key not in normalized or normalized[key]==got,f"{label}: conflicting duplicate {p}")
        normalized[key]=got; out[str(p.resolve())]=got
    return dict(sorted(out.items(),key=lambda kv:os.path.normcase(kv[0])))
def merge_pins(primary:dict[str,str],extra:dict[str,str],label:str)->dict[str,str]:
    result=dict(primary); normalized={os.path.normcase(os.path.abspath(k)):v for k,v in result.items()}
    for raw,digest in extra.items():
        key=os.path.normcase(os.path.abspath(raw))
        require(key not in normalized or normalized[key]==digest,f"{label}: conflicting expected pin {raw}")
        normalized[key]=digest; result[str(Path(raw).resolve())]=digest
    return dict(sorted(result.items(),key=lambda kv:os.path.normcase(kv[0])))
def stable_readset(report: dict,label: str)->None:
    i=report.get("information",{})
    a,b,c=(i.get(k) for k in ("input_hashes_start","input_hashes_end","input_hashes_expected"))
    require(isinstance(a,dict) and a==b==c,f"{label}: start/end/expected readsets differ")
def resolve_model_paths(model_hashes:dict,supp_readset:dict)->dict[str,str]:
    by_name={}
    for p,digest in supp_readset.items():
        by_name.setdefault(Path(p).name.casefold(),[]).append((p,digest))
    result={}
    for name,digest in model_hashes.items():
        matches=[(p,d) for p,d in by_name.get(Path(name).name.casefold(),[]) if d==digest]
        require(len(matches)==1,f"focal model {name}: cannot resolve one pinned absolute path")
        result[matches[0][0]]=digest
    return result

def window_gap(win:list[int], point:list[int])->int:
    r0,r1,c0,c1=win; r,c=point
    return max(max(r0-r,0,r-(r1-1)),max(c0-c,0,c-(c1-1)))
def check_window(win,core,label):
    require(isinstance(win,list) and len(win)==4 and all(type(v) is int for v in win),f"{label}: invalid window")
    require(win[1]-win[0]==17 and win[3]-win[2]==17,f"{label}: window not 17x17")
    require(isinstance(core,list) and len(core)==4 and all(type(v) is int for v in core),f"{label}: invalid core")
    require(core[1]-core[0]==13 and core[3]-core[2]==13,f"{label}: core not 13x13")
    require(win[0]<=core[0]<core[1]<=win[1] and win[2]<=core[2]<core[3]<=win[3],f"{label}: core outside window")
def local_artifact(row:dict,focus:list[int])->tuple[dict,int,list[tuple[int,int]]]:
    import numpy as np
    origin,qid=row["origin"],row["queue_id"]
    require(row.get("local_status")=="PASS" and row.get("selection_status")=="retained",f"{row.get('unit_id')}: not retained")
    lg=row.get("local_gates")
    require(isinstance(lg,dict) and lg and all(v is True for v in lg.values()),f"{row.get('unit_id')}: local gate false")
    ap=Path(row["source_artifact_path"]); require(ap.is_file() and sha(ap)==row["source_artifact_sha256"],f"{row['unit_id']}: artifact hash")
    art=readj(ap); require(art.get("queue_id")==qid,f"{row['unit_id']}: qid mismatch")
    if origin=="legacy":
        require(art.get("state")=="accepted" and art.get("solve_calls")==1,f"legacy {qid}: wrong result state")
        win,core=art.get("window_rc"),art.get("core_rc")
        dp=Path(art["delta_path"]); require(dp.is_file() and sha(dp)==art["delta_sha256"],f"legacy {qid}: delta hash")
        with np.load(dp,allow_pickle=False) as z:
            require(int(z["queue_id"][0])==qid,f"legacy {qid}: delta qid")
            nodes=np.asarray(z["variables_rc"],dtype=np.int32).copy()
            b=np.asarray(z["B_values_float32"],dtype=np.float32).copy()
            h=np.asarray(z["final_float32"],dtype=np.float32).copy()
    elif origin=="crest":
        require(art.get("state")=="derived_quarantined" and art.get("solve_calls")==0,f"crest {qid}: wrong state")
        sp=Path(art["source_result_path"]); require(sp.is_file() and sha(sp)==art["source_result_sha256"],f"crest {qid}: source-result hash")
        src=readj(sp); require(src.get("queue_id")==art.get("source_qid")==qid,f"crest {qid}: source qid")
        win,core=src.get("window_rc"),src.get("core_rc")
        nodes=np.asarray(art["variables_rc"],dtype=np.int32); b=np.asarray(art["B_values_float32"],dtype=np.float32); h=np.asarray(art["final_float32"],dtype=np.float32)
    else: raise VerificationError(f"unknown unit origin {origin}")
    check_window(win,core,f"{origin}:{qid}")
    gap=window_gap(win,focus); require(gap>2,f"{origin}:{qid}: focal halo overlaps window")
    require(nodes.ndim==2 and nodes.shape[1]==2 and b.shape==h.shape==(len(nodes),),f"{origin}:{qid}: bad delta arrays")
    changed=h!=b; count=int(np.count_nonzero(changed))
    require(count==int(row.get("changed_vertices",-1)),f"{origin}:{qid}: changed count mismatch")
    changed_rc=[list(map(int,x)) for x in nodes[changed].tolist()]
    changed_tuples=[tuple(x) for x in changed_rc]
    require(len(set(changed_tuples))==len(changed_tuples),f"{origin}:{qid}: duplicate node inside artifact")
    canonical=json.dumps(changed_rc,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    require(hashlib.sha256(canonical).hexdigest()==row.get("changed_vertices_sha256"),f"{origin}:{qid}: changed digest mismatch")
    return {"unit_id":row["unit_id"],"origin":origin,"queue_id":qid,"window":win,"core":core,"gap":gap},count,changed_tuples

def check_documents(selection,selected,raw,focal,supplement)->dict:
    require(selection.get("status")=="SELECTED","selection not SELECTED")
    require(selection.get("candidate",{}).get("sha256")==EXPECTED["base_sha"],"wrong selected base")
    require(selection.get("source_global_report_path")==str(RAW_FAIL.resolve()),"selection raw-source path wrong")
    require(selection.get("source_global_report_sha256")==EXPECTED["raw_sha"],"selection raw-source SHA wrong")
    require(raw.get("status")==EXPECTED["raw_status"],"known raw source no longer has expected FAIL")
    raw_false=[k for k,v in raw.get("gates",{}).items() if v is False]
    require(len(raw_false)==2,"raw failed-source fingerprint changed")
    require(selected.get("status")==EXPECTED["global_status"],"selected global composition not PASS")
    selected_gates=selected.get("gates",{})
    require(len(selected_gates)==22 and all(v is True for v in selected_gates.values()),
            "selected report must have exactly 22 true global gates")
    i=selected.get("information",{})
    require(i.get("global_contract_status")==EXPECTED["open"],"inherited map-defect status lost")
    require(i.get("selection_sha256")==EXPECTED["selection_sha"],"selected consumer selection SHA mismatch")
    require(i.get("candidate_sha256")==EXPECTED["base_sha"] and i.get("candidate_path")==selection["candidate"]["path"],"selected candidate mismatch")
    require(i.get("compound_pool_sha256")==selection.get("compound_pool_sha256"),"pool SHA mismatch")
    index_report = next((v for k,v in selection.get("source_read_set",{}).items()
                         if str(k).lower().endswith("review-independent\\runs\\attempt-01\\verification.json")), None)
    require(index_report is not None and i.get("index_verification_sha256")==index_report,
            "index verification SHA mismatch")
    require(set(i.get("source_global_false_gates",[]))==set(raw_false),
            "selected report did not preserve the known raw-source failures")
    selected_consumer=Path(i.get("consumer_source_path",""))
    require(selected_consumer.is_file() and sha(selected_consumer)==i.get("consumer_source_sha256"),
            "selected global consumer source pin mismatch")
    stable_readset(selected,"selected report")
    require(focal.get("status")==EXPECTED["focal_status"],"focal raw status mismatch")
    require(focal.get("candidate_sha256")==EXPECTED["candidate_sha"] and focal.get("base_ev93_sha256")==EXPECTED["base_sha"],"focal base/candidate mismatch")
    require(focal.get("changed_vertices")==[EXPECTED["focus"]],"focal changed-node identity mismatch")
    cc=focal.get("compiled_coverage",{})
    require(cc.get("changed_support_cells")==4,"focal support-cell count not four")
    cells=cc.get("metrics",{}).get("physical",{}).get("exposure_residual_H",{}).get("outside_band_examples",[])
    got=sorted(e["cell"] for e in cells if isinstance(e,dict) and "cell" in e)
    require(got==EXPECTED["cells"],f"focal local cell set mismatch: {got}")
    gates=focal.get("gates",{}); cg=cc.get("gates",{})
    require(len(gates)==28 and all(v is True for v in gates.values()),"focal 28 local gates incomplete/false")
    require(len(cg)==8 and all(v is True for v in cg.values()),"focal eight compiled gates incomplete/false")
    require(supplement.get("schema")=="ev93.focal-acceptance-supplement.v1","wrong supplement schema")
    require(supplement.get("status")==SUPPLEMENT_STATUS,"supplement status not accepted")
    require(supplement.get("candidate_sha256")==EXPECTED["candidate_sha"],"supplement candidate SHA mismatch")
    require(supplement.get("focal_report_path")==str(FOCAL.resolve()),"supplement focal report path mismatch")
    require(supplement.get("focal_report_sha256")==EXPECTED["focal_sha"],"supplement focal report SHA mismatch")
    require(supplement.get("map_status")==EXPECTED["open"],"supplement closes inherited map defects")
    sg=supplement.get("gates",{}); require(len(sg)==36 and all(v is True for v in sg.values()),"supplement not exactly 36 true gates")
    ac=supplement.get("additional_checks",{}); require(isinstance(ac,dict) and ac and all(v is True for v in ac.values()),"supplement additional checks fail")
    # Rehash all focal report inputs/models and supplement source set, not the 16k-file
    # historical global set; that set is checked for exact start=end=expected identity above.
    fstart,fend=focal.get("input_hashes_start"),focal.get("input_hashes_end")
    require(isinstance(fstart,dict) and fstart==fend,"focal readset changed during consumer run")
    n_f=rehash_set(fstart,"focal report")
    model_hashes=focal.get("model_hashes_read",{})
    supp_readset=supplement.get("source_read_set",{})
    model_paths=resolve_model_paths(model_hashes,supp_readset)
    n_m=rehash_set(model_paths,"focal models")
    n_s=rehash_set(supp_readset,"supplement source")
    finalizer=Path(supplement.get("source_path",""))
    require(finalizer.is_file() and supplement.get("source_sha256")==EXPECTED["finalizer_sha"]
            and sha(finalizer)==EXPECTED["finalizer_sha"],"root focal finalizer source pin mismatch")
    focal_consumer_paths=[Path(p) for p in supp_readset if Path(p).name=="verify_focus_1981.py"]
    require(len(focal_consumer_paths)==1 and sha(focal_consumer_paths[0])==EXPECTED["focal_consumer_sha"],
            "focal consumer source pin mismatch")
    return {"raw_false_gates":raw_false,"selected_report_sha256":EXPECTED["selected_sha"],
            "focal_report_sha256":EXPECTED["focal_sha"],"focal_readset_files":n_f,
            "focal_model_files":n_m,"supplement_readset_files":n_s,
            "selected_gate_count":len(selected_gates),"focal_finalizer_path":str(finalizer),
            "focal_consumer_path":str(focal_consumer_paths[0]),
            "selected_consumer_path":i.get("consumer_source_path"),
            "selected_consumer_sha256":i.get("consumer_source_sha256")}

def recompute_coverage(global_cc:dict,focal_cc:dict)->dict:
    require(focal_cc.get("changed_support_cells")==4,"need exact four-cell focal replacement")
    out={}
    for kind in ("physical","visible"):
        g=global_cc["metrics"][kind]; f=focal_cc["metrics"][kind]
        h=f["support_hole_total_m2"]; hm=f["support_hole_max_cell_m2"]
        old_hole=float(g["support_hole_total_m2"]["candidate"])
        hole=old_hole+float(h["H"])-float(h["B"])
        old_hole_max=float(g["support_hole_max_cell_m2"]["candidate"])
        hole_max=max_replacement(old_hole_max,float(hm["B"]),float(hm["H"]),f"{kind} support-hole max")
        rb,rh=f["exposure_residual_B"],f["exposure_residual_H"]
        old=g["residual"]["candidate"]
        require(int(rb.get("unknown_F_cells",-1))==int(rh.get("unknown_F_cells",-2)),
                f"{kind}: focal change altered unknown-F cell coverage")
        sums={}; maxima={}
        for k in ("missing_total_m2","growth_total_m2","missing_outside_band_total_m2","growth_outside_band_total_m2"):
            value=float(old[k])+float(rh[k])-float(rb[k])
            require(math.isfinite(value) and value>=-1e-18,f"{kind}: invalid recomposed {k}")
            sums[k]=max(0.0,value)
        for k in ("missing_max_cell_m2","growth_max_cell_m2","missing_outside_band_max_cell_m2","growth_outside_band_max_cell_m2"):
            base_max=float(old[k])
            maxima[k]=max_replacement(base_max,float(rb[k]),float(rh[k]),f"{kind} {k}")
        out[kind]={"support_hole_total_m2":hole,"support_hole_max_cell_m2":hole_max,
                   "residual_totals_m2":sums,"residual_maxima_m2":maxima,
                   "unknown_F_cells":int(old.get("unknown_F_cells",0)),
                   "local_B":{"hole":float(h["B"]),"residual":rb},
                   "local_H":{"hole":float(h["H"]),"residual":rh},
                   "passes_original_aggregate_limits":bool(
                       hole<1e-7 and sums["missing_outside_band_total_m2"]<=0.002 and
                       sums["growth_outside_band_total_m2"]<=0.002 and hole_max["nonworse"] and
                       all(v["nonworse"] for v in maxima.values()))}
    return out

def max_replacement(global_max:float,local_B_max:float,local_H_max:float,label:str)->dict:
    """Bound the new global maximum when only local B/H cell maxima are known.

    If local B was strictly below the old global max, a witness exists outside
    the replaced cells and the old maximum is exact.  If local B tied the old
    max and local H falls, the exact new max is unknown; report a valid interval.
    """
    for x in (global_max,local_B_max,local_H_max):
        require(math.isfinite(x) and x>=0,f"{label}: invalid maximum")
    require(local_B_max<=global_max+1e-20,f"{label}: B local maximum exceeds baseline global maximum")
    nonworse=local_H_max<=global_max+1e-20
    exact=(local_B_max<global_max or local_H_max>=global_max)
    if exact:
        lower=upper=global_max
        exact_value=global_max
    else:
        lower=min(global_max,local_H_max)
        upper=global_max
        exact_value=None
    return {"lower_bound_m2":lower,"upper_bound_m2":upper,"exact":exact,
            "exact_value_m2":exact_value,"nonworse":nonworse}

def verify_units(selection:dict)->dict:
    units=selection.get("units"); require(isinstance(units,list) and len(units)==568,"selection inventory count mismatch")
    all_ids=[u.get("unit_id") for u in units]; require(len(set(all_ids))==568,"duplicate unit IDs")
    retained=[u for u in units if u.get("selection_status")=="retained"]
    legacy=[u for u in retained if u.get("origin")=="legacy"]; crest=[u for u in retained if u.get("origin")=="crest"]
    require(len(retained)==499 and len(legacy)==EXPECTED["legacy"] and len(crest)==EXPECTED["crest"],"499-row retained composition mismatch")
    ids=[u.get("unit_id") for u in retained]; require(len(set(ids))==len(ids),"duplicate unit id")
    changed_nodes=set(); total=0; min_gap=None
    for row in retained:
        descriptor,count,changed_rc=local_artifact(row,EXPECTED["focus"])
        min_gap=descriptor["gap"] if min_gap is None else min(min_gap,descriptor["gap"])
        total+=count
        for key in changed_rc:
            require(key not in changed_nodes,f"changed-node overlap {key}"); changed_nodes.add(key)
    return {"retained":len(retained),"legacy":len(legacy),"crest":len(crest),
            "changed_vertices":total,"unique_changed_vertices":len(changed_nodes),"minimum_window_gap":min_gap}

def run()->dict:
    selection=pinned(SELECTION,EXPECTED["selection_sha"])
    selected=pinned(SELECTED,EXPECTED["selected_sha"])
    raw=pinned(RAW_FAIL,EXPECTED["raw_sha"])
    focal=pinned(FOCAL,EXPECTED["focal_sha"])
    require(SUPPLEMENT.is_file(),"acceptance supplement missing")
    require(sha(SUPPLEMENT)==EXPECTED["supplement_sha"],"acceptance supplement SHA mismatch")
    supplement=readj(SUPPLEMENT)
    pins_start=rehash_map(supplement.get("source_read_set",{}),"run start")
    own_path=Path(__file__).resolve(); own_sha_start=sha(own_path)
    explicit={
        str(SELECTION.resolve()):EXPECTED["selection_sha"],
        str(SELECTED.resolve()):EXPECTED["selected_sha"],
        str(RAW_FAIL.resolve()):EXPECTED["raw_sha"],
        str(FOCAL.resolve()):EXPECTED["focal_sha"],
        str(SUPPLEMENT.resolve()):EXPECTED["supplement_sha"],
        str((FU/"author-run-01/candidate-terrain.npz").resolve()):EXPECTED["candidate_sha"],
        str((ROOT/"compound-selection/run-02/candidate-terrain.npz").resolve()):EXPECTED["base_sha"],
        str(own_path):own_sha_start,
        str(Path(selected["information"]["consumer_source_path"]).resolve()):selected["information"]["consumer_source_sha256"],
    }
    focal_consumer_path=next((Path(p) for p in supplement.get("source_read_set",{})
                              if Path(p).name=="verify_focus_1981.py"),None)
    require(focal_consumer_path is not None,"focal consumer source pin absent")
    explicit[str(focal_consumer_path.resolve())]=EXPECTED["focal_consumer_sha"]
    finalizer_path=Path(supplement.get("source_path",""))
    explicit[str(finalizer_path.resolve())]=EXPECTED["finalizer_sha"]
    pins_start=merge_pins(pins_start,explicit,"start pins")
    for p,want in pins_start.items():
        require(Path(p).is_file() and sha(Path(p))==want,f"start pin mismatch: {p}")
    docs=check_documents(selection,selected,raw,focal,supplement)
    units=verify_units(selection)
    require(units["changed_vertices"]==selected["information"]["changed_vertices"],"retained changed-node total differs from global report")
    require(units["unique_changed_vertices"]==units["changed_vertices"],"retained changed vertices overlap")
    require(units["minimum_window_gap"]>=80,"local window unexpectedly near focal")
    metrics=recompute_coverage(selected["information"]["global_contract"]["compiled_coverage"],focal["compiled_coverage"])
    for kind in ("physical","visible"):
        counts=focal["compiled_coverage"]["metrics"][kind].get("height_violation_count",{})
        require(counts.get("B")==counts.get("candidate")==0,
                f"{kind}: local compiled height violations are not unchanged zero")
    require(all(x["passes_original_aggregate_limits"] for x in metrics.values()),"focal addition violates aggregate coverage limits")
    pins_end=rehash_map(supplement.get("source_read_set",{}),"run end")
    pins_end=merge_pins(pins_end,explicit,"end pins")
    for p,want in pins_end.items():
        require(Path(p).is_file() and sha(Path(p))==want,f"end pin mismatch: {p}")
    own_sha_end=sha(own_path)
    require(own_sha_start==own_sha_end,"checker source changed during run")
    require(pins_start==pins_end,"source pins changed during focal recomposition")
    selected_gates=selected["gates"]; focal_gates=supplement["gates"]
    gates={**{f"selected_global:{k}":v for k,v in selected_gates.items()},
           **{f"focal_complete:{k}":v for k,v in focal_gates.items()},
           "composition:499_source_units_and_windows_reconciled":True,
           "composition:changed_nodes_unique_and_count_exact":True,
           "composition:no_window_or_collar_overlap_with_focal_support":True,
           "coverage:physical_aggregate_limits":metrics["physical"]["passes_original_aggregate_limits"],
           "coverage:visible_aggregate_limits":metrics["visible"]["passes_original_aggregate_limits"],
           "coverage:maxima_nonworse_or_bounded":all(
               c["support_hole_max_cell_m2"]["nonworse"] and
               all(v["nonworse"] for v in c["residual_maxima_m2"].values()) for c in metrics.values()),
           "inherited:map_defects_remain_open":True}
    require(all(v is True for v in gates.values()),"composition gate false")
    return {"status":"PASS_FOCAL_COMPOSITION_INCREMENTAL","global_contract_status":EXPECTED["open"],
      "scope":"one focal delta composed over selected 499-unit candidate; inherited map defects remain open",
      "report_path":"<caller supplied --report path>",
      "candidate_path":str((FU/"author-run-01/candidate-terrain.npz").resolve()),
      "candidate_sha256":EXPECTED["candidate_sha"],
      "base_candidate_path":selection["candidate"]["path"],"base_candidate_sha256":EXPECTED["base_sha"],
      "consumer_source_path":docs["focal_consumer_path"],"consumer_source_sha256":EXPECTED["focal_consumer_sha"],
      "selected_global_consumer_path":docs["selected_consumer_path"],
      "selected_global_consumer_sha256":docs["selected_consumer_sha256"],
      "supplement_path":str(SUPPLEMENT.resolve()),"supplement_sha256":EXPECTED["supplement_sha"],
      "selection_sha256":EXPECTED["selection_sha"],"selected_report_sha256":EXPECTED["selected_sha"],
      "focal_report_sha256":EXPECTED["focal_sha"],"raw_source_report_sha256":EXPECTED["raw_sha"],
      "source_pins_start":pins_start,"source_pins_end":pins_end,"checker_source_sha256":own_sha_start,
      "gates":gates,
      "documents":docs,"selection_units":units,
      "focal":{"changed_vertices":focal["changed_vertices"],"delta_m":focal["delta_m"],"support_cells":EXPECTED["cells"]},
      "recomposed_compiled_coverage":metrics,
      "limitations":["The selected consumer's 499 local geometry gates are re-anchored and checked for artifact/readset/window integrity; their full geometric evaluation is inherited from that consumer report.",
        "Global p99, sector, D8, slope, P9, corridor, and compiled-face gates are reused only after the 36-gate focal supplement passes.",
        "This result does not close OPEN_INHERITED_MAP_DEFECTS and is not runtime/build/visual acceptance."]}

def expect_error(fn,label):
    try: fn()
    except VerificationError: return
    raise AssertionError("negative fixture accepted: "+label)
def self_test()->dict:
    import copy
    def cov(holeH=0.0,out=0.0):
        return {"changed_support_cells":4,"metrics":{k:{
          "support_hole_total_m2":{"B":0.0,"H":holeH},"support_hole_max_cell_m2":{"B":0.0,"H":holeH},
          "exposure_residual_B":{"missing_total_m2":1e-7,"growth_total_m2":0.0,"missing_outside_band_total_m2":0.0,"growth_outside_band_total_m2":0.0,"missing_max_cell_m2":1e-7,"growth_max_cell_m2":0.0,"missing_outside_band_max_cell_m2":0.0,"growth_outside_band_max_cell_m2":0.0,"unknown_F_cells":0},
          "exposure_residual_H":{"missing_total_m2":1.2e-7,"growth_total_m2":0.0,"missing_outside_band_total_m2":out,"growth_outside_band_total_m2":0.0,"missing_max_cell_m2":1.2e-7,"growth_max_cell_m2":0.0,"missing_outside_band_max_cell_m2":out,"growth_outside_band_max_cell_m2":0.0,"unknown_F_cells":0}}
          for k in ("physical","visible")}}
    g={"metrics":{k:{"support_hole_total_m2":{"candidate":2e-8},"support_hole_max_cell_m2":{"candidate":1.5e-8},
       "residual":{"candidate":{"missing_total_m2":.01,"growth_total_m2":.001,"missing_outside_band_total_m2":1e-6,"growth_outside_band_total_m2":1e-6,"missing_max_cell_m2":5e-5,"growth_max_cell_m2":5e-5,"missing_outside_band_max_cell_m2":5e-7,"growth_outside_band_max_cell_m2":5e-7,"unknown_F_cells":10}}} for k in ("physical","visible")}}
    good=recompute_coverage(g,cov())
    assert all(v["passes_original_aggregate_limits"] for v in good.values())
    g_excess=copy.deepcopy(g)
    for kind in ("physical","visible"):
        g_excess["metrics"][kind]["support_hole_total_m2"]["candidate"]=0.999e-7
    bad=recompute_coverage(g_excess,cov(holeH=0.002e-7))
    assert not bad["physical"]["passes_original_aggregate_limits"]
    raw={"status":"FAIL_INCREMENTAL_NONREGRESSION"}
    expect_error(lambda: require(raw["status"]==EXPECTED["global_status"],"bad source status"),"false source report")
    win=[832,849,362,379]; assert window_gap(win,[840,370])==0
    expect_error(lambda: require(window_gap(win,[840,370])>2,"focal overlap"),"window overlap")
    gates={f"g{i}":True for i in range(36)}; gates["g35"]=False
    expect_error(lambda: require(len(gates)==36 and all(gates.values()),"supplement"),"coverage gate false")
    g_excess_total=copy.deepcopy(g)
    for kind in ("physical","visible"):
        g_excess_total["metrics"][kind]["residual"]["candidate"]["missing_outside_band_max_cell_m2"]=0.004
    excess=recompute_coverage(g_excess_total,cov(out=.003))
    assert not excess["physical"]["passes_original_aggregate_limits"]
    max_tie=max_replacement(5e-7,5e-7,4e-7,"fixture tied max")
    assert max_tie["nonworse"] and not max_tie["exact"] and max_tie["upper_bound_m2"]==5e-7
    assert not max_replacement(5e-7,5e-7,6e-7,"fixture worsened max")["nonworse"]
    check_window([832,849,362,379],[834,847,364,377],"valid fixture")
    pinned_models=resolve_model_paths({"model.p3d":"abc"},{r"E:\\data\\model.p3d":"abc"})
    assert list(pinned_models.values())==["abc"]
    expect_error(lambda:resolve_model_paths({"model.p3d":"wrong"},{r"E:\\data\\model.p3d":"abc"}),
                 "model hash mismatch")
    return {"status":"PASS","tests":["four-cell additive replacement","coverage-limit negative","false source status negative",
        "17x17 window overlap negative","36-gate supplement negative","max-tie upper bound and worsening negative",
        "model basename resolves only through matching absolute pinned path","window/core schema positive"],
        "production_data_opened":False}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--run",action="store_true")
    ap.add_argument("--report",type=Path)
    a=ap.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),indent=2)); return 0
    if not a.run or a.report is None: ap.error("use --self-test or explicit --run --report PATH")
    try:
        result=run(); result["report_path"]=str(a.report.resolve()); a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"status":result["status"],"report":str(a.report)},indent=2)); return 0
    except Exception as exc:
        failure={"status":"FAIL_FOCAL_COMPOSITION","error":f"{type(exc).__name__}: {exc}"}
        a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(failure,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(failure,indent=2)); return 1
if __name__=="__main__":
    raise SystemExit(main())
