from pathlib import Path
B=Path(__file__).parent; OLD=B.parent/'v30-volkhov-bed-proposal-20261009'
code=(OLD/'verify.py').read_text()
needle='depth_error=0.;visible_error=0.'
insert='''depth_error=0.;visible_error=0.
# Independent support from all physical/visible positive-depth native triangles.
hv=np.stack([h[dr:dr+2047,dc:dc+2047] for dr,dc in nw],axis=2)
required=np.zeros(f.shape,bool)
for tri in [(0,1,3),(0,2,3)]:
    wet=np.isfinite(p)&(np.maximum(p[:,:,None]-hv,f-hv)[:,:,tri].max(axis=2)>1e-8)
    for k in tri:required[:,:,k]|=wet
'''
assert code.count(needle)==1; code=code.replace(needle,insert)
code=code.replace('finite=np.isfinite(p)','finite=np.isfinite(p)&required[:,:,j]')
needle="gates=dict(outside_exact="
insert='''
# Re-evaluate the original local level policy against this actual terrain.
perched_bad=[]; rings=json.loads((R/'v30-low-flowing-support-scope-20261009/volkhov-policy.json').read_text())['all_rings']
allwater=np.zeros(h.shape,bool)
for dr,dc in nw:allwater[dr:dr+2047,dc:dc+2047]|=np.isfinite(p)
for ring in rings:
    r,c=ring['row'],ring['col']; ar,br=max(0,r-10),min(2048,r+12); ac,bc=max(0,c-10),min(2048,c+12)
    rows,cols=np.mgrid[ar:br,ac:bc]; dist=np.hypot(rows-r-.5,cols-c-.5)*6
    mask=(a['cls'][ar:br,ac:bc]==0)&~allwater[ar:br,ac:bc]&~d['fixed'][ar:br,ac:bc]&(dist>ring['inner'])&(dist<=ring['outer'])
    assert int(mask.sum())==ring['vertices']
    old=float(p[r,c]-np.median(h[ar:br,ac:bc][mask])); new=float(q[r,c]-np.median(v[ar:br,ac:bc][mask]))
    if new>max(.3,old)+1e-6:perched_bad.append(dict(row=r,col=c,before=old,after=new))
negatives=dict(stale_terrain_rejected=geometry(h,np.repeat(q[:,:,None],4,axis=2),cells).symmetric_difference(gb).area>.002)
assert all(negatives.values())
gates=dict(converged=rec['solver_success'],perched_policy=not perched_bad,outside_exact='''
assert code.count(needle)==1; code=code.replace(needle,insert)
code=code.replace("report=dict(status=","report=dict(perched_failures=perched_bad,policy_rings=len(rings),negatives=negatives,status=")
code=code.replace("'Independent geometry, not native deployment or graphical proof.'","'Independent geometry; depth is preserved on actually wet triangles, and dry faces are checked by GEOS/connectivity. Native and graphics pending.'")
(B/'verify.py').write_text(code)
