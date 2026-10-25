"""Compare complete native exports, ignoring only order of object records."""
from pathlib import Path
import argparse, hashlib, json, struct, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from verify_texture_grid_change import read

def inspect(first, reopened):
    a, b = read(first), read(reopened)
    left = {o['id']: o for o in a['objects']}
    right = {o['id']: o for o in b['objects']}
    changes = []
    for ident in sorted(left.keys() & right.keys()):
        x, y = left[ident], right[ident]
        if (x['name'].lower(), x['matrix']) != (y['name'].lower(), y['matrix']):
            mx = struct.unpack('<12f', bytes.fromhex(x['matrix']))
            my = struct.unpack('<12f', bytes.fromhex(y['matrix']))
            changes.append(dict(id=ident, model_before=x['name'], model_after=y['name'],
                                matrix_before=mx, matrix_after=my,
                                delta=[v-u for u,v in zip(mx,my)]))
    checks = dict(preobjects_exact=a['bytes'][:a['objects_start']]==b['bytes'][:b['objects_start']],
                  unique_ids=len(left)==len(a['objects']) and len(right)==len(b['objects']),
                  same_ids=left.keys()==right.keys(), canonical_records_exact=not changes)
    return dict(status='PASS_EXACT_NATIVE_PERSISTENCE' if all(checks.values()) else 'FAIL',
                checks=checks, first=str(first), reopened=str(reopened),
                first_sha256=hashlib.sha256(first.read_bytes()).hexdigest(),
                reopened_sha256=hashlib.sha256(reopened.read_bytes()).hexdigest(),
                objects_first=len(left), objects_reopened=len(right), changes=changes,
                limits=['UI close/reopen provenance is separate. No runtime proof.'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--first',type=Path,required=True)
    p.add_argument('--reopened',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError('Preserve prior evidence')
    r=inspect(a.first,a.reopened);a.out.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2));raise SystemExit(0 if r['status'].startswith('PASS_') else 1)
