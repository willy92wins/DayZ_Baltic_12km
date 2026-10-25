"""Global terrain normal map for the world config key terrainNormalTexture (Chernarus and Livonia declare it together with
heightBlendingMode=1 and bicubicMode=1; the Baltic world declared none of the three).

Encoding measured on 2026-10-14 by decoding P:\\DZ\\worlds\\chernarusplus\\data\\global_nohq.paa (ImageToPAA -> RGBA PNG,
1024 x 1024 over 15,360 m) against the Chernarus heightmap of the vanilla survey
(E:/DayZ-Baltic-Build/vanilla-tricks-20261013/data/chernarus_height.npy, 7.5 m):
  R = 0.498 + 0.461 nx   (corr 0.976)    nx = east component of the unit terrain normal
  G = 0.498 + 0.461 nz   (corr 0.972)    nz = north component
  B = 0.385 (1 - ny)     (corr 0.890)    ny = up component
  A = 1
  image row 0 = south (with the rows flipped the correlations fall to 0.09 / -0.03).
The fitted 0.461 slope comes from comparing against a 2x2-averaged heightmap; this tool writes the plain 0.5 scale.
Usage: global_normal_map.py <terrain.npz> <out_global_nohq.png>  (heights row 0 = north, 6 m), then
       ImageToPAA <out_global_nohq.png> <out_global_nohq.paa>
"""
import sys
import numpy as np
from PIL import Image

STEP = 6.0


def main():
    tpath, out = sys.argv[1:3]
    H = np.load(tpath)["heights"].astype(np.float64)[::-1]               # row 0 = south
    gz, gx = np.gradient(H, STEP)
    nn = np.sqrt(gx * gx + gz * gz + 1.0)
    nx, nz, ny = -gx / nn, -gz / nn, 1.0 / nn
    img = np.zeros(H.shape + (4,), np.uint8)
    img[:, :, 0] = np.clip(np.rint((0.5 + 0.5 * nx) * 255), 0, 255)
    img[:, :, 1] = np.clip(np.rint((0.5 + 0.5 * nz) * 255), 0, 255)
    img[:, :, 2] = np.clip(np.rint(0.385 * (1.0 - ny) * 255), 0, 255)
    img[:, :, 3] = 255
    Image.fromarray(img, "RGBA").save(out)
    print(out, img.shape)


if __name__ == "__main__":
    main()
