"""Freeze unchanged road criteria on V33 with a uniform 48m dry transition."""
from pathlib import Path
import hashlib
import inspect
import json
import refine_road_network_v16 as source

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'tests/regional_road_network_v24_constraints'


def main():
    path=Path(source.__file__)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(path)=='92640b4a25e3bc8037fc9d62ebe775232b31fb66ad1051a9a0db3e6cf6cb98de'
    parent=ROOT/'tests/regional_outline_smoothing_v33/reference.npz'
    assert sha(parent)=='8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a'
    trace=ROOT/'tests/regional_road_network_v22_constraints/conflict-v23-trace/fixed-boundary.json'
    assert sha(trace)=='78a516862ecae5e14ad1e360525cee77711d410ad820917611929bc2b53859cf'
    code=inspect.getsource(source.main)
    for before,after in {
        "source=ROOT/'tests/regional_foundation_combined_v10/reference.npz'":"source=ROOT/'tests/regional_outline_smoothing_v33/reference.npz'",
        'support=(distance_transform_edt(~support)*6<=12)&allowed':'support=(distance_transform_edt(~support)*6<=48)&allowed',
        'maximum_allowed_delta_m=2.05':'maximum_allowed_delta_m=6.0',
    }.items():
        assert code.count(before)==1,before
        code=code.replace(before,after)
    code=code[:code.index('    cap=2.05;matrix=')]+'''    receipt.update(status='FROZEN_CONSTRAINTS_ONLY',lateral_transition_m=48.,maximum_geographic_distance_m=60.5,source_npz='tests/regional_outline_smoothing_v33/reference.npz',original_delta_cap_m=6.)
    receipt['constraints_sha256']=hashlib.sha256((OUT/'constraints.npz').read_bytes()).hexdigest()
    receipt['variables_sha256']=hashlib.sha256((OUT/'variables.npz').read_bytes()).hexdigest()
    (OUT/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}),flush=True)
'''
    scope=dict(vars(source),OUT=OUT)
    exec(compile(code,str(path)+' [V24 V33 uniform48m]','exec'),scope)
    scope['main']()


if __name__=='__main__':main()
