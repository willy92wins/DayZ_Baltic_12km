from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile

import numpy as np

import test_structured_operator as ref
from structured_operator import build_operators

SRC=Path(__file__).with_name('measure_global_actions.py')
spec=importlib.util.spec_from_file_location('measure_global_actions_fixture',SRC)
bench=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


def run():
    bench.self_test()
    vals=bench.deterministic_vector(32,4)
    assert np.array_equal(vals,bench.deterministic_vector(32,4))
    assert not np.array_equal(vals,bench.deterministic_vector(32,5))
    tiny=np.arange(64,dtype=np.float64).reshape(8,8)
    nodes=np.column_stack(np.nonzero((tiny.astype(np.int32)%3)!=0)).astype(np.int32)
    tiny_op=build_operators(tiny,nodes)
    ev88=ref.load_pinned(ref.EV88_PATH,ref.PINS[ref.EV88_PATH],'ev88_nnz_ref')
    cp=ref.load_pinned(ref.CP_PATH,ref.PINS[ref.CP_PATH],'cp_nnz_ref')
    refs=ref.references(tiny,nodes,ev88,cp)
    actual=bench.exact_structural_nnz(tiny_op)
    assert actual=={'A':refs[2].nnz,'C':refs[6].nnz,'G':refs[8].nnz},(actual,refs[2].nnz,refs[6].nnz,refs[8].nnz)
    parts,total=bench.persistent_array_estimate_bytes((2048,2048),2712136,11095396,4182435,16760836)
    assert total==sum(parts.values()) and parts['A_anchor_rc_int32']==8*(11095396-2712136)
    # Review pin must bind the operator and the exact fixture report.
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'review.json'
        p.write_text(json.dumps({'status':bench.REVIEW_STATUS,
                                 'operator_sha256':bench.OPERATOR_SHA,
                                 'fixture_report_sha256':bench.FIXTURE_SHA,
                                 'measurement_driver_sha256':bench.sha256_file(SRC)}),encoding='utf-8')
        review,sha=bench.review_gate(p,bench.sha256_file(p))
        assert review['status']==bench.REVIEW_STATUS and len(sha)==64
        p.write_text(json.dumps({'status':'FAIL','operator_sha256':bench.OPERATOR_SHA,
                                 'fixture_report_sha256':bench.FIXTURE_SHA,
                                 'measurement_driver_sha256':bench.sha256_file(SRC)}),encoding='utf-8')
        try: bench.review_gate(p,bench.sha256_file(p))
        except RuntimeError: pass
        else: raise AssertionError('non-PASS independent review accepted')
        p.write_text(json.dumps({'status':bench.REVIEW_STATUS,'operator_sha256':'0'*64,
                                 'fixture_report_sha256':bench.FIXTURE_SHA,
                                 'measurement_driver_sha256':bench.sha256_file(SRC)}),encoding='utf-8')
        try: bench.review_gate(p,bench.sha256_file(p))
        except RuntimeError: pass
        else: raise AssertionError('review for another operator accepted')
    print(json.dumps({'status':'PASS_MEASUREMENT_DRIVER_FIXTURES','persistent_estimate_bytes':total,
                      'array_estimates_bytes':parts,'run_dir':str(bench.RUN_DIR)},indent=2))


if __name__=='__main__': run()
