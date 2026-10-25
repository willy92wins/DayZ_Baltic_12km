"""Reject corruptions of an independently observed, complete native chase."""
import json
import rasterio
from verify_native_chase import ROOT, verify

folder = ROOT/'evidence/navigation/native-chase-v2'
text = (folder/'engine.log').read_text()
ref = json.loads((ROOT/'evidence/navigation/native-chase-reference-v2.json').read_text())
with rasterio.open(ROOT/'tests/narva_navigation_v3/narva_navigation_v1.asc') as ds:
    height = ds.read(1)
assert verify(text,ref,height)['status'].startswith('PASS')


def change_sample(column, value):
    lines=text.splitlines()
    index=next(i for i,l in enumerate(lines) if l.startswith('SAMPLE;') and l.split(';')[2]=='1')
    cells=lines[index].split(';');cells[column]=value;lines[index]=';'.join(cells)
    return '\n'.join(lines)+'\n'


lines=text.splitlines()
prey_i=next(i+1 for i,l in enumerate(lines) if l.startswith('SAMPLE;') and l.split(';')[2]=='1')
prey=lines[prey_i].split(';');prey[3]='<2500, 9, 6880>';lines[prey_i]=';'.join(prey)
cases={
    'wrong_world': text.replace('world=BalticTrial','world=ChernarusPlus'),
    'truncated': text[:text.index('COMPLETE_ALL_STAGES')],
    'nonfinite_health': change_sample(8,'nan'),
    'dead_actor': change_sample(8,'0'),
    'below_road': change_sample(4,'1.25'),
    'off_corridor_or_inconsistent_axis': change_sample(5,'6910'),
    'moved_prey': '\n'.join(lines)+'\n',
    'missing_prey': text.replace(text.splitlines()[prey_i]+'\n','',1),
}
out={}
for name, value in cases.items():
    try:
        result=verify(value,ref,height)
        rejected=not result['status'].startswith('PASS')
        reason=result.get('issues')
    except (ValueError,KeyError,IndexError) as exc:
        rejected=True;reason=str(exc)
    assert rejected,name
    out[name]={'rejected':True,'reason':reason}
(folder/'negative-controls.json').write_text(json.dumps({'positive_fixture':'engine.log','negative_controls':out},indent=2)+'\n')
print(f'PASS: real consumer fixture accepted; {len(cases)} corruptions rejected')
