"""Stitch V30 tiles into native-import sources; schedule away from physical motion tests."""
from pathlib import Path
import argparse
import hashlib
import io
import json

import numpy as np
from PIL import Image
import rasterio
from rasterio.shutil import copy as raster_copy
from rasterio.transform import from_origin
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[2]
EDITOR = Path('E:/DayZ-Baltic-Build/editor-v30-delta/world')
EV = ROOT / 'evidence/v30-native-editor-2026-10-02'
OUT = EDITOR / 'native_sources'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-layers', type=Path,
                    help='New build_surface_v30 output; omitting retains the original frozen editor source.')
    ap.add_argument('--out', type=Path, default=OUT)
    ap.add_argument('--receipt', type=Path, default=EV/'surface-source-preparation.json')
    ap.add_argument('--legend-prefix', default='baltic_editor_v30_delta\\native_sources')
    args = ap.parse_args()
    out = args.out
    assert not out.exists() and not args.receipt.exists()
    if args.source_layers:
        source_layers = args.source_layers
        reference = {'data/layers/'+p.name.lower():sha(p) for p in source_layers.glob('*.png')}
        assert len(reference) == 2048, 'A full satellite/mask build is required'
    else:
        source_layers = EDITOR/'data/layers'
        original = json.loads((EV/'prepare.json').read_text())['source_hashes']
        reference = {k.lower():v for k,v in original.items()}
        assert len(reference) == len(original), 'Case-colliding source entries'
    out.mkdir(parents=True)
    results = []
    inputs = {}
    # 64 MB cache and a row of source tiles. This does not bound PNG driver/internal allocations.
    with rasterio.Env(GDAL_CACHEMAX=64000000):
        for kind, pattern in [('satellite', 's_{a:03d}_{b:03d}_lco.png'),
                              ('mask', 'm_{a:03d}_{b:03d}_lca.png')]:
            tif = out / (kind+'.tif')
            previous = [None]*32
            overlap_checks = 0
            with rasterio.open(tif, 'w', driver='GTiff', width=12288, height=12288,
                               count=3, dtype='uint8', transform=from_origin(200000, 12288, 1, 1),
                               tiled=True, blockxsize=384, blockysize=384,
                               compress='deflate', predictor=2) as dst:
                for b in range(32):
                    left = None
                    for a in range(32):
                        rel = 'data/layers/'+pattern.format(a=a, b=b)
                        data = (source_layers/Path(rel).name).read_bytes()
                        digest = hashlib.sha256(data).hexdigest()
                        assert digest == reference[rel], rel
                        inputs[rel] = digest
                        with Image.open(io.BytesIO(data)) as im:
                            assert im.size == (512, 512)
                            raw = np.asarray(im)
                            if kind == 'mask':
                                assert raw.shape == (512, 512, 4) and np.all(raw[:, :, 3] == 255)
                                assert np.all((raw[:, :, :3] == 0) | (raw[:, :, :3] == 255))
                                assert np.all(np.sum(raw[:, :, :3] == 255, axis=2) <= 1)
                            tile = raw[:, :, :3].copy()
                        if left is not None:
                            assert np.array_equal(left[:, 384:], tile[:, :128]), ('horizontal overlap', kind, a, b)
                            overlap_checks += 1
                        if previous[a] is not None:
                            assert np.array_equal(previous[a][384:], tile[:128]), ('vertical overlap', kind, a, b)
                            overlap_checks += 1
                        dst.write(tile[64:448, 64:448].transpose(2, 0, 1), window=Window(a*384, b*384, 384, 384))
                        left = previous[a] = tile
                    if b % 8 == 0:
                        print(f'{kind}: {b+1}/32 tile rows', flush=True)
            png = out / (kind+'.png')
            raster_copy(tif, png, driver='PNG', strict=True)
            # A separate GDAL decode proves the exported PNG preserves every assembled pixel.
            with rasterio.open(tif) as a, rasterio.open(png) as b:
                assert (a.width, a.height, a.count) == (b.width, b.height, b.count) == (12288, 12288, 3)
                for row in range(32):
                    window = Window(0, row*384, 12288, 384)
                    assert np.array_equal(a.read(window=window), b.read(window=window)), (kind, row)
            (out/(kind+'.pgw')).write_text('1\n0\n0\n-1\n200000.5\n12287.5\n', encoding='ascii')
            results.append(dict(kind=kind, tif_sha256=sha(tif), png_sha256=sha(png),
                                overlap_checks=overlap_checks, png_pixels_exact=True))
    old = ROOT/'source/layers.cfg'
    cfg = old.read_text()
    # New mask inputs use red=conifer, green=grass. Legacy source legend uses the reverse.
    assert cfg.count('cp_conifer_common1[] = {{0,255,0}};') == 1
    assert cfg.count('cp_grass[] = {{255,0,0}};') == 1
    cfg = cfg.replace('cp_conifer_common1[] = {{0,255,0}};', 'cp_conifer_common1[] = {{255,0,0}};')
    cfg = cfg.replace('cp_grass[] = {{255,0,0}};', 'cp_grass[] = {{0,255,0}};')
    assert cfg.count('DayZ_Baltic_12km_dev\\source\\mapLegend.png') == 1
    cfg = cfg.replace('DayZ_Baltic_12km_dev\\source\\mapLegend.png', args.legend_prefix+'\\legend.png')
    (out/'layers.cfg').write_text(cfg, encoding='utf-8')
    Image.fromarray(np.array([[[0,0,0], [255,0,0], [0,255,0], [0,0,255]]], dtype=np.uint8)).save(out/'legend.png')
    report = dict(status='PASS_LOSSLESS_NATIVE_SOURCE_PREPARATION_NOT_IMPORTED', output=str(out),
                  dimensions=[12288,12288], pixel_size_m=1, upper_left_local=[200000,12288],
                  source_pngs=len(inputs), input_hashes=inputs, rasters=results,
                  old_legend_sha256=sha(old), files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
                  limits=['Outer 64px tile padding outside the map is not part of the full image.',
                          'Generate Layers can assign palettes differently; native WRP/material validation remains required.',
                          'No editor save, map mutation, packaging, deployment or new navmesh acceptance.'])
    args.receipt.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','dimensions','source_pngs','rasters')}), flush=True)


if __name__ == '__main__':
    main()
