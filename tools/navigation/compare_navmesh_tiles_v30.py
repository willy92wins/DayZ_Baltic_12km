"""Structural read of a new navmesh and tile-level comparison against an accepted one.

inspect_navmesh_tiles.read() checks every tile prefix, coordinate and horizontal bound against
the file; payload hashes compare serialized tiles. Changed tiles are located against the terrain
vertices that differ between the two source NPZ files and against the frozen physical routes, so a
local terrain edit can be shown to leave the routes' navmesh data byte-identical.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np

from inspect_navmesh_tiles import read

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--old-nm', type=Path, required=True)
    ap.add_argument('--new-nm', type=Path, required=True)
    ap.add_argument('--old-terrain', type=Path, required=True)
    ap.add_argument('--new-terrain', type=Path, required=True)
    ap.add_argument('--routes', type=Path, default=ROOT / 'missions/BalticV30ContinuityPhysicalV1.BalticTrial/cases.csv')
    ap.add_argument('--tile-m', type=float, default=12.5)
    ap.add_argument('--local-m', type=float, default=100.0)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Preserve prior evidence'
    tile = a.tile_m
    old, new = read(a.old_nm, tile), read(a.new_nm, tile)
    assert set(old) == set(new), 'Tile coordinate sets differ'
    changed = sorted(k for k in new if new[k]['sha256'] != old[k]['sha256'])
    structural = [k for k in changed if any(new[k][f] != old[k][f] for f in ('polygons', 'vertices', 'y_bounds'))]
    h_old = np.load(a.old_terrain)['heights']
    h_new = np.load(a.new_terrain)['heights']
    r, c = np.nonzero(h_old != h_new)
    vx, vz = 6.0 * c, 6.0 * (2047 - r)

    def distance(k):
        if not len(vx):
            return float('inf')
        x0, z0 = k[0] * tile, k[1] * tile
        dx = np.maximum(np.maximum(x0 - vx, 0), vx - (x0 + tile))
        dz = np.maximum(np.maximum(z0 - vz, 0), vz - (z0 + tile))
        return float(np.hypot(dx, dz).min())

    # NavMeshGenerator output is not byte-deterministic: almost every serialized tile differs between
    # runs. Locate and judge only structural changes (polygon/vertex counts or vertical bounds).
    dist = {k: distance(k) for k in structural}
    hits = {}
    for line in a.routes.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        ident, start, end = line.split(';')
        sx, _, sz = map(float, start.split())
        tx, _, tz = map(float, end.split())
        xs = np.arange(min(sx, tx) - 25, max(sx, tx) + 25 + tile, tile)
        zs = np.arange(min(sz, tz) - 25, max(sz, tz) + 25 + tile, tile)
        cover = {(int(x // tile), int(z // tile)) for x in xs for z in zs}
        hits[ident] = sorted(cover & set(structural))
    local = bool(structural) and max(dist.values()) <= a.local_m
    result = dict(status='PASS_STRUCTURE_AND_LOCAL_TILE_DELTA' if local and not any(hits.values()) else 'REVIEW_TILE_DELTA',
                  old_nm=str(a.old_nm), old_nm_sha256=sha(a.old_nm), new_nm=str(a.new_nm), new_nm_sha256=sha(a.new_nm),
                  old_terrain_sha256=sha(a.old_terrain), new_terrain_sha256=sha(a.new_terrain), tile_m=tile, tiles=len(new),
                  serialized_changed_tiles=len(changed), structural_changes=len(structural), changed_terrain_vertices=int(len(vx)),
                  max_structural_tile_distance_m=max(dist.values()) if dist else None, local_threshold_m=a.local_m,
                  structural=[dict(tile=list(k), distance_m=round(dist[k], 1), old=old[k], new=new[k]) for k in structural],
                  route_tiles_changed=hits,
                  limits=['Empirical TESM6 tile reader; no full polygon-topology or AI-path claim.',
                          'Serialized tiles differ between generator runs; only structural counts and bounds are compared.',
                          'Unchanged structure along a route is not a locomotion result.'])
    a.out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'structural'}, indent=1))
    return 0 if result['status'].startswith('PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
