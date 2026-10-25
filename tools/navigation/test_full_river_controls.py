"""Challenge the channel aggregator with corrupted copies of a real completed run."""
from pathlib import Path
import argparse, hashlib, json, shutil, tempfile
import rasterio
from verify_full_river_consumer import check

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--folder',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve prior evidence')
    ref=json.loads(a.reference.read_text());terrain=Path(ref['terrain'])
    if sha(terrain)!=ref['terrain_sha256']:raise ValueError('Terrain identity changed')
    with rasterio.open(terrain) as ds:height=ds.read(1)
    positive=check(ref,a.folder,height)
    if not positive['status'].startswith('PASS_'):raise ValueError('Actual complete positive required')
    prefix=ref['log_prefix'];first=a.folder/f'{prefix}0.log';second=a.folder/f'{prefix}1.log'
    base=first.read_text(encoding='utf-8-sig').splitlines()
    sample=next(i for i,line in enumerate(base) if line.startswith('B;0;'))
    def changed(index,value):
        rows=base.copy();parts=rows[sample].split(';');parts[index]=value;rows[sample]=';'.join(parts)
        return '\n'.join(rows)+'\n'
    mutations={
        'missing_channel':None,
        'swapped_channel_log':second.read_text(encoding='utf-8-sig'),
        'wrong_header':'WRONG_WORLD_LOG\n'+'\n'.join(base[1:])+'\n',
        'missing_terminal':'\n'.join(base[:-1])+'\n',
        'no_motion':'\n'.join(line for line in base if not line.startswith('B;'))+'\n',
        'nonfinite_ground':changed(19,'nan'),
        'wrong_ground':changed(19,str(float(base[sample].split(';')[19])+1)),
        'duplicate_sample':'\n'.join(base[:sample]+[base[sample]]+base[sample:])+'\n',
    }
    results=[]
    with tempfile.TemporaryDirectory(prefix='baltic-river-controls-') as scratch:
        target=Path(scratch)
        for case in ref['cases']:
            name=f'{prefix}{case["case"]}.log';shutil.copy2(a.folder/name,target/name)
        p=target/first.name
        for name,text in mutations.items():
            if text is None:p.unlink()
            else:p.write_text(text)
            report=check(ref,target,height)
            if report['status'].startswith('PASS_'):raise ValueError('False acceptance: '+name)
            results.append(dict(name=name,status='EXPECTED_REJECTION',case0_status=report['cases'][0]['status'],
                modified_log_sha256=sha(p) if p.exists() else None))
            shutil.copy2(first,p)
    result=dict(status='PASS_ACTUAL_CHANNEL_COVERAGE_AND_NEGATIVES',reference_sha256=sha(a.reference),
        source_logs_sha256=positive['logs_sha256'],controls=results,
        limit='Verifier robustness only; physical scope remains the frozen selected channels and empty boat.')
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],negative_controls=len(results))))

if __name__=='__main__':main()
