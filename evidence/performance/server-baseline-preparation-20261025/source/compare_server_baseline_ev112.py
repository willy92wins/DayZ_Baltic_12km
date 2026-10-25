"""Compare six revalidated empty-server measurements; no client or capacity claim."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from read_server_baseline_ev112 import require_inputs, verify

ORDER=('BalticTrial','ChernarusPlus','ChernarusPlus','BalticTrial','BalticTrial','ChernarusPlus')


def compare(reports):
    if len(reports)!=6 or tuple(r.get('world') for r in reports)!=ORDER:
        raise ValueError('Six passes in A-B-B-A-A-B order required')
    if any(r.get('status')!='PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT' for r in reports):
        raise ValueError('Incomplete measurement')
    if len({(r['process_id'],r['start_utc']) for r in reports})!=6:
        raise ValueError('Repeated process identity')
    result=dict(status='INCONCLUSIVE',order=list(ORDER),metrics={},limits=[
        'Only empty dedicated-server process RAM and CPU; no CE/AI/players/client.',
        'No client FPS, VRAM or production-capacity verdict.',
        'Configuration and file identities cannot prove the absence of unrelated host load.'])
    for name in ('working_set_mib','private_mib','cpu_percent_one_logical_core'):
        values=[r[name]['median'] if name!='cpu_percent_one_logical_core' else r[name] for r in reports]
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in values):
            raise ValueError('Invalid measurement value')
        a=[values[i] for i in (0,3,4)];b=[values[i] for i in (1,2,5)]
        ma=statistics.median(a);mb=statistics.median(b)
        da=(max(a)-min(a))/ma;db=(max(b)-min(b))/mb
        ratios=[x/y for x,y in zip(a,b)];ratio=ma/mb
        if name=='cpu_percent_one_logical_core':verdict='DESCRIPTIVE_ONLY'
        elif max(da,db)>.05:verdict='INCONCLUSIVE_DISPERSION'
        elif ratio<=1.1:verdict='PASS_LOCAL_RAM_BUDGET'
        elif sum(r>1.1 for r in ratios)>=2:verdict='FAIL_LOCAL_RAM_BUDGET'
        else:verdict='INCONCLUSIVE_PAIRED_EXCESS'
        result['metrics'][name]=dict(baltic=a,chernarus=b,baltic_median=ma,chernarus_median=mb,ratio=ratio,
                                    paired_ratios=ratios,baltic_dispersion=da,chernarus_dispersion=db,status=verdict)
    verdicts=[result['metrics'][k]['status'] for k in ('working_set_mib','private_mib')]
    if 'FAIL_LOCAL_RAM_BUDGET' in verdicts:result['status']='FAIL_EMPTY_SERVER_RAM_BUDGET'
    elif all(v=='PASS_LOCAL_RAM_BUDGET' for v in verdicts):result['status']='PASS_EMPTY_SERVER_RAM_BUDGET'
    return result


def conditions_identity(ref):
    hashes={str(Path(p).resolve()):v for p,v in ref['inputs'].items()}
    roles=ref['artifacts']
    config=hashes[str(Path(roles['server_config']).resolve())]
    executable=hashes[str(Path(roles['executable']).resolve())]
    mission=Path(roles['mission']).read_text(encoding='utf-8-sig')
    world=ref['world'].lower()
    if mission.count('"'+world+'"')!=1:raise ValueError('Mission world guard missing or repeated')
    canonical=mission.replace('"'+world+'"','"EXPECTED_WORLD"')
    log_names=re.findall(r'baltic_ab_\d{2}_[0-9a-f]{12}\.log',canonical)
    if len(log_names)!=2 or len(set(log_names))!=1 or Path(roles['engine']).name!=log_names[0]:
        raise ValueError('Mission and engine log identity differ')
    canonical,n=re.subn(r'baltic_ab_\d{2}_[0-9a-f]{12}\.log','BASELINE_LOG',canonical)
    if n!=2:raise ValueError('Unique mission log identity missing')
    packages=ref.get('packages',{})
    if not packages:raise ValueError('Package identities missing')
    actual={str(Path(p).resolve()):digest for p,digest in packages.items()}
    if any(hashes.get(p)!=digest for p,digest in actual.items()):raise ValueError('Package not bound to inputs')
    return dict(server_config=config,executable=executable,engine_name=log_names[0],
                canonical_mission=hashlib.sha256(canonical.encode('utf-8')).hexdigest(),
                packages=hashlib.sha256(json.dumps(actual,sort_keys=True).encode()).hexdigest())


def load_pass(reference):
    ref=json.loads(reference.read_text(encoding='utf-8-sig'))
    engine=Path(ref['artifacts']['engine']);host=Path(ref['artifacts']['host'])
    require_inputs(ref,engine,host)
    report=verify(ref['world'],ref['process_id'],ref['start_utc'],engine.read_text(encoding='utf-8-sig'),
                  [json.loads(x) for x in host.read_text(encoding='utf-8-sig').splitlines()])
    return report,conditions_identity(ref)


def require_equivalent(loaded):
    if len(loaded)!=6:raise ValueError('Six bound captures required')
    if len({x[1]['engine_name'] for x in loaded})!=6:raise ValueError('Repeated engine log identity')
    for key in ('executable','server_config','canonical_mission'):
        if len({x[1][key] for x in loaded})!=1:raise ValueError('Common conditions changed')
    for world in ORDER[:2]:
        if len({x[1]['packages'] for x in loaded if x[0]['world']==world})!=1:
            raise ValueError('World packages changed between repetitions')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--references',type=Path,nargs=6,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh comparison output required')
    loaded=[load_pass(p) for p in a.references]
    require_equivalent(loaded)
    report=compare([x[0] for x in loaded])
    report['inputs']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in a.references}
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='PASS_EMPTY_SERVER_RAM_BUDGET' else 1


if __name__=='__main__':sys.exit(main())
