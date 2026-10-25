from __future__ import annotations
import hashlib, json, math, os, sys, tempfile
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT=Path(r'E:/DayZ-Baltic-Build')
OUT=ROOT/'v30-bank-multiscale-census-20261010'
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
EV79C=ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz'
PRIOR=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
P=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
WRP=ROOT/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
AUTHOR=ROOT/'v30-global-strict-bank-relief-20261010/author_ev87.py'
CONSUMER=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
NOTE=ROOT/'v30-global-strict-bank-relief-20261010/selector-coverage-p12-note.md'
GIS_PY=Path(r'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe')
N=2048; CELL=6.0; SEA=.85; ANGLE_THRESHOLD=30.0001; PROM_THRESHOLD_M=.1
EXPECTED={
 'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 'EV79_CONSTRAINTS':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
 'PRIOR_CONSTRAINTS':'18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
 'P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 'F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 'WRP':'3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def atomic_json(path,obj):
 path=Path(path); tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
 os.replace(tmp,path)
def load_npz(path):
 with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def edge_angles(h):
 nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:];one=np.ones_like(nw)
 ea=np.stack((6*one,ne-nw,np.zeros_like(nw)),axis=-1)
 dg=np.stack((6*one,se-nw,-6*one),axis=-1)
 eb=np.stack((np.zeros_like(nw),sw-nw,-6*one),axis=-1)
 a=np.cross(ea,dg);b=np.cross(dg,eb)
 a/=np.linalg.norm(a,axis=-1)[...,None];b/=np.linalg.norm(b,axis=-1)[...,None]
 return {'diag':np.degrees(np.arctan2(np.linalg.norm(np.cross(a,b),axis=-1),np.einsum('...i,...i->...',a,b))),
         'vertical':np.degrees(np.arctan2(np.linalg.norm(np.cross(a[:,:-1],b[:,1:]),axis=-1),np.einsum('...i,...i->...',a[:,:-1],b[:,1:]))),
         'horizontal':np.degrees(np.arctan2(np.linalg.norm(np.cross(b[:-1,:],a[1:,:]),axis=-1),np.einsum('...i,...i->...',b[:-1,:],a[1:,:])))}
def edge_vertex_slices(mask,kind):
 if kind=='diag':return (mask[:-1,:-1],mask[:-1,1:],mask[1:,:-1],mask[1:,1:])
 if kind=='vertical':return (mask[:-1,:-2],mask[:-1,1:-1],mask[1:,1:-1],mask[1:,2:])
 return (mask[:-2,:-1],mask[1:-1,:-1],mask[1:-1,1:],mask[2:,1:])
def node_stats(angles):
 vmax=np.full((N,N),-np.inf,dtype=np.float64);hot=np.zeros((N,N),dtype=bool)
 for kind,arr in angles.items():
  for dst in edge_vertex_slices(vmax,kind):np.maximum(dst,arr,out=dst)
  for dst in edge_vertex_slices(hot,kind):dst|=arr>ANGLE_THRESHOLD
 return vmax,hot
def vertex_levels(p,f):
 out=np.full((N,N),SEA,dtype=np.float64)
 # Same four-corner incidence and max semantics as EV87 consumer.
 pv=np.nan_to_num(p.astype(np.float64),nan=SEA)
 for i,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
  fv=np.nan_to_num(f[:,:,i].astype(np.float64),nan=SEA)
  level=np.maximum(SEA,np.maximum(pv,fv))
  dst=out[dr:dr+N-1,dc:dc+N-1]
  np.maximum(dst,level,out=dst)
 return out
def summarize_mask(mask):return int(np.count_nonzero(mask))
def counts_by_group(mask,groups):return {name:int(np.count_nonzero(mask & g)) for name,g in groups.items()}
def encode_rank(mask,score,ew,ns):
 idx=np.flatnonzero(mask.ravel())
 if idx.size:
  vals=score.ravel()[idx]
  # Deterministic descending score, then row, col (flat index order).
  order=np.lexsort((idx,-vals));idx=idx[order];vals=vals[order]
  ax=np.where(ew.ravel()[idx]>=ns.ravel()[idx],0,1).astype(np.uint8)
 else:vals=np.empty(0,np.float32);ax=np.empty(0,np.uint8)
 return idx.astype(np.int32),vals.astype(np.float32),ax
def sector_top(mask,score,ew,ns,topn=3):
 out={}
 for sr in range(N//64):
  for sc in range(N//64):
   r0,c0=sr*64,sc*64
   sm=mask[r0:r0+64,c0:c0+64]
   if not sm.any():continue
   vals=score[r0:r0+64,c0:c0+64]
   loc=np.flatnonzero(sm.ravel());lv=vals.ravel()[loc]
   order=np.lexsort((loc,-lv))[:topn];items=[]
   e=ew[r0:r0+64,c0:c0+64];n=ns[r0:r0+64,c0:c0+64]
   for k in order:
    lr,lc=divmod(int(loc[k]),64);items.append({'row':r0+lr,'col':c0+lc,'prominence_m':float(lv[k]),'axis':'EW' if e[lr,lc]>=n[lr,lc] else 'NS','ew_m':float(e[lr,lc]),'ns_m':float(n[lr,lc])})
   out[f'{sr},{sc}']=items
 return out

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 paths={'B':B,'EV79_CONSTRAINTS':EV79C,'PRIOR_CONSTRAINTS':PRIOR,'P':P,'F':F,'WRP':WRP,'EV87_AUTHOR':AUTHOR,'EV87_CONSUMER':CONSUMER,'EV87_SELECTOR_NOTE':NOTE}
 before={k:sha(v) for k,v in paths.items()}
 for k,v in EXPECTED.items():
  if k in before and before[k].lower()!=v.lower():raise RuntimeError(f'{k} SHA mismatch: {before[k]} != {v}')
 if not GIS_PY.exists():raise RuntimeError(f'GIS Python missing: {GIS_PY}')
 b=load_npz(B);cons=load_npz(EV79C);prior=load_npz(PRIOR)
 h=b['heights'].astype(np.float64);cls=b['cls']
 if h.shape!=(N,N) or cls.shape!=(N,N):raise RuntimeError('B shape mismatch')
 p=np.load(P,allow_pickle=False).astype(np.float64);f=np.load(F,allow_pickle=False).astype(np.float64)
 if p.shape!=(N-1,N-1) or f.shape!=(N-1,N-1,4):raise RuntimeError(f'P/F shape mismatch: {p.shape}, {f.shape}')
 # EV87 P12 membership masks, reconstructed exactly from author_ev87.population_masks.
 dry=(cls==0)&~cons['wet_support'].astype(bool)&~b['reserve'].astype(bool)&~b['platform'].astype(bool)
 bank=dry&(distance_transform_edt(~np.isin(cls,(3,5,6)),sampling=CELL)<=96.+1e-9)
 interior=dry&~bank
 groups={'bank':bank,'interior':interior}
 # EV87 explicit eligibility (author_ev87.py main); separate fixed masks from level blockage.
 level=vertex_levels(p,f)
 explicit_fixed=(cls!=0)|cons['other_fixed'].astype(bool)|cons['engineering_halo'].astype(bool)|prior['large_lake_banks'].astype(bool)
 eligible=(cls==0)&~cons['other_fixed'].astype(bool)&~cons['engineering_halo'].astype(bool)&~prior['large_lake_banks'].astype(bool)&(h>level)
 if np.any(explicit_fixed&eligible):raise RuntimeError('Eligibility overlaps explicit fixed union')
 waterline_blocked=(cls==0)&~(cons['other_fixed'].astype(bool)|cons['engineering_halo'].astype(bool)|prior['large_lake_banks'].astype(bool))&(h<=level)
 wet_support=cons['wet_support'].astype(bool)
 # Author exact one-step pre-spacing seed rule: incident hinge >30.0001 and either cardinal axis >0.1m over BOTH neighbors.
 vmax,hot=node_stats(edge_angles(h))
 base_ew=np.zeros((N,N),np.float64);base_ns=np.zeros_like(base_ew)
 base_ew[:,1:-1]=h[:,1:-1]-np.maximum(h[:,:-2],h[:,2:])
 base_ns[1:-1,:]=h[1:-1,:]-np.maximum(h[:-2,:],h[2:,:])
 seed6=eligible&hot&((base_ew>PROM_THRESHOLD_M)|(base_ns>PROM_THRESHOLD_M))
 score_fields={};support_fields={};ranking={};summary={'schema':'v30-bank-multiscale-census-v1','source_hashes':before,'dimensions':{'vertices':[N,N],'cell_m':CELL,'sector_nodes':64,'sector_m':384},'formula':{'for_distance_nodes_d':'max(0,H[r,c]-max(H[r-d,c],H[r+d,c])) and analogously for EW/NS','distances_nodes':[1,2,4],'distances_m':[6,12,24],'complete_context':'only rows/cols with d vertices available on both sides; otherwise NaN','peak_both_axes':'EW>0 AND NS>0','selector6_exact':'EV87 pre-spacing: eligible AND any incident hinge angle >30.0001 deg AND (EW one-step >0.1m OR NS one-step >0.1m)'},'thresholds_from_EV87':{'hinge_deg_strict_gt':ANGLE_THRESHOLD,'one_step_prominence_m_strict_gt':PROM_THRESHOLD_M},'mask_counts':{'vertices':N*N,'bank_population':summarize_mask(bank),'interior_population':summarize_mask(interior),'dry_population':summarize_mask(dry),'eligible':summarize_mask(eligible),'explicit_fixed_protected_union':summarize_mask(explicit_fixed),'waterline_blocked_not_explicit_fixed':summarize_mask(waterline_blocked),'wet_support_diagnostic':summarize_mask(wet_support),'seed6_pre_spacing':summarize_mask(seed6),'eligible_overlaps_bank':summarize_mask(eligible&bank),'eligible_overlaps_interior':summarize_mask(eligible&interior),'wet_support_and_eligible_overlap':summarize_mask(wet_support&eligible)}}
 arrays={'bank':bank,'interior':interior,'eligible':eligible,'explicit_fixed_protected':explicit_fixed,'waterline_blocked':waterline_blocked,'wet_support':wet_support,'seed6_pre_spacing':seed6,'max_incident_angle_deg':vmax.astype(np.float32)}
 for d in (1,2,4):
  ew=np.full((N,N),np.nan,np.float32);ns=np.full((N,N),np.nan,np.float32)
  valid=np.zeros((N,N),bool);valid[d:N-d,d:N-d]=True
  ev=np.maximum(0.0,h[d:N-d,d:N-d]-np.maximum(h[d:N-d,d-d:d-d+(N-2*d)],h[d:N-d,d+d:d+d+(N-2*d)])) if False else None
  # Explicit slices make the compared coordinates unambiguous.
  ew[d:N-d,d:N-d]=np.maximum(0.0,h[d:N-d,d:N-d]-np.maximum(h[d:N-d,d-d:N-2*d],h[d:N-d,2*d:N]))
  ns[d:N-d,d:N-d]=np.maximum(0.0,h[d:N-d,d:N-d]-np.maximum(h[0:N-2*d,d:N-d],h[2*d:N,d:N-d]))
  anypos=valid&((ew>0)|(ns>0));both=valid&(ew>0)&(ns>0);score=np.maximum(ew,ns)
  missed=anypos&~seed6
  groups_all={'total':valid,'bank':valid&bank,'interior':valid&interior,'eligible':valid&eligible,'explicit_fixed_protected':valid&explicit_fixed,'waterline_blocked':valid&waterline_blocked}
  groups_pos={k:v&anypos for k,v in groups_all.items()}
  groups_both={k:v&both for k,v in groups_all.items()}
  groups_missed={k:v&missed for k,v in groups_all.items()}
  groups_missed_gt01={k:v&missed&(score>PROM_THRESHOLD_M) for k,v in groups_all.items()}
  prefix=f'd{d}'
  arrays[f'{prefix}_ew_m']=ew;arrays[f'{prefix}_ns_m']=ns;arrays[f'{prefix}_valid']=valid;arrays[f'{prefix}_positive_any']=anypos;arrays[f'{prefix}_positive_both_axes']=both;arrays[f'{prefix}_positive_missed_seed6']=missed
  summary[prefix]={'distance_m':d*CELL,'context_vertices':int(valid.sum()),'positive_any_axis':counts_by_group(anypos,groups_all),'positive_both_axes':counts_by_group(both,groups_all),'positive_missed_seed6':counts_by_group(missed,groups_all),'missed_seed6_with_score_gt_0_1m':counts_by_group(missed&(score>PROM_THRESHOLD_M),groups_all),'positive_one_step_gt_0_1m':counts_by_group((ew>PROM_THRESHOLD_M)|(ns>PROM_THRESHOLD_M),groups_all),'peak_both_axes_percent_of_total_context':(100*int(both.sum())/int(valid.sum()) if valid.sum() else None)}
  allidx,allvals,allaxis=encode_rank(anypos,score,ew,ns);midx,mvals,maxis=encode_rank(missed,score,ew,ns);ranking[prefix+'_all']=(allidx,allvals,allaxis);ranking[prefix+'_missed_seed6']=(midx,mvals,maxis)
  summary[prefix]['top3_per_384m_sector_all_positive']=sector_top(anypos,score,ew,ns)
  summary[prefix]['top3_per_384m_sector_missed_seed6']=sector_top(missed,score,ew,ns)
  score_fields[prefix]=score;support_fields[prefix]=valid
 # Full rankings in separate compact arrays; flat indices are row*N+col and deterministic score-descending.
 for name,(idx,vals,axis) in ranking.items():
  arrays[f'rank_{name}_flat_index']=idx;arrays[f'rank_{name}_prominence_m']=vals;arrays[f'rank_{name}_axis']=axis
 # Hash all sources a second time before publishing any census result.
 after={k:sha(v) for k,v in paths.items()}
 if before!=after:raise RuntimeError('Source changed during census; refusing to write report')
 npz_path=OUT/'multiscale-arrays-and-rankings.npz';tmp_npz=OUT/'multiscale-arrays-and-rankings.tmp.npz'
 np.savez_compressed(tmp_npz,**arrays);os.replace(tmp_npz,npz_path)
 summary['artifacts']={'arrays_rankings_path':str(npz_path),'arrays_rankings_sha256':sha(npz_path),'ranking_encoding':'flat int32 row*N+col; sorted by descending max(EW,NS), then row,col; axis 0=EW, 1=NS','source_hashes_rechecked':after}
 atomic_json(OUT/'summary.json',summary)
 readme='''# Censo cardinal multiescala sobre B\n\nFuente base: EV82-B, sin candidato nuevo ni solver. Para cada vértice con contexto completo y d∈{1,2,4}, se calcula por separado EW y NS: max(0, Hc−max(H−d,H+d)); d equivale a 6, 12 y 24 m. “Ambos ejes” significa prominencia estrictamente positiva en EW y NS. El selector EV87 de 6 m se reconstruye antes de la separación de ventanas: elegible, bisagra incidente >30.0001° y prominencia de un paso >0.1 m en cualquiera de los dos ejes.\n\nLas máscaras bank/interior son las de `author_ev87.population_masks`; elegibilidad y unión de protecciones explícitas siguen `author_ev87.py`. Nodos bloqueados solo por estar bajo/equal al nivel P/F/SEA se cuentan aparte de la unión explícita de máscaras fijas. El sector de 384 m se indexa por bloques raster de 64×64 nodos. Los rankings contienen todos los positivos, no una cuota de modificación.\n\nEsto es prominencia cardinal respecto a dos muestras, no prominencia topográfica de silla, curvatura de superficie, artefacto visual ni una decisión de diseño. No implica elegibilidad de cambio ni autorización para alterar alturas. Identidades y fórmulas completas en `summary.json`; arrays y rankings completos en `multiscale-arrays-and-rankings.npz`.\n'''
 (OUT/'README.md').write_text(readme,encoding='utf-8')
 print(json.dumps({'status':'CENSUS_COMPLETE','summary':str(OUT/'summary.json'),'arrays_sha256':summary['artifacts']['arrays_rankings_sha256'],'counts':summary['mask_counts'],'d1':{k:v for k,v in summary['d1'].items() if not k.startswith('top3')},'d2':{k:v for k,v in summary['d2'].items() if not k.startswith('top3')},'d4':{k:v for k,v in summary['d4'].items() if not k.startswith('top3')}},ensure_ascii=False))
if __name__=='__main__':main()


