"""Challenge actual pursuit evidence; a passing control never promotes a failed bridge."""
from pathlib import Path
import argparse,hashlib,json
import rasterio
from verify_continuous_pursuit_v2 import verify

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--folder',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--control-case-zero',action='store_true')
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve evidence')
    ref=json.loads(a.reference.read_text());terrain=Path(ref['terrain'])
    assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as ds:height=ds.read(1)
    sp=a.folder/'engine.log';cp=a.folder/'client-input.log'
    server=sp.read_text(encoding='utf-8-sig');client=cp.read_text(encoding='utf-8-sig')
    original=verify(ref,server,client,height)
    def accepted(report):
        if not a.control_case_zero:return report['status'].startswith('PASS_')
        return (report['cases'][0]['status']=='PASS' and all(report['global_checks'][k]
            for k in ('server_header','client_header','client_end','no_parse_errors')))
    if not server.splitlines()[-1].startswith('END;'):raise ValueError('Completed original run required')
    if not accepted(original):raise ValueError('Actual positive required for selected scope')
    base=server.splitlines();cbase=client.splitlines()
    spawn=next(i for i,s in enumerate(base) if s.startswith('P;0;') and s.split(';')[3]=='SPAWN')
    sample=next(i for i in range(spawn+1,len(base)) if base[i].startswith('P;0;') and base[i].split(';')[3]=='SAMPLE')
    reached=next(i for i,s in enumerate(base) if s.startswith('P;0;') and s.split(';')[3]=='REACHED')
    def field(index,value,selected=sample):
        rows=base.copy();parts=rows[selected].split(';');parts[index]=str(value);rows[selected]=';'.join(parts)
        return '\n'.join(rows)+'\n'
    def move(value,delta):
        nums=[float(x) for x in value[1:-1].split(',')]
        return '<'+', '.join(f'{x+d:.6f}' for x,d in zip(nums,delta))+'>'
    row=base[sample].split(';')
    changes={
        'dead_actor':(field(6,0),client),
        'dead_prey':(field(7,0),client),
        'unconscious_prey':(field(17,'true'),client),
        'nonfinite_health':(field(6,'nan'),client),
        'wrong_ground':(field(10,move(row[10],[0,1,0])),client),
        'floating_actor':(field(4,move(row[4],[0,2,0])),client),
        'wrong_goal':(field(14,move(row[14],[1,0,0])),client),
        'wrong_spawn':(field(4,move(base[spawn].split(';')[4],[1,0,0]),spawn),client),
        'false_arrival':(field(4,base[spawn].split(';')[4],reached),client),
        'unknown_marker':(field(3,'FORGED_PASS'),client),
        'clock_backwards':(field(2,0),client),
        'missing_spawn':('\n'.join(base[:spawn]+base[spawn+1:])+'\n',client),
        'duplicate_spawn':('\n'.join(base[:spawn]+[base[spawn]]+base[spawn:])+'\n',client),
        'missing_input':(server,'\n'.join(s for s in cbase if not (s.startswith('C;') and s.split(';')[2]=='1'))+'\n'),
        'client_missing_end':(server,'\n'.join(cbase[:-1])+'\n'),
    }
    results=[]
    for name,(s,c) in changes.items():
        if s==server and c==client:raise ValueError('No mutation: '+name)
        result=verify(ref,s,c,height)
        if accepted(result):raise ValueError('False acceptance: '+name)
        # Invalid data must still produce strict JSON, including zero-time displacements.
        json.dumps(result,allow_nan=False)
        results.append(dict(name=name,status='EXPECTED_REJECTION',
            control_failures=[k for k,v in result['cases'][0].get('checks',{}).items() if not v],
            parse_errors=result['errors'],server_sha256=hashlib.sha256(s.encode()).hexdigest(),
            client_sha256=hashlib.sha256(c.encode()).hexdigest()))
    report=dict(status='PASS_ACTUAL_PURSUIT_POSITIVE_AND_NEGATIVE_CONTROLS',
        full_run_status=original['status'],scope='actual control case0 only' if a.control_case_zero else 'complete actual run',
        limits='Robustness of verifier only; original bridge failures remain unchanged.',
        reference_sha256=sha(a.reference),server_sha256=sha(sp),client_sha256=sha(cp),controls=results)
    a.out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=report['status'],scope=report['scope'],negatives=len(results))))

if __name__=='__main__':main()
