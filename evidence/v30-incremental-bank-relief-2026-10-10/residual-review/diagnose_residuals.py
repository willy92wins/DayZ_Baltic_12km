from pathlib import Path
import sys, json, hashlib, importlib.util
import numpy as np
from scipy.ndimage import distance_transform_edt
import matplotlib.pyplot as plt

B = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010')
OUT = B / 'residual-review'
EV79 = Path(r'E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010')
EV80 = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010')
SRC, REF, CAND = (EV79 / 'candidate/terrain.npz', EV80 / 'candidate/terrain.npz', B / 'candidate/terrain.npz')
EXPECTED = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EV80_SHA = '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

assert sha(CAND) == EXPECTED and sha(REF) == EV80_SHA
authoring = json.loads((B / 'authoring.json').read_text(encoding='utf-8'))
consumer_report = json.loads((B / 'review-luna/report.json').read_text(encoding='utf-8'))
ev80_report = json.loads((EV80 / 'review-luna/report.json').read_text(encoding='utf-8'))
assert consumer_report.get('status') == 'PASS_EV82_CONSUMER'
assert consumer_report.get('candidate_sha256') == EXPECTED and all(consumer_report.get('gates', {}).values())
spec = importlib.util.spec_from_file_location('ev82_author', B / 'author.py')
author = importlib.util.module_from_spec(spec); spec.loader.exec_module(author)
sys.path.insert(0, str(B / 'review-luna'))
import verify as consumer

source, ev80, candidate = np.load(SRC), np.load(REF), np.load(CAND)
h79 = source['heights'].astype(np.float64)
h80 = ev80['heights'].astype(np.float64)
h82 = candidate['heights'].astype(np.float64)
cls = source['cls']
con = np.load(EV79 / 'constraints.npz')
wet = con['wet_support'].astype(bool); fixed = con['fixed'].astype(bool)
flow = np.isin(cls, (3, 5, 6))
distance = distance_transform_edt(~flow, sampling=6.0)
bank = ((cls == 0) & ~wet & ~source['water'] & ~source['beach'] & ~source['reserve'] &
        ~source['platform'] & (distance <= 96.0 + 1e-9))
domain = (cls == 0) & (distance <= 96.0 + 1e-9) & ~fixed
selector = domain & author.source_fold_nodes(h79)
assert int(selector.sum()) == authoring['selector']['selector_nodes_processed'] == 4329
changed = h82 != h80
decisions = {(int(q['row']), int(q['col'])): q for q in authoring['node_decisions']}
assert len(decisions) == 4329
plane = np.load(EV79 / 'candidate/plane.npy', mmap_mode='r')
visible = np.load(EV79 / 'candidate/visible-field.npy', mmap_mode='r')
assert sha(EV79 / 'candidate/plane.npy') == sha(EV80 / 'candidate/plane.npy') == sha(B / 'candidate/plane.npy')
assert sha(EV79 / 'candidate/visible-field.npy') == sha(EV80 / 'candidate/visible-field.npy') == sha(B / 'candidate/visible-field.npy')
water_floor = author.incident_water_floor(h79, plane, visible)
lower = np.maximum.reduce((h79 - 2.0, water_floor, np.minimum(h79, 1.8)))
cap = h79 + 2.0
assert np.all(h82[selector] >= lower[selector] - 1e-6)
assert np.all(h82[selector] <= cap[selector] + 1e-6)
up = np.maximum(0.0, cap - h82); down = np.maximum(0.0, h82 - lower)

def corners(kind, r, c):
    if kind == 'diagonal': return ((r,c),(r,c+1),(r+1,c),(r+1,c+1))
    if kind == 'vertical': return ((r,c),(r,c+1),(r+1,c+1),(r+1,c+2))
    return ((r,c),(r+1,c),(r+1,c+1),(r+2,c+1))

def center(kind, r, c):
    if kind == 'diagonal': return 6*c+3, 12282-6*r-3
    if kind == 'vertical': return 6*(c+1), 12282-6*r-3
    return 6*c+3, 12282-6*(r+1)

def peak_prominence(rc):
    best = (-1e9, None)
    for r,c in rc:
        ring = [h82[r+dr,c+dc] for dr,dc in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))]
        value = float(h82[r,c] - np.median(ring))
        if value > best[0]: best = (value, (r,c))
    return best

edges80 = dict(consumer.edge_angles(h80)); edges82 = dict(consumer.edge_angles(h82))
records=[]; by_kind={}
for kind, a82 in edges82.items():
    a80 = edges80[kind]
    mixed = consumer.incident_any(bank,kind) & consumer.incident_any(wet,kind)
    residual = mixed & (a82 > 30.0)
    before = mixed & (a80 > 30.0)
    rr,cc = np.where(residual)
    by_kind[kind] = {'ev80_over30':int(before.sum()), 'ev82b_over30':int(len(rr)),
                     'reduced':int(before.sum()-len(rr)),
                     'max_ev80_deg':float(a80[mixed].max()) if mixed.any() else None,
                     'max_ev82b_deg':float(a82[mixed].max()) if mixed.any() else None}
    for r,c in zip(rr.tolist(),cc.tolist()):
        rc = corners(kind,r,c); is_sel=[bool(selector[q]) for q in rc]; is_changed=[bool(changed[q]) for q in rc]
        reasons=sorted({decisions[q]['decision_reason'] for q,on in zip(rc,is_sel) if on})
        x,z=center(kind,r,c); prom,prom_rc=peak_prominence(rc)
        bank_rc=[q for q in rc if bank[q]]
        blockers={'fixed':sum(bool(fixed[q]) for q in bank_rc),
          'wet_support':sum(bool(wet[q]) for q in bank_rc),
          'engineering_halo':sum(bool(con['engineering_halo'][q]) for q in bank_rc),
          'narva':sum(bool(con['narva'][q]) for q in bank_rc),
          'other_fixed':sum(bool(con['other_fixed'][q]) for q in bank_rc)}
        hv82=[float(h82[q]) for q in rc]
        records.append({'kind':kind,'edge_row':r,'edge_col':c,'x_m':x,'z_m':z,
          'angle_ev80_deg':float(a80[r,c]),'angle_ev82b_deg':float(a82[r,c]),
          'angle_reduction_deg':float(a80[r,c]-a82[r,c]),'height_range_b_m':max(hv82)-min(hv82),
          'selector_corners':sum(is_sel),'changed_selector_corners':sum(s and d for s,d in zip(is_sel,is_changed)),
          'unchanged_selector_corners':sum(s and not d for s,d in zip(is_sel,is_changed)),
          'decision_reasons':reasons,'bank_corner_count':len(bank_rc),'fixed_mask_hits_nonexclusive':blockers,
          'peak_prominence_m':prom,'prominence_vertex_rc':list(prom_rc) if prom_rc else None,
          'corner_heights_ev80_m':[float(h80[q]) for q in rc],'corner_heights_b_m':hv82,
          'corner_rc':[list(q) for q in rc]})

states={'no_selector_corner':0,'selector_unchanged_only':0,'selector_changed_only':0,'selector_changed_and_unchanged':0}
for e in records:
    n=e['selector_corners']; c=e['changed_selector_corners']; u=e['unchanged_selector_corners']
    key='no_selector_corner' if not n else ('selector_changed_and_unchanged' if c and u else ('selector_changed_only' if c else 'selector_unchanged_only'))
    states[key]+=1
reason_hits={}
for e in records:
    for reason in e['decision_reasons']: reason_hits[reason]=reason_hits.get(reason,0)+1
residual_nodes={tuple(q) for e in records for q in e['corner_rc'] if selector[tuple(q)]}
upv=np.array([up[q] for q in residual_nodes]); downv=np.array([down[q] for q in residual_nodes])
def pct(a): return np.percentile(a,[0,25,50,75,95,100]).astype(float).tolist() if len(a) else []

# A pyramid-like focus requires several steep faces converging at a dry vertex,
# a positive local peak over its eight neighbors, and at least one residual
# mixed wet/bank hinge incident to that vertex.
slope_a, slope_b = consumer.face_slopes(h82)
steep_a, steep_b = slope_a > 30.0, slope_b > 30.0
face_hits = np.zeros(cls.shape, dtype=np.uint8)
face_hits[:-1,:-1] += steep_a; face_hits[:-1,1:] += steep_a; face_hits[1:,1:] += steep_a
face_hits[:-1,:-1] += steep_b; face_hits[1:,:-1] += steep_b; face_hits[1:,1:] += steep_b
residual_hits = np.zeros(cls.shape, dtype=np.uint16)
for e in records:
    for q in e['corner_rc']: residual_hits[tuple(q)] += 1
padded = np.pad(h82, 1, mode='edge')
ring = np.stack([padded[1+dr:1+dr+2048,1+dc:1+dc+2048]
                 for dr,dc in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))])
prominence_field = h82 - np.median(ring, axis=0)
peak_mask = bank & (face_hits >= 4) & (residual_hits > 0) & (prominence_field >= 0.5)
pr,pc = np.where(peak_mask)
representative_by_vertex={}
for edge in records:
    for q in edge['corner_rc']:
        key=tuple(q)
        if key not in representative_by_vertex or edge['angle_ev82b_deg']>representative_by_vertex[key]['angle_ev82b_deg']:
            representative_by_vertex[key]=edge
peak_candidates=[]
for r,c in zip(pr.tolist(),pc.tolist()):
    representative=representative_by_vertex[(r,c)]
    peak_candidates.append({'row':r,'col':c,'x_m':6*c,'z_m':12282-6*r,
      'height_ev80_m':float(h80[r,c]),'height_ev82b_m':float(h82[r,c]),
      'delta_m':float(h82[r,c]-h80[r,c]),'prominence_m':float(prominence_field[r,c]),
      'steep_faces_gt30':int(face_hits[r,c]),'residual_hinges_incident':int(residual_hits[r,c]),
      'selector_vertex':bool(selector[r,c]),'decision_reason':decisions[(r,c)]['decision_reason'] if selector[r,c] else None,
      'representative_residual':representative})
peak_candidates.sort(key=lambda p:(-p['prominence_m'],-p['steep_faces_gt30'],-p['residual_hinges_incident'],p['row'],p['col']))

# 64x64-cell sector bins based on corrected geographic edge centers.
sector_counts={}
for e in records:
    key=(int((12288-e['z_m'])//384),int(e['x_m']//384))
    sector_counts[key]=sector_counts.get(key,0)+1
top_sectors=sorted(sector_counts.items(),key=lambda item:(-item[1],item[0]))[:10]
# The strict pyramid classifier can return zero. Use pre-existing measured
# consumer anchors for descriptive profiles, never relabel them as pyramids.
anchors=consumer_report['mixed_edge_counts_and_focuses']['focus_anchors']
ev80_anchors=ev80_report['mixed_edge_counts_and_focuses']['focus_anchors']
ranked_anchors=sorted(ev80_anchors,key=lambda q:(q['local_energy_reduction'],abs(q['candidate_height_m']-q['source_height_m'])))
focus_specs=[ranked_anchors[-1],ranked_anchors[0]]
focuses=[]
for q in focus_specs:
    r,c=int(q['row']),int(q['col'])
    nearest=min(records,key=lambda e:(e['x_m']-q['x_m'])**2+(e['z_m']-q['z_m'])**2,default=None)
    focuses.append({'row':r,'col':c,'x_m':int(q['x_m']),'z_m':int(q['z_m']),
      'height_ev79_m':float(h79[r,c]),'height_ev80_m':float(h80[r,c]),'height_ev82b_m':float(h82[r,c]),
      'delta_ev82b_vs_ev80_m':float(h82[r,c]-h80[r,c]),
      'local_energy_reduction_ev79_to_ev80':float(q.get('local_energy_reduction',0.0)),
      'steep_faces_gt30_at_anchor':int(face_hits[r,c]),'prominence8_m_at_anchor':float(prominence_field[r,c]),
      'residual_hinges_at_anchor':int(residual_hits[r,c]),'nearest_residual':nearest,
      'selector_vertex':bool(selector[r,c]),'decision_reason':decisions[(r,c)]['decision_reason'] if selector[r,c] else None})
focus_a,focus_b=focuses

# Coverage map: x east, z north. The two anchors get outlines.
fig,ax=plt.subplots(figsize=(10,10),dpi=180)
for k,col in ((3,'#61a6d7'),(5,'#24a092'),(6,'#536eb2')):
    rr,cc=np.where(cls==k); ax.scatter(6*cc+3,12282-6*rr-3,s=.14,c=col,alpha=.42,rasterized=True,label=f'cauce clase {k}')
with_sel=[e for e in records if e['selector_corners']]; without_sel=[e for e in records if not e['selector_corners']]
for arr,col,mark,label in ((with_sel,'#f3a43b','o',f'residual con selector ({len(with_sel)})'),(without_sel,'#ed3562','x',f'sin selector ({len(without_sel)})')):
    ax.scatter([e['x_m'] for e in arr],[e['z_m'] for e in arr],s=8 if mark=='o' else 11,c=col,marker=mark,linewidths=.6,alpha=.9,rasterized=True,label=label)
for i,e in enumerate((focus_a,focus_b),1):
    ax.scatter([e['x_m']],[e['z_m']],s=130,facecolors='none',edgecolors='black',linewidths=1.4,label=f'anchor descriptivo {i}')
ax.set(xlim=(0,12288),ylim=(0,12288),xlabel='x este (m)',ylabel='z norte (m)',title='EV82-B · residuales geométricos offline, no captura DayZ\nBisagras mixed-any >30°, planta 12.288 × 12.288 km')
ax.set_aspect('equal'); ax.legend(loc='lower left',fontsize=8,framealpha=.9,ncol=2); fig.tight_layout(); fig.savefig(OUT/'residual-map.png'); plt.close(fig)

# Cardinal cuts through both anchors, all panels share axes and vertical scale.
# Three 6 m cells each way gives a 36 m total crop, preserving true 1:1 scale.
fig,axs=plt.subplots(4,1,figsize=(16,8),dpi=180,sharex=True,sharey=True)
all_values=[]
for e in focuses:
    r,c=e['row'],e['col']
    all_values.extend(h80[r,c-3:c+4].tolist()); all_values.extend(h82[r,c-3:c+4].tolist())
    all_values.extend(h80[r-3:r+4,c].tolist()); all_values.extend(h82[r-3:r+4,c].tolist())
ymin,ymax=min(all_values),max(all_values); pad=max(.25,(ymax-ymin)*.06)
for i,e in enumerate(focuses):
    r,c=e['row'],e['col']
    cols=np.arange(c-3,c+4); dx=6*(cols-c)
    rows=np.arange(r-3,r+4); dz=-6*(rows-r)
    for ax,d,a,b,label in ((axs[2*i],dx,h80[r,cols],h82[r,cols],'x este'),
                           (axs[2*i+1],dz,h80[rows,c],h82[rows,c],'z norte')):
        ax.plot(d,a,'o-',ms=2.5,lw=1.15,color='#4778a8',label='EV80')
        ax.plot(d,b,'o-',ms=2.5,lw=1.15,color='#d98322',label='EV82-B')
        ax.axvline(0,color='#333',lw=.7,ls='--'); ax.set_xlim(-18,18); ax.set_ylim(ymin-pad,ymax+pad)
        ax.set_aspect('equal',adjustable='box'); ax.grid(alpha=.25)
        ax.set_xlabel(f'distancia {label} (m)'); ax.set_ylabel('elevación (m)'); ax.legend(fontsize=7,loc='best')
    axs[2*i].set_title(f"Anchor ({e['x_m']}, {e['z_m']}) m · x este · delta B−EV80 {e['delta_ev82b_vs_ev80_m']:+.3f} m")
    axs[2*i+1].set_title(f"Anchor ({e['x_m']}, {e['z_m']}) m · z norte")
fig.suptitle('EV80 → EV82-B · perfiles geométricos offline, no captura DayZ · recorte 36 m · escala 1:1',y=.995)
fig.tight_layout(); fig.savefig(OUT/'ev80-to-b-sections.png'); plt.close(fig)

# Existing EV82 solver, dry-run only at the three published focus anchors.
# Protect the height and contract arrays from accidental writes in this probe.
engineering=(source['reserve'].astype(bool)|source['platform'].astype(bool))
for arr in (h79,h80,h82,cls,fixed,wet,plane,visible,water_floor,engineering): arr.flags.writeable=False
p99_bank=float(authoring['p99_bank_reference_ev80'])
p99_interior=float(authoring['p99_interior_reference_ev80'])
local_solver=[]
def direct_local_validation(r,c,value,bank_limit,interior_limit,angular_reference):
    current_patch=np.asarray(h82[r-2:r+3,c-2:c+3],dtype=np.float64)
    ref_patch=np.asarray(angular_reference[r-2:r+3,c-2:c+3],dtype=np.float64)
    patch=np.array(current_patch,copy=True); patch[2,2]=np.float32(value).item()
    def normal(arr,tri):
        xyz=np.asarray([(dc*6.0,arr[dr+2,dc+2],-dr*6.0) for dr,dc in tri],dtype=np.float64)
        n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])
        if n[1] < 0: n=-n
        return n
    def slope(n): return float(np.degrees(np.arctan2(np.hypot(n[0],n[2]),abs(n[1]))))
    def hinge(a,b):
        cosine=np.clip(float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b))),-1.0,1.0)
        return float(np.degrees(np.arccos(cosine)))
    current_normals=[normal(current_patch,t) for t in author.TRIANGLES]
    ref_normals=[normal(ref_patch,t) for t in author.TRIANGLES]
    test_normals=[normal(patch,t) for t in author.TRIANGLES]
    face_before={i:slope(ref_normals[i]) for i in author.INCIDENT}
    face_after={i:slope(test_normals[i]) for i in author.INCIDENT}
    hinge_current=[]; hinge_reference=[]; hinge_after=[]; sectors=[]; categories=[]
    for edge,(ta,tb) in author.HINGES:
        hinge_current.append(hinge(current_normals[ta],current_normals[tb]))
        hinge_reference.append(hinge(ref_normals[ta],ref_normals[tb]))
        hinge_after.append(hinge(test_normals[ta],test_normals[tb]))
        sectors.append(author.edge_sector(edge,r,c))
        ids=[(r+dr,c+dc) for dr,dc in set(author.TRIANGLES[ta]+author.TRIANGLES[tb])]
        is_bank=all(cls[rr,cc]==0 and not wet[rr,cc] and not engineering[rr,cc] and distance[rr,cc]<=96.0+1e-9 for rr,cc in ids)
        is_interior=all(cls[rr,cc]==0 and not wet[rr,cc] and not engineering[rr,cc] and distance[rr,cc]>96.0+1e-9 for rr,cc in ids)
        categories.append('bank' if is_bank else ('interior' if is_interior else None))
    sector_caps={}
    for sec,a in zip(sectors,hinge_reference): sector_caps[sec]=max(sector_caps.get(sec,-np.inf),a)
    failures=[]
    for i,v in face_after.items():
        limit=max(35.0,face_before[i])
        if v>limit+2e-8: failures.append(f'slope_{i}')
    for i,v in enumerate(hinge_after):
        limits=[sector_caps[sectors[i]]]
        if hinge_reference[i]<=30.0+1e-4: limits.append(30.0)
        if categories[i]=='bank' and hinge_reference[i]<=bank_limit+1e-8: limits.append(bank_limit)
        if categories[i]=='interior' and hinge_reference[i]<=interior_limit+1e-8: limits.append(interior_limit)
        if any(v>lim+2e-8 for lim in limits): failures.append(f'hinge_{i}')
    old_h=float(h82[r,c]); new_h=float(np.float32(value)); orig=float(h79[r,c])
    floor=float(water_floor[r,c])
    if new_h<min(orig,1.8)-1e-8 or new_h<floor-1e-8: failures.append('floor')
    if abs(new_h-orig)>2.0+1e-8: failures.append('EV79_budget')
    before_energy=float(np.dot(hinge_current,hinge_current)); after_energy=float(np.dot(hinge_after,hinge_after))
    if before_energy<=1e-18 or (before_energy-after_energy)/before_energy<1e-4: failures.append('material_benefit')
    return {'float32_height_m':new_h,'independent_failures':failures,'six_face_slope_reference_deg':[face_before[i] for i in author.INCIDENT],
      'six_face_slope_after_deg':[face_after[i] for i in author.INCIDENT],
      'twelve_hinge_current_deg':hinge_current,'twelve_hinge_reference_deg':hinge_reference,'twelve_hinge_after_deg':hinge_after,
      'incident_hinge_squared_energy_before':before_energy,'incident_hinge_squared_energy_after':after_energy,
      'independent_pass':not failures,'method':'direct triangle cross-products and normal-pair dot products; solver topology indices only'}
for q in anchors:
    r,c=int(q['row']),int(q['col']); interval_trace=[]; decision_trace=[]
    proposal,reason=author.solve_node(r,c,h82,h79,h80,cls,fixed,wet,engineering,distance,water_floor,
                                      p99_bank,p99_interior,max_delta=2.0,
                                      interval_trace=interval_trace,decision_trace=decision_trace)
    lo,hi=author.original_budget_interval(h79[r,c],h82[r,c],water_floor[r,c],2.0)
    component_lo=max((v[0] for v in interval_trace),default=None)
    component_hi=min((v[1] for v in interval_trace),default=None)
    local_solver.append({'row':r,'col':c,'x_m':int(q['x_m']),'z_m':int(q['z_m']),
      'current_ev82b_m':float(h82[r,c]),'original_ev79_m':float(h79[r,c]),
      'scalar_step_interval_ev79_budget_m':[float(lo),float(hi)],
      'solver_proposal_m':None if proposal is None else float(proposal),'solver_reason':reason,
      'interval_component_count':len(interval_trace),
      'intersection_of_recorded_components_m':[component_lo,component_hi],
      'decision_trace':decision_trace[-1] if decision_trace else None,
      'candidate_array_unchanged':True,
      'scope':'solve_node dry-run at this node only; proposal not applied; producer-local diagnostic, not independent consumer proof'})
    if proposal is not None:
        local_solver[-1]['independent_float32_check_ev80_reference']=direct_local_validation(r,c,proposal,p99_bank,p99_interior,h80)
    # A second producer-local probe uses B itself as angular reference and B's
    # accepted p99 caps, measuring remaining local freedom without accumulation.
    interval_b=[]; decision_b=[]
    bank_limit_b=float(consumer_report['angles']['stats']['bank']['candidate']['p99'])
    interior_limit_b=float(consumer_report['angles']['stats']['interior']['candidate']['p99'])
    proposal_b,reason_b=author.solve_node(r,c,h82,h79,h82,cls,fixed,wet,engineering,distance,water_floor,
                                         bank_limit_b,interior_limit_b,max_delta=2.0,
                                         interval_trace=interval_b,decision_trace=decision_b)
    local_solver[-1]['preserve_b_reference_probe']={'angular_reference':'EV82-B current candidate',
      'p99_bank_cap_deg':bank_limit_b,'p99_interior_cap_deg':interior_limit_b,
      'scalar_step_interval_ev79_budget_m':[float(lo),float(hi)],
      'solver_proposal_m':None if proposal_b is None else float(proposal_b),'solver_reason':reason_b,
      'interval_component_count':len(interval_b),
      'intersection_of_recorded_components_m':[max((v[0] for v in interval_b),default=None),min((v[1] for v in interval_b),default=None)],
      'decision_trace':decision_b[-1] if decision_b else None,
      'independent_float32_check':None if proposal_b is None else direct_local_validation(r,c,proposal_b,bank_limit_b,interior_limit_b,h82),
      'candidate_array_unchanged':True,'scope':'producer-local dry-run; proposal not applied'}

report={'status':'OFFLINE_RESIDUAL_DIAGNOSIS_EV82B_NOT_NEW_AUTHORING','candidate_sha256':EXPECTED,'ev80_sha256':EV80_SHA,
 'diagnostic_script_sha256':sha(__file__),'ev80_consumer_candidate_sha256':ev80_report.get('candidate_sha256'),
 'ev79_source_sha256':sha(SRC),'consumer_status':consumer_report['status'],'consumer_gates_all_true':True,
 'scope':{'residual':'candidate B hinge >30 degrees and incident_any(EV79-derived bank mask) and incident_any(EV79 native wet_support)',
 'bank':'class 0, no wet support/source water/beach/reserve/platform, within 96m of classes 3/5/6',
 'selector':'exact EV82 author.py source_fold_nodes over EV79 domain/fixed masks; corrected diagonal/vertical/horizontal corner incidence',
 'budget':'EV79 total +/-2m bounds and original lower water/design floor; no cumulative allowance',
 'visual_limit':'geometry only; no DayZ render/LOD or causal acceptance'},
 'selector_nodes':int(selector.sum()),'changed_vertices_vs_ev80':int(changed.sum()),
 'residual':{'ev80_count':sum(v['ev80_over30'] for v in by_kind.values()),'ev82b_count':len(records),
 'reduction':sum(v['ev80_over30'] for v in by_kind.values())-len(records),'by_kind':by_kind,'participant_state':states,'decision_reason_hits_nonexclusive':reason_hits,
 'top_sectors_64x64':[{'row':k[0],'col':k[1],'count':v} for k,v in top_sectors]},
 'remaining_scalar_budget_for_unique_selector_vertices_at_residuals':{'count':len(residual_nodes),'up_m_percentiles_min_25_50_75_95_max':pct(upv),'down_m_percentiles_min_25_50_75_95_max':pct(downv),'up_gt_0_1m':int(np.count_nonzero(upv>.1)),'down_gt_0_1m':int(np.count_nonzero(downv>.1)),'not_an_angular_feasibility_claim':True},
 'pyramid_like_convergence_definition':{'bank_vertex':True,'incident_face_slope_threshold_deg':30.0,'minimum_incident_steep_faces':4,'positive_peak_over_eight_neighbors_m':0.5,'minimum_incident_mixed_residual_hinges':1},
 'pyramid_like_convergence_count':len(peak_candidates),'pyramid_like_convergence_top_20':peak_candidates[:20],
 'pyramid_classifier_interpretation':'0 means no vertex met this exact conjunction (4 incident faces >30 degrees, prominence >=0.5m, residual hinge); it does not establish absence of pyramid-like relief under other definitions.',
 'focuses':[focus_a,focus_b],
 'local_solver_dry_runs':local_solver,
 'figures':{'residual-map.png':sha(OUT/'residual-map.png'),'ev80-to-b-sections.png':sha(OUT/'ev80-to-b-sections.png')},
 'limits':['The detector only counts mixed-any hinges >30 degrees; sub-30 faceting and long straight/planar stretches are outside its scope and may still match the visual complaint.','An unchanged selected corner identifies an unedited EV82 node; its recorded decision reason is not proof that no other value passes.','A changed corner with residual >30 means this accepted edit did not remove that hinge; it does not prove infeasibility of another locally feasible value.','Budget headroom is scalar only; angular p99/EV80 cap, sector, water, slope and benefit gates still constrain any future edit.','The zero strict-convergence count applies only to the exact conjunction in this report and is not evidence that all pyramid-like relief is absent.','The local solver probes are producer-local diagnostics; proposals were not applied. The direct float32 check independently recomputes 6 face normals and 12 hinges only at these nodes, not the full consumer gates.','No new terrain, second-pass candidate, package or engine run was made. Profiles show cardinal cuts, not full 3D appearance.']}
bank_dist=consumer_report['ev80_comparison']['distributions']['bank']
candidate_bank_key=next(k for k in bank_dist if k != 'ev80')
report['bank_distribution_ev80_vs_current_candidate']={'current_candidate_sha256':EXPECTED,'report_candidate_label':candidate_bank_key,
 'ev80_mean_square':bank_dist['ev80']['mean_square'],'current_mean_square':bank_dist[candidate_bank_key]['mean_square'],
 'mean_square_delta':bank_dist[candidate_bank_key]['mean_square']-bank_dist['ev80']['mean_square'],
 'ev80_p99_deg':bank_dist['ev80']['p99'],'current_p99_deg':bank_dist[candidate_bank_key]['p99'],
 'note':'El reporte del consumidor etiqueta el lado candidato como ev81, pero inputs.candidate_sha256 coincide con EV82-B; se cita por hash.'}
(OUT/'residual-diagnosis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# Diagnóstico residual EV82-B','',f"Candidato B SHA-256: `{EXPECTED}`  ",f"Baseline EV80 SHA-256: `{EV80_SHA}`",'', 'Censo geométrico offline: residual = bisagra mixed-any (bank y wet support incidentes) con ángulo >30°. No diagnostica apariencia ni causa visual.','', '![Mapa de residuales](residual-map.png)','', '## Conteos','',f"EV80: {report['residual']['ev80_count']} bisagras; EV82-B: {len(records)}; reducción: {report['residual']['reduction']}.",'', '|Orientación|EV80 >30°|EV82-B >30°|Reducción|','|---|---:|---:|---:|']
for k,v in by_kind.items(): lines.append(f"|{k}|{v['ev80_over30']}|{v['ev82b_over30']}|{v['reduced']}|")
lines += ['', '|Participación de esquinas selector|Bisagras residuales|','|---|---:|']
for k,v in states.items(): lines.append(f'|{k}|{v}|')
lines += ['', 'Razones de decisión registradas en esquinas selector incidentes; conteos por bisagra y solapados:']
for k,v in sorted(reason_hits.items()): lines.append(f'- `{k}`: {v}')
lines += ['', '## Margen escalar EV79 restante','',f"En {len(residual_nodes)} vértices selector únicos que tocan residuales: {int(np.count_nonzero(upv>.1))} conservan >0.1m hacia arriba y {int(np.count_nonzero(downv>.1))} >0.1m hacia abajo. Percentiles min/25/50/75/95/máx arriba `{pct(upv)}`m; abajo `{pct(downv)}`m.",'', 'Esto mide espacio escalar dentro del presupuesto total EV79 y su suelo, no cuántos nodos superan límites angulares. No se hizo un segundo pase ni se creó candidato.', '', '## Sectores más densos','', '|#|Sector 64×64|Bisagras|','|---:|---:|---:|']
for i,(k,v) in enumerate(top_sectors,1): lines.append(f'|{i}|{k[0]},{k[1]}|{v}|')
lines += ['', '## Clasificador estricto y focos de perfil','', f"El clasificador estricto de convergencia (vértice de banco, al menos 4 caras incidentes >30°, prominencia local ≥0.5m y bisagra residual) encontró **{len(peak_candidates)}** nodos. Cero significa que ninguna ubicación satisface esa conjunción exacta; no demuestra que no existan relieves piramidales bajo otra definición.", '', 'Los perfiles se centran en dos anchors medidos ya publicados por el consumidor, no en nodos seleccionados por el clasificador estricto: uno con la mayor reducción local de energía EV79→EV80 y otro con la menor entre los tres anchors. Son ejemplos descriptivos de residuales, no pirámides probadas.', '']
for i,e in enumerate(focuses,1):
    lines.append(f"- Anchor {i}: ({e['x_m']}, {e['z_m']})m, filas/columnas ({e['row']},{e['col']}); elevaciones EV79/EV80/B {e['height_ev79_m']:.3f}/{e['height_ev80_m']:.3f}/{e['height_ev82b_m']:.3f}m; B−EV80 {e['delta_ev82b_vs_ev80_m']:+.3f}m; caras locales >30°={e['steep_faces_gt30_at_anchor']}, prominencia 8-neighbors={e['prominence8_m_at_anchor']:+.3f}m; bisagras residuales incidentes al nodo={e['residual_hinges_at_anchor']}; selector={e['selector_vertex']} ({e['decision_reason']}).")
lines += ['', '![Cortes EV80 a B, escala 1:1](ev80-to-b-sections.png)', '', 'Cada anchor tiene corte cardinal este-oeste y norte-sur con tres celdas de 6m a cada lado: 36m de ancho total. Los cuatro paneles comparten límites de altura y aspecto 1:1. Son perfiles, no la superficie triangular completa ni una captura de DayZ.', '', '## Sondeo local del solver (sin aplicar propuestas)','', 'Se llamó al solve_node existente en los tres anchors publicados por el consumidor EV82-B, con EV82-B como altura actual, EV79 como presupuesto/floor, EV80 como referencia angular y los mismos p99 de autoría. Las alturas están protegidas como solo lectura; ningún resultado se escribió. Es un sondeo del productor, no una verificación independiente del consumidor.']
for q in local_solver:
    proposal='sin propuesta' if q['solver_proposal_m'] is None else f"propuesta {q['solver_proposal_m']:.6f}m"
    bprobe=q['preserve_b_reference_probe']; bproposal='sin propuesta' if bprobe['solver_proposal_m'] is None else f"propuesta {bprobe['solver_proposal_m']:.6f}m"
    direct=q.get('independent_float32_check_ev80_reference')
    direct_text='sin propuesta que comprobar' if direct is None else f"float32 directo={'PASS' if direct['independent_pass'] else 'FAIL '+str(direct['independent_failures'])}"
    direct_b=bprobe['independent_float32_check']; direct_b_text='sin propuesta que comprobar' if direct_b is None else f"float32 directo={'PASS' if direct_b['independent_pass'] else 'FAIL '+str(direct_b['independent_failures'])}"
    delta_b='' if bprobe['solver_proposal_m'] is None else f"; cambio B {bprobe['solver_proposal_m']-q['current_ev82b_m']:+.6f}m"
    energy_text='' if direct_b is None else f"; energía local {direct_b['incident_hinge_squared_energy_before']:.3f}→{direct_b['incident_hinge_squared_energy_after']:.3f} ({100*(direct_b['incident_hinge_squared_energy_before']-direct_b['incident_hinge_squared_energy_after'])/direct_b['incident_hinge_squared_energy_before']:.3f}% menos)"
    ulp_trace=bprobe['decision_trace']; ulp_text='' if not ulp_trace else f"; fallback {ulp_trace['selected_ulp']} ULP"
    lines.append(f"- ({q['x_m']}, {q['z_m']})m, actual {q['current_ev82b_m']:.6f}m; intervalo escalar EV79 {q['scalar_step_interval_ev79_budget_m'][0]:+.6f}..{q['scalar_step_interval_ev79_budget_m'][1]:+.6f}m. Referencia EV80: {proposal}; motivo `{q['solver_reason']}`; {direct_text}. Referencia B + p99 B ({bprobe['p99_bank_cap_deg']:.4f}° banco, {bprobe['p99_interior_cap_deg']:.4f}° interior): {bproposal}{delta_b}{energy_text}{ulp_text}; motivo `{bprobe['solver_reason']}`; {direct_b_text}; componentes angulares={bprobe['interval_component_count']}.")
bd=report['bank_distribution_ev80_vs_current_candidate']
lines += ['', '## Redistribución de curvatura del banco seco','', f"La energía angular incidente global baja 13.5% según el consumidor, pero el mean-square del banco sube de {bd['ev80_mean_square']:.8f} a {bd['current_mean_square']:.8f} ({bd['mean_square_delta']:+.8f}); el p99 apenas cambia ({bd['ev80_p99_deg']:.8f}° → {bd['current_p99_deg']:.8f}°). La mejora no es uniforme: parte de la curvatura se redistribuye dentro del banco seco. El reporte etiqueta `ev81` al candidato, pero su `candidate_sha256` coincide con el SHA EV82-B.", '', '## Clasificación de límites y lectura','', 'El detector cuenta bisagras mixed-any de más de 30°. Facetas sub-30° y tramos rectos amplios quedan fuera; por tanto, este censo no cubre todo lo que el usuario puede percibir como rectángulo, pirámide o ribera facetada. Las bisagras sin esquina selector quedan fuera del alcance de esta pasada. Las que sí tocan el selector incluyen nodos editados y no editados; `benefit_below_material_floor` describe la decisión para esa altura, no demuestra imposibilidad. La segunda llamada al solver toma B como referencia angular y usa p99 B para medir libertad local restante respecto al estado actual; conserva presupuesto y floor EV79. El chequeo float32 directo recalcula seis caras y doce bisagras con productos vectoriales y productos punto de normales, además de floor, presupuesto y beneficio local. No sustituye los gates globales del consumidor.', '', 'Límites: offline; no render/LOD; los hits de máscaras se solapan; perfiles cardinales parciales; el solver local no es consumidor independiente. No se alteró terreno ni consumidor, no se creó candidato y no hubo paquete ni ejecución del motor.']
(OUT/'residual-diagnosis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'ev80_residuals':report['residual']['ev80_count'],'ev82b_residuals':len(records),'reduction':report['residual']['reduction'],'state':states,'reason_hits':reason_hits,'strict_pyramid_classifier_count':len(peak_candidates),'focuses':[{'x':e['x_m'],'z':e['z_m'],'delta_b_vs_ev80':e['delta_ev82b_vs_ev80_m'],'steep_faces':e['steep_faces_gt30_at_anchor'],'prominence8':e['prominence8_m_at_anchor']} for e in focuses],'local_solver_dry_runs':local_solver,'budget_vertices':len(residual_nodes)},indent=2))
