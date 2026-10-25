#!/usr/bin/env python
"""EV80 independent global selector consumer; never imports author/generator."""
from __future__ import annotations
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(r'E:/DayZ-Baltic-Build')
EXPECTED_SOURCE_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
EXPECTED_EV79_CONSTRAINTS_SHA = 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
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



def main():
    ap=argparse.ArgumentParser(); build=ROOT/'v30-mixed-bank-constrained-20261010'
    ap.add_argument('--candidate',type=Path,default=build/'candidate/terrain.npz')
    ap.add_argument('--constraints',type=Path,default=ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz')
    ap.add_argument('--source',type=Path,default=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/terrain.npz')
    ap.add_argument('--prior-constraints',type=Path,default=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz')
    ap.add_argument('--valley-masks',type=Path,default=ROOT/'v30-valley-smoothing-20261008/candidate-a/masks.npz')
    ap.add_argument('--terminal',type=Path,default=ROOT/'v30-native-terminal-finish-20261009/constraints.npz')
    ap.add_argument('--temporal-reference',type=Path,default=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-global-contour-pass-2026-10-09/global-contour-temporal-reference.json'))
    ap.add_argument('--plane',type=Path,default=None); ap.add_argument('--visible-field',type=Path,default=None)
    ap.add_argument('--expected-candidate-sha',required=True); ap.add_argument('--expected-constraints-sha',default=EXPECTED_EV79_CONSTRAINTS_SHA)
    ap.add_argument('--report',type=Path,default=Path(__file__).with_name('report.json'))
    args=ap.parse_args(); started=time.time()
    plane_path=args.plane or args.source.parent/'plane.npy'; visible_path=args.visible_field or args.source.parent/'visible-field.npy'
    input_paths=(args.source,args.candidate,args.constraints,plane_path,visible_path,args.prior_constraints,args.valley_masks,args.terminal,args.temporal_reference,build/'plan.md',Path(__file__))
    report=dict(status='FAIL',verifier='EV80 independent global selector consumer',timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        inputs={str(x):sha(x) for x in input_paths if x.exists()})
    try:
        assert sha(args.source)==EXPECTED_SOURCE_SHA,'source EV79 hash mismatch'
        assert sha(args.candidate)==args.expected_candidate_sha,'candidate hash mismatch'
        assert sha(args.constraints)==args.expected_constraints_sha,'constraints hash mismatch'
        source=load_npz(args.source); candidate=load_npz(args.candidate); constraints=load_npz(args.constraints)
        prior=load_npz(args.prior_constraints); valley_masks=load_npz(args.valley_masks); terminal=load_npz(args.terminal)
        controls_mask=temporal_controls(args.temporal_reference)
        assert np.array_equal(controls_mask,terminal['controls']),'temporal controls do not reconstruct terminal mask'
        p=np.load(plane_path,allow_pickle=False).astype(np.float64); visible=np.load(visible_path,allow_pickle=False).astype(np.float64)
        assert source['heights'].shape==candidate['heights'].shape==(N,N) and p.shape==(N-1,N-1) and visible.shape==(N-1,N-1,4)
        assert metadata_equal(source,candidate),'source/candidate metadata differ'
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
        angles=angles_and_sectors(h0,candidate['heights'].astype(np.float64),source,expected)
        mixed=mixed_counts_and_anchors(h0,candidate['heights'].astype(np.float64),source,expected)
        sys.path.insert(0,str(Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/tools/terrain')))
        from verify_roads_v30 import evaluate as evaluate_roads
        roads=evaluate_roads(candidate['heights'].astype(np.float64),source['water'].astype(bool)); gates['roads_pass']=roads['status']=='PASS'
        identity,_=evaluate(h0,source,source,constraints,expected,p,visible,wet0,support)
        ctrl=controls(); ctrl['source_identity_preserves_invariants']=all(identity.values())
        negative=negative_controls(h0,source,candidate,constraints,expected,p,visible,wet0,support)
        gates['geometry_controls_pass']=all(ctrl[k] for k in ('inclined_plane_zero_dihedral','known_45_degree_fold','source_identity_preserves_invariants'))
        gates['negative_controls_reject']=all(negative.get(k,False) for k in ('wet_vertex_rejected','engineering_vertex_rejected','below_floor_rejected','dry_spike_rejected'))
        gates.update(angles['gates'])
        report.update(dict(status='PASS_EV80_CONSUMER' if all(gates.values()) else 'FAIL_EV80_CONSUMER',
            source_sha256=sha(args.source),candidate_sha256=sha(args.candidate),constraints_sha256=sha(args.constraints),
            source_plane_sha256=sha(plane_path),source_visible_sha256=sha(visible_path),gates=gates,counts=counts,
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
                'EV79 motor PASS is provenance only and does not validate EV80.']))
    except Exception as exc:
        report.update(dict(status='ERROR_EV80_CONSUMER',error=repr(exc),runtime_seconds=round(time.time()-started,3)))
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('angles','roads')},indent=2,allow_nan=False))
    if report['status']!='PASS_EV80_CONSUMER' or not all(report.get('gates',{}).values()): raise SystemExit(1)

if __name__=='__main__': main()
