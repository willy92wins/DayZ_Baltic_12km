"""Compare every height/material/object through a native WRP import/export."""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from wrp0wzd import read


def compare(a, b):
    def records(w):
        return Counter((o['name'].lower(), tuple(o['matrix'])) for o in w['objects'])
    left, right = records(a), records(b)
    checks = dict(
        dimensions_and_header_exact=a['header'] == b['header'],
        all_heights_exact=np.array_equal(a['heights'], b['heights']),
        finite_heights_and_poses=bool(np.isfinite(b['heights']).all() and all(
            np.isfinite(o['matrix']).all() for o in b['objects'])),
        material_grid_and_names_exact=a['materials'] == b['materials'],
        all_models_and_poses_exact=left == right,
        unique_object_ids=len({o['id'] for o in b['objects']}) == len(b['objects']),
        terminator_exact=a['terminator'] == b['terminator'])
    same_shape = a['heights'].shape == b['heights'].shape
    amap, bmap = {o['id']: o for o in a['objects']}, {o['id']: o for o in b['objects']}
    return dict(status='PASS_NATIVE_IMPORT_CONTENT' if all(checks.values()) else 'FAIL',
        checks=checks, objects=[len(a['objects']), len(b['objects'])],
        height_differences=int(np.sum(a['heights'] != b['heights'])) if same_shape else None,
        max_height_delta_m=float(np.max(np.abs(a['heights'].astype(float) - b['heights']))) if same_shape else None,
        missing_pose_records=sum((left-right).values()), extra_pose_records=sum((right-left).values()),
        ids_identical=amap.keys() == bmap.keys(),
        poses_identical_by_id=amap.keys() == bmap.keys() and all(
            amap[k]['matrix'] == bmap[k]['matrix'] and amap[k]['name'].lower() == bmap[k]['name'].lower() for k in amap),
        limits=['All object poses compared as a multiset; ID reassignment reported separately.',
                'Native save/reopen provenance and runtime acceptance are separate.'])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--export', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args=ap.parse_args()
    assert not args.out.exists(), 'Preserve prior evidence'
    result=compare(read(args.reference), read(args.export))
    result['files']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.reference,args.export)}
    args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)


if __name__=='__main__':
    main()
