"""Compare a deduplicated world against its exact pre-optimization world.

All ground, material bytes, instance IDs/poses and unrelated PBO entries must
stay exact. A model-name change is accepted only through the proved byte alias.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from wrp0wzd import read


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before',type=Path,required=True)
    ap.add_argument('--after',type=Path,required=True)
    ap.add_argument('--aliases',type=Path,required=True)
    ap.add_argument('--before-pbo-check',type=Path,required=True)
    ap.add_argument('--after-pbo-check',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    assert sha(a.before)=='a464cd162ba5720b6d0a07c88ad5aab301c316c05c348a25b1c72df4e140e4bb'
    old,new=read(a.before),read(a.after)
    aliases=json.loads(a.aliases.read_text())
    assert aliases['status']=='PASS_EXACT_MODEL_DEDUPLICATION_PENDING_WORLD_AND_ENGINE'
    assert aliases['raw_and_compiled_alias_bytes_exact'] and aliases['transforms_exact']
    pairs=list(zip(old['objects'],new['objects']));renamed=0;wrong=[]
    for before,after in pairs:
        expected=before['name']
        if expected.startswith('baltic_water_v30\\'):
            stem=expected.split('\\')[-1][:-4]
            expected='baltic_water_v30\\'+aliases['aliases'][stem]+'.p3d'
        if before['id']!=after['id'] or before['matrix']!=after['matrix'] or after['name']!=expected:
            wrong.append(dict(id=before['id'],before_name=before['name'],after_name=after['name']))
        renamed+=int(before['name']!=after['name'])
    bp=json.loads(a.before_pbo_check.read_text());ap_=json.loads(a.after_pbo_check.read_text())
    assert bp['pbo_sha256']=='572d4124c7343f7a39ebf84b81aae913636e942aa441bb5ba95e5e79d37c3b7c'
    assert bp['status']==ap_['status']=='PASS_PACKED_CONTENT'
    bentries={r['name']:r['sha256'] for r in bp['entries']}
    aentries={r['name']:r['sha256'] for r in ap_['entries']}
    samekeys=bentries.keys()==aentries.keys()
    differences=[k for k in bentries.keys()&aentries.keys() if bentries[k]!=aentries[k]]
    checks=dict(headers_exact=old['header']==new['header'],heights_exact=bool(np.array_equal(old['heights'],new['heights'])),
                materials_exact=old['materials']==new['materials'],terminator_exact=old['terminator']==new['terminator'],
                instance_count_exact=len(old['objects'])==len(new['objects'])==17646,
                poses_ids_and_aliases_exact=not wrong,bridges_exact=all(x['bytes']==y['bytes'] for x,y in pairs[:9]),
                distinct_model_count=len({o['name'] for o in new['objects'] if o['name'].startswith('baltic_water_v30\\')})==8775,
                packed_entry_names_exact=samekeys,only_compiled_wrp_changed=samekeys and differences==['baltic_trial.wrp'])
    result=dict(status='PASS_EXACT_DEDUP_WORLD_CONTENT' if all(checks.values()) else 'FAIL',checks=checks,
                renamed_instances=renamed,bad_object_records=wrong,changed_pbo_entries=differences,
                before_world_pbo_sha256=bp['pbo_sha256'],after_world_pbo_sha256=ap_['pbo_sha256'],
                files={str(p):sha(p) for p in (a.before,a.after,a.aliases,a.before_pbo_check,a.after_pbo_check)},
                limits=['Source model and placement equivalence plus packed-entry parity; no FPS or runtime claim.',
                        'The compiled world must still load and be paired with its generated navmesh.'])
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':raise SystemExit(main())
