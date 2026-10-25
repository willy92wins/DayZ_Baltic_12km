"""Mutation checks against the actual accepted V14 pilot; never write altered ASC."""
from pathlib import Path
import json,hashlib
import numpy as np
from verify_road_width_pilot import audit,ROOT

def main():
    folder=ROOT/'tests/regional_road_triangles_pilot_v14';out=folder/'negative-controls.json';assert not out.exists()
    data=np.load(folder/'reference.npz');h=data['candidate'];base=data['parent']
    positive=audit(folder,maximum_delta_m=2.05);assert positive['status'].startswith('PASS_')
    tests=[]
    def case(name,heights,key):
        result=audit(folder,heights,maximum_delta_m=2.05)
        rejected=result['status']=='FAIL_OFFLINE_PILOT' and not result['checks'][key]
        tests.append(dict(test=name,expected_gate=key,rejected=bool(rejected)));print(json.dumps(tests[-1]),flush=True);assert rejected
    case('untreated_parent',base,'routes')
    changed=h.copy();r,c=np.argwhere(data['wet']&(np.indices(h.shape)[0]>50))[0];changed[r,c]+=.25
    case('protected_water_vertex',changed,'protected_exact')
    changed=h.copy();changed[1000,1000]+=.25
    case('outside_declared_corridors',changed,'declared_support_exact')
    changed=h.copy();r=int(round((12282-7682.4)/6));c=int(round(7434.94/6));changed[r,c]+=.3
    case('intermediate_road_bump',changed,'routes')
    changed=h.copy();r,c=np.argwhere(data['pilot_support'])[0];changed[r,c]=base[r,c]+2.2
    case('excessive_grading',changed,'delta_limit')
    receipt=dict(status='PASS_FIVE_EXPECTED_REJECTIONS',positive=positive['status'],asc_sha256=positive['asc_sha256'],consumer_sha256=hashlib.sha256((ROOT/'tools/navigation/verify_road_width_pilot.py').read_bytes()).hexdigest(),tests=tests)
    out.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(receipt['status'])

if __name__=='__main__':main()
