"""Rebuild the complete affected EV87 surface footprint after independent PASS."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

B = Path(__file__).parent
RUN = B.parent
ROOT = RUN.parent
PREV = ROOT / 'v30-mixed-bank-incremental-fixed-20261010'
CANDIDATE = RUN / 'selective/candidate-terrain.npz'
REPORT = RUN / 'selective/selective-review.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    started = time.monotonic()
    anchor = json.loads((B / 'build-inputs.json').read_text())
    for path, digest in anchor['inputs'].items():
        assert sha(path) == digest, f'build input changed: {path}'
    assert anchor['candidate_sha256'] == sha(CANDIDATE)
    review = json.loads(REPORT.read_text())
    assert review['status'] == 'PASS_INCREMENTAL_NONREGRESSION'
    assert review['global_representation_status']=='FAIL_WITH_INHERITED_OPEN'
    assert review['information']['global_contract_status']=='FAIL_WITH_INHERITED_OPEN' and review['information']['inherited_open']
    assert review['gates'] and all(review['gates'].values())
    assert review['information']['changed_vertices'] > 0, 'Do not build a no-op proposal'
    assert anchor['inputs'][str(REPORT)] == sha(REPORT)
    for path, digest in review['inputs'].items():
        assert sha(path) == digest, f'consumer input changed: {path}'
    reference = json.loads((B / 'reference-inputs.json').read_text())
    assert reference['status'] == 'PASS_EV82_COMPOSITE_REFERENCE'
    helpers = module(PREV / 'build_changed_surface.py', 'ev82_surface_footprint_helpers')
    assert sha(helpers.GENERATOR) == helpers.GENERATOR_SHA
    assert sha(helpers.OLD_CONSUMER) == helpers.CONSUMER_SHA
    assert sha(helpers.SOURCE_P) == helpers.PLANE_SHA
    assert sha(helpers.SOURCE_F) == helpers.VISIBLE_SHA
    previous = helpers.load_npz(PREV / 'candidate/terrain.npz')
    candidate = helpers.load_npz(CANDIDATE)
    assert helpers.metadata_exact(previous, candidate)
    vertices, cells = helpers.changed_native_cells(previous['heights'], candidate['heights'])
    assert int(vertices.sum()) == review['information']['changed_vertices']
    tiles, footprints = helpers.select_padded_tiles(cells)
    selected = set(tiles)
    assert tiles and len(tiles) <= 1024
    assert all(not cells[r0:r1, c0:c1].any() for ab, (r0,r1,c0,c1) in footprints.items() if ab not in selected)
    assert all(not (B / name).exists() for name in ('surface', 'decoded', 'surface-verification.json'))
    arguments = [sys.executable, str(helpers.GENERATOR), str(CANDIDATE), str(B / 'surface'),
                 '--tiles', ';'.join(f'{a},{b}' for a,b in tiles), '--workers', '4',
                 '--bed-tone', 'depth-all', '--bed-surface', 'gravel', '--shore-ring', 'flowing',
                 '--landcover', 'smooth', '--landcover-sigma', '1.0',
                 '--water-plane', str(helpers.SOURCE_P), '--water-plane-sha256', helpers.PLANE_SHA]
    with (B / 'surface-generation.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(arguments, stdout=log, stderr=subprocess.STDOUT)
    assert result.returncode == 0, 'Surface generator failed; preserve outputs'
    spec = json.loads((B / 'surface/surface.json').read_text())
    assert spec['tiles'] == len(tiles) and spec['terrain_sha256'] == sha(CANDIDATE)
    assert spec['water_field']['sha256'] == helpers.PLANE_SHA
    assert (spec['bed_tone'],spec['bed_surface'],spec['shore_ring'],spec['landcover'],spec['landcover_sigma']) == ('depth-all','gravel','flowing','smooth',1.0)
    indexed = helpers.IndexedReferenceLayers(reference['textures'])
    consumer = module(helpers.OLD_CONSUMER, 'ev87_surface_consumer')
    consumer.B = B
    consumer.T = CANDIDATE
    consumer.P = helpers.SOURCE_P
    consumer.OLD = indexed
    consumer.MASK = indexed
    consumer.H = candidate['heights'].astype(float)
    consumer.F = np.load(helpers.SOURCE_P, allow_pickle=False)
    consumer.TOOL = helpers.IMAGE_TO_PAA
    (B / 'decoded').mkdir()
    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(consumer.process, tiles))
    assert len(files) == len(tiles)
    def read_layer(prefix, suffix, ab):
        a,b = ab
        path = B / 'surface/layers' / f'{prefix}_{a:03d}_{b:03d}_{suffix}.png' if ab in selected else indexed / f'{prefix}_{a:03d}_{b:03d}_{suffix}.png'
        with Image.open(path) as image:
            return np.asarray(image).copy()
    bad_overlaps = []
    overlap_count = 0
    for prefix,suffix in [('s','lco'),('m','lca')]:
        for b in range(32):
            for a in range(32):
                for da,db in ((1,0),(0,1)):
                    other = (a+da,b+db)
                    if other[0]>=32 or other[1]>=32 or ((a,b) not in selected and other not in selected):
                        continue
                    one,two = read_layer(prefix,suffix,(a,b)),read_layer(prefix,suffix,other)
                    left,right = (one[:,384:],two[:,:128]) if da else (one[384:],two[:128])
                    if not np.array_equal(left,right):
                        bad_overlaps.append([prefix,a,b,da,db,int(np.count_nonzero(left!=right))])
                    overlap_count += 1
    keys = ('pixels','wet_pixels','source_wet_not_gravel','compiled_interior_non_gravel',
            'compiled_wet_non_gravel','satellite_changed_pixels','mask_changed_pixels')
    totals = {key:sum(item[key] for item in files) for key in keys}
    artifact_exact = True
    for item in files:
        a,b = item['tile']
        for kind,suffix in [('s','lco'),('m','lca')]:
            stem = f'{kind}_{a:03d}_{b:03d}_{suffix}'
            for folder,extension,key in [('surface/layers','.png','png_sha256'),('surface/layers','.paa','paa_sha256'),('decoded','.png','decoded_sha256')]:
                artifact_exact &= sha(B / folder / (stem+extension)) == item['files'][kind][key]
    gates = dict(selected_tiles=len(files)==len(tiles), excluded_padded_tiles_identity=True,
                 wet_gravel=totals['source_wet_not_gravel']==0,
                 compiled_interior_gravel=totals['compiled_interior_non_gravel']==0,
                 alpha=all(x['source_alpha_exact'] for x in files), palette=all(x['valid_mask_palette'] for x in files),
                 every_selected_artifact_exact=artifact_exact, overlap_exact=not bad_overlaps,
                 negative_controls=any(x['negative_control'] for x in files) and all(x['negative_control'] is not False for x in files))
    out = dict(status='PASS_EV87_AFFECTED_SURFACE' if all(gates.values()) else 'FAIL_EV87_AFFECTED_SURFACE',
               gates=gates, tiles=[list(t) for t in tiles], files=files, counts=totals,
               overlaps=overlap_count,bad_overlaps=bad_overlaps,terrain_sha256=sha(CANDIDATE),
               source_terrain_sha256=sha(PREV/'candidate/terrain.npz'),
               changed_vertices=int(vertices.sum()),changed_native_cells=int(cells.sum()),excluded_tiles=1024-len(tiles),
               generator_sha256=sha(helpers.GENERATOR),consumer_sha256=sha(helpers.OLD_CONSUMER),
               reference_inputs_sha256=sha(B/'reference-inputs.json'),geometry_review_sha256=sha(REPORT),
               seconds=round(time.monotonic()-started,3),
               limits=['Offline surface/PAA checks only. Mips, package identity and engine readback remain separate.'])
    (B/'surface-verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in out.items() if key!='files'}))
    assert all(gates.values()), 'Preserve rejected surface artifacts'


if __name__ == '__main__':
    main()
