"""Freeze the SAME six routes and criteria against the new compiled geometry."""
from pathlib import Path
import hashlib
import json
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
B = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008')
OUT = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
old_ref = ROOT/'evidence/v30-luga-navigation-2026-10-07/boat-reference.json'
reference = json.loads(old_ref.read_text())
terrain = B/'combined/terrain_inland.npz'
assert sha(terrain) == 'a292b6c39ad5c4fa19936e5498dc0ddaa064ee6ce4ecdb3115a763a3f0bc57c1'
asc = B/'combined-reference.asc'
ref_path = OUT/'boat-reference.json'
assert not asc.exists() and not ref_path.exists()
heights = np.load(terrain)['heights']
with asc.open('x', encoding='ascii', newline='\n') as stream:
    stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
    np.savetxt(stream, heights, fmt='%.9g')
with rasterio.open(asc) as ds:
    assert np.array_equal(ds.read(1), heights), 'ASC precision changed source'
deployment = {
    'P:/Mods/@DayZ_Baltic_BoundedSmoothingPreview/Addons/narva_trial.pbo': '9768119eb687517957831f126156fb1707c954ebac76b6dc271d57bef33421aa',
    'P:/Mods/@DayZ_Baltic_BoundedSmoothingPreview/Addons/baltic_water_v30.pbo': '07c5295f112746d621e96324467b1d54fccc415a785c227feb245f59adff503f',
    'P:/Mods/@BalticBoatInputProbe/Addons/baltic_boat_input.pbo': 'c5414ffe385eae5b85e1fe6dfef671db568d50a8eb11c74a3f4346f7c6417b2e',
}
for path, digest in deployment.items():
    assert sha(path) == digest, path
for source, digest in reference['mission'].items():
    assert sha(source) == digest
    deployed = Path(reference['deployed_mission'])/Path(source).name
    assert sha(deployed) == digest
reference.update(status='FROZEN_BEFORE_COMBINED_ENGINE_REPEAT', terrain=str(asc), terrain_sha256=sha(asc),
                 inputs={str(old_ref): sha(old_ref), str(terrain): sha(terrain), str(Path(__file__)): sha(__file__)},
                 deployment=deployment,
                 scope='Same V12 sectors, waypoints, water levels, thresholds and deployed mission; new composite terrain only.')
ref_path.write_text(json.dumps(reference, indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(dict(status='PREPARED_NOT_RUN', reference_sha256=sha(ref_path), terrain_sha256=sha(asc), cases=len(reference['cases'])), indent=2))
