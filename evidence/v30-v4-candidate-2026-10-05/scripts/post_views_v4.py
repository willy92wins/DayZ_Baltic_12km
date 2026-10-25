"""After the v4 views: per-pose capture folders -> frame-groups.json, a flat shots folder and a hashed manifest.

Usage: post_views_v4.py VIEWS_DIR POSES_JSON [POSES_JSON ...]
VIEWS_DIR/<POSE>/capture_*.jpg as capture_screenshot saved them (one save_dir per pose).
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

views = Path(sys.argv[1])
poses = {}
for pj in sys.argv[2:]:
    for p in json.loads(Path(pj).read_text(encoding='utf-8')):
        poses[p['name']] = p
flat = views / 'shots'
assert not flat.exists(), 'fresh shots folder required'
flat.mkdir()
groups, manifest = {}, []
for d in sorted(x for x in views.iterdir() if x.is_dir() and x.name in poses):
    frames = []
    for f in sorted(d.glob('capture_*.jpg')):
        g = re.search(r'_(\d{6}_\d{3})\.jpg$', f.name)
        frames.append(g.group(1))
        shutil.copyfile(f, flat / f.name)
        b = (flat / f.name).read_bytes()
        assert b == f.read_bytes()
        manifest.append({'pose': d.name, 'name': f.name, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})
    groups[d.name] = {'cam': poses[d.name]['cam_pos'], 'look': poses[d.name]['look_at'], 'frames': frames}
(views / 'frame-groups.json').write_text(json.dumps(groups, indent=1) + '\n', encoding='utf-8')
(views / 'shots-manifest.json').write_text(json.dumps({'folder': str(flat), 'count': len(manifest), 'files': manifest},
                                                      indent=1) + '\n', encoding='utf-8')
print({k: len(v['frames']) for k, v in groups.items()}, len(manifest))
