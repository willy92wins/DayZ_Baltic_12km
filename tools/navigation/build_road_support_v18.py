"""Freeze V16 road geometry with a 24m blending strip; do not solve/import."""
from pathlib import Path
import hashlib,inspect,json
import refine_road_network_v16 as source
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'tests/regional_road_network_v18_constraints'

def main():
    p=Path(source.__file__);assert hashlib.sha256(p.read_bytes()).hexdigest()=='92640b4a25e3bc8037fc9d62ebe775232b31fb66ad1051a9a0db3e6cf6cb98de'
    code=inspect.getsource(source.main)
    before='support=(distance_transform_edt(~support)*6<=12)&allowed';assert code.count(before)==1;code=code.replace(before,'support=(distance_transform_edt(~support)*6<=24)&allowed')
    code=code.replace('maximum_allowed_delta_m=2.05','maximum_allowed_delta_m=3.0')
    code=code[:code.index('    cap=2.05;matrix=')]+'''    receipt.update(status='FROZEN_CONSTRAINTS_ONLY',lateral_transition_m=24.,maximum_geographic_distance_m=36.5)
    receipt['constraints_sha256']=hashlib.sha256((OUT/'constraints.npz').read_bytes()).hexdigest()
    receipt['variables_sha256']=hashlib.sha256((OUT/'variables.npz').read_bytes()).hexdigest()
    (OUT/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\\n',encoding='utf-8')
    (OUT/'solve.json').write_text(json.dumps(receipt,indent=2)+'\\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}),flush=True)
'''
    scope=dict(vars(source),OUT=OUT);exec(compile(code,str(p)+' [V18 support24m]','exec'),scope);scope['main']()

if __name__=='__main__':main()
