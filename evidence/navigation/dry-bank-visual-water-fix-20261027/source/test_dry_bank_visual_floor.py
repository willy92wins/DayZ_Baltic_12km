"""Same controls plus the actual false-PASS regression; at most 3 read-only CLIs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,importlib.util,json,sys
import numpy as np

def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def main():
    p=argparse.ArgumentParser();p.add_argument('--context',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();args.output.mkdir(exist_ok=False)
    checker=module('verify_dry_bank_visual_floor');runner=module('run_dry_bank_visual_floor')
    ctx=checker.read(args.context);source=Path(ctx['paths']['source']);arrays=checker.load(source)
    masks=checker.reconstruct(ctx,arrays);qs=masks['qs'];station=arrays['station'];mid=len(station)//2
    caprow=int(np.flatnonzero((station>0)&(station<6))[0]);col=lambda q:int(np.flatnonzero(qs==q)[0])
    free_point=tuple(map(int,np.argwhere(masks['eligible'])[0]));protected=np.argwhere(masks['protected'])
    failed_row=checker.read(ctx['paths']['rounding_diagnosis'])['rows'][0]
    regression_point=(failed_row['row'],failed_row['column'],1)
    cases=[('identity',None,None,None),('cap_interior','bed',(caprow,col(5),1),'cap_exact'),
           ('wet_bed','bed',(mid,col(2),1),'wet_exact'),('water_y','water',(mid,0,1),'water_exact'),
           ('bed_xz','bed',(mid,col(5),0),'bed_xz_exact'),('outer_border','bed',(mid,col(18),1),'border_exact'),
           ('ceiling','bed',(*free_point,1),'bounds'),('nonfinite','water',(mid,0,1),'invalid'),
           ('actual_dry_floor','bed',regression_point,'bounds'),('retired_candidate',None,None,'bounds')]
    results=[]
    if len(protected):
        cases.append(('protected','bed',(*map(int,protected[0]),1),'protected_exact'))
    else:results.append(dict(case='protected_mutant',result='NOT_APPLICABLE',reason='Zero frozen baseline vertices in protected terrain.'))
    for name,key,index,gate in cases:
        folder=args.output/name;folder.mkdir()
        if name=='retired_candidate':
            (folder/'candidate.npz').write_bytes(Path(ctx['paths']['rejected_candidate']).read_bytes());continue
        values={k:v.copy() for k,v in arrays.items()}
        if key:values[key][index]+=1/512 if name=='ceiling' else -1/512
        if name=='nonfinite':values[key][index]=np.nan
        np.savez_compressed(folder/'candidate.npz',**values)
    def run_case(case):
        name,key,index,gate=case;folder=args.output/name
        command=[sys.executable,'-I',str(Path(__file__).with_name('verify_dry_bank_visual_floor.py')),
                 '--baseline',str(source),'--candidate',str(folder/'candidate.npz'),'--context',str(args.context),
                 '--output',str(folder/'result.json')]
        rc=runner.bounded(command,ctx['worktree'],folder,240);result=checker.read(folder/'result.json')
        assert rc==2,(name,rc,result)
        if name=='identity':
            assert result['gates']['preservation'] and result['gates']['bounds']
            assert not result['gates']['changed'] and not result['gates']['energy_strictly_lower']
        elif gate=='invalid':assert result['status']=='REJECTED_INVALID_INPUT'
        elif gate=='bounds':assert result['gates']['bounds'] is False
        else:assert result['preservation'][gate] is False
        print('CONTROL PASS',name,flush=True)
        return dict(case=name,result='PASS',expected_failed_gate=gate,exitcode=rc)
    with ThreadPoolExecutor(max_workers=3) as pool:results.extend(pool.map(run_case,cases))
    folder=args.output/'timeout';folder.mkdir()
    rc=runner.bounded([sys.executable,'-I','-c','import time;time.sleep(30)'],ctx['worktree'],folder,.15)
    assert rc==124 and checker.read(folder/'completion.json')['timeout']
    results.append(dict(case='timeout_propagation',result='PASS',exitcode=rc))
    assert not checker.identical(np.array([0.]),np.array([-0.]))
    results.append(dict(case='bitwise_signed_zero',result='PASS'))
    checker.check_sources(ctx)
    (args.output/'summary.json').write_text(json.dumps(dict(status='PASS',tests=results),indent=2)+'\n',encoding='utf-8')
    print('PASS',sum(r['result']=='PASS' for r in results),'controls; NOT_APPLICABLE',sum(r['result']=='NOT_APPLICABLE' for r in results))

if __name__=='__main__':main()
