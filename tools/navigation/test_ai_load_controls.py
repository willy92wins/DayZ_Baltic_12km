"""Positive real load record plus targeted false-pass controls."""
import argparse
import json
from pathlib import Path
from verify_ai_load import ROOT,verify

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--folder',type=Path,default=ROOT/'evidence/performance/ai-load-v1')
parser.add_argument('--reference',type=Path,default=ROOT/'evidence/performance/ai-load-reference-v1.json')
parser.add_argument('--out',type=Path)
args=parser.parse_args()
folder=args.folder
output=args.out or folder/'negative-controls.json'
if output.exists():raise ValueError('Preserve prior evidence')
text=(folder/'engine.log').read_text()
ref=json.loads(args.reference.read_text(encoding='utf-8-sig'))
assert verify(text,ref)['status'].startswith('PASS')


def change_phase(column,value):
    lines=[]
    for line in text.splitlines():
        cells=line.split(';')
        if cells[:2]==['S','2']:
            cells[column]=value
        lines.append(';'.join(cells))
    return '\n'.join(lines)+'\n'


rows=text.splitlines()
target=next(l for l in rows if l.startswith('S;2;1;'))
cases={
    'truncated':text[:text.index('COMPLETE;')],
    'wrong_world':text.replace('BalticTrial','chernarusplus'),
    'nonfinite_cpu_independent_engine_field':change_phase(8,'nan'),
    'missing_population':change_phase(11,'99'),
    'asleep_population':change_phase(12,'0'),
    'moved_target':change_phase(15,'3'),
    'missing_sample':text.replace(target+'\n','',1),
    'duplicate_sample':text.replace(target+'\n',target+'\n'+target+'\n',1),
}
results={}
for name,value in cases.items():
    try:
        result=verify(value,ref)
        rejected=not result['status'].startswith('PASS');reason=result.get('issues')
    except (ValueError,KeyError,IndexError) as exc:
        rejected=True;reason=str(exc)
    assert rejected,name
    results[name]={'rejected':rejected,'reason':reason}
output.write_text(json.dumps({'positive':str(folder/'engine.log'),'reference':str(args.reference),'cases':results},indent=2)+'\n')
print(f'PASS: real load accepted, {len(cases)} corrupted records rejected')
