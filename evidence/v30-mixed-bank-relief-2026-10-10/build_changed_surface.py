"""EV80 affected-tile surface rebuild and compiled-PAA consumer.

The full EV72+EV79 composite is read through reference-inputs.json. This script
regenerates only tiles whose padded native-cell footprint intersects an EV80
height change, then verifies generated and untouched neighboring layers.
"""
from pathlib import Path
import sys, json, hashlib, subprocess, importlib.util, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

B = Path(__file__).parent
R = B.parent
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
EV79 = R / 'v30-narva-dry-bank-relief-20261010'
SOURCE = EV79 / 'candidate/terrain.npz'
SOURCE_P = EV79 / 'candidate/plane.npy'
SOURCE_F = EV79 / 'candidate/visible-field.npy'
CANDIDATE = B / 'candidate/terrain.npz'
CANDIDATE_P = B / 'candidate/plane.npy'
CANDIDATE_F = B / 'candidate/visible-field.npy'
EV79_CONSTRAINTS = EV79 / 'constraints.npz'
EV79_REPORT = EV79 / 'review-luna/report.json'
EV80_REPORT = B / 'review-luna/report.json'
REFERENCE_INPUTS = B / 'reference-inputs.json'
OLD_SURFACE = R / 'v30-complete-dry-surface-20261009'
OLD_INPUTS = OLD_SURFACE / 'inputs.json'
# Use the byte-exact consumer pinned by `inputs.json`, retained in the aligned
# surface run. The complete-map EV72 copy has the same barycentric/process
# functions; its only differences are the top-level T/P defaults and main's
# source hash, so the imported verifier behavior is identical after overrides.
OLD_CONSUMER = R / 'v30-surface-aligned-20261009/compile_and_verify_surface.py'
GENERATOR = W / 'tools/terrain/build_surface_v30.py'
IMAGE_TO_PAA = Path(r'C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/ImageToPAA/ImageToPAA.exe')

EV79_SOURCE_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
EV80_CANDIDATE_SHA = '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
EV79_CONSTRAINTS_SHA = 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
EV80_CONSUMER_SHA = 'b53d77e0b5c499dd735306f9fe84b30725a4c5132334bd792ae6d1c4a997cf92'
EV80_REPORT_SHA = '1f93c335d78d572de3a5c020c09d0cc397951cdb88b33f45ee1af144f3d0a60e'
REFERENCE_INPUTS_SHA = 'b3bc7347c914c5fcab726991667fd939f49eeb664adac3db862f4eb8e4881ac0'
GENERATOR_SHA = '1bf5c1cd9467b31fecd8b9dad218b84f623f663f07c6d1fa36f955f58e7983ab'
CONSUMER_SHA = '556e64ceb3abf45c02d9303522e139129eba175c2d1db691451d5d87489da3ef'
EV79_SURFACE_REPORT_SHA = '6d7a843221b69317e4901811e75f4207df3972e9f1f7d726279b9609bd232c8a'
EV72_SURFACE_REPORT_SHA = 'e2b041e547480c7eba23a3806582ee97a863687dc78c14bd131760c2e27d3e1c'
WORLD_SHA = 'df00806c598181e9ddca160781790cd0edc9314095262f6f106a87ed4d464213'
WATER_SHA = '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
PLANE_SHA = '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
VISIBLE_SHA = 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
N = 2048


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_npz(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def metadata_exact(source, candidate):
    return set(source) == set(candidate) and all(
        np.array_equal(source[k], candidate[k], equal_nan=True)
        for k in source if k != 'heights')


def changed_native_cells(base, changed):
    assert base.shape == changed.shape == (N, N)
    vertices = changed != base
    cells = vertices[:-1, :-1] | vertices[:-1, 1:] | vertices[1:, :-1] | vertices[1:, 1:]
    return vertices, cells


def select_padded_tiles(cells):
    selected = []
    footprints = {}
    for b in range(32):
        for a in range(32):
            # 512 px tile: 64 px overlap plus the generator's 8 px filter padding.
            xmin, xmax = 384*a - 72, 384*a + 456
            zmax, zmin = 12288 - 384*b + 72, 12288 - 384*b - 456
            c0, c1 = max(0, int(np.floor(xmin/6))), min(2047, int(np.ceil(xmax/6)))
            r0, r1 = max(0, int(np.floor((12282-zmax)/6))), min(2047, int(np.ceil((12282-zmin)/6)))
            hit = bool(cells[r0:r1, c0:c1].any())
            footprints[(a, b)] = (r0, r1, c0, c1)
            if hit:
                selected.append((a, b))
    return selected, footprints


class IndexedReferenceLayers:
    """Resolve a requested texture stem via the frozen composite reference index."""
    def __init__(self, index):
        self.index = index
        self.checked = {}

    def __truediv__(self, name):
        stem = Path(name).stem
        assert stem in self.index, f'missing reference texture stem: {stem}'
        item = self.index[stem]
        assert item['pbo_entry'] == f'data/layers/{stem}.paa', f'bad indexed PAA entry for {stem}'
        path = Path(item['png'])
        if stem not in self.checked:
            assert path.is_file(), f'missing reference PNG: {path}'
            actual = sha(path)
            assert actual == item['png_sha256'], f'reference PNG hash mismatch: {stem}'
            self.checked[stem] = dict(path=str(path), png_sha256=actual, paa_sha256=item['paa_sha256'],
                                      pbo_entry=item['pbo_entry'])
        return path


def reference_guards():
    assert sha(SOURCE) == EV79_SOURCE_SHA
    assert sha(CANDIDATE) == EV80_CANDIDATE_SHA
    assert sha(EV79_CONSTRAINTS) == EV79_CONSTRAINTS_SHA
    assert sha(EV80_REPORT) == EV80_REPORT_SHA
    report = json.loads(EV80_REPORT.read_text(encoding='utf-8'))
    assert report['status'] == 'PASS_EV80_CONSUMER'
    assert report['candidate_sha256'] == EV80_CANDIDATE_SHA
    assert report['source_sha256'] == EV79_SOURCE_SHA
    assert sha(B / 'review-luna/verify.py') == EV80_CONSUMER_SHA
    assert sha(SOURCE_P) == sha(CANDIDATE_P) == PLANE_SHA
    assert sha(SOURCE_F) == sha(CANDIDATE_F) == VISIBLE_SHA
    assert sha(GENERATOR) == GENERATOR_SHA
    old = json.loads(OLD_INPUTS.read_text(encoding='utf-8'))
    assert old['status'] == 'VERIFIED_EV71_GEOMETRY_SAME_GENERATOR'
    assert old['generator_sha256'] == GENERATOR_SHA
    assert old['consumer_source_sha256'] == CONSUMER_SHA
    assert sha(OLD_CONSUMER) == CONSUMER_SHA
    assert IMAGE_TO_PAA.is_file()

    ref = json.loads(REFERENCE_INPUTS.read_text(encoding='utf-8'))
    assert sha(REFERENCE_INPUTS) == REFERENCE_INPUTS_SHA
    assert ref['status'] == 'PASS_EV79_COMPOSITE_REFERENCE'
    assert ref['world_sha256'] == WORLD_SHA and ref['water_sha256'] == WATER_SHA
    assert ref['entries'] == 6827 and ref['png_and_deployed_paa_verified'] == 2048
    assert ref['reference_tiles'] == 1024 and ref['ev79_overlay_tiles'] == 18
    expected_reports = {
        str(OLD_SURFACE / 'surface-verification.json'): EV72_SURFACE_REPORT_SHA,
        str(EV79 / 'surface-verification.json'): EV79_SURFACE_REPORT_SHA,
    }
    assert ref['reference_reports'] == expected_reports
    assert sha(OLD_SURFACE / 'surface-verification.json') == EV72_SURFACE_REPORT_SHA
    assert sha(EV79 / 'surface-verification.json') == EV79_SURFACE_REPORT_SHA
    expected_stems = {
        f'{prefix}_{a:03d}_{b:03d}_{suffix}'
        for b in range(32) for a in range(32)
        for prefix, suffix in (('s', 'lco'), ('m', 'lca'))
    }
    assert set(ref['textures']) == expected_stems
    return ref


def main():
    started = time.monotonic()
    ref = reference_guards()
    source = load_npz(SOURCE)
    candidate = load_npz(CANDIDATE)
    assert metadata_exact(source, candidate), 'EV80 changed terrain metadata beside heights'
    base_h = source['heights']
    h = candidate['heights']
    vertices, cells = changed_native_cells(base_h, h)
    assert int(vertices.sum()) == 2591, 'EV80 changed-vertex count differs from PASS report'
    tiles, footprints = select_padded_tiles(cells)
    assert tiles and len(tiles) < 1024
    selected = set(tiles)
    excluded_hit = [(a, b) for (a, b), (r0, r1, c0, c1) in footprints.items()
                    if (a, b) not in selected and cells[r0:r1, c0:c1].any()]
    assert not excluded_hit, f'excluded padded tiles intersect changed cells: {excluded_hit[:8]}'
    # Never overwrite a prior EV80 surface attempt.
    assert not (B / 'surface').exists(), 'EV80 surface output already exists'
    assert not (B / 'decoded').exists(), 'EV80 decoded output already exists'
    assert not (B / 'surface-generation.log').exists(), 'EV80 generation log already exists'
    assert not (B / 'surface-verification.json').exists(), 'EV80 verification already exists'

    tile_arg = ';'.join(f'{a},{b}' for a, b in tiles)
    args = [
        sys.executable, str(GENERATOR), str(CANDIDATE), str(B / 'surface'),
        '--tiles', tile_arg, '--workers', '4', '--bed-tone', 'depth-all',
        '--bed-surface', 'gravel', '--shore-ring', 'flowing', '--landcover', 'smooth',
        '--landcover-sigma', '1.0', '--water-plane', str(CANDIDATE_P),
        '--water-plane-sha256', PLANE_SHA,
    ]
    with (B / 'surface-generation.log').open('w', encoding='utf-8') as log:
        generation = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT)
    assert generation.returncode == 0, f'surface generator exited {generation.returncode}'
    surface_spec = json.loads((B / 'surface/surface.json').read_text(encoding='utf-8'))
    assert surface_spec['tiles'] == len(tiles)
    assert surface_spec['terrain_sha256'] == EV80_CANDIDATE_SHA
    assert surface_spec['water_field']['sha256'] == PLANE_SHA
    assert surface_spec['bed_tone'] == 'depth-all' and surface_spec['bed_surface'] == 'gravel'
    assert surface_spec['shore_ring'] == 'flowing'
    assert surface_spec['landcover'] == 'smooth' and surface_spec['landcover_sigma'] == 1.0

    spec = importlib.util.spec_from_file_location('ev80_surface_consumer', OLD_CONSUMER)
    consumer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consumer)
    indexed = IndexedReferenceLayers(ref['textures'])
    consumer.B = B
    consumer.T = CANDIDATE
    consumer.P = CANDIDATE_P
    consumer.OLD = indexed
    consumer.MASK = indexed
    consumer.H = h.astype(float)
    consumer.F = np.load(CANDIDATE_P, allow_pickle=False)
    consumer.TOOL = IMAGE_TO_PAA
    (B / 'decoded').mkdir(exist_ok=False)
    with ThreadPoolExecutor(max_workers=4) as pool:
        reports = list(pool.map(consumer.process, tiles))
    assert len(reports) == len(tiles)

    overlap_count = 0
    bad_overlaps = []
    def read_layer(prefix, suffix, ab):
        a, b = ab
        if ab in selected:
            path = B / 'surface/layers' / f'{prefix}_{a:03d}_{b:03d}_{suffix}.png'
            assert path.is_file(), f'missing generated layer {path}'
            return np.array(Image.open(path))
        path = indexed / f'{prefix}_{a:03d}_{b:03d}_{suffix}.png'
        return np.array(Image.open(path))

    for prefix, suffix in [('s', 'lco'), ('m', 'lca')]:
        for b in range(32):
            for a in range(32):
                for da, db in ((1, 0), (0, 1)):
                    other = (a + da, b + db)
                    if other[0] >= 32 or other[1] >= 32 or ((a, b) not in selected and other not in selected):
                        continue
                    one, two = read_layer(prefix, suffix, (a, b)), read_layer(prefix, suffix, other)
                    left, right = (one[:, 384:], two[:, :128]) if da else (one[384:], two[:128])
                    if not np.array_equal(left, right):
                        bad_overlaps.append([prefix, a, b, da, db, int(np.count_nonzero(left != right))])
                    overlap_count += 1

    total_keys = ('pixels', 'wet_pixels', 'source_wet_not_gravel',
                  'compiled_interior_non_gravel', 'compiled_wet_non_gravel',
                  'satellite_changed_pixels', 'mask_changed_pixels')
    totals = {k: sum(q[k] for q in reports) for k in total_keys}
    artifact_hashes_valid = all(
        isinstance(q['files'].get(kind), dict) and all(
            isinstance(q['files'][kind].get(key), str) and len(q['files'][kind][key]) == 64
            and all(ch in '0123456789abcdef' for ch in q['files'][kind][key])
            for key in ('png_sha256', 'paa_sha256', 'decoded_sha256'))
        for q in reports for kind in ('s', 'm'))
    artifacts_exist = all(
        (B / 'surface/layers' / f'{prefix}_{q["tile"][0]:03d}_{q["tile"][1]:03d}_{suffix}.{ext}').is_file()
        for q in reports for prefix, suffix in (('s', 'lco'), ('m', 'lca'))
        for ext in ('png', 'paa')) and all(
        (B / 'decoded' / f'{prefix}_{q["tile"][0]:03d}_{q["tile"][1]:03d}_{suffix}.png').is_file()
        for q in reports for prefix, suffix in (('s', 'lco'), ('m', 'lca')))
    gates = dict(
        selected_tiles=len(reports) == len(tiles),
        excluded_padded_tiles_identity=not excluded_hit,
        wet_gravel=totals['source_wet_not_gravel'] == 0,
        compiled_interior_gravel=totals['compiled_interior_non_gravel'] == 0,
        alpha=all(q['source_alpha_exact'] for q in reports),
        palette=all(q['valid_mask_palette'] for q in reports),
        every_selected_png_paa_decoded=artifact_hashes_valid and artifacts_exist,
        indexed_reference_png_hashes_exact=len(indexed.checked) > 0,
        overlap_exact=not bad_overlaps,
        negative_controls=any(q['negative_control'] for q in reports) and all(q['negative_control'] is not False for q in reports),
    )
    out = dict(
        status='PASS_EV80_AFFECTED_SURFACE' if all(gates.values()) else 'FAIL_EV80_AFFECTED_SURFACE',
        gates=gates, tiles=[list(t) for t in tiles], counts=totals,
        overlaps=overlap_count, bad_overlaps=bad_overlaps, files=reports,
        terrain_sha256=sha(CANDIDATE), source_terrain_sha256=sha(SOURCE),
        generator_sha256=sha(GENERATOR), reference_inputs_sha256=sha(REFERENCE_INPUTS),
        baseline_surface_report_sha256=sha(OLD_SURFACE / 'surface-verification.json'),
        ev79_overlay_report_sha256=sha(EV79 / 'surface-verification.json'),
        reference_pngs_checked=indexed.checked,
        changed_vertices=int(vertices.sum()), changed_native_cells=int(cells.sum()),
        excluded_tiles=int(1024 - len(tiles)),
        unchanged_tile_proof='All four vertices of every native cell in each excluded padded tile are unchanged; EV79 source, EV80 consumer PASS, metadata, P/F, generator, baseline texture index and options are hash-anchored.',
        mip_status='PENDING_ROOT',
        seconds=round(time.monotonic() - started, 3),
        limits=[
            'Offline affected-surface and compiled-PAA consumer only; no package, deployment, engine, or visual acceptance.',
            'Overlap checks cover every neighbor pair where either tile is regenerated; excluded tiles resolve through the frozen EV72+EV79 composite index.',
            'Mipmap regeneration/check is intentionally pending root-owned work.',
        ],
    )
    (B / 'surface-verification.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k not in ('files', 'reference_pngs_checked')}, indent=2))
    assert all(gates.values()), 'affected-surface validation failed; preserve outputs for diagnosis'


if __name__ == '__main__':
    main()
