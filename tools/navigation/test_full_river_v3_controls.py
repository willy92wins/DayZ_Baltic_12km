"""Adversarial mutations of one real completed V3 case; no whole-map claim."""
from pathlib import Path
import argparse,hashlib,json,tempfile
import rasterio
from verify_full_river_v3 import check

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',required=True,type=Path);ap.add_argument('--folder',required=True,type=Path)
    ap.add_argument('--case',type=int,default=11);ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args();assert not a.out.exists()
    ref=json.loads(a.reference.read_text(encoding='utf-8'))
    ref['cases']=[next(c for c in ref['cases'] if c['case']==a.case)]
    assert sha(Path(ref['terrain']))==ref['terrain_sha256']
    with rasterio.open(ref['terrain']) as ds:height=ds.read(1)
    positive=check(ref,a.folder,height)
    assert all(c['status']=='PASS' for c in positive['cases']),positive
    name=f'{ref["log_prefix"]}{a.case}.log';source=a.folder/name
    rows=source.read_text(encoding='utf-8-sig').splitlines()
    bs=[i for i,l in enumerate(rows) if l.startswith('B;')];ts=[i for i,l in enumerate(rows) if l.startswith('T;')]
    def modified(row,index,value):
        result=rows.copy();f=result[row].split(';');f[index]=value;result[row]=';'.join(f);return result
    def mutate_pos():
        result=rows.copy();f=result[bs[len(bs)//2]].split(';');p=[float(v) for v in f[22].strip('<>').split(',')]
        p[0]+=50;f[3]=f'{p[0]:.6g}';f[22]='<'+', '.join(f'{v:.6f}' for v in p)+'>'
        result[bs[len(bs)//2]]=';'.join(f);return result
    tests={
        'missing_case':None,
        'missing_terminal':rows[:-1],
        'nonfinite_position':modified(bs[0],3,'nan'),
        'physical_teleport':mutate_pos(),
        'health_loss':modified(bs[len(bs)//2],8,'500'),
        'wrong_ground':modified(bs[0],19,str(float(rows[bs[0]].split(';')[19])+1)),
        'omitted_transition':rows[:ts[1]]+rows[ts[1]+1:],
        'duplicated_transition':rows[:ts[1]]+[rows[ts[1]]]+rows[ts[1]:],
        'skipped_target_index':modified(ts[1],4,'1000'),
        'unordered_transition_time':modified(ts[1],2,'0'),
        'arrival_without_motion':[l for l in rows if not l.startswith('B;')],
        'final_engine_active':modified(bs[-1],9,'true'),
    }
    result=[]
    with tempfile.TemporaryDirectory(prefix='baltic-fullriver-v3-controls-') as temp:
        folder=Path(temp);target=folder/name
        for label,mutated in tests.items():
            if mutated is None:
                if target.exists():target.unlink()
            else:target.write_text('\n'.join(mutated)+'\n',encoding='utf-8')
            observed=check(ref,folder,height)
            assert not observed['status'].startswith('PASS_'),label
            result.append(dict(name=label,status='EXPECTED_REJECTION'))
    report=dict(status='PASS_REAL_CASE_AND_12_NEGATIVES',scope_case=a.case,reference_sha256=sha(a.reference),source_log_sha256=sha(source),controls=result,limit='Verifier robustness on the stated real case only; not four-case or whole-map acceptance.')
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='controls'}))

if __name__=='__main__':main()
