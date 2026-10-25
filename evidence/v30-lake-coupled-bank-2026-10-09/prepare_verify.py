from pathlib import Path
B=Path(__file__).parent;old=Path('E:/DayZ-Baltic-Build/v30-lake-native-bank-finish-20261009')
s=(old/'verify.py').read_text()
s=s.replace("fixed=np.load('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/constraints.npz')['fixed']|support|t['water']|t['beach']|(t['cls']!=0)","""f=np.load('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy')
 pmax=np.full(h.shape,-np.inf);pmin=np.full(h.shape,np.inf);fmax=np.full(h.shape,-np.inf)
 for slot,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
  valid=np.isfinite(p);sl=np.s_[dr:dr+2047,dc:dc+2047]
  pmax[sl]=np.fmax(pmax[sl],p);pmin[sl]=np.fmin(pmin[sl],p);fmax[sl]=np.maximum(fmax[sl],np.where(valid,f[:,:,slot],-np.inf))
 maxwater=np.maximum(pmax,fmax);dry_support=support&(h>maxwater)
 mixed=support&((pmax-pmin)>1e-5)
 fixed=np.load('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/constraints.npz')['fixed']|(support&~dry_support)|mixed|t['water']|t['beach']|(t['cls']!=0)""")
s=s.replace("floor[scope]=np.minimum(h[scope],target);banks[name]=bank", """local_floor=np.full(h.shape,target);local_floor[dry_support]=np.maximum(1.8,maxwater[dry_support]+.0501)
  floor[scope]=np.minimum(h[scope],local_floor[scope]);banks[name]=bank""")
s=s.replace("gates=basic(h,v,allowed,fixed,support,floor);", "gates=basic(h,v,allowed,fixed,support&~dry_support,floor);")
s=s.replace("result=dict(status='PASS_LAKE_NATIVE_BANK_SOURCE' if all(gates.values()) else 'REJECTED_LAKE_NATIVE_BANK_SOURCE'", """crossing=verify_crossings(h,v,p,f)
 gates['physical_visible_signs_exact']=crossing['sign_changes']==0
 gates['max_crossing_displacement']=crossing['maximum_m']<=4.100001
 result=dict(status='PASS_LAKE_COUPLED_BANK_SOURCE' if all(gates.values()) else 'REJECTED_LAKE_COUPLED_BANK_SOURCE'""")
s=s.replace("controls=tests,limits=", "controls=tests,crossings=crossing,limits=")
s=s.replace("Water levels, bed, outline and all native water support vertices exact.","Water levels and bed exact; dry shoreline supports and subcell crossings intentionally change. Coverage is a separate gate.")
extra='''
def verify_crossings(h,v,p,f):
 changed=v!=h
 touch=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
 rr,cc=np.nonzero(touch&np.isfinite(p))
 old=np.stack((h[rr,cc],h[rr,cc+1],h[rr+1,cc],h[rr+1,cc+1]),axis=1)
 new=np.stack((v[rr,cc],v[rr,cc+1],v[rr+1,cc],v[rr+1,cc+1]),axis=1)
 signs=0;shifts=[];counts={}
 for name,field in [('physical',np.repeat(p[rr,cc,None],4,axis=1)),('visible',f[rr,cc])]:
  a=field-old;b=field-new;signs+=int(np.count_nonzero(np.sign(a)!=np.sign(b)));parts=[]
  for i,j,length in [(0,1,6),(0,2,6),(0,3,6*2**.5),(1,3,6),(2,3,6)]:
   crossing=a[:,i]*a[:,j]<0
   ta=a[crossing,i]/(a[crossing,i]-a[crossing,j]);tb=b[crossing,i]/(b[crossing,i]-b[crossing,j]);parts.extend((abs(ta-tb)*length).tolist())
  shifts.extend(parts);counts[name]=dict(edges=len(parts),maximum_m=float(max(parts,default=0)),p90_m=float(np.percentile(parts,90)) if parts else 0)
 return dict(changed_water_cells=len(rr),sign_changes=signs,maximum_m=float(max(shifts,default=0)),fields=counts)

'''
s=s.replace("if __name__=='__main__':main()",extra+"if __name__=='__main__':main()")
(B/'verify.py').write_text(s)
print(B/'verify.py')
