"""Challenge a genuinely accepted full dry-network candidate with targeted damage."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from verify_road_network_land import audit,ROOT


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--positive',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
    positive=json.loads(a.positive.read_text(encoding='utf-8'));asc=next(a.folder.glob('*.asc'))
    assert positive['status']=='PASS_OFFLINE_EDITABLE_DRY_NETWORK_GEOMETRY'
    assert positive['asc_sha256']==hashlib.sha256(asc.read_bytes()).hexdigest()
    data=np.load(a.folder/'reference.npz');h=data['candidate'];base=data['parent']
    kwargs=dict(maximum_delta_m=positive['maximum_delta_m'],maximum_geographic_distance_m=positive['maximum_geographic_distance_m'],local_transition_v22=positive['local_transition_v22'],outline_v33_parent=positive.get('outline_v33_parent',False))
    real=audit(a.folder,**kwargs);assert real['status']==positive['status']
    tests=[]
    def case(name,heights,key):
        report=audit(a.folder,heights,**kwargs)
        rejected=report['status']=='FAIL_OFFLINE_NETWORK_GEOMETRY' and not report['checks'][key]
        record=dict(name=name,expected_gate=key,rejected=bool(rejected));tests.append(record)
        print(json.dumps(record),flush=True);assert rejected
    case('untreated_parent',base,'routes')
    changed=h.copy();r,c=np.argwhere(data['wet'])[0];changed[r,c]+=.25
    case('protected_water_vertex',changed,'protected_exact')
    changed=h.copy();r,c=np.argwhere(~data['pilot_support']&data['pilot_allowed'])[0];changed[r,c]+=.25
    case('outside_declared_support',changed,'declared_support_exact')
    changed=h.copy();r=int(round((12282-7682.4)/6));c=int(round(7434.94/6));changed[r,c]+=.3
    case('intermediate_road_bump',changed,'routes')
    changed=h.copy();r,c=np.argwhere(data['pilot_support'])[0];changed[r,c]=base[r,c]+kwargs['maximum_delta_m']+.2
    case('excessive_grading',changed,'delta_limit')
    if kwargs['outline_v33_parent']:
        original=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz')['candidate']
        changed=h.copy();r,c=np.argwhere(data['pilot_support'])[0];changed[r,c]=original[r,c]+6.2
        case('excessive_composed_grading',changed,'composed_delta_limit')
    # A distant dry vertex tests the independent geographic limit, even if
    # other guards also reject it. Its declared mask cannot grant this scope.
    changed=h.copy();changed[1000,1000]+=.25
    case('unrelated_geographic_edit',changed,'independent_geographic_support')
    result=dict(status='PASS_FULL_NETWORK_POSITIVE_AND_NEGATIVES',negative_count=len(tests),positive_sha256=hashlib.sha256(a.positive.read_bytes()).hexdigest(),asc_sha256=positive['asc_sha256'],consumer_sha256=hashlib.sha256((ROOT/'tools/navigation/verify_road_network_land.py').read_bytes()).hexdigest(),tests=tests)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
