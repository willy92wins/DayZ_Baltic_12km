#!/usr/bin/env python
"""EV79 independent Narva-only dry-bank consumer; never imports author/generator."""
from __future__ import annotations
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(r'E:/DayZ-Baltic-Build')
EXPECTED_SOURCE_SHA = 'b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36'
EXPECTED_CANDIDATE_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
EXPECTED_CONSTRAINTS_SHA = 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
N = 2048
TOL_DEG = 1e-4
TOL_HEIGHT = 1e-6


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def equal(a, b):
    return np.array_equal(a, b, equal_nan=True)


def load_npz(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def wet_faces(h, p, visible):
    """Return the two native NW-SE triangle wet masks, evaluated against every corner."""
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    hv = [h[dr:dr+N-1, dc:dc+N-1] for dr, dc in corners]
    nominal = np.fmax(p, 0.85)
    vis = np.where(np.isfinite(p)[:, :, None], visible, 0.85)
    out = []
    for tri in ((0, 1, 3), (0, 2, 3)):
        wet = np.zeros(p.shape, dtype=bool)
        for i in tri:
            wet |= (nominal > hv[i]) | (vis[:, :, i] > hv[i])
        out.append(wet)
    return out


def wet_support(faces):
    support = np.zeros((N, N), dtype=bool)
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for wet, tri in zip(faces, ((0, 1, 3), (0, 2, 3))):
        for i in tri:
            dr, dc = corners[i]
            support[dr:dr+N-1, dc:dc+N-1] |= wet
    return support


def water_floor(base, p, visible):
    """At each vertex, max P/F/sea over its own incident cell-corner samples."""
    vertex_level = np.full(base.shape, 0.85, dtype=np.float64)
    f = np.where(np.isfinite(p)[:, :, None], visible, 0.85)
    for i, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
        cell = np.maximum(0.85, np.maximum(np.nan_to_num(p.astype(np.float64), nan=0.85),
                                           np.nan_to_num(f[:, :, i].astype(np.float64), nan=0.85)))
        dst = vertex_level[dr:dr+N-1, dc:dc+N-1]
        np.maximum(dst, cell, out=dst)
    return np.minimum(base, vertex_level + 1e-4)


def face_normals(h):
    nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    ones = np.ones_like(nw)
    ea = np.stack((6*ones, ne-nw, np.zeros_like(nw)), axis=-1)
    diagonal = np.stack((6*ones, se-nw, -6*ones), axis=-1)
    eb = np.stack((np.zeros_like(nw), sw-nw, -6*ones), axis=-1)
    a = np.cross(ea, diagonal)
    b = np.cross(diagonal, eb)
    a /= np.linalg.norm(a, axis=-1)[..., None]
    b /= np.linalg.norm(b, axis=-1)[..., None]
    return a, b


def face_slopes(h):
    a, b = face_normals(h)
    return (np.degrees(np.arctan2(np.hypot(a[..., 0], a[..., 2]), np.abs(a[..., 1]))),
            np.degrees(np.arctan2(np.hypot(b[..., 0], b[..., 2]), np.abs(b[..., 1]))))


def edge_angles(h):
    a, b = face_normals(h)
    pairs = [('diagonal', a, b), ('vertical', a[:, :-1], b[:, 1:]), ('horizontal', b[:-1, :], a[1:, :])]
    for name, x, y in pairs:
        yield name, np.degrees(np.arctan2(np.linalg.norm(np.cross(x, y), axis=-1), np.einsum('ijk,ijk->ij', x, y)))


def incident_all(mask, kind):
    if kind == 'diagonal':
        return mask[:-1, :-1] & mask[:-1, 1:] & mask[1:, :-1] & mask[1:, 1:]
    if kind == 'vertical':
        return mask[:-1, :-2] & mask[:-1, 1:-1] & mask[1:, 1:-1] & mask[1:, 2:]
    return mask[:-2, :-1] & mask[1:-1, :-1] & mask[1:-1, 1:] & mask[2:, 1:]


def incident_any(mask, kind):
    return ~incident_all(~mask, kind)


def summaries(values):
    a = np.concatenate(values) if values else np.empty(0, dtype=np.float64)
    if not len(a):
        return dict(n=0, mean_square=None, p99=None, max=None, above30=0,
                    histogram_5deg=[0]*36)
    return dict(n=int(len(a)), mean_square=float(np.mean(a*a)), p99=float(np.percentile(a, 99)),
                max=float(a.max()), above30=int(np.count_nonzero(a > 30)),
                histogram_5deg=np.histogram(a, bins=np.arange(0, 185, 5))[0].astype(int).tolist())


def reconstruct(source, valley_masks, terminal, prior, controls, wet):
    cls = source['cls']; h, w = cls.shape
    assert (h, w) == (N, N)
    rr, cc = np.indices((N, N)); x = cc*6.0; z = 12282.0-rr*6.0
    radial620 = np.hypot(x-2417.1428225906, z-6889.8850822322) <= 620.0
    narva = radial620 | source['narva'].astype(bool)
    r1 = np.zeros((N, N), dtype=bool)
    axes_path = ROOT/'v30-continuation-20261008/junction-fix-r2/axes.json'
    axes = json.loads(axes_path.read_text(encoding='utf-8'))
    for r, c in axes['R1']['removed_cells']:
        r1[r:r+2, c:c+2] = True
    r1dist = distance_transform_edt(~r1, sampling=6.0)
    narva_old_guard = narva & (r1dist >= 150.0)
    oldborder66 = (x < 66) | (x > 12216) | (z < 66) | (z > 12216)
    outer24 = (x < 24) | (x > 12258) | (z < 24) | (z > 12258)
    engineering = source['reserve'].astype(bool) | source['platform'].astype(bool)
    sea = np.isin(cls, (1, 4)); beach = source['beach'].astype(bool)
    corridor = valley_masks['corridor'].astype(bool); summits = valley_masks['summits'].astype(bool)
    # Reconstruct the historical Narva guard as a diagnostic only. EV79 removes only this
    # guard and the Narva raster from the fixed union; all named protections remain explicit.
    old_formula = engineering | corridor | summits | oldborder66 | sea | beach | narva_old_guard
    assert np.array_equal(old_formula, valley_masks['fixed']), 'EV78 source fixed components do not reconstruct'
    controls = controls.astype(bool)
    terminal_formula = (valley_masks['fixed'] & ~oldborder66) | outer24 | engineering | corridor | summits | sea | beach | source['narva'].astype(bool) | controls
    assert np.array_equal(terminal_formula, terminal['fixed']), 'terminal fixed components do not reconstruct'
    other_fixed = (source['water'].astype(bool) | beach | (cls != 0) | corridor | summits |
                   ((rr < 11) | (rr >= 2037) | (cc < 11) | (cc >= 2037)) | controls)
    engineering_halo = binary_dilation(engineering, structure=np.ones((3, 3), dtype=bool))
    fixed = other_fixed | prior['large_lake_banks'].astype(bool) | wet | engineering_halo
    near_water = np.isin(cls, (3, 5, 6))
    dist_water = distance_transform_edt(~near_water, sampling=6.0)
    bank_domain = (cls == 0) & (dist_water <= 96.0 + 1e-9) & narva
    return dict(old_narva_guard=narva_old_guard, narva=narva, other_fixed=other_fixed,
                fixed=fixed, bank_domain=bank_domain, engineering=engineering,
                engineering_halo=engineering_halo, corridor=corridor, summits=summits,
                controls=controls, border11=(rr < 11) | (rr >= 2037) | (cc < 11) | (cc >= 2037),
                large_lakes=prior['large_lake_banks'].astype(bool), wet_support=wet)


def expected_constraints(source, prior, valley_masks, terminal, controls, p, visible, wet):
    masks = reconstruct(source, valley_masks, terminal, prior, controls, wet)
    bank_domain = masks['bank_domain']; fixed = masks['fixed']; halo = masks['engineering_halo']
    allowed = bank_domain & ~fixed
    # Quintic transition in 18 m from the fixed edge into the independently rebuilt allowed domain.
    d = distance_transform_edt(allowed, sampling=6.0)
    x = np.clip(d / 18.0, 0.0, 1.0)
    smooth = x*x*x*(10.0 - 15.0*x + 6.0*x*x)
    cap = 2.0*smooth
    base = source['heights'].astype(np.float64)
    floor = np.minimum(base, 1.8)
    lower = np.maximum.reduce((base-cap, floor, water_floor(base, p, visible)))
    return dict(**masks, allowed=allowed, cap=cap, lower=lower)


def metadata_equal(src, cand):
    return set(src) == set(cand) and all(equal(src[k], cand[k]) for k in src if k != 'heights')


def evaluate(candidate_heights, source, candidate, constraints, expected, p, visible, source_wet_faces, source_wet_support):
    base = source['heights'].astype(np.float64)
    v = candidate_heights.astype(np.float64)
    changed = v != base
    wet_v_faces = wet_faces(v, p, visible)
    wet_face_new = sum(int(np.count_nonzero(n & ~o)) for n, o in zip(wet_v_faces, source_wet_faces))
    # Explicit face-level comparison prevents false assurance from preserving only old wet vertices.
    lower = expected['lower']
    slopes0 = face_slopes(base); slopes1 = face_slopes(v)
    bad_slope = 0; max_excess = 0.0; slope_summary = {}
    for i, (a, b) in enumerate(zip(slopes0, slopes1)):
        delta = b - np.maximum(a, 35.0)
        bad_slope += int(np.count_nonzero(delta > TOL_DEG))
        max_excess = max(max_excess, float(delta.max(initial=-np.inf)))
        slope_summary['triangle_'+str(i)] = dict(source_max=float(a.max()), candidate_max=float(b.max()),
                                                  bad_faces=int(np.count_nonzero(delta > TOL_DEG)))
    gates = {
        'finite_full_map': bool(np.isfinite(v).all()),
        'metadata_exact': metadata_equal(source, candidate),
        'fixed_exact': not bool((changed & expected['fixed']).any()),
        'outside_allowed_exact': not bool((changed & ~expected['allowed']).any()),
        'wet_support_exact': not bool((changed & source_wet_support).any()),
        'no_new_wet_faces': wet_face_new == 0,
        'engineering_halo_exact': not bool((changed & expected['engineering_halo']).any()),
        'road_platform_exact': not bool((changed & expected['engineering']).any()),
        'bank_domain_exact_constraints': np.array_equal(constraints['bank_domain'], expected['bank_domain']),
        'narva_scope_exact_constraints': np.array_equal(constraints['narva'], expected['narva']),
        'other_fixed_reconstructed': np.array_equal(constraints['other_fixed'], expected['other_fixed']),
        'fixed_mask_reconstructed': np.array_equal(constraints['fixed'], expected['fixed']),
        'allowed_mask_reconstructed': np.array_equal(constraints['allowed'], expected['allowed']),
        'wet_support_mask_reconstructed': np.array_equal(constraints['wet_support'], source_wet_support),
        'engineering_halo_mask_reconstructed': np.array_equal(constraints['engineering_halo'], expected['engineering_halo']),
        'cap_field_reconstructed': bool(np.allclose(constraints['cap'], expected['cap'], rtol=0, atol=1e-8)),
        'lower_field_reconstructed': bool(np.allclose(constraints['lower'], expected['lower'], rtol=0, atol=1e-6)),
        'lower_floor': bool(np.all(v >= lower - TOL_HEIGHT)),
        'local_cap_and_2m': bool(np.all(np.abs(v-base) <= np.minimum(expected['cap'], 2.0) + TOL_HEIGHT)),
        'native_face_slope_limit': bad_slope == 0,
    }
    counts = dict(changed_vertices=int(changed.sum()), fixed_vertices=int(expected['fixed'].sum()),
                  allowed_vertices=int(expected['allowed'].sum()), bank_domain_vertices=int(expected['bank_domain'].sum()),
                  source_wet_support_vertices=int(source_wet_support.sum()), newly_wet_native_faces=wet_face_new,
                  source_wet_native_faces=int(sum(x.sum() for x in source_wet_faces)),
                  candidate_wet_native_faces=int(sum(x.sum() for x in wet_v_faces)),
                  max_abs_delta_m=float(np.abs(v-base).max()), max_cap_m=float(expected['cap'].max()),
                  min_candidate_m=float(v.min()), min_lower_margin_m=float((v-lower).min()),
                  max_slope_excess_degrees=max_excess, slope_faces=slope_summary)
    return gates, counts


def angles_and_sectors(base, cand, source, expected):
    changed = cand != base
    dry = (source['cls'] == 0) & ~expected['wet_support'] & ~(source['reserve'].astype(bool) | source['platform'].astype(bool))
    bank = dry & (distance_transform_edt(~np.isin(source['cls'], (3, 5, 6)), sampling=6.0) <= 96.0 + 1e-9)
    interior = dry & ~bank
    buckets = {'bank': [[], []], 'interior': [[], []], 'changed_incident': [[], []]}
    sector_map = {}
    top_cases = []
    new_over30 = 0
    new_fold_cases = []
    modified_bank_cases = []
    for (kind, old), (kind2, new) in zip(edge_angles(base), edge_angles(cand)):
        assert kind == kind2
        domains = {'bank': incident_all(bank, kind), 'interior': incident_all(interior, kind),
                   'changed_incident': incident_any(changed, kind)}
        for key, mask in domains.items():
            buckets[key][0].append(old[mask]); buckets[key][1].append(new[mask])
        new_mask = (old <= 30.0 + TOL_DEG) & (new > 30.0 + TOL_DEG)
        new_over30 += int(np.count_nonzero(new_mask))
        for ix in np.flatnonzero(new_mask):
            r, c = np.unravel_index(ix, old.shape)
            if kind == 'vertical': xx, zz = (c+1)*6, 12282-(r+0.5)*6
            elif kind == 'horizontal': xx, zz = (c+0.5)*6, 12282-(r+1)*6
            else: xx, zz = (c+0.5)*6, 12282-(r+0.5)*6
            new_fold_cases.append(dict(kind=kind, row=int(r), col=int(c), x=float(xx), z=float(zz),
                source_dihedral_deg=float(old[r,c]), candidate_dihedral_deg=float(new[r,c])))
        valid = domains['changed_incident']
        for r0 in range(0, old.shape[0], 64):
            for c0 in range(0, old.shape[1], 64):
                sl = np.s_[r0:min(r0+64, old.shape[0]), c0:min(c0+64, old.shape[1])]
                ok = valid[sl]
                if not ok.any():
                    continue
                aa, bb = old[sl][ok], new[sl][ok]
                key = (r0//64, c0//64)
                row = sector_map.setdefault(key, dict(row=key[0], col=key[1], edges=0,
                    before_sum_sq=0.0, after_sum_sq=0.0, before_max=0.0, after_max=0.0,
                    before_above30=0, after_above30=0, kinds=[]))
                row['edges'] += int(len(aa)); row['before_sum_sq'] += float(aa@aa); row['after_sum_sq'] += float(bb@bb)
                row['before_max'] = max(row['before_max'], float(aa.max(initial=0)))
                row['after_max'] = max(row['after_max'], float(bb.max(initial=0)))
                row['before_above30'] += int(np.count_nonzero(aa > 30.0))
                row['after_above30'] += int(np.count_nonzero(bb > 30.0))
                row['kinds'].append(kind)
        mask = incident_all(bank, kind)
        changed_bank = mask & incident_any(changed, kind)
        for ix in np.flatnonzero(changed_bank & (old >= 30.0)):
            r, c = np.unravel_index(ix, old.shape)
            if kind == 'vertical': xx, zz = (c+1)*6, 12282-(r+0.5)*6
            elif kind == 'horizontal': xx, zz = (c+0.5)*6, 12282-(r+1)*6
            else: xx, zz = (c+0.5)*6, 12282-(r+0.5)*6
            modified_bank_cases.append(dict(kind=kind, row=int(r), col=int(c), x=float(xx), z=float(zz),
                source_dihedral_deg=float(old[r,c]), candidate_dihedral_deg=float(new[r,c]),
                reduction_deg=float(old[r,c]-new[r,c])))
        idx = np.flatnonzero(mask & (old >= 30.0))
        if len(idx):
            take = idx[np.argsort(old.ravel()[idx])[-min(40, len(idx)):]]
            for ix in take:
                r, c = np.unravel_index(ix, old.shape)
                top_cases.append(dict(kind=kind, row=int(r), col=int(c),
                    x=float((c+0.5)*6), z=float(12282-(r+0.5)*6),
                    source_dihedral_deg=float(old[r,c]), candidate_dihedral_deg=float(new[r,c]),
                    reduction_deg=float(old[r,c]-new[r,c])))
    stats = {}
    for name, (oldparts, newparts) in buckets.items():
        s0, s1 = summaries(oldparts), summaries(newparts)
        reduction = None if not s0['mean_square'] else 1.0-s1['mean_square']/s0['mean_square']
        stats[name] = dict(source=s0, candidate=s1, angular_energy_reduction=reduction)
    changed_stats = stats['changed_incident']
    energy_gate = changed_stats['angular_energy_reduction'] is not None and changed_stats['angular_energy_reduction'] >= 0.05
    bank_stats, interior_stats = stats['bank'], stats['interior']
    bank_gate = bank_stats['candidate']['n'] > 0 and bank_stats['candidate']['p99'] <= bank_stats['source']['p99'] + TOL_DEG and bank_stats['candidate']['above30'] <= bank_stats['source']['above30']
    interior_gate = interior_stats['candidate']['n'] > 0 and interior_stats['candidate']['p99'] <= interior_stats['source']['p99'] + TOL_DEG and interior_stats['candidate']['above30'] <= interior_stats['source']['above30']
    sectors = sorted(sector_map.values(), key=lambda x: (x['row'], x['col']))
    for row in sectors:
        row['kinds'] = sorted(set(row['kinds']))
        row['max_increase_deg'] = row['after_max'] - row['before_max']
        row['no_max_regression'] = row['max_increase_deg'] <= TOL_DEG
    sector_gate = all(x['no_max_regression'] for x in sectors)
    top_cases.sort(key=lambda x: x['source_dihedral_deg'], reverse=True)
    modified_bank_cases.sort(key=lambda x: x['source_dihedral_deg'], reverse=True)
    return dict(stats=stats, sectors=sectors,
                gates=dict(changed_incident_angular_energy_reduction_ge_5pct=energy_gate,
                           bank_p99_and_over30_nonworse=bank_gate,
                           interior_p99_and_over30_nonworse=interior_gate,
                           zero_new_edges_over30_from_at_most30=new_over30 == 0,
                           modified_sector_max_nonworse=sector_gate),
                new_edges_over30_from_at_most30=int(new_over30), modified_sector_count=len(sectors),
                modified_sector_regressions=[x for x in sectors if not x['no_max_regression']],
                top_source_bank_dihedral_cases=top_cases[:30],
                modified_source_bank_dihedral_cases=modified_bank_cases[:30],
                new_edge_over30_cases=new_fold_cases)


def narva_and_wet_dry_counts(base, cand, source, expected):
    cls = source['cls']; support = expected['wet_support']
    flow_dist = distance_transform_edt(~np.isin(cls, (3, 5, 6)), sampling=6.0)
    dry_bank = ((cls == 0) & ~support & ~source['water'].astype(bool) & ~source['beach'].astype(bool) &
                ~source['reserve'].astype(bool) & ~source['platform'].astype(bool) & (flow_dist <= 96.0 + 1e-9))
    narva_dry_bank = dry_bank & expected['narva']
    arrays = dict(source=dict(), candidate=dict())
    anchors = [
        ('diagonal', 927, 364, 49.970557745066266),
        ('horizontal', 902, 429, 34.62593947983456),
        ('horizontal', 893, 382, 34.47946038646811),
        ('diagonal', 980, 446, 32.80730145522656),
    ]
    angle_maps = {'source': dict(edge_angles(base)), 'candidate': dict(edge_angles(cand))}
    anchors_result = []
    for rank, (kind, row, col, expected_source_deg) in enumerate(anchors, 1):
        before = float(angle_maps['source'][kind][row, col]); after = float(angle_maps['candidate'][kind][row, col])
        anchors_result.append(dict(rank=rank, kind=kind, row=row, col=col,
            x_m=float((col+0.5)*6 if kind != 'vertical' else (col+1)*6),
            z_m=float(12282-(row+0.5)*6 if kind in ('diagonal','vertical') else 12282-(row+1)*6),
            source_dihedral_deg=before, candidate_dihedral_deg=after, descent_deg=before-after,
            source_anchor_matches_audit=abs(before-expected_source_deg) <= 1e-8))
    anchor_max_source = max(x['source_dihedral_deg'] for x in anchors_result)
    anchor_max_candidate = max(x['candidate_dihedral_deg'] for x in anchors_result)
    for label, h in (('source', base), ('candidate', cand)):
        counts = dict(strict_dry_bank_over30=0, narva_strict_dry_bank_over30=0,
                      touching_dry_bank_over30=0, touching_not_four_of_four_over30=0,
                      touching_actual_wet_support_over30=0, touching_dry_bank_edges=0,
                      strict_dry_bank_edges=0, touching_wet_support_edges=0)
        for kind, angles in edge_angles(h):
            any_bank = incident_any(dry_bank, kind); all_bank = incident_all(dry_bank, kind)
            any_narva = incident_any(narva_dry_bank, kind); all_narva = incident_all(narva_dry_bank, kind)
            any_wet = incident_any(support, kind)
            high = angles > 30.0
            counts['touching_dry_bank_edges'] += int(any_bank.sum())
            counts['strict_dry_bank_edges'] += int(all_bank.sum())
            counts['touching_wet_support_edges'] += int((any_bank & any_wet).sum())
            counts['touching_dry_bank_over30'] += int((any_bank & high).sum())
            counts['strict_dry_bank_over30'] += int((all_bank & high).sum())
            counts['touching_not_four_of_four_over30'] += int((any_bank & ~all_bank & high).sum())
            counts['touching_actual_wet_support_over30'] += int((any_bank & any_wet & high).sum())
            counts['narva_strict_dry_bank_over30'] += int((all_narva & high).sum())
        arrays[label] = counts
    anchor_gate = (all(x['source_anchor_matches_audit'] for x in anchors_result) and
                   anchor_max_candidate < anchor_max_source - TOL_DEG)
    narva_count_gate = arrays['candidate']['narva_strict_dry_bank_over30'] < arrays['source']['narva_strict_dry_bank_over30']
    source_scope_matches = (arrays['source']['strict_dry_bank_over30'] == 59 and
                            arrays['source']['touching_dry_bank_over30'] == 4827 and
                            arrays['source']['touching_not_four_of_four_over30'] == 4768 and
                            arrays['source']['touching_actual_wet_support_over30'] == 4740)
    return dict(source_counts=arrays['source'], candidate_counts=arrays['candidate'], anchors=anchors_result,
        anchor_max_source_deg=anchor_max_source, anchor_max_candidate_deg=anchor_max_candidate,
        anchor_max_descent_deg=anchor_max_source-anchor_max_candidate,
        gates=dict(source_59_vs_4827_scope_matches_audit=source_scope_matches,
                   narva_anchor_max_decreases_by_gt_1e_4=anchor_gate,
                   narva_strict_dry_over30_count_decreases=narva_count_gate))


def controls():
    # Independent cross-product geometry controls, deliberately tiny and deterministic.
    r, c = np.indices((8, 8)); plane = 3.0 + c*0.31 - r*0.27
    p0 = face_normals(plane)
    plane_max = max(float(np.max(v)) for _, v in edge_angles(plane))
    fold = np.maximum(0.0, c-4)*6.0
    fold_max = float(max(np.max(a) for _, a in edge_angles(fold)))
    return dict(inclined_plane_zero_dihedral=plane_max < 1e-12,
                known_45_degree_fold=abs(fold_max-45.0) < 1e-10,
                measured=dict(plane_dihedral_max_degrees=plane_max, fold_dihedral_max_degrees=fold_max))


def negative_controls(base, source, candidate, constraints, expected, p, visible, wet_faces0, wet_support):
    basev = candidate['heights'].astype(np.float32, copy=True)
    results = {}
    choices = [
        ('wet_vertex', wet_support, 0.01),
        ('engineering_vertex', expected['engineering'], 0.01),
    ]
    for name, mask, amount in choices:
        if mask.any():
            r, c = map(int, np.argwhere(mask)[len(np.argwhere(mask))//2])
            mutant = basev.copy(); mutant[r, c] += amount
            gates, _ = evaluate(mutant, source, candidate, constraints, expected, p, visible, wet_faces0, wet_support)
            target_gate = 'wet_support_exact' if name == 'wet_vertex' else 'road_platform_exact'
            results[name+'_rejected'] = not gates[target_gate]
            results[name+'_triggered_gate'] = target_gate
        else:
            results[name+'_rejected'] = False; results[name+'_reason'] = 'no eligible source vertices'
    if expected['allowed'].any():
        points = np.argwhere(expected['allowed']); r, c = map(int, points[len(points)//2])
        mutant = basev.copy(); mutant[r, c] = np.float32(expected['lower'][r, c]-0.01)
        gates, _ = evaluate(mutant, source, candidate, constraints, expected, p, visible, wet_faces0, wet_support)
        results['below_floor_rejected'] = not gates['lower_floor']
        r, c = map(int, points[min(len(points)-1, len(points)//3)])
        mutant = basev.copy(); mutant[r, c] = np.float32(base[r, c]+10.0)
        gates, _ = evaluate(mutant, source, candidate, constraints, expected, p, visible, wet_faces0, wet_support)
        results['dry_spike_rejected'] = (not gates['local_cap_and_2m']) and (not gates['native_face_slope_limit'])
        results['dry_spike_triggered'] = dict(cap_gate=not gates['local_cap_and_2m'], slope_gate=not gates['native_face_slope_limit'])
    else:
        results['below_floor_rejected'] = False; results['dry_spike_rejected'] = False
        results['reason'] = 'empty allowed domain'
    return results


def temporal_controls(reference_path):
    record = json.loads(reference_path.read_text(encoding='utf-8'))
    controls = np.zeros((N, N), dtype=bool)
    for q in record['points']:
        r = int(np.floor((12282.0-q['z'])/6.0)); c = int(np.floor(q['x']/6.0))
        controls[max(0,r):min(N,r+2), max(0,c):min(N,c+2)] = True
    return controls


def main():
    ap = argparse.ArgumentParser()
    build = ROOT/'v30-narva-dry-bank-relief-20261010'
    ap.add_argument('--candidate', type=Path, default=build/'candidate/terrain.npz')
    ap.add_argument('--constraints', type=Path, default=build/'constraints.npz')
    ap.add_argument('--source', type=Path, default=ROOT/'v30-remaining-exact-dry-support-20261009/candidate/terrain.npz')
    ap.add_argument('--prior-constraints', type=Path, default=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz')
    ap.add_argument('--valley-masks', type=Path, default=ROOT/'v30-valley-smoothing-20261008/candidate-a/masks.npz')
    ap.add_argument('--terminal', type=Path, default=ROOT/'v30-native-terminal-finish-20261009/constraints.npz')
    ap.add_argument('--temporal-reference', type=Path, default=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-global-contour-pass-2026-10-09/global-contour-temporal-reference.json'))
    ap.add_argument('--plane', type=Path, default=None)
    ap.add_argument('--visible-field', type=Path, default=None)
    ap.add_argument('--report', type=Path, default=Path(__file__).with_name('report.json'))
    args = ap.parse_args()
    started = time.time()
    plane_path = args.plane or args.source.parent/'plane.npy'
    visible_path = args.visible_field or args.source.parent/'visible-field.npy'
    input_paths = (args.source, args.candidate, args.constraints, plane_path, visible_path,
                   args.prior_constraints, args.valley_masks, args.terminal, args.temporal_reference,
                   build/'authoring.json', build/'plan.md', Path(__file__))
    report = dict(status='FAIL', verifier='EV79 independent Narva dry-bank consumer', timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                  inputs={str(x): sha(x) for x in input_paths})
    try:
        assert sha(args.source) == EXPECTED_SOURCE_SHA, 'source hash mismatch'
        assert sha(args.candidate) == EXPECTED_CANDIDATE_SHA, 'candidate hash mismatch'
        assert sha(args.constraints) == EXPECTED_CONSTRAINTS_SHA, 'constraints hash mismatch'
        source = load_npz(args.source); candidate = load_npz(args.candidate); constraints = load_npz(args.constraints)
        prior = load_npz(args.prior_constraints); valley_masks = load_npz(args.valley_masks); terminal = load_npz(args.terminal)
        temporal_mask = temporal_controls(args.temporal_reference)
        assert np.array_equal(temporal_mask, terminal['controls']), 'temporal control points do not reconstruct terminal controls'
        p = np.load(plane_path, allow_pickle=False).astype(np.float64)
        visible = np.load(visible_path, allow_pickle=False).astype(np.float64)
        assert source['heights'].shape == candidate['heights'].shape == (N, N)
        assert p.shape == (N-1, N-1) and visible.shape == (N-1, N-1, 4)
        assert metadata_equal(source, candidate), 'metadata/terrain keys differ'
        required = {'fixed','allowed','wet_support','engineering_halo','cap','lower','bank_domain','narva','other_fixed'}
        assert required <= set(constraints), f'missing constraint keys {sorted(required-set(constraints))}'
        source_faces = wet_faces(source['heights'].astype(np.float64), p, visible)
        source_support = wet_support(source_faces)
        expected = expected_constraints(source, prior, valley_masks, terminal, temporal_mask, p, visible, source_support)
        gates, counts = evaluate(candidate['heights'], source, candidate, constraints, expected, p, visible, source_faces, source_support)
        # Frozen P/F must be copied exactly beside the candidate; hashes and bytes are both recorded.
        candidate_plane = args.candidate.parent/'plane.npy'; candidate_visible = args.candidate.parent/'visible-field.npy'
        gates['frozen_plane_exact'] = candidate_plane.exists() and sha(candidate_plane) == sha(plane_path)
        gates['frozen_visible_field_exact'] = candidate_visible.exists() and sha(candidate_visible) == sha(visible_path)
        angles = angles_and_sectors(source['heights'].astype(np.float64), candidate['heights'].astype(np.float64), source, expected)
        crease_counts = narva_and_wet_dry_counts(source['heights'].astype(np.float64), candidate['heights'].astype(np.float64), source, expected)
        roads = None
        sys.path.insert(0, str(Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/tools/terrain')))
        from verify_roads_v30 import evaluate as evaluate_roads
        roads = evaluate_roads(candidate['heights'].astype(np.float64), source['water'].astype(bool))
        gates['roads_pass'] = roads['status'] == 'PASS'
        controls_result = controls()
        identity_gates, _ = evaluate(source['heights'], source, source, constraints, expected, p, visible, source_faces, source_support)
        controls_result['source_identity_preserves_invariants'] = all(identity_gates.values())
        negatives = negative_controls(source['heights'].astype(np.float64), source, candidate, constraints, expected, p, visible, source_faces, source_support)
        gates['geometry_controls_pass'] = all(controls_result[k] for k in ('inclined_plane_zero_dihedral','known_45_degree_fold','source_identity_preserves_invariants'))
        gates['negative_controls_reject'] = all(negatives.get(k, False) for k in ('wet_vertex_rejected','engineering_vertex_rejected','below_floor_rejected','dry_spike_rejected'))
        gates.update(angles['gates'])
        gates.update(crease_counts['gates'])
        report.update(dict(status='PASS_EV79_CONSUMER' if all(gates.values()) else 'FAIL_EV79_CONSUMER',
            source_sha256=sha(args.source), candidate_sha256=sha(args.candidate), constraints_sha256=sha(args.constraints),
            source_plane_sha256=sha(plane_path), source_visible_sha256=sha(visible_path), gates=gates, counts=counts,
            transition=dict(cap_reconstruction='2 * quintic(EDT(allowed)*6/18)', cap_max=float(expected['cap'].max()), lower_formula='max(base-cap, min(base,1.8), min(base,max_incident(P,F,0.85)+1e-4))'),
                           bank_domain='cls==0 and distance<=96m from cls in {3,5,6} and (radius620 or t.narva)',
                           engineering_halo='3x3 dilation of reserve|platform',
                           fixed_reconstruction='water|beach|cls!=0|corridor|summits|border11|temporal controls|large_lake_banks|wet_support|engineering_halo',
                           removed_narva_terms='narva_old_guard and t.narva raster only',
                           candidate_edit_counts={'authoring_json':json.loads((build/'authoring.json').read_text(encoding='utf-8')).get('counts',{}),
                                                  'independent_constraints':{'bank_domain':int(expected['bank_domain'].sum()),'allowed':int(expected['allowed'].sum())}},
            angles=angles, crease_counts=crease_counts, roads=roads, controls=controls_result, negative_controls=negatives,
            runtime_seconds=round(time.time()-started, 3), limits=[
                'Offline geometry consumer only; no DayZ rendering, LOD, material, WRP/PBO or artistic acceptance.',
                'Bank/interior distribution uses all four unique vertices incident to each native dihedral edge; bank=class-0 dry vertices within 96m of classes 3/5/6; interior=other dry class-0 vertices, excluding reserve/platform.',
                'Localized fold records are high source dihedral cases, not proof that an image patch is the same feature or that it is artistically a pyramid.'
            ]))
    except Exception as exc:
        report.update(dict(status='ERROR_EV79_CONSUMER', error=repr(exc), runtime_seconds=round(time.time()-started, 3)))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('angles','roads')}, indent=2, allow_nan=False))
    if report['status'] not in ('PASS_EV79_CONSUMER',):
        raise SystemExit(1)

if __name__ == '__main__':
    main()






