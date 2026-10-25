from __future__ import annotations
import hashlib,json,math,pathlib
import numpy as np

ROOT=pathlib.Path(r'E:\DayZ-Baltic-Build')
BASE=ROOT/'v30-mixed-bank-incremental-fixed-20261010'
EV79=ROOT/'v30-narva-dry-bank-relief-20261010'
OUT=ROOT/'v30-global-strict-bank-relief-20261010/residual-review'
DISC=OUT/'focus-profile-discovery.json'
CENTER=(840,370)
SEA=0.85

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 bpath=BASE/'candidate/terrain.npz'; ep=EV79/'candidate/terrain.npz'; ppath=EV79/'candidate/plane.npy'; fpath=EV79/'candidate/visible-field.npy'; cpath=EV79/'constraints.npz'; prev=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
 b=np.load(bpath,allow_pickle=False); e=np.load(ep,allow_pickle=False); p=np.load(ppath,allow_pickle=False); f=np.load(fpath,allow_pickle=False)
 c=np.load(cpath,allow_pickle=False); prior=np.load(prev,allow_pickle=False)
 h=b['heights']; cls=b['cls']; base=e['heights']; assert h.shape==base.shape==(2048,2048) and p.shape==(2047,2047) and f.shape==(2047,2047,4)
 assert sha(bpath)=='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
 assert sha(EV79/'candidate/terrain.npz')=='dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
 assert sha(ppath)=='768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
 assert sha(fpath)=='f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
 assert sha(cpath)=='ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
 assert sha(DISC)=='77e37ac8c9928420b2e80af2987031c92edda104124870e7bf863c0f840b933a'
 r0,c0=CENTER; windows={
   '7x7_window':(r0-3,r0+4,c0-3,c0+4),'5x5_core':(r0-2,r0+3,c0-2,c0+3),
   '9x9_window':(r0-4,r0+5,c0-4,c0+5),
   '17x17_window':(r0-8,r0+9,c0-8,c0+9),'13x13_core':(r0-6,r0+7,c0-6,c0+7),
 }
 # Per vertex maximum of available water planes from incident cell corners and SEA.
 # This is a sign/margin diagnostic, not an inferred water polygon.
 rlo,rhi=r0-9,r0+10; clo,chi=c0-9,c0+10
 level=np.full((rhi-rlo,chi-clo),SEA,dtype=float); has_design=np.zeros_like(level,dtype=bool)
 corner_offsets=((0,0,0),(0,1,1),(1,0,2),(1,1,3))
 for cr in range(rlo-1,rhi):
  for cc in range(clo-1,chi):
   if cr<0 or cc<0 or cr>=p.shape[0] or cc>=p.shape[1]:continue
   pl=float(p[cr,cc]); ff=np.asarray(f[cr,cc],dtype=float)
   for dr,dc,k in corner_offsets:
    vr,vc=cr+dr,cc+dc
    if rlo<=vr<rhi and clo<=vc<chi:
     vals=[SEA]
     if math.isfinite(pl):vals.append(pl)
     if math.isfinite(float(ff[k])):vals.append(float(ff[k]))
     ii,jj=vr-rlo,vc-clo; level[ii,jj]=max(level[ii,jj],max(vals))
     if math.isfinite(pl) or math.isfinite(float(ff[k])):has_design[ii,jj]=True
 hloc=h[rlo:rhi,clo:chi].astype(float); lev_margin=hloc-level
 wet=hloc<level
 # Protection union reconstructed from independent EV79/prior masks and B metadata.
 other=c['other_fixed']; eng=c['engineering_halo']; wet_support=c['wet_support']; large=prior['large_lake_banks']
 reserve=b['reserve'].astype(bool); platform=b['platform'].astype(bool); cls0=(cls==0)
 protected=other|eng|large|reserve|platform
 unprotected_class0=cls0 & ~protected
 # Also require EV79 +/-2 budget and no-rise B. Here, report headroom only; no candidate proposed.
 base_loc=base[rlo:rhi,clo:chi].astype(float)
 lower=np.maximum(base_loc-2.0,level+1e-4)
 upper=np.minimum(base_loc+2.0,hloc)
 downward_room=np.maximum(0.0,hloc-lower)
 # B metric profile and local objective observables, without generating variants.
 profile=[]
 for axis in ('east_west','north_south'):
  for k in range(-8,9):
   rr,cc=(r0,c0+k) if axis=='east_west' else (r0+k,c0)
   idx=(rr-rlo,cc-clo)
   profile.append({'axis':axis,'offset':k,'row':rr,'col':cc,'x_m':cc*6,'z_m':12282-rr*6,'height_B_m':float(h[rr,cc]),'class':int(cls[rr,cc]),'max_incident_water_level_m':float(level[idx]),'dry_margin_m':float(lev_margin[idx]),'wet_support_mask':bool(wet_support[rr,cc]),'actual_wet_vertex_by_sign':bool(wet[idx]),'other_fixed':bool(other[rr,cc]),'engineering_halo':bool(eng[rr,cc]),'large_lake_bank':bool(large[rr,cc]),'reserve':bool(reserve[rr,cc]),'platform':bool(platform[rr,cc]),'safe_free_rule':bool(unprotected_class0[rr,cc] and not wet[idx]),'downward_room_under_EV79_budget_and_sign_m':float(downward_room[idx])})
 def counts(bounds):
  ra,rb,ca,cb=bounds; sl=np.s_[ra:rb,ca:cb]
  loc=np.s_[ra-rlo:rb-rlo,ca-clo:cb-clo]
  total=(rb-ra)*(cb-ca); free=unprotected_class0[sl] & ~wet[loc]; levels=lev_margin[loc]; rooms=downward_room[loc]; iswet=wet[loc]
  lower_ok=lower[loc] <= upper[loc]
  return {'bounds_rc_half_open':[ra,ca,rb,cb],'nodes':total,'free_class0_dry_unprotected':int(free.sum()),'not_class0':int((~cls0[sl]).sum()),'other_fixed':int(other[sl].sum()),'engineering_halo':int(eng[sl].sum()),'large_lake_bank':int(large[sl].sum()),'reserve':int(reserve[sl].sum()),'platform':int(platform[sl].sum()),'union_protected':int(protected[sl].sum()),'EV79_wet_support':int(wet_support[sl].sum()),'actually_wet_by_incident_P_F_SEA_sign':int(iswet.sum()),'wet_support_but_sign_dry':int((wet_support[sl]&~iswet).sum()),'actual_dry_water_design_or_SEA':int((~iswet).sum()),'free_wet_support_vertices':int((free&wet_support[sl]).sum()),'free_dry_no_support_vertices':int((free&~wet_support[sl]).sum()),'free_nodes_with_feasible_EV79_budget_and_sign_lower':int((free&lower_ok).sum()),'free_nodes_with_room_ge_0_1m':int((free&(rooms>=.1)).sum()),'free_nodes_with_room_ge_0_5m':int((free&(rooms>=.5)).sum()),'free_nodes_with_room_ge_1m':int((free&(rooms>=1.0)).sum()),'minimum_dry_margin_among_free_m':float(levels[free].min()) if free.any() else None,'maximum_dry_margin_among_free_m':float(levels[free].max()) if free.any() else None,'minimum_downward_room_free_m':float(rooms[free].min()) if free.any() else None,'maximum_downward_room_free_m':float(rooms[free].max()) if free.any() else None}
 c_metrics=[]
 for name,bounds in windows.items(): c_metrics.append({'window':name,**counts(bounds)})
 # The exact 5x5 target core and wider 13x13 core are the potential mutable zones;
 # the 17x17 window supplies a two-node (12m) fixed collar.
 b_profile={x['offset']:x['height_B_m'] for x in profile if x['axis']=='east_west'}
 n_profile={x['offset']:x['height_B_m'] for x in profile if x['axis']=='north_south'}
 center=float(h[r0,c0]); axial={}
 for axis,pr in [('east_west',b_profile),('north_south',n_profile)]:
  axial[axis]={'negative_neighbor_m':pr[-1],'positive_neighbor_m':pr[1], 'center_minus_negative_m':center-pr[-1], 'center_minus_positive_m':center-pr[1], 'prominence_vs_higher_1step_neighbor_m':center-max(pr[-1],pr[1]),'1step_difference_m':[pr[-1]-center,pr[1]-center]}
 lap=4*center-(float(h[r0-1,c0])+float(h[r0+1,c0])+float(h[r0,c0-1])+float(h[r0,c0+1]))
 discovery=json.loads(DISC.read_text(encoding='utf-8'))
 seed=next(s for s in discovery['foci'][0]['residual_seed_examples'] if s['row']==r0 and s['col']==c0)
 wide=next(x for x in c_metrics if x['window']=='17x17_window'); core=next(x for x in c_metrics if x['window']=='13x13_core')
 collar={'nodes':wide['nodes']-core['nodes'],'would_be_free_but_fixed_by_2node_collar':wide['free_class0_dry_unprotected']-core['free_class0_dry_unprotected'],'protected_or_actual_wet':wide['union_protected']-core['union_protected'],'EV79_wet_support':wide['EV79_wet_support']-core['EV79_wet_support'],'actual_wet_by_sign':wide['actually_wet_by_incident_P_F_SEA_sign']-core['actually_wet_by_incident_P_F_SEA_sign']}
 result={'status':'READ_ONLY_PROFILE_PILOT_DIAGNOSIS','base':{'name':'EV82-B deployed preview; do not use EV87 as base','B_sha256':sha(bpath),'EV82B_deploy_status':json.loads((BASE/'deploy.json').read_text(encoding='utf-8'))['status'],'compiled_wrp_sha256':json.loads((BASE/'deploy.json').read_text(encoding='utf-8'))['compiled_wrp_sha256'],'water_pbo_sha256':json.loads((BASE/'deploy.json').read_text(encoding='utf-8'))['files']['baltic_water_v30.pbo'],'EV79_budget_source_sha256':sha(ep),'P_sha256':sha(ppath),'F_sha256':sha(fpath),'constraints_sha256':sha(cpath),'discovery_sha256':sha(DISC)},'focus':{'row':r0,'col':c0,'x_m':c0*6,'z_m':12282-r0*6,'B_height_m':center,'B_cls':int(cls[r0,c0]),'max_incident_angle_from_discovery_deg':float(seed['angle_deg']),'axial_prominence_from_discovery_m':float(seed['prominence_m']),'EV79_fixed':bool(c['fixed'][r0,c0]),'EV79_wet_support':bool(wet_support[r0,c0]),'other_fixed':bool(other[r0,c0]),'engineering_halo':bool(eng[r0,c0]),'large_lake_bank':bool(large[r0,c0]),'reserve':bool(reserve[r0,c0]),'platform':bool(platform[r0,c0]),'max_incident_water_level_B_m':float(level[r0-rlo,c0-clo]),'dry_margin_B_m':float(lev_margin[r0-rlo,c0-clo]),'nearest_local_wet_polygon_distance_from_discovery_m':4.304323275835005,'axial_prominence_recomputed_from_B_m':axial,'4neighbor_discrete_laplacian_m':lap},'window_counts':c_metrics,'17x17_outer_two_node_collar':collar,'profile_cuts_B':profile,'limitations':['F/SEA sign level diagnostic uses max over incident corner samples; it does not infer a fixed water polygon.','Water crossings and exact connected components need the independent face-based consumer; these counts are not an acceptance gate.','Free-node counts do not imply a feasible curvature solution.']}
 out=OUT/'profile-pilot-diagnostic.json';out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({'output':str(out),'focus':result['focus'],'windows':c_metrics},indent=2))
if __name__=='__main__':main()
