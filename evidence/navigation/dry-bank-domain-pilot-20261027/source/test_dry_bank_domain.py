"""Closed counterexample list, CLI-level saved-file tests plus timeout regression."""
from pathlib import Path
import argparse
import importlib.util
import json
import subprocess
import sys
import numpy as np

def module(name):
    path=Path(__file__).with_name(name+'.py')
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def main():
    p=argparse.ArgumentParser();p.add_argument('--context',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();args.output.mkdir(exist_ok=False)
    checker=module('verify_dry_bank_domain');runner=module('run_dry_bank_domain')
    context=checker.read(args.context);source=Path(context['paths']['source']);arrays=checker.load(source)
    masks=checker.reconstruct(context,arrays);qs=masks['qs'];station=arrays['station'];n=len(station)
    caprow=int(np.flatnonzero((station>0)&(station<6))[0]);mid=n//2
    col=lambda q:int(np.flatnonzero(qs==q)[0])
    protected_points=np.argwhere(masks['protected'])
    free_point=tuple(map(int,np.argwhere(masks['eligible'])[0]))
    cases=[('identity',None,None,None),
           ('cap_interior','bed',(caprow,col(5),1),'cap_exact'),
           ('wet_bed','bed',(mid,col(2),1),'wet_exact'),
           ('water_y','water',(mid,0,1),'water_exact'),
           ('bed_xz','bed',(mid,col(5),0),'bed_xz_exact'),
           ('outer_border','bed',(mid,col(18),1),'border_exact'),
           ('ceiling','bed',(*free_point,1),'bounds'),
           ('nonfinite','water',(mid,0,1),'invalid')]
    results=[]
    if len(protected_points):
        protected_point=tuple(map(int,protected_points[0]))
        cases.append(('protected','bed',(*protected_point,1),'protected_exact'))
    else:
        results.append(dict(case='protected_mutant',result='NOT_APPLICABLE',
                            reason='Frozen baseline has zero vertices touching protected terrain. No mutant claimed.'))
    for name,key,index,failed_gate in cases:
        folder=args.output/name;folder.mkdir();candidate=folder/'candidate.npz'
        values={k:v.copy() for k,v in arrays.items()}
        if key:
            values[key][index] += 1/512 if name=='ceiling' else -1/512
        if name=='nonfinite':values[key][index]=np.nan
        np.savez_compressed(candidate,**values)
        command=[sys.executable,'-I',str(Path(__file__).with_name('verify_dry_bank_domain.py')),
                 '--baseline',str(source),'--candidate',str(candidate),'--context',str(args.context),'--output',str(folder/'result.json')]
        rc=runner.bounded(command,context['worktree'],folder,180)
        result=checker.read(folder/'result.json')
        assert rc==2,(name,rc,result)
        if name=='identity':
            assert result['gates']['preservation'] and result['gates']['bounds']
            assert not result['gates']['changed'] and not result['gates']['energy_strictly_lower']
        elif failed_gate=='invalid':assert result['status']=='REJECTED_INVALID_INPUT'
        elif failed_gate=='bounds':assert result['gates']['bounds'] is False
        else:assert result['preservation'][failed_gate] is False
        results.append(dict(case=name,result='PASS',expected_failed_gate=failed_gate,exitcode=rc))
    # Simulate an owned child timing out; timeout receipt and caller code must both fail.
    folder=args.output/'timeout';folder.mkdir()
    rc=runner.bounded([sys.executable,'-I','-c','import time; time.sleep(30)'],context['worktree'],folder,.15)
    assert rc==124 and checker.read(folder/'completion.json')['timeout'] is True
    results.append(dict(case='timeout_propagation',result='PASS',exitcode=rc))
    # Byte identity must detect signed-zero changes even when numeric equality holds.
    assert not checker.identical(np.array([0.]),np.array([-0.]))
    results.append(dict(case='bitwise_signed_zero',result='PASS'))
    checker.check_sources(context)
    (args.output/'summary.json').write_text(json.dumps(dict(status='PASS',tests=results),indent=2)+'\n',encoding='utf-8')
    print('PASS',sum(r['result']=='PASS' for r in results),'controls;',
          sum(r['result']=='NOT_APPLICABLE' for r in results),'not applicable; candidate acceptance remains separate')

if __name__=='__main__':main()
