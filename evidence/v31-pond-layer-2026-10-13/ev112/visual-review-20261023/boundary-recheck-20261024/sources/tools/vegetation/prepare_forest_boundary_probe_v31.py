"""Freeze all boundary roots and dense native-terrain samples from a staged WRP.

Sampling finds counterexamples; it does not replace the exact continuous-disc gate.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import uuid
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_visual_forest_support_v31 import forest_arrays, read, outside_measured_domain


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def disc_points(x, z, radius):
    """Centre, <=0.25 m perimeter spacing and a 0.5 m interior grid."""
    points = {(float(np.float32(x)), float(np.float32(z)))}
    n = max(16, math.ceil(2 * math.pi * radius / .25))
    for theta in np.arange(n) * (2 * math.pi / n):
        points.add((float(np.float32(x + radius * math.cos(theta))), float(np.float32(z + radius * math.sin(theta)))))
    for xx in np.arange(math.ceil((x-radius)*2), math.floor((x+radius)*2)+1) / 2:
        for zz in np.arange(math.ceil((z-radius)*2), math.floor((z+radius)*2)+1) / 2:
            if (xx-x)**2 + (zz-z)**2 <= radius**2:
                points.add((float(xx), float(zz)))
    return sorted(points)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'stage', 'merged', 'mod', 'output', 'mission'):
        ap.add_argument('--'+name, type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists() or a.mission.exists():
        raise FileExistsError('fresh output and mission required')
    source = a.stage/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    terrain = a.merged/'terrain-buried.npz'
    sr = json.loads((a.stage/'stage-report.json').read_text())
    reference = Path(sr['forest_reference']['path'])
    if sha(reference) != sr['forest_reference']['sha256']:
        raise ValueError('forest reference identity changed')
    models = json.loads(reference.read_text())['models']
    oldids = {o['id'] for o in read(a.build/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')['objects']}
    H = np.load(terrain)['heights']
    count = sr['remaining_objects']-(len(oldids)-sr['removed_old_kit_records'])
    names, ids, matrices = forest_arrays(source, oldids, sorted(models), count, H)
    A = matrices[:,:9].reshape(-1,3,3).transpose(0,2,1).astype(float)
    origin = matrices[:,9:]-np.einsum('nij,nj->ni', A, np.array([models[n]['bc'] for n in names]))
    scale = np.linalg.norm(A[:,:,0], axis=1)
    families = np.array([models[n]['family'] for n in names])
    trees = np.isin(families, ['conifer','broadleaf','bush'])
    trunk = np.array([models[n]['trunk_radius'] for n in names])*scale
    embed = np.array([-min(models[n]['visual_bottom_local'],0.) for n in names])*scale
    radius = np.where(families=='reed', .25, np.array([models[n]['base_radius_plan'] for n in names])*scale+.25)
    required = np.maximum(radius, np.where(trees,trunk,0.))
    ix = np.flatnonzero(outside_measured_domain(origin,required))
    # A dedicated sea-band survey is valid only without native ponds near these
    # boundaries. Do not silently classify an omitted pond as a sea-only margin.
    plane = np.load(a.merged/'bury-work/fp0/footprint.npz')['plane']
    k = math.ceil(float(required[ix].max()) / 6)+2
    if any(np.isfinite(v).any() for v in (plane[:k],plane[-k:],plane[:,:k],plane[:,-k:])):
        raise ValueError('boundary pond requires a pond-aware probe')
    objects, points = [], []
    for i in ix:
        x, y, z = origin[i]; oid = int(ids[i])
        objects.append(dict(id=oid, model=str(names[i]), root_x=float(x), root_y=float(y), root_z=float(z),
                            embed=float(embed[i]), support_required=bool(trees[i]),
                            trunk_radius=float(trunk[i]), margin_radius=float(radius[i])))
        def add(xx, zz, kind):
            points.append(dict(id=len(points), object_id=oid, kind=kind, x=float(np.float32(xx)), z=float(np.float32(zz))))
        add(x,z,'root')
        if trees[i]:
            for xx, zz in disc_points(x,z,trunk[i]): add(xx,zz,'support')
        for xx, zz in disc_points(x,z,radius[i]): add(xx,zz,'margin')
    a.output.mkdir(parents=True); a.mission.mkdir(parents=True)
    init = Path(__file__).resolve().parents[2]/'missions/BalticForestBoundaryV1.BalticTrial/init.c'
    shutil.copy2(init,a.mission/'init.c')
    csv = ''.join(f"{p['id']};{p['x']:.9f} 0 {p['z']:.9f}\n" for p in points)
    (a.mission/'points.csv').write_text(csv,encoding='ascii')
    survey_id = str(uuid.uuid4())
    (a.mission/'identity.txt').write_text(survey_id+'\n',encoding='ascii')
    doc = dict(schema='forest-boundary-survey-v1', survey_id=survey_id, objects=objects, points=points,
               source_wrp_sha256=sha(source), terrain_sha256=sha(terrain), reference_sha256=sha(reference),
               mod_sha256={p.name:sha(p) for p in sorted((a.mod/'Addons').glob('*.pbo'))},
               mission=str(a.mission), init_sha256=sha(init), csv_sha256=sha(a.mission/'points.csv'), identity_sha256=sha(a.mission/'identity.txt'),
               scope='Finite samples: all boundary roots; 0.25 m perimeter / 0.5 m grid. No whole-disc PASS.')
    (a.output/'points.json').write_text(json.dumps(doc,separators=(',',':'),allow_nan=False),encoding='utf-8')
    summary={k:v for k,v in doc.items() if k not in ('objects','points')}
    summary.update(objects=len(objects),points=len(points))
    (a.output/'preparation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
