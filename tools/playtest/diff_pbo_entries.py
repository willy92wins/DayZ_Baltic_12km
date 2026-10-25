"""Entry-level diff of two uncompressed PBOs with the project's own reader.

Uses tools/playtest/attach_navmesh.py read_pbo (rejects compressed, unsafe or duplicate entries) and
compares every entry by SHA-256, plus the header properties. Read-only.
"""
from pathlib import Path
import argparse
import hashlib
import json

from attach_navmesh import read_pbo


def entries_and_props(path):
    parts = read_pbo(path)
    entries = next(x for x in parts if isinstance(x, dict) and len(x) > 100)
    props = next(x for x in parts if isinstance(x, dict) and len(x) <= 100)
    return {k: hashlib.sha256(bytes(v)).hexdigest() for k, v in entries.items()}, props


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--old', type=Path, required=True)
    ap.add_argument('--new', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Preserve prior evidence'
    old, old_props = entries_and_props(a.old)
    new, new_props = entries_and_props(a.new)
    differing = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    result = dict(old=str(a.old), new=str(a.new), entries=[len(old), len(new)], props_equal=old_props == new_props,
                  only_old=sorted(set(old) - set(new)), only_new=sorted(set(new) - set(old)),
                  differing=differing, differing_count=len(differing),
                  differing_non_layer=[k for k in differing if not k.startswith('data/layers/')])
    a.out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 12 else f'{len(v)} items')
                      for k, v in result.items()}, indent=1))


if __name__ == '__main__':
    main()
