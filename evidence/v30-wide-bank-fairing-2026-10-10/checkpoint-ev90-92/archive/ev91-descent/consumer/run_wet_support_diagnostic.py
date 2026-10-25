#!/usr/bin/env python
"""Run only the separate wet-support metric on pinned B/H; no EV91 full consumer."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
CANDIDATE=HERE.parent/'candidate-terrain.npz'
EXPECTED_CANDIDATE_SHA='865901ab24aa3736da57847f9112d3c73181085213f89b48ef2e3e7a9f6ee702'
GIS_PYTHON=Path(r'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe')

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise ImportError(f'cannot load {path}')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,default=HERE/'runs/wet-support-diagnostic-real.json')
    args=ap.parse_args()
    consumer=load_module('ev91_readonly_consumer',HERE/'verify_ev91.py')
    for path,want in consumer.PINNED.items():
        if sha(path)!=want:raise AssertionError(f'pinned input changed: {path}')
    if sha(CANDIDATE)!=EXPECTED_CANDIDATE_SHA:raise AssertionError('candidate SHA differs from approved EV91 authored artifact')
    ev=consumer.load_pinned('ev88_wet_diagnostic_helpers',consumer.EV88_PATH,consumer.PINNED[str(consumer.EV88_PATH)])
    bundle=ev.checked_sources()
    ev87=ev.import_file('ev87_wet_diagnostic',consumer.EV87_PATH)
    with np.load(CANDIDATE,allow_pickle=False) as z:
        if 'heights' not in z.files:raise AssertionError('candidate has no heights array')
        h=np.asarray(z['heights'])
    b=np.asarray(bundle['B']['heights'])
    if b.shape!=(2048,2048) or h.shape!=b.shape or b.dtype!=np.float32 or h.dtype!=np.float32:
        raise AssertionError('unexpected B/H terrain shape or dtype')
    angles_b=dict(ev87.edge_angles(b));angles_h=dict(ev87.edge_angles(h))
    metrics=consumer.eligible_wet_support_diagnostic(ev,ev87,bundle,angles_b,angles_h)
    expected={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),
        str(HERE/'verify_ev91.py'):sha(HERE/'verify_ev91.py'),
        str(CANDIDATE):sha(CANDIDATE),str(consumer.POPULATION_RECONCILIATION):sha(consumer.POPULATION_RECONCILIATION),
        **bundle['hashes']}
    for path,digest in expected.items():
        if sha(path)!=digest:raise AssertionError(f'input changed during diagnostic: {path}')
    report={'status':'WET_SUPPORT_DIAGNOSTIC_ONLY','runtime_python':sys.executable,
        'python_version':sys.version,'candidate_sha256':sha(CANDIDATE),'source_hashes':expected,
        'metrics':metrics,'scope_limit':'Diagnostic only. Does not run EV91 coverage, shape, corridor, or acceptance gates.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'population':metrics['eligible_wet_support_nodes'],
        'hinges':metrics['B']['n'],'B_p99':metrics['B']['p99'],'H_p99':metrics['H']['p99'],
        'new_over30':metrics['new_over30_count'],'output':str(args.output)}))

if __name__=='__main__':main()
