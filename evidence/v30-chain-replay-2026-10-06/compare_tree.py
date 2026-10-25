"""Compare every file of an archived tree with the replayed one by sha256. Usage: compare_tree.py LABEL REPLAY ARCHIVED"""
import hashlib
import sys
from pathlib import Path

label, replay, archived = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


files = sorted(p.relative_to(archived) for p in archived.rglob('*') if p.is_file())
extra = sorted(p.relative_to(replay) for p in replay.rglob('*') if p.is_file() and not (archived / p.relative_to(replay)).exists())
diff = [f for f in files if not (replay / f).exists() or sha(replay / f) != sha(archived / f)]
for f in diff[:3]:
    print(f'    differs: {f}')
for f in extra[:3]:
    print(f'    only in replay: {f}')
print(f"  {'MATCH' if not diff and not extra else 'DIFF'} {label}: {len(files)} files, {len(diff)} differ, {len(extra)} extra")
