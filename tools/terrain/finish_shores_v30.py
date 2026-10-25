"""Bounded regional bank profile on the retained V30 delta candidate.

Authoring only: source and all water metadata stay immutable. Native river
triangle vertices, engineering platforms, Narva and the reserve are fixed.
Existing consumer gates must run after this builder, before any promotion.
"""
from pathlib import Path
import argparse
import json

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt
from shapely.geometry import shape

from audit_fairway_triangles_v30 import records, save, sha
from v30_common import cell_planes, grid_xz, vertex_plane_bounds

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')
EXPECTED = 'a84dfff053523b94717b2068a96845193d01a21f0ea7ff01e0f9111280630081'
PARAMS = dict(dry_lower_max_m=3., wet_raise_max_m=1.5, wet_reach_m=6.,
              dry_reach_m=12., dry_full_m=6., protection_blend_m=12.,
              bank_grade=.12, bank_freeboard_m=.061, wet_min_depth_m=.101,
              sea_low_m=.5, sea_low_clearance_m=.05,
              piece_depth_m=.0501, piece_freeboard_m=.0301, narva_radius_m=620.,
              dry_floor_m=1.4001, axis_cap_m=2.88, iterations_max=256)


def ease(v):
    t = np.clip(v, 0, 1)
    return t*t*t*(10+t*(-15+6*t))


def protect_corridors(planes, sources=None):
    fixed = np.zeros((2048, 2048), bool)
    if sources is None:
        sources = [ROOT/'evidence/v30-offline-followup-2026-10-02/corridors.geojson',
                   ROOT/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']
    entries = []
    for path in sources:
        for f in json.loads(path.read_text())['features']:
            if f['properties'].get('kind', 'corridor24m') != 'corridor24m':
                continue
            rec = records(shape(f['geometry']), planes)
            ids = np.unique(rec['ids'])
            fixed.ravel()[ids] = True
            entries.append(dict(name=f['properties'].get('name', f['properties'].get('river')),
                                face_vertices=len(ids)))
    if len(entries) < 20:
        raise ValueError('Incomplete main and delta channel protection')
    # A vertex margin prevents the bank shoulder from starting on the last
    # certified face. Exact main/delta protected faces are also saved separately.
    return fixed, binary_dilation(fixed), entries, sources


def recover_dry_gradients(h, original, dry):
    """Cancel excessive dry-bank lowering at a fixed neighbour, never raise
    land above original or touch water. Existing per-edge differences larger
    than 2.88 are retained as ceilings, not newly imposed on an old surface.
    Geometry is assessed independently on both native triangle halves later.
    """
    cx = np.maximum(PARAMS['axis_cap_m'], np.abs(np.diff(original, axis=1)))
    cy = np.maximum(PARAMS['axis_cap_m'], np.abs(np.diff(original, axis=0)))
    dx, dy = dry[:, :-1] & dry[:, 1:], dry[:-1, :] & dry[1:, :]
    for iteration in range(PARAMS['iterations_max']):
        nh = h.copy()
        nh[:, 1:] = np.maximum(nh[:, 1:], np.where(dx, h[:, :-1]-cx, -np.inf))
        nh[:, :-1] = np.maximum(nh[:, :-1], np.where(dx, h[:, 1:]-cx, -np.inf))
        nh[1:, :] = np.maximum(nh[1:, :], np.where(dy, h[:-1, :]-cy, -np.inf))
        nh[:-1, :] = np.maximum(nh[:-1, :], np.where(dy, h[1:, :]-cy, -np.inf))
        if np.any(nh[dry] > original[dry]+1e-7):
            raise ValueError('Dry recovery cannot increase the source')
        delta = float(np.max(np.abs(nh-h)))
        h = nh
        if delta < 1e-6:
            return h, iteration+1
    raise ValueError('Dry recovery did not converge within the declared budget')


def discard_steeper_land_faces(proposal, original, cls):
    """Keep useful edits, but cancel an edit if it creates/worsens a >35 deg
    native face touching land. Reverting one face can affect its neighbours,
    so propagate until stable. Reversion only restores original vertices;
    it cannot lower a dry floor or make a wet vertex shallower.
    """
    n = original.shape[0]
    row, col = np.indices((n-1, n-1))
    limits = []
    for offsets in [((0,0),(0,1),(1,1)), ((0,0),(1,0),(1,1))]:
        ids = [(row+dr)*n+col+dc for dr,dc in offsets]
        a,b,c = [original.ravel()[ix] for ix in ids]
        angle = np.degrees(np.arctan(np.hypot(b-a,c-b)/6.))
        land = np.logical_or.reduce([cls.ravel()[ix]==0 for ix in ids])
        limits.append((ids, np.maximum(angle, 35.) + 1e-4, land))
    h = proposal.astype('float32').astype(float)
    reverted = np.zeros_like(cls, dtype=bool)
    for iteration in range(PARAMS['iterations_max']):
        undo = np.zeros_like(cls, dtype=bool)
        for ids, ceiling, land in limits:
            a,b,c = [h.ravel()[ix] for ix in ids]
            angle = np.degrees(np.arctan(np.hypot(b-a,c-b)/6.))
            bad = land & (angle > ceiling)
            for ix in ids:
                undo.ravel()[ix[bad]] = True
        undo &= h != original
        if not undo.any():
            return h, dict(iterations=iteration+1, reverted_vertices=int(reverted.sum()))
        h[undo] = original[undo]
        reverted |= undo
    raise ValueError('Face recovery did not converge within the declared budget')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--source', type=Path, default=SOURCE)
    ap.add_argument('--source-sha', default=EXPECTED)
    ap.add_argument('--water-v30', type=Path, default=ROOT/'tests/terrain_v30/water_v30.npz')
    ap.add_argument('--nature', type=Path, default=ROOT/'tests/regional_outline_v1/reference.npz')
    ap.add_argument('--corridors', type=Path, nargs='+', default=None)
    a = ap.parse_args()
    if a.out.exists() or (a.source_sha != 'any' and sha(a.source) != a.source_sha):
        raise ValueError('Fresh destination and exact source required')
    a.out.mkdir(parents=True)
    t = np.load(a.source)
    wpath = a.water_v30
    naturepath = a.nature
    w = np.load(wpath)
    h = t['heights'].astype(float)
    cls, level = t['cls'], t['level'].astype(float)
    wet, dry = cls > 0, cls == 0
    planes = cell_planes(cls, level)
    pmin, pmax = vertex_plane_bounds(planes)
    corridor, corridor_margin, entries, sources = protect_corridors(planes, sources=a.corridors)
    # Conservative preservation of the original full nature envelope. Its
    # inclusion is a no-change promise, not a claim about legal park borders.
    nature = np.load(naturepath)['reserve'].astype(bool)
    x, z = grid_xz()
    fixed = corridor_margin | t['platform'] | t['reserve'] | t['narva'] | nature
    fixed |= np.hypot(x-2417.1428225906, z-6889.8850822322) <= PARAMS['narva_radius_m']
    fixed |= (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
    guard = ease(distance_transform_edt(~fixed, sampling=6.) / PARAMS['protection_blend_m'])
    dist, nearest = distance_transform_edt(dry, sampling=6., return_indices=True)
    near_level = level[nearest[0], nearest[1]]
    sd, sea_sd = w['sd'].astype(float), w['sd_sea'].astype(float)
    # Select the nearer existing outline. Newly reclassified delta vertices
    # whose sign disagrees with this original field are excluded automatically.
    use_sea = np.isfinite(sea_sd) & (~np.isfinite(sd) | (np.abs(sea_sd) < np.abs(sd)))
    signed = np.where(use_sea, sea_sd, sd)
    valid = np.isfinite(signed) & ~fixed
    dry_allowed = valid & dry & (signed >= 0) & (signed < PARAMS['dry_reach_m'])
    dry_allowed &= dist <= 18
    # Keep the authored intertidal beach intact; interior ground always has its
    # existing dry floor and pond clearance. No new low coastal pocket is made.
    dry_allowed &= ~t['beach']
    dry_floor = np.maximum(PARAMS['dry_floor_m'], near_level + PARAMS['bank_freeboard_m'])
    dry_floor = np.maximum(dry_floor, np.nan_to_num(pmax, nan=-np.inf)+PARAMS['piece_freeboard_m'])
    dry_target = np.maximum(dry_floor, near_level + PARAMS['bank_freeboard_m'] +
                            PARAMS['bank_grade']*np.nan_to_num(signed, nan=0.))
    dry_blend = guard*ease((PARAMS['dry_reach_m']-np.nan_to_num(signed, nan=1e9)) /
                         (PARAMS['dry_reach_m']-PARAMS['dry_full_m']))
    proposal = h.copy()
    proposal[dry_allowed] -= dry_blend[dry_allowed]*np.clip(
        h[dry_allowed]-dry_target[dry_allowed], 0, PARAMS['dry_lower_max_m'])
    proposal, iterations = recover_dry_gradients(proposal, h, dry)
    wet_allowed = valid & wet & (signed < 0) & (signed > -PARAMS['wet_reach_m'])
    wet_allowed &= ~w['groove']
    wet_target = level - np.maximum(PARAMS['wet_min_depth_m'],
                                   PARAMS['bank_grade']*np.abs(signed))
    wet_target = np.minimum(wet_target, np.nan_to_num(pmin, nan=np.inf)-PARAMS['piece_depth_m'])
    # Sea-connected water oscillates down to 0.5 m. Raising a vertex towards
    # mean level minus 0.101 would expose it at low tide (349 in the first
    # candidate); keep altered coastal wet vertices below that envelope.
    tidal = wet & ((level <= .8) | ~np.isfinite(pmin))
    wet_target[tidal] = np.minimum(wet_target[tidal], PARAMS['sea_low_m']-PARAMS['sea_low_clearance_m'])
    wet_blend = guard*ease((PARAMS['wet_reach_m']-np.abs(np.nan_to_num(signed, nan=1e9)))/3.)
    proposal[wet_allowed] += wet_blend[wet_allowed]*np.clip(
        wet_target[wet_allowed]-h[wet_allowed], 0, PARAMS['wet_raise_max_m'])
    proposal, face_recovery = discard_steeper_land_faces(proposal, h, cls)
    candidate = proposal.astype('float32')
    changed = candidate != t['heights']
    if not changed.any() or np.any(changed & ~(dry_allowed | wet_allowed)):
        raise ValueError('Empty candidate or change outside the authoring domain')
    if np.any(changed & fixed):
        raise ValueError('Protected height changed')
    delta = candidate.astype(float)-h
    if delta.max() > PARAMS['wet_raise_max_m']+1e-5 or -delta.min() > PARAMS['dry_lower_max_m']+1e-5:
        raise ValueError('Delta exceeds the declared bound')
    dest = a.out/'terrain_v30.npz'
    with dest.open('xb') as stream:
        np.savez_compressed(stream, **{k: candidate if k == 'heights' else t[k] for k in t.files})
    asc = a.out/'baltic_terrain_v30.asc'
    with asc.open('x', encoding='ascii', newline='\n') as stream:
        stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(stream, candidate, fmt='%.9g')
    with (a.out/'authoring_masks.npz').open('xb') as stream:
        np.savez_compressed(stream, changed=changed, fixed=fixed, corridors=corridor,
                            nature=nature, dry_allowed=dry_allowed, wet_allowed=wet_allowed)
    report = dict(status='BUILT_PENDING_GROUPED_GATES_AND_VISUAL', params=PARAMS,
                  source_sha256=a.source_sha if a.source_sha != 'any' else sha(a.source),
                  candidate_sha256=sha(dest), asc_sha256=sha(asc),
                  changed_vertices=int(changed.sum()), dry_lowered=int((changed & dry).sum()),
                  wet_raised=int((changed & wet).sum()), max_raise_m=float(delta.max()),
                  max_lower_m=float(-delta.min()), dry_recovery_iterations=iterations,
                  face_recovery=face_recovery,
                  protected_corridors=entries,
                  inputs={str(p):sha(p) for p in [a.source,wpath,naturepath,*sources,Path(__file__)]},
                  limits=['Heights only; water classes, levels, pieces and design outline unchanged.',
                          'No deployment or navigation claim; shore appearance requires engine views.',
                          'Full original nature envelope preserved, not a revised legal reserve boundary.'])
    save(a.out/'build.json', report)
    print(json.dumps({k:report[k] for k in ['status','changed_vertices','dry_lowered','wet_raised',
                                         'max_raise_m','max_lower_m','dry_recovery_iterations']}, indent=2))


if __name__ == '__main__':
    main()
