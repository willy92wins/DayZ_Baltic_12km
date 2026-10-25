"""One isolated physical river case with closed logs and absolute clock checks."""
from pathlib import Path
import argparse,hashlib,json,math
import rasterio
from verify_full_river_v3 import check
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def clock_check(lines,case):
    clocks={};times=[];errors=[]
    for line in lines:
        f=line.split(';')
        try:
            if f[0] in ['ABS_SPAWN_MS','ABS_END_MS']:
                if len(f)!=3 or int(f[1])!=case or f[0] in clocks:raise ValueError('Clock schema, case or duplicate')
                clocks[f[0]]=int(f[2])
            elif f[0]=='B':times.append(float(f[2]))
        except (ValueError,IndexError) as e:errors.append(str(e))
    schema=not errors and set(clocks)=={'ABS_SPAWN_MS','ABS_END_MS'}
    valid=schema and bool(times) and all(math.isfinite(t) for t in times)
    elapsed=(clocks['ABS_END_MS']-clocks['ABS_SPAWN_MS'])/1000 if schema else None
    valid=valid and clocks['ABS_SPAWN_MS']>=0 and elapsed>0 and max(times)-.05<=elapsed<=max(times)+1
    return dict(passed=bool(valid),clocks=clocks,elapsed_s=elapsed,errors=errors)

def audit(ref,folder,height):
    assert len(ref['cases'])==1
    case=ref['cases'][0]['case'];report=check(ref,folder,height)
    path=folder/f'{ref["log_prefix"]}{case}.log'
    clock=clock_check(path.read_text(encoding='utf-8-sig').splitlines(),case) if path.exists() else dict(passed=False,errors=['Missing log'])
    report.update(status='PASS_ONE_ISOLATED_RIVER_CASE' if clock['passed'] and all(c['status']=='PASS' for c in report['cases']) else 'FAIL_OR_INCOMPLETE',scope_case=case,clock=clock)
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
    ref=json.loads(a.reference.read_text(encoding='utf-8'))
    for p,digest in {**ref['mission'],**ref['inputs'],**ref['deployment'],ref['terrain']:ref['terrain_sha256']}.items():assert sha(Path(p))==digest,p
    with rasterio.open(ref['terrain']) as ds:h=ds.read(1)
    report=audit(ref,a.folder,h);report['reference_sha256']=sha(a.reference)
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['cases','limits']}));raise SystemExit(0 if report['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
