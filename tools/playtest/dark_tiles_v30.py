"""Colour/flatness heuristic for engine captures (BALTIC-019): terrain whose layer textures have not loaded is drawn
as flat, dark, uniform tiles with straight edges. Per capture: the share of 16 x 16 px blocks in the lower part of the
client frame that are flat (luminance std under --flat-std) and dark (mean under --dark-mean), and the same with the
colour test (untextured tiles are grey-blue, land texture is green or brown). One JSON row per file.
The defaults separate the 07-10-2026 series: untextured land views 0.37-0.63, textured ones 0.00-0.15 (water counts
as flat, so a view dominated by water reads higher). The historical 0.2 cutoff
is NOT a texture-loading acceptance gate: distant haze, smooth textured land
and water can all satisfy the same pixel predicates. Conversely, contrast/noise
can lower the score without loading any terrain layer. It does not inspect
straight tile edges or read engine residency. Use matched visual evidence.
Usage: dark_tiles_v30.py CAPTURE.jpg [...] [--lower 0.55] [--flat-std 0.8] [--dark-mean 140]"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def client(p):
    im = Image.open(p).convert('RGB')
    return im.crop((11, 45, 11 + 1920, 45 + 1080)) if im.size == (1942, 1136) else im


def measure(p, lower, flat_std, dark_mean, b=16):
    a = np.asarray(client(p), dtype=np.float32)
    h, w, _ = a.shape
    a = a[int(h * (1 - lower)):]
    hh, ww = (a.shape[0] // b) * b, (w // b) * b
    blk = a[:hh, :ww].reshape(hh // b, b, ww // b, b, 3).transpose(0, 2, 1, 3, 4).reshape(hh // b, ww // b, b * b, 3)
    lum = blk @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    std, mean = lum.std(axis=2), lum.mean(axis=2)
    rgb = blk.mean(axis=2)
    bluish = rgb[..., 2] >= rgb[..., 1]                       # grey-blue, not green or brown
    flat_dark = (std < flat_std) & (mean < dark_mean)
    return {'file': str(p), 'blocks': int(std.size),
            'assessment': 'HEURISTIC_ONLY_NOT_TEXTURE_ACCEPTANCE',
            'flat_dark_share': round(float(flat_dark.mean()), 4),
            'flat_dark_bluish_share': round(float((flat_dark & bluish).mean()), 4),
            'lower_mean_lum': round(float(mean.mean()), 1)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('files', nargs='+', type=Path)
    ap.add_argument('--lower', type=float, default=0.55)
    ap.add_argument('--flat-std', type=float, default=0.8)
    ap.add_argument('--dark-mean', type=float, default=140.0)
    a = ap.parse_args()
    for p in a.files:
        print(json.dumps(measure(p, a.lower, a.flat_std, a.dark_mean)))


if __name__ == '__main__':
    main()
