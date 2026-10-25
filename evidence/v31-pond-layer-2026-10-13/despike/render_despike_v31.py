"""Before/after hillshade crops of the despike pass: the N worst free-domain sites of the input (largest prominence,
>= SEP m apart) plus named sites. Exact planar-triangle surface (NW-SE split) at K px per 6 m cell, two suns (315/35 deg
and 45/25 deg, contrast-stretched), water mask tinted blue; red square = site vertex, yellow dots = vertices the pass changed.
Usage: render_despike_v31.py <census.py dir> <in.npz> <out.npz> <envelope.npy> <out_dir> [--n 5] [--site name,x,z ...]
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

HALF, K, SEP = 24, 8, 300.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("libdir"); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("envelope"); ap.add_argument("dst")
    ap.add_argument("--n", type=int, default=5); ap.add_argument("--site", nargs="*", default=[])
    o = ap.parse_args()
    sys.path.insert(0, o.libdir)
    import census_pyramids_v31 as c
    os.makedirs(o.dst, exist_ok=False)
    zi = np.load(o.inp); zo = np.load(o.out)
    I = {k: zi[k] for k in zi.files}
    H0 = I["heights"].astype(np.float64); H1 = zo["heights"].astype(np.float64)
    masks, prot = c.protected_masks(I, np.load(o.envelope))
    pk0, pt0, _, _ = c.prominence(H0); pk1, pt1, _, _ = c.prominence(H1)
    M0 = np.maximum(pk0, pt0); M1 = np.maximum(pk1, pt1)
    order = np.argsort(np.where(~prot, M0, -np.inf), axis=None)[::-1]
    picks = []
    for i in order[:20000]:
        r, cc = np.unravel_index(i, H0.shape)
        x, z = 6.0 * cc, 12282.0 - 6.0 * r
        if all(np.hypot(x - p["x"], z - p["z"]) >= SEP for p in picks):
            picks.append(dict(name=f"worst{len(picks) + 1}", x=x, z=z, r=int(r), c=int(cc)))
        if len(picks) == o.n:
            break
    for s in o.site:
        nm, x, z = s.split(","); x, z = float(x), float(z)
        picks.append(dict(name=nm, x=x, z=z, r=int(round((12282 - z) / 6)), c=int(round(x / 6))))
    changed = H1 != H0
    tiles, rows = [], []
    for p in picks:
        r, cc = p["r"], p["c"]
        win = (slice(max(0, r - HALF), r + HALF), slice(max(0, cc - HALF), cc + HALF))
        chv = np.argwhere(changed[win])
        imgs = []
        for H, lbl, Mx in ((H0, "before EV110", M0), (H1, "after despike", M1)):
            marks = [(r, cc, (1.0, 0.1, 0.1))]
            rgb, (r0, c0) = c.crop_rgb(H, I["water"], r, cc, HALF, K, marks)
            g = rgb.astype(np.float64) / 255.0
            g = np.clip((g - 0.35) / 0.55, 0, 1) ** 0.9          # contrast stretch of the hillshade
            rgb = (g * 255).astype(np.uint8)
            im = Image.fromarray(rgb); d = ImageDraw.Draw(im)
            if lbl.startswith("after"):
                for (a, b) in chv:
                    y, x = (a + win[0].start - r0) * K, (b + win[1].start - c0) * K
                    d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(255, 220, 0))
            sub = Mx[win]; sub = sub[np.isfinite(sub)]
            d.rectangle([0, 0, im.width, 28], fill=(0, 0, 0))
            d.text((3, 1), f"{p['name']} ({p['x']:.0f}, {p['z']:.0f})  {lbl}", fill=(255, 255, 255))
            d.text((3, 14), f"prominence: site {Mx[r, cc]:.2f} m, crop max {sub.max():.2f} m", fill=(255, 255, 255))
            imgs.append(im)
        w = imgs[0].width + imgs[1].width + 6
        t = Image.new("RGB", (w, imgs[0].height), (40, 40, 40)); t.paste(imgs[0], (0, 0)); t.paste(imgs[1], (imgs[0].width + 6, 0))
        fn = os.path.join(o.dst, f"{p['name']}.png"); t.save(fn); tiles.append(t)
        rows.append(dict(p, prom_before=round(float(M0[r, cc]), 3), prom_after=round(float(M1[r, cc]), 3),
                         window_max_before=round(float(M0[win].max()), 3), window_max_after=round(float(M1[win].max()), 3),
                         changed_in_window=int(len(chv)), protected_at_site="|".join(k for k, v in masks.items() if v[r, cc]),
                         file=fn))
    W = max(t.width for t in tiles); Ht = sum(t.height + 6 for t in tiles)
    sheet = Image.new("RGB", (W, Ht), (255, 255, 255)); y = 0
    for t in tiles:
        sheet.paste(t, (0, y)); y += t.height + 6
    sheet.save(os.path.join(o.dst, "contact-sheet.png"))
    json.dump(rows, open(os.path.join(o.dst, "crops.json"), "w"), indent=1)
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
