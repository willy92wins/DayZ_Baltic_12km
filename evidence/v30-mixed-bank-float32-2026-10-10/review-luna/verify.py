#!/usr/bin/env python
"""EV81 independent source consumer plus EV80-deployed delta comparison; never imports author/generator."""
from __future__ import annotations
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(r'E:/DayZ-Baltic-Build')
EXPECTED_SOURCE_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
EXPECTED_EV79_CONSTRAINTS_SHA = 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
EXPECTED_CANDIDATE_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
EXPECTED_EV80_CANDIDATE_SHA = '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
EXPECTED_EV80_REPORT_SHA = '1f93c335d78d572de3a5c020c09d0cc397951cdb88b33f45ee1af144f3d0a60e'
EXPECTED_EV80_DEPLOY_SHA = 'ab2684801e2a951a69a1066cabc32fbec3e27a7b1560dc1819e5563932592503'
EXPECTED_EV80_DEPLOYED_PBO_SHA = 'ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038'
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
    cls=source['cls']; assert cls.shape==(N,N)
    rr,cc=np.indices((N,N))
    engineering=source['reserve'].astype(bool)|source['platform'].astype(bool)
    beach=source['beach'].astype(bool); corridor=valley_masks['corridor'].astype(bool); summits=valley_masks['summits'].astype(bool)
    border11=(rr<11)|(rr>=2037)|(cc<11)|(cc>=2037)
    controls=controls.astype(bool)
    other_fixed=source['water'].astype(bool)|beach|(cls!=0)|corridor|summits|border11|controls
    engineering_halo=binary_dilation(engineering,structure=np.ones((3,3),dtype=bool))
    large_lakes=prior['large_lake_banks'].astype(bool)
    fixed=other_fixed|large_lakes|wet|engineering_halo
    near=np.isin(cls,(3,5,6)); dist=distance_transform_edt(~near,sampling=6.0)
    bank_domain=(cls==0)&(dist<=96.0+1e-9)
    return dict(other_fixed=other_fixed,fixed=fixed,bank_domain=bank_domain,engineering=engineering,
       engineering_halo=engineering_halo,corridor=corridor,summits=summits,controls=controls,
       border11=border11,large_lakes=large_lakes,wet_support=wet)


def selector_from_source(allowed,h):
    touch=np.zeros((N,N),dtype=bool)
    for kind,angles in edge_angles(h):
        m=angles>30.0+TOL_DEG
        if kind=='diagonal':
            touch[:-1,:-1]|=m; touch[:-1,1:]|=m; touch[1:,:-1]|=m; touch[1:,1:]|=m
        elif kind=='vertical':
            touch[:-1,:-2]|=m; touch[:-1,1:-1]|=m; touch[1:,1:-1]|=m; touch[1:,2:]|=m
        else:
            touch[:-2,:-1]|=m; touch[1:-1,:-1]|=m; touch[1:-1,1:]|=m; touch[2:,1:]|=m
    return allowed&touch




def expected_constraints(source, prior, valley_masks, terminal, controls, p, visible, wet):
    masks=reconstruct(source,valley_masks,terminal,prior,controls,wet)
    allowed=masks['bank_domain']&~masks['fixed']
    selector=selector_from_source(allowed,source['heights'].astype(np.float64))
    base=source['heights'].astype(np.float64)
    lower=np.maximum(np.minimum(base,1.8),water_floor(base,p,visible))
    return dict(**masks,allowed=allowed,selector=selector,lower=lower)


def metadata_equal(src, cand):
    return set(src) == set(cand) and all(equal(src[k], cand[k]) for k in src if k != 'heights')




def evaluate(candidate_heights,source,candidate,constraints,expected,p,visible,source_wet_faces,source_wet_support):
    base=source['heights'].astype(np.float64); v=candidate_heights.astype(np.float64); changed=v!=base
    wet_v_faces=wet_faces(v,p,visible)
    wet_face_new=sum(int(np.count_nonzero(n&~o)) for n,o in zip(wet_v_faces,source_wet_faces))
    slopes0=face_slopes(base); slopes1=face_slopes(v); bad=0; max_excess=0.0; slope_summary={}
    for i,(a,b) in enumerate(zip(slopes0,slopes1)):
        delta=b-np.maximum(a,35.0); bad+=int(np.count_nonzero(delta>TOL_DEG))
        max_excess=max(max_excess,float(delta.max(initial=-np.inf)))
        slope_summary['triangle_'+str(i)]=dict(source_max=float(a.max()),candidate_max=float(b.max()),bad_faces=int(np.count_nonzero(delta>TOL_DEG)))
    gates=dict(
        finite_full_map=bool(np.isfinite(v).all()),metadata_exact=metadata_equal(source,candidate),
        fixed_exact=not bool((changed&expected['fixed']).any()),
        outside_selector_exact=not bool((changed&~expected['selector']).any()),
        wet_support_exact=not bool((changed&source_wet_support).any()),no_new_wet_faces=wet_face_new==0,
        engineering_halo_exact=not bool((changed&expected['engineering_halo']).any()),
        road_platform_exact=not bool((changed&expected['engineering']).any()),
        fixed_mask_matches_EV79=np.array_equal(constraints['fixed'],expected['fixed']),
        other_fixed_matches_EV79=np.array_equal(constraints['other_fixed'],expected['other_fixed']),
        wet_support_mask_matches_EV79=np.array_equal(constraints['wet_support'],source_wet_support),
        engineering_halo_matches_EV79=np.array_equal(constraints['engineering_halo'],expected['engineering_halo']),
        lower_floor=bool(np.all(v>=expected['lower']-TOL_HEIGHT)),
        height_budget_2m=bool(np.all(np.abs(v-base)<=2.0+TOL_HEIGHT)),
        native_face_slope_limit=bad==0)
    counts=dict(changed_vertices=int(changed.sum()),selector_vertices=int(expected['selector'].sum()),
        fixed_vertices=int(expected['fixed'].sum()),allowed_global_vertices=int(expected['allowed'].sum()),
        bank_domain_global_vertices=int(expected['bank_domain'].sum()),source_wet_support_vertices=int(source_wet_support.sum()),
        newly_wet_native_faces=wet_face_new,source_wet_native_faces=int(sum(x.sum() for x in source_wet_faces)),
        candidate_wet_native_faces=int(sum(x.sum() for x in wet_v_faces)),max_abs_delta_m=float(np.abs(v-base).max()),
        min_candidate_m=float(v.min()),min_lower_margin_m=float((v-expected['lower']).min()),
        max_slope_excess_degrees=max_excess,slope_faces=slope_summary,
        changed_outside_selector=int(np.count_nonzero(changed&~expected['selector'])))
    return gates,counts


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



def mixed_counts_and_anchors(base,cand,source,expected):
    cls=source['cls']; support=expected['wet_support']
    dist=distance_transform_edt(~np.isin(cls,(3,5,6)),sampling=6.0)
    dry=(cls==0)&~support&~source['water'].astype(bool)&~source['beach'].astype(bool)&~source['reserve'].astype(bool)&~source['platform'].astype(bool)
    bank=dry&(dist<=96.0+1e-9)
    focus=[]; a0=dict(edge_angles(base)); a1=dict(edge_angles(cand))
    for x,z in ((2196,1578),(5538,3918),(1140,1002)):
        r=int(np.floor((12282-z)/6)); c=int(np.floor(x/6))
        rlo=max(0,r-2); rhi=min(N-1,r+3); clo=max(0,c-2); chi=min(N-1,c+3)
        old=[]; new=[]
        for kind in a0:
            if kind=='diagonal': sl=np.s_[rlo:rhi,clo:chi]
            elif kind=='vertical': sl=np.s_[rlo:rhi,max(0,clo-1):min(N-2,chi)]
            else: sl=np.s_[max(0,rlo-1):min(N-2,rhi),clo:chi]
            old.append(a0[kind][sl].ravel()); new.append(a1[kind][sl].ravel())
        old=np.concatenate(old); new=np.concatenate(new)
        focus.append(dict(x_m=x,z_m=z,row=r,col=c,source_height_m=float(base[r,c]),candidate_height_m=float(cand[r,c]),
            changed=bool(base[r,c]!=cand[r,c]),selector=bool(expected['selector'][r,c]),fixed=bool(expected['fixed'][r,c]),
            wet_support=bool(support[r,c]),local_edge_count=int(old.size),local_energy_before=float(old@old),
            local_energy_after=float(new@new),local_energy_reduction=None if not float(old@old) else float(1-(new@new)/(old@old)),
            local_max_before=float(old.max()),local_max_after=float(new.max()),
            local_over30_before=int(np.count_nonzero(old>30)),local_over30_after=int(np.count_nonzero(new>30))))
    scenarios={}
    for label,h in (('source',base),('candidate',cand)):
        total=dict(bank_all4_edges=0,bank_all4_over30=0,bank_any_edges=0,bank_any_over30=0,
            mixed_any_edges=0,mixed_any_over30=0,bank_any_not_all4_over30=0)
        kinds={}
        for kind,a in edge_angles(h):
            allb=incident_all(bank,kind); anyb=incident_any(bank,kind); anyw=incident_any(support,kind)
            mixed=anyb&anyw; high=a>30.0
            row=dict(bank_all4_edges=int(allb.sum()),bank_all4_over30=int((allb&high).sum()),
                bank_any_edges=int(anyb.sum()),bank_any_over30=int((anyb&high).sum()),
                mixed_any_edges=int(mixed.sum()),mixed_any_over30=int((mixed&high).sum()),
                bank_any_not_all4_over30=int((anyb&~allb&high).sum()))
            kinds[kind]=row
            for k,v in row.items(): total[k]+=v
        scenarios[label]=dict(total=total,by_edge_kind=kinds)
    return dict(distributions=scenarios,focus_anchors=focus)


def compare_against_ev80(ev80_h, candidate_h, source, expected):
    """Compare EV81 with deployed EV80 on identical edge masks and domains."""
    delta = candidate_h != ev80_h
    before = dict(edge_angles(ev80_h))
    after = dict(edge_angles(candidate_h))
    energy_before = 0.0
    energy_after = 0.0
    energy_edges = 0
    new_over30 = 0
    for kind in before:
        incident = incident_any(delta, kind)
        a, b = before[kind], after[kind]
        energy_before += float(np.sum(a[incident] * a[incident], dtype=np.float64))
        energy_after += float(np.sum(b[incident] * b[incident], dtype=np.float64))
        energy_edges += int(incident.sum())
        new_over30 += int(np.count_nonzero((a <= 30.0 + TOL_DEG) & (b > 30.0 + TOL_DEG)))
    energy_reduction = None if energy_before <= 1e-18 else 1.0 - energy_after / energy_before

    cls = source['cls']
    support = expected['wet_support']
    dry = ((cls == 0) & ~support & ~(source['reserve'].astype(bool) | source['platform'].astype(bool)))
    dist = distance_transform_edt(~np.isin(cls, (3, 5, 6)), sampling=6.0)
    bank = dry & (dist <= 96.0 + 1e-9)
    interior = dry & ~bank
    distributions = {}
    distribution_gates = {}
    for name, mask in (('bank', bank), ('interior', interior)):
        old_parts = [before[k][incident_all(mask, k)] for k in before]
        new_parts = [after[k][incident_all(mask, k)] for k in after]
        old_summary, new_summary = summaries(old_parts), summaries(new_parts)
        distributions[name] = dict(ev80=old_summary, ev81=new_summary)
        distribution_gates[name] = (
            new_summary['n'] == old_summary['n'] and
            new_summary['p99'] <= old_summary['p99'] + TOL_DEG and
            new_summary['above30'] <= old_summary['above30'])

    # Sector maxima use the exact same edge set: every hinge incident to a
    # vertex whose EV81 height differs from EV80. Grouping is 64x64 native cells.
    sector_pairs = {}
    for kind in before:
        mask = incident_any(delta, kind)
        for r, c in np.argwhere(mask):
            key = (int(r) // 64, int(c) // 64)
            rec = sector_pairs.setdefault(key, dict(edges=0, ev80_max=0.0, ev81_max=0.0))
            rec['edges'] += 1
            rec['ev80_max'] = max(rec['ev80_max'], float(before[kind][r, c]))
            rec['ev81_max'] = max(rec['ev81_max'], float(after[kind][r, c]))
    sectors = []
    for (row, col), rec in sorted(sector_pairs.items()):
        rec.update(row=row, col=col, max_increase_deg=rec['ev81_max'] - rec['ev80_max'],
                   no_max_regression=rec['ev81_max'] <= rec['ev80_max'] + TOL_DEG)
        sectors.append(rec)
    energy_gate = energy_reduction is not None and energy_reduction >= 0.05
    return dict(
        changed_vertices_vs_ev80=int(delta.sum()),
        changed_incident=dict(edges=energy_edges, ev80_sum_sq=energy_before,
                              ev81_sum_sq=energy_after, reduction=energy_reduction,
                              reduction_ge_5pct=energy_gate),
        zero_new_over30=dict(count=new_over30, tolerance_degrees=TOL_DEG, pass_gate=new_over30 == 0),
        mixed_count_threshold=dict(limit_exclusive=3384),
        distributions=distributions,
        distribution_gates=dict(bank_p99_and_count_nonworse=distribution_gates['bank'],
                                interior_p99_and_count_nonworse=distribution_gates['interior']),
        sectors=sectors,
        sector_maxima_nonworse=all(q['no_max_regression'] for q in sectors),
    )


def audit_fallback_fixtures(path):
    """Check the recorded ULP fixtures and independently recompute float32 steps."""
    fixture = json.loads(path.read_text(encoding='utf-8'))
    policy = fixture.get('fallback_policy_fixture', {})
    required = ('already_valid_uses_original', 'one_ulp_boundary_rescues',
                'true_limit_failure_rejected_at_two_ulp', 'benefit_floor_failure_not_bypassed')
    assertions = {k: policy.get(k) is True for k in required}
    try:
        current = np.float32(policy['one_ulp_inside_limit'])
        proposal = np.float32(policy['original_proposal'])
        tol = float(policy['strict_tolerance_deg'])
        steps = [proposal]
        for _ in range(2):
            steps.append(np.nextafter(steps[-1], current, dtype=np.float32))
        one_boundary = float(steps[0]) > float(current) + tol and float(steps[1]) <= float(current) + tol
        hard_limit = float(current) - 1e-6 + tol
        real_failure = float(steps[2]) > hard_limit
        mechanics = dict(one_ulp_rescues=one_boundary, two_ulp_cannot_reach_hard_limit=real_failure,
                         float32_steps=[float(x) for x in steps], hard_limit=hard_limit,
                         selected_one_ulp_equals_boundary=float(steps[1]) == float(current))
    except Exception as exc:
        mechanics = dict(error=repr(exc))
    assertions['reported_status_pass'] = fixture.get('status') == 'PASS'
    assertions['one_ulp_fixture_numerically_reproduced'] = mechanics.get('one_ulp_rescues') is True
    assertions['two_ulp_true_failure_numerically_reproduced'] = mechanics.get('two_ulp_cannot_reach_hard_limit') is True
    return dict(status=all(assertions.values()), assertions=assertions, fixture=fixture,
                independent_float32_mechanics=mechanics)


def audit_node_trace(authoring, source_h, candidate_h, selector, source_sha, candidate_sha,
                     constraints_sha, plane_sha, visible_sha):
    """Validate per-node proposal/ULP trace without importing the author."""
    checks = {
        'status_pending_consumer': authoring.get('status') == 'CANDIDATE_AUTHORED_PENDING_INDEPENDENT_CONSUMER',
        'source_identity': authoring.get('source_sha256') == source_sha,
        'candidate_identity': authoring.get('candidate_sha256') == candidate_sha,
        'constraints_identity': authoring.get('constraints_sha256') == constraints_sha,
        'plane_identity': authoring.get('plane_sha256') == plane_sha,
        'visible_identity': authoring.get('visible_field_sha256') == visible_sha,
        'selector_count_matches': authoring.get('selector', {}).get('selector_vertices') == int(selector.sum()),
        'all_selector_nodes_logged_once': False,
        'attempts_obey_float32_nextafter': False,
        'accepted_values_match_candidate': False,
        'no_accepted_log_entry_for_unchanged_or_rejected_node': False,
        'complete_run_under_180_seconds': False,
    }
    decisions = authoring.get('node_decisions', [])
    coords = [(int(q.get('row', -1)), int(q.get('col', -1))) for q in decisions]
    expected_coords = set(map(tuple, np.argwhere(selector).tolist()))
    checks['all_selector_nodes_logged_once'] = len(coords) == len(set(coords)) and set(coords) == expected_coords
    sequential = True
    accepted = set()
    for q in decisions:
        r, c = int(q['row']), int(q['col'])
        proposal = q.get('proposal_float32')
        attempts = q.get('attempts', [])
        selected = q.get('selected_ulp')
        if proposal is None:
            if attempts or selected is not None or candidate_h[r, c] != source_h[r, c]:
                sequential = False
            continue
        v = np.float32(proposal)
        if not attempts or attempts[0].get('ulps') != 0 or float(np.float32(attempts[0].get('value'))) != float(v):
            sequential = False
            continue
        if len(attempts) > 3:
            sequential = False
            continue
        for i, attempt in enumerate(attempts):
            if attempt.get('ulps') != i or float(np.float32(attempt.get('value'))) != float(v):
                sequential = False
            if i < len(attempts) - 1:
                if not attempt.get('failures'):
                    sequential = False
                v = np.nextafter(v, np.float32(source_h[r, c]), dtype=np.float32)
        if selected is None:
            if len(attempts) != 3 or any(not a.get('failures') for a in attempts):
                sequential = False
            if candidate_h[r, c] != source_h[r, c]:
                sequential = False
        else:
            if selected not in (0, 1, 2) or len(attempts) != selected + 1:
                sequential = False
            elif attempts[-1].get('failures') or float(candidate_h[r, c]) != float(np.float32(attempts[-1]['value'])):
                sequential = False
            else:
                accepted.add((r, c))
    checks['attempts_obey_float32_nextafter'] = sequential
    changed_coords = set(map(tuple, np.argwhere(candidate_h != source_h).tolist()))
    checks['accepted_values_match_candidate'] = changed_coords == accepted
    checks['no_accepted_log_entry_for_unchanged_or_rejected_node'] = changed_coords <= expected_coords and accepted <= expected_coords
    method = authoring.get('method', {})
    checks['complete_run_under_180_seconds'] = (
        method.get('max_seconds', float('inf')) <= 180.0 and
        method.get('elapsed_seconds', float('inf')) <= 180.0 and
        authoring.get('counts', {}).get('node_decision_count') == len(decisions))
    return dict(status=all(checks.values()), checks=checks,
                decision_count=len(decisions), accepted_trace_count=len(accepted),
                candidate_changed_count=len(changed_coords),
                fallback_counts=authoring.get('counts', {}).get('fallback_counts'))


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



def negative_controls(base,source,candidate,constraints,expected,p,visible,wet_faces0,wet_support):
    basev=candidate['heights'].astype(np.float32,copy=True); results={}
    choices=[('wet_vertex',wet_support,0.01),('engineering_vertex',expected['engineering'],0.01)]
    for name,mask,amount in choices:
        if mask.any():
            r,c=map(int,np.argwhere(mask)[len(np.argwhere(mask))//2])
            mutant=basev.copy(); mutant[r,c]+=amount
            gates,_=evaluate(mutant,source,candidate,constraints,expected,p,visible,wet_faces0,wet_support)
            target='wet_support_exact' if name=='wet_vertex' else 'road_platform_exact'
            results[name+'_rejected']=not gates[target]; results[name+'_triggered_gate']=target
        else:
            results[name+'_rejected']=False; results[name+'_reason']='empty mask'
    if expected['selector'].any():
        points=np.argwhere(expected['selector']); r,c=map(int,points[len(points)//2])
        mutant=basev.copy(); mutant[r,c]=np.float32(expected['lower'][r,c]-0.01)
        gates,_=evaluate(mutant,source,candidate,constraints,expected,p,visible,wet_faces0,wet_support)
        results['below_floor_rejected']=not gates['lower_floor']
        r,c=map(int,points[min(len(points)-1,len(points)//3)])
        mutant=basev.copy(); mutant[r,c]=np.float32(base[r,c]+10.0)
        gates,_=evaluate(mutant,source,candidate,constraints,expected,p,visible,wet_faces0,wet_support)
        results['dry_spike_rejected']=(not gates['height_budget_2m']) and (not gates['native_face_slope_limit'])
        results['dry_spike_triggered']=dict(height_budget=not gates['height_budget_2m'],slope=not gates['native_face_slope_limit'])
    else:
        results['below_floor_rejected']=False; results['dry_spike_rejected']=False
        results['reason']='empty selector'
    return results


def temporal_controls(reference_path):
    record = json.loads(reference_path.read_text(encoding='utf-8'))
    controls = np.zeros((N, N), dtype=bool)
    for q in record['points']:
        r = int(np.floor((12282.0-q['z'])/6.0)); c = int(np.floor(q['x']/6.0))
        controls[max(0,r):min(N,r+2), max(0,c):min(N,c+2)] = True
    return controls


def verify_ev80_deployed_reference(ev80_build):
    deploy_path = ev80_build / 'deploy.json'
    report_path = ev80_build / 'review-luna/report.json'
    terrain_path = ev80_build / 'candidate/terrain.npz'
    deploy = json.loads(deploy_path.read_text(encoding='utf-8'))
    report = json.loads(report_path.read_text(encoding='utf-8'))
    checks = {
        'ev80_report_sha_exact': sha(report_path) == EXPECTED_EV80_REPORT_SHA,
        'ev80_deploy_manifest_sha_exact': sha(deploy_path) == EXPECTED_EV80_DEPLOY_SHA,
        'ev80_consumer_pass': report.get('status') == 'PASS_EV80_CONSUMER' and all(report.get('gates', {}).values()),
        'ev80_candidate_sha_exact': sha(terrain_path) == EXPECTED_EV80_CANDIDATE_SHA == deploy.get('terrain_sha256'),
        'ev80_deploy_status': deploy.get('status') == 'DEPLOYED_EV80_PREVIEW_NATIVE_READBACK_PENDING',
    }
    addons = Path(deploy.get('mod', '')) / 'Addons'
    world_path = addons / 'narva_trial.pbo'
    water_path = addons / 'baltic_water_v30.pbo'
    checks['ev80_world_deployed_sha_exact'] = world_path.is_file() and sha(world_path) == EXPECTED_EV80_DEPLOYED_PBO_SHA == deploy.get('files', {}).get('narva_trial.pbo')
    checks['ev80_water_deployed_sha_exact'] = water_path.is_file() and sha(water_path) == deploy.get('files', {}).get('baltic_water_v30.pbo')
    pbo_entries = {}
    try:
        sys.path.insert(0, str(Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/playtest')))
        from attach_navmesh import read_pbo
        _, _, pbo_entries = read_pbo(world_path)
        wrp = pbo_entries['baltic_trial.wrp']
        checks['ev80_deployed_oprw_payload_exact'] = wrp.startswith(b'OPRW') and hashlib.sha256(wrp).hexdigest() == deploy.get('compiled_wrp_sha256')
        checks['ev80_deployed_entry_count'] = len(pbo_entries) == deploy.get('total_entries') == 6827
    except Exception as exc:
        checks['ev80_deployed_oprw_payload_exact'] = False
        checks['ev80_deployed_entry_count'] = False
        checks['ev80_pbo_read_error'] = repr(exc)
    return dict(status=all(v for k, v in checks.items() if k != 'ev80_pbo_read_error'),
                checks=checks, world_path=str(world_path),
                world_sha256=sha(world_path) if world_path.is_file() else None,
                water_sha256=sha(water_path) if water_path.is_file() else None,
                pbo_entries=len(pbo_entries),
                deployed_wrp_sha256=hashlib.sha256(pbo_entries.get('baltic_trial.wrp', b'')).hexdigest() if pbo_entries else None)


def main():
    ap=argparse.ArgumentParser(); build=ROOT/'v30-mixed-bank-float32-20261010'
    ev80_build=ROOT/'v30-mixed-bank-constrained-20261010'
    ap.add_argument('--candidate',type=Path,default=build/'candidate/terrain.npz')
    ap.add_argument('--constraints',type=Path,default=ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz')
    ap.add_argument('--source',type=Path,default=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/terrain.npz')
    ap.add_argument('--authoring',type=Path,default=build/'authoring.json')
    ap.add_argument('--fixtures',type=Path,default=build/'ev81-fixture-test.json')
    ap.add_argument('--ev80-candidate',type=Path,default=ev80_build/'candidate/terrain.npz')
    ap.add_argument('--ev80-report',type=Path,default=ev80_build/'review-luna/report.json')
    ap.add_argument('--ev80-deploy',type=Path,default=ev80_build/'deploy.json')
    ap.add_argument('--prior-constraints',type=Path,default=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz')
    ap.add_argument('--valley-masks',type=Path,default=ROOT/'v30-valley-smoothing-20261008/candidate-a/masks.npz')
    ap.add_argument('--terminal',type=Path,default=ROOT/'v30-native-terminal-finish-20261009/constraints.npz')
    ap.add_argument('--temporal-reference',type=Path,default=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-global-contour-pass-2026-10-09/global-contour-temporal-reference.json'))
    ap.add_argument('--plane',type=Path,default=None); ap.add_argument('--visible-field',type=Path,default=None)
    ap.add_argument('--expected-candidate-sha',required=True); ap.add_argument('--expected-constraints-sha',default=EXPECTED_EV79_CONSTRAINTS_SHA)
    ap.add_argument('--report',type=Path,default=Path(__file__).with_name('report.json'))
    args=ap.parse_args(); started=time.time()
    plane_path=args.plane or args.source.parent/'plane.npy'; visible_path=args.visible_field or args.source.parent/'visible-field.npy'
    input_paths=(args.source,args.candidate,args.constraints,plane_path,visible_path,args.prior_constraints,args.valley_masks,args.terminal,args.temporal_reference,build/'plan.md',args.authoring,args.fixtures,args.ev80_candidate,args.ev80_report,args.ev80_deploy,Path(__file__))
    report=dict(status='FAIL',verifier='EV81 independent EV79 consumer plus deployed EV80 comparison',timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        inputs={str(x):sha(x) for x in input_paths if x.exists()})
    try:
        assert sha(args.source)==EXPECTED_SOURCE_SHA,'source EV79 hash mismatch'
        assert sha(args.candidate)==args.expected_candidate_sha,'candidate hash mismatch'
        assert sha(args.constraints)==args.expected_constraints_sha,'constraints hash mismatch'
        assert sha(args.ev80_candidate)==EXPECTED_EV80_CANDIDATE_SHA,'EV80 baseline candidate identity mismatch'
        assert sha(args.ev80_report)==EXPECTED_EV80_REPORT_SHA,'EV80 baseline report identity mismatch'
        assert sha(args.ev80_deploy)==EXPECTED_EV80_DEPLOY_SHA,'EV80 deployment manifest identity mismatch'
        source=load_npz(args.source); candidate=load_npz(args.candidate); constraints=load_npz(args.constraints); ev80=load_npz(args.ev80_candidate)
        prior=load_npz(args.prior_constraints); valley_masks=load_npz(args.valley_masks); terminal=load_npz(args.terminal)
        controls_mask=temporal_controls(args.temporal_reference)
        assert np.array_equal(controls_mask,terminal['controls']),'temporal controls do not reconstruct terminal mask'
        p=np.load(plane_path,allow_pickle=False).astype(np.float64); visible=np.load(visible_path,allow_pickle=False).astype(np.float64)
        assert source['heights'].shape==candidate['heights'].shape==ev80['heights'].shape==(N,N) and p.shape==(N-1,N-1) and visible.shape==(N-1,N-1,4)
        assert metadata_equal(source,candidate),'source/candidate metadata differ'
        assert metadata_equal(source,ev80),'EV80 baseline metadata differ from EV79 source'
        required={'fixed','wet_support','engineering_halo','other_fixed'}
        assert required<=set(constraints),f'missing constraint keys {sorted(required-set(constraints))}'
        h0=source['heights'].astype(np.float64); wet0=wet_faces(h0,p,visible); support=wet_support(wet0)
        expected=expected_constraints(source,prior,valley_masks,terminal,controls_mask,p,visible,support)
        gates,counts=evaluate(candidate['heights'],source,candidate,constraints,expected,p,visible,wet0,support)
        changed=candidate['heights']!=source['heights']
        gates['outside_selector_exact']=not bool((changed&~expected['selector']).any())
        gates['author_selector_matches_independent']=('selector' not in constraints) or np.array_equal(constraints['selector'],expected['selector'])
        cp=args.candidate.parent/'plane.npy'; cv=args.candidate.parent/'visible-field.npy'
        gates['frozen_plane_exact']=cp.exists() and sha(cp)==sha(plane_path)
        gates['frozen_visible_field_exact']=cv.exists() and sha(cv)==sha(visible_path)
        ev80_plane=args.ev80_candidate.parent/'plane.npy'; ev80_visible=args.ev80_candidate.parent/'visible-field.npy'
        gates['P_identical_to_EV79_and_EV80']=ev80_plane.exists() and cp.exists() and sha(cp)==sha(plane_path)==sha(ev80_plane)
        gates['F_identical_to_EV79_and_EV80']=ev80_visible.exists() and cv.exists() and sha(cv)==sha(visible_path)==sha(ev80_visible)
        angles=angles_and_sectors(h0,candidate['heights'].astype(np.float64),source,expected)
        mixed=mixed_counts_and_anchors(h0,candidate['heights'].astype(np.float64),source,expected)
        ev80_comparison=compare_against_ev80(ev80['heights'].astype(np.float64),candidate['heights'].astype(np.float64),source,expected)
        ev80_deploy_check=verify_ev80_deployed_reference(args.ev80_candidate.parent.parent)
        sys.path.insert(0,str(Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/tools/terrain')))
        from verify_roads_v30 import evaluate as evaluate_roads
        roads=evaluate_roads(candidate['heights'].astype(np.float64),source['water'].astype(bool)); gates['roads_pass']=roads['status']=='PASS'
        identity,_=evaluate(h0,source,source,constraints,expected,p,visible,wet0,support)
        ctrl=controls(); ctrl['source_identity_preserves_invariants']=all(identity.values())
        negative=negative_controls(h0,source,candidate,constraints,expected,p,visible,wet0,support)
        gates['geometry_controls_pass']=all(ctrl[k] for k in ('inclined_plane_zero_dihedral','known_45_degree_fold','source_identity_preserves_invariants'))
        gates['negative_controls_reject']=all(negative.get(k,False) for k in ('wet_vertex_rejected','engineering_vertex_rejected','below_floor_rejected','dry_spike_rejected'))
        gates.update(angles['gates'])
        mixed_count=mixed['distributions']['candidate']['total']['mixed_any_over30']
        gates['mixed_any_over30_below_3384']=mixed_count < 3384
        gates['energy_incident_delta_vs_EV80_ge_5pct']=ev80_comparison['changed_incident']['reduction_ge_5pct']
        gates['zero_new_edges_over30_vs_EV80']=ev80_comparison['zero_new_over30']['pass_gate']
        gates['bank_p99_and_over30_nonworse_vs_EV80']=ev80_comparison['distribution_gates']['bank_p99_and_count_nonworse']
        gates['interior_p99_and_over30_nonworse_vs_EV80']=ev80_comparison['distribution_gates']['interior_p99_and_count_nonworse']
        gates['modified_sector_maxima_nonworse_vs_EV80']=ev80_comparison['sector_maxima_nonworse']
        gates['EV80_deployed_identity_exact']=ev80_deploy_check['status']
        fixtures=audit_fallback_fixtures(args.fixtures)
        authoring=json.loads(args.authoring.read_text(encoding='utf-8'))
        trace=audit_node_trace(authoring,h0,candidate['heights'],expected['selector'],
                               sha(args.source),sha(args.candidate),sha(args.constraints),
                               sha(plane_path),sha(visible_path))
        gates['float32_fallback_fixtures_pass']=fixtures['status']
        gates['author_node_trace_complete_and_consistent']=trace['status']
        report.update(dict(status='PASS_EV81_CONSUMER' if all(gates.values()) else 'FAIL_EV81_CONSUMER',
            source_sha256=sha(args.source),candidate_sha256=sha(args.candidate),constraints_sha256=sha(args.constraints),
            source_plane_sha256=sha(plane_path),source_visible_sha256=sha(visible_path),
            ev80_candidate_sha256=sha(args.ev80_candidate),ev80_deployed=ev80_deploy_check,
            authoring_trace=trace,float32_fixtures=fixtures,ev80_comparison=ev80_comparison,
            gates=gates,counts=counts,
            selector_audit=dict(scope='EV79 class0 within 96m of cls3/5/6, outside semantic fixed, incident to source native dihedral >30 degrees',
                narva_not_a_fixed_or_scope_term=True,selector_vertices=int(expected['selector'].sum()),
                fixed_formula='water|beach|cls!=0|corridor|summits|border11|temporal controls|large_lake_banks|wet_support|3x3(reserve|platform)',
                height_budget='source height +/- 2m inside independently reconstructed selector',
                lower_formula='max(min(base,1.8),min(base,max_incident(P,F,0.85)+1e-4))'),
            angles=angles,mixed_edge_counts_and_focuses=mixed,roads=roads,controls=ctrl,negative_controls=negative,
            runtime_seconds=round(time.time()-started,3),limits=[
                'Offline geometry consumer only; no motor/render/material acceptance.',
                'bank p99/over30 gates exactly preserve EV79 distribution semantics; the dry-bank/mixed-any census is reported separately.',
                'Three focus anchors are local diagnostics, not artistic classification.',
                'EV79/EV80 native passes are provenance only; this consumer is offline geometry, not EV81 motor/render/material acceptance.']))
    except Exception as exc:
        report.update(dict(status='ERROR_EV81_CONSUMER',error=repr(exc),runtime_seconds=round(time.time()-started,3)))
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('angles','roads')},indent=2,allow_nan=False))
    if report['status']!='PASS_EV81_CONSUMER' or not all(report.get('gates',{}).values()): raise SystemExit(1)

if __name__=='__main__': main()
