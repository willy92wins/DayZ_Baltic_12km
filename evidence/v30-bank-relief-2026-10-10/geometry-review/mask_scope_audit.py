from pathlib import Path
import json,sys
import numpy as np
from scipy.ndimage import distance_transform_edt
R=Path(r'E:/DayZ-Baltic-Build'); B=Path(r'E:/DayZ-Baltic-Build/v30-bank-relief-review-20261010/luna-geometry')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
C=R/'v30-remaining-exact-dry-support-20261009/candidate'; t=dict(np.load(C/'terrain.npz')); h=t['heights'].astype(float)
sem=dict(np.load(R/'v30-global-contour-pass-20261009/candidate-repaired/terrain.npz'))
report=json.loads((B/'report.json').read_text()); m=dict(np.load(R/'v30-valley-smoothing-20261008/candidate-a/masks.npz'))
scope=np.load(R/'v30-low-dry-domain-classification-20261009/domain.npz'); term=np.load(R/'v30-native-terminal-finish-20261009/constraints.npz'); prior=np.load(R/'v30-native-hinge-finish-20261009/constraints.npz'); ev=np.load(R/'v30-remaining-exact-dry-support-20261009/constraints.npz')
r,c=np.indices(h.shape); x=c*6; z=12282-r*6
radial620=np.hypot(x-2417.1428225906,z-6889.8850822322)<=620
object_narva=sem['narva'].astype(bool); narva=radial620|object_narva
oldborder66=(x<66)|(x>12216)|(z<66)|(z>12216);outer24=(x<24)|(x>12258)|(z<24)|(z>12258);border11=(r<11)|(r>=2037)|(c<11)|(c>=2037)
sea=np.isin(sem['cls'],[1,4]);beach=sem['beach'].astype(bool);engineering=sem['reserve'].astype(bool)|sem['platform'].astype(bool)
axes=json.loads((R/'v30-continuation-20261008/junction-fix-r2/axes.json').read_text());r1=np.zeros(h.shape,bool)
for rr,cc in axes['R1']['removed_cells']:r1[rr:rr+2,cc:cc+2]=True
r1dist=distance_transform_edt(~r1,sampling=6.);narva_old_guard=narva&(r1dist>=150)
nature=m['nature'].astype(bool);corridor=m['corridor'].astype(bool);summits=m['summits'].astype(bool)
controls=np.zeros(h.shape,bool)
for q in json.loads((W/'evidence/v30-global-contour-pass-2026-10-09/global-contour-temporal-reference.json').read_text())['points']:
 rr=int(np.floor((12282-q['z'])/6));cc=int(np.floor(q['x']/6));controls[max(0,rr):min(2048,rr+2),max(0,cc):min(2048,cc+2)]=True
# Verify exact source-mask construction; nature is reported separately, not a fixed term here.
old_formula=engineering|corridor|summits|oldborder66|sea|beach|narva_old_guard
assert np.array_equal(old_formula,m['fixed']), 'candidate-a fixed formula did not reconstruct'
term_formula=(m['fixed']&~oldborder66)|outer24|engineering|corridor|summits|sea|beach|object_narva|controls
assert np.array_equal(term_formula,term['fixed']) and np.array_equal(scope['fixed'],term['fixed']), 'terminal/scope fixed source mismatch'
assert np.array_equal(ev['fixed'],ev['other_fixed']|ev['water_support'])
# Existing 59 high creases, reconstructed on exact bank domain. This is not a whole-map visual review.
sys.path.insert(0,str(R/'v30-surface-crease-audit-20261009')); import audit_native_surface as audit
support=ev['water_support'].astype(bool);seed=np.isin(t['cls'],[3,5,6]);belt=distance_transform_edt(~seed,sampling=6)<=96
dryland=belt&(t['cls']==0)&~support
bank=dryland&~t['water'].astype(bool)&~t['beach'].astype(bool)&~t['reserve'].astype(bool)&~t['platform'].astype(bool)
movable=bank&~ev['fixed'].astype(bool)
def vv(kind,rr,cc):return {'diagonal':[(rr,cc),(rr,cc+1),(rr+1,cc),(rr+1,cc+1)],'vertical':[(rr,cc),(rr,cc+1),(rr+1,cc+1),(rr+1,cc+2)],'horizontal':[(rr,cc),(rr+1,cc),(rr+1,cc+1),(rr+2,cc+1)]}[kind]
components={'Narva radius620':radial620,'Narva raster/object':object_narva,'old Narva guard (radius/object AND R1dist>=150)':narva_old_guard,'corridor24':corridor,'nature label':nature,'beach':beach,'sea cls 1/4':sea,'platform/reserve':engineering,'summit':summits,'old border66':oldborder66,'outer border24':outer24,'EV71 border11':border11,'temporal controls':controls,'legacy any-finite-P support':prior['water_support'],'actual wet P/F support':support,'large-lake protection':ev['large_lake_banks'],'current fixed':ev['fixed']}
hits={k:{'any_vertex':0,'all_four':0,'touching_bank_any_edge':0} for k in components};high=[]; scope_by_hinge={}
# Edge-scope comparison: `any` includes every shared edge pair with >=1 eligible dry-bank vertex;
# `all` is the strict 4/4 dry domain used for the 59-fold result.
edge_scope={k:{'touching_physical_dryland96':0,'fully_physical_dryland96_4of4':0,'touching_physical_but_not_4of4':0,'touching_dry_bank':0,'fully_dry_bank_4of4':0,'touching_but_not_4of4':0,'also_touches_actual_wet_support':0,'above30_touching':0,'above30_not_4of4':0,'above30_also_touches_wet_support':0} for k in ('diagonal','vertical','horizontal')}
for kind,angles in audit.hinges(h):
 anydry=audit.incident_any(dryland,kind);alldry=audit.incident_all(dryland,kind); anybank=audit.incident_any(bank,kind); allbank=audit.incident_all(bank,kind);anywet=audit.incident_any(support,kind)
 zscope=edge_scope[kind];zscope['touching_physical_dryland96']=int(anydry.sum());zscope['fully_physical_dryland96_4of4']=int(alldry.sum());zscope['touching_physical_but_not_4of4']=int((anydry&~alldry).sum());zscope['touching_dry_bank']=int(anybank.sum());zscope['fully_dry_bank_4of4']=int(allbank.sum());zscope['touching_but_not_4of4']=int((anybank&~allbank).sum());zscope['also_touches_actual_wet_support']=int((anybank&anywet).sum());zscope['above30_touching']=int((anybank&(angles>30)).sum());zscope['above30_not_4of4']=int((anybank&~allbank&(angles>30)).sum());zscope['above30_also_touches_wet_support']=int((anybank&anywet&(angles>30)).sum())
 rs,cs=np.nonzero(allbank&(angles>30))
 for rr,cc in zip(rs.tolist(),cs.tolist()):
  v=vv(kind,rr,cc);rec={'kind':kind,'row':rr,'col':cc,'angle_deg':float(angles[rr,cc]),'movable_vertices':sum(bool(movable[y,x]) for y,x in v)}
  rec['x_m']=(cc+.5)*6 if kind!='vertical' else (cc+1)*6
  rec['z_m']=12282-(rr+.5)*6 if kind in ('diagonal','vertical') else 12282-(rr+1)*6
  flags={k:int(sum(bool(mask[y,x]) for y,x in v)) for k,mask in components.items()};rec['flags']=flags;high.append(rec)
  for k,mask in components.items():
   n=flags[k]
   if n>0:hits[k]['any_vertex']+=1
   if n==4:hits[k]['all_four']+=1
assert len(high)==59 and all(q['movable_vertices']==0 for q in high)
# Classify which 59 have only Narva-source protection after excluding overlaps with any other current fixed cause.
other_current=[corridor,beach,sea,engineering,summits,outer24,controls,support,ev['large_lake_banks'],t['water'].astype(bool),t['cls']!=0,border11]
only_narva=sum(all(bool(narva_old_guard[y,x] or object_narva[y,x]) for y,x in vv(q['kind'],q['row'],q['col'])) and not any(any(bool(mask[y,x]) for y,x in vv(q['kind'],q['row'],q['col'])) for mask in other_current) for q in high)
controls_overlap=[q for q in high if q['flags']['temporal controls']>0]
anchors=[]
for a in report['representative_maxima']:
 v=vv(a['kind'],a['row'],a['col'])
 anchors.append({'rank':a['rank'],'kind':a['kind'],'row':a['row'],'col':a['col'],'x_m':a['x_m'],'z_m':a['z_m'],'dihedral_deg':a['dihedral_deg'],'vertices_rc':[list(q) for q in v],'membership_count_of_4':{k:int(sum(bool(mask[y,x]) for y,x in v)) for k,mask in components.items()},'mean_R1_distance_m':float(np.mean([r1dist[y,x] for y,x in v]))})
summary={k:dict(any_physical_dryland_96=int(sum(v['touching_physical_dryland96'] for v in edge_scope.values())),physical_dryland_4of4=int(sum(v['fully_physical_dryland96_4of4'] for v in edge_scope.values())),physical_dryland_touch_not_4of4=int(sum(v['touching_physical_but_not_4of4'] for v in edge_scope.values())),any_crease=int(sum(v['touching_dry_bank'] for v in edge_scope.values())),fully_dry_4of4=int(sum(v['fully_dry_bank_4of4'] for v in edge_scope.values())),touching_not_fully_dry=int(sum(v['touching_but_not_4of4'] for v in edge_scope.values())),also_actual_wet_support=int(sum(v['also_touches_actual_wet_support'] for v in edge_scope.values())),above30=int(sum(v['above30_touching'] for v in edge_scope.values())),above30_not_4of4=int(sum(v['above30_not_4of4'] for v in edge_scope.values())),above30_actual_wet_support=int(sum(v['above30_also_touches_wet_support'] for v in edge_scope.values())))}
out={'status':'READ_ONLY_SCOPE_AND_MASK_PROVENANCE','high_creases_over30':59,'high_creases_over45':4,'high_creases_movable':0,'high_creases_only_narva_protection_no_other_overlap':int(only_narva),'high_creases_touching_temporal_control':len(controls_overlap),'edge_scope_by_type':edge_scope,'edge_scope_totals':summary,'semantic_mask_hits_across_59_high_creases':hits,'representative_anchors':anchors,'high_crease_records':high,'reconstructions':{'smooth_valley_candidate_a_fixed_formula_equals_mask':True,'native_terminal_fixed_formula_equals_constraints':True,'low_dry_scope_fixed_equals_native_terminal_fixed':True,'actual_wet_support_reused_from_ev71_exact_consumer':True},'interpretation':['The 59 count is strict: all four unique vertices of the two incident source triangles must be dry, class 0, within 96 m of class 3/5/6 and outside exact wet support, t.water/beach, reserve/platform. It excludes any hinge touching wet support or any other excluded vertex.','Edge-scope totals additionally count every paired hinge touching at least one eligible dry bank vertex, even when its other vertices are wet/protected/outside the bank band; these totals are not a dry-only crease count.','Nature is a diagnostic label from smooth_valley.py and is not in its fixed-mask union.','Narva old guard is (620 m radial-or-object region) intersect R1 distance >=150 m; the following native-terminal pass additionally fixed t.narva object pixels. The old broad mask is a historical rule, not proof that every point is still contractually protected.','This is mask membership/provenance only; no vertex was released or changed.']}
(B/'mask-scope-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('representative_anchors','high_crease_records')},indent=2));print('ANCHORS',json.dumps(anchors,indent=2))

