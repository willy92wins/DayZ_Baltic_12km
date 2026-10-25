"""Gate rasters of the EV112 map, rebuilt from the inputs (never from the placer's work/ rasters).

Usage: python -I grasters.py <dir>   (writes <dir>/slot1m.npy, wsea1m.npy, bog1m.npy, g5m.npz, grasters.json)
1 m, row 0 = north edge (z = 12288 - i - 0.5), column j (x = j + 0.5):
  slot1m  shipped surface slot (0 gravel, 1 forest floor, 2 grass, 3 tall grass) from the PNGs whose PAA is
          byte-identical to the EV110 world PBO entry (forest_v31.Mask, the texture reader only)
  wsea1m  bit 0 visible water (h < pond plane or h < 0.75), bit 1 engine sea band (h < 1.0 outside the envelope)
  bog1m   bilinear OSM wetland vertex fraction >= 0.5
5 m, row 0 = south edge (cell (r, c): x in [5c, 5c + 5), z in [5r, 5r + 5); 2458 x 2458, beyond the map = water):
  tex_major  >= 50 % of the 25 one-metre pixels are forest floor (the old G2 'forest_surface')
  tex_samp   forest floor at the 12.5 m sample nearest to the cell centre (Livonia's enoch_surf sampling)
  tsd        signed distance to tex_samp (EDT x 5 m, inside > 0), Livonia's surface_sd
  water      >= 50 % of the 25 pixels visible water (bit 0)        dw  distance to water (EDT x 5 m)
  bog        >= 50 % of the 25 pixels bog (gate_common.bog_cells)   bogm  bog or within 25 m of it (r2 margin)"""
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402

T = gcfg.tool()
MAP, NB = gcfg.MAP, 2458


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(d):
    d = Path(d)
    d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    mk = T.Mask(gcfg.PBO, gcfg.LAYER_DIRS)
    slot = mk.compose(0, 0, MAP, MAP)
    t = np.load(gcfg.TERRAIN)
    fp = np.load(gcfg.FOOTPRINT)
    H = t["heights"].astype(np.float64)
    W = np.load(gcfg.LAYERS)["osm_wetland"].astype(np.float64)
    wsea = np.zeros((MAP, MAP), np.uint8)
    bog = np.zeros((MAP, MAP), bool)
    for i0 in range(0, MAP, 512):
        X, Z = np.meshgrid(np.arange(MAP) + 0.5, MAP - (i0 + np.arange(512)) - 0.5)
        w, s = T.wet_at(H, fp["plane"], fp["env_plane"], X, Z)
        wsea[i0:i0 + 512] = w.astype(np.uint8) | (s.astype(np.uint8) << 1)
        bog[i0:i0 + 512] = T.vertex_bilinear(W, X, Z) >= 0.5
    import kit_water_consumer
    wsea |= kit_water_consumer.mask().astype(np.uint8)
    np.save(d / "slot1m.npy", slot)
    np.save(d / "wsea1m.npy", wsea)
    np.save(d / "bog1m.npy", bog)

    def to5(a, fill):
        f = np.full((NB * 5, NB * 5), fill, a.dtype)
        f[:MAP, :MAP] = a[::-1]                                     # row 0 = south
        return f.reshape(NB, 5, NB, 5)
    tex_major = (to5(slot, 255) == 1).mean(axis=(1, 3)) >= 0.5
    water = (to5(wsea, 3) & 1).mean(axis=(1, 3)) >= 0.5
    bog5 = to5(bog, False).mean(axis=(1, 3)) >= 0.5
    cc = (np.arange(NB) + 0.5) * 5
    s = np.rint(cc / 12.5) * 12.5
    jj = np.clip(np.floor(s).astype(int), 0, MAP - 1)
    ii = np.clip(np.floor(MAP - s).astype(int), 0, MAP - 1)       # north-up row of the sample at z = s
    tex_samp = slot[ii][:, jj] == 1                                 # rows follow z: row 0 = south
    tex_samp[cc >= MAP] = False
    tex_samp[:, cc >= MAP] = False
    tsd = np.where(tex_samp, ndimage.distance_transform_edt(tex_samp), -ndimage.distance_transform_edt(~tex_samp)) * 5.0
    dw = ndimage.distance_transform_edt(~water) * 5.0
    bogm = bog5 | (ndimage.distance_transform_edt(~bog5) * 5.0 <= 25.0)
    # Narva urban area (terrain 'narva' vertex cells + 6 m, the placer's exclusion): 5 m cells whose centre lies there
    cm = t["narva"][:-1, :-1] | t["narva"][1:, :-1] | t["narva"][:-1, 1:] | t["narva"][1:, 1:]
    GX, GZ = np.meshgrid(cc, cc)
    ci = np.clip(np.floor(GX / 6.0).astype(int), 0, gcfg.N - 2)
    ri = np.clip(np.floor((gcfg.ZTOP - GZ) / 6.0).astype(int), 0, gcfg.N - 2)
    # streambed kit pieces and kit stones (non-water, non-bridge objects of the staged base WRP): 5 m cells whose centre
    # lies inside a plan hull (visual bbox); the piece's mesh covers that ground (inferred from the models' plan size)
    from matplotlib.path import Path as MPath
    kit = np.zeros(GX.shape, bool)
    for h in T.object_hulls(gcfg.STAGE_WRP)[0]:
        if h["kind"] != "kit":
            continue
        hb = h["hull"]
        c0_, c1_ = int(hb[:, 0].min() // 5), int(hb[:, 0].max() // 5) + 1
        r0_, r1_ = int(hb[:, 1].min() // 5), int(hb[:, 1].max() // 5) + 1
        sub = MPath(hb).contains_points(np.c_[GX[r0_:r1_ + 1, c0_:c1_ + 1].ravel(), GZ[r0_:r1_ + 1, c0_:c1_ + 1].ravel()])
        kit[r0_:r1_ + 1, c0_:c1_ + 1] |= sub.reshape(r1_ - r0_ + 1, c1_ - c0_ + 1)
    # bridge exclusion zone: within 6 m (crown half-width + 1 m of the placer, rounded up) of a bridge plan hull or of
    # the v31_bridge_cut / v31_bridge_fill cells: no tree by product rule (G1); the earthwork keeps its texture
    bridge = np.zeros(GX.shape, bool)
    bc_ = t["v31_bridge_cut"] | t["v31_bridge_fill"]
    bcm = bc_[:-1, :-1] | bc_[1:, :-1] | bc_[:-1, 1:] | bc_[1:, 1:]
    nb_ = ndimage.binary_dilation(bcm, iterations=3)[ri, ci]
    bridge[nb_] = T.cell_distance(bc_, GX[nb_], GZ[nb_], 10.0) < 6.0 + 3.54
    for h in T.object_hulls(gcfg.STAGE_WRP)[0]:
        if h["kind"] != "bridge":
            continue
        hb = h["hull"]
        c0_, c1_ = int(hb[:, 0].min() // 5) - 3, int(hb[:, 0].max() // 5) + 4
        r0_, r1_ = int(hb[:, 1].min() // 5) - 3, int(hb[:, 1].max() // 5) + 4
        sx_, sz_ = GX[r0_:r1_, c0_:c1_], GZ[r0_:r1_, c0_:c1_]
        bridge[r0_:r1_, c0_:c1_] |= T.dist_to_polygon(sx_, sz_, hb) < 6.0 + 3.54
    near = ndimage.binary_dilation(cm, iterations=3)[ri, ci]
    narva = np.zeros(near.shape, bool)
    narva[near] = T.cell_distance(t["narva"], GX[near], GZ[near], 10.0) < 6.0 + 3.54   # + half the 5 m cell diagonal
    np.savez_compressed(d / "g5m.npz", tex_major=tex_major, tex_samp=tex_samp, tsd=tsd.astype(np.float32), water=water,
                        dw=dw.astype(np.float32), bog=bog5, bogm=bogm, narva=narva, kit=kit, bridge=bridge)
    meta = {"inputs": {"pbo": gcfg.PBO, "terrain_sha256": sha(gcfg.TERRAIN), "footprint_sha256": sha(gcfg.FOOTPRINT),
                       "layers_sha256": sha(gcfg.LAYERS), "layer_dirs": gcfg.LAYER_DIRS},
            "mask_png_sha256": {k: v["png_sha256"] for k, v in sorted(mk.src.items())},
            "files": {p.name: sha(p) for p in sorted(d.glob("*.np*"))}, "script_sha256": sha(__file__),
            "forest_floor_land_km2": float(((slot == 1) & (wsea == 0)).sum()) / 1e6, "seconds": round(time.time() - t0, 1)}
    (d / "grasters.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k not in ("mask_png_sha256",)}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
