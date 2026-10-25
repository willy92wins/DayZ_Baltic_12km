"""Independent EV112 OT4b gate. Shared geometry only; no producer diagnostics trusted.
This gate covers c2-c7 after the separately checked c0/c1 pass. The 015-45 disk
always remains PENDING, including when every measurable site criterion passes.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
import numpy as np
from scipy.spatial import cKDTree

P=Path(__file__).resolve().parents[4]
BASE_SHA='c91fdffe675ab45e8b62439ff16fe9d4fc39958a707316e4022712831cd91e83'
INPUT_HASHES={'cover':'9253ae323a9f04252604dda33224464e8b1e394c6d4b8c64bcf40782172ee16e','envelope':'cc45e2ef667ae2ba78de4c11283c648d2293c53303148f9247361b639a0e73a6'}
SITES={'c2':(10235,9398),'c3':(8568,10414),'c4':(10417,9426),'c5':(8227,10468),'c6':(3588,6867),'c7':(9678,2661)}
POCKET=np.array([[482,1705],[483,1704],[483,1705],[484,1702],[484,1703],[484,1704],[484,1705],[485,1701],[485,1702],[485,1703],[485,1704]])
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser()
 for k in ('before','after','cover','envelope','out'):ap.add_argument(k,type=Path)
 a=ap.parse_args();a.out.mkdir(exist_ok=False)
 sys.path[:0]=[str(P/'tools/water'),str(P/'tools/terrain')];import shore_ramp_v31 as sr
 fail=[];rep={'schema':'ev112-ot4b-gate.v1','inputs':{k:{'path':str(getattr(a,k)),'sha256':sha(getattr(a,k))} for k in ('before','after','cover','envelope')},'tool_sha256':sha(__file__),'pending':{'015-45':{'centre':[10397.4,9421.9],'radius_m':60,'status':'PENDING'}}}
 if rep['inputs']['before']['sha256']!=BASE_SHA:raise ValueError('before terrain is not the frozen EV112 chain after c0/c1')
 for k,expected in INPUT_HASHES.items():
  if rep['inputs'][k]['sha256']!=expected:raise ValueError(k+' is not the frozen EV112 chain input')
 rep['dependencies']={str(p):sha(p) for p in (P/'tools/water/shore_ramp_v31.py',P/'tools/water/pond_footprint_v31.py',P/'tools/water/bury_edges_v31.py')}
 b=np.load(a.before,allow_pickle=False);n=np.load(a.after,allow_pickle=False);hb=b['heights'];hn=n['heights'];ch=hn!=hb
 if hn.shape!=(2048,2048) or hn.dtype!=np.float32 or not np.isfinite(hn).all():raise ValueError('invalid finite float32 heights')
 if set(b.files)!=set(n.files):fail.append('array inventory changed')
 for k in set(b.files)&set(n.files)-{'heights','v31_causeway'}:
  if b[k].dtype!=n[k].dtype or not np.array_equal(b[k],n[k],equal_nan=b[k].dtype.kind=='f'):fail.append('array changed: '+k)
 if not np.array_equal(n['v31_causeway'],b['v31_causeway']|ch):fail.append('causeway mask mismatch')
 cross,src=sr.pending_crossings(extra_built=[str(P/'evidence/v31-pond-layer-2026-10-13/bridges/ev110/sites-ev110.json')]);prot,pinfo=sr.base_protection(b,cross,sr.PARAMS);rep['protected_changed']=int((ch&prot).sum());rep['crossings']=src
 if rep['protected_changed']:fail.append('protected terrain changed')
 r,c=np.nonzero(ch);x,z=sr.vxz(r,c);inside=np.zeros(len(r),bool)
 for sx,sz in SITES.values():inside|=(abs(x-sx)<=220)&(abs(z-sz)<=220)
 if not inside.all():fail.append('changed vertices outside the six site work areas')
 slope=sr.slope_guard(hb,r,c,hn[r,c],sr.PARAMS);rep['slope']=slope
 if slope[0]:fail.append('new or worsened steep triangles')
 approved=np.zeros(hn.shape,bool);approved[POCKET[:,0],POCKET[:,1]]=True
 if not np.all(hn[approved]==np.float32(1.05)) or not np.all(hb[approved]<.75):fail.append('exact approved 11-vertex fill not present')
 undo=hn.copy();undo[approved]=hb[approved];top,bad=sr.sea_topology(hb,undo);rep['sea_without_approved_fill']=top
 if bad:fail.append('unapproved sea component change')
 top,bad=sr.sea_topology(hb,hn);rep['sea']=top
 if top!=dict(before=82,after=81,created=0,removed=1,split=0,merged=0):fail.append('sea change is not solely the approved pocket')
 fps=[]
 for tag,terrain in [('before',a.before),('after',a.after)]:
  dest=a.out/('fp-'+tag)
  with (a.out/(tag+'-fp.log')).open('w') as f:rc=subprocess.run([sys.executable,'-I',str(P/'tools/water/pond_footprint_v31.py'),str(terrain),str(a.cover),str(dest),str(a.envelope)],stdout=f,stderr=subprocess.STDOUT).returncode
  if rc:raise RuntimeError('physical footprint generation failed: '+tag)
  fps.append(np.load(dest/'footprint.npz',allow_pickle=False))
 fb,fn=fps;env=np.isfinite(np.load(a.envelope));mb=sr.fp_masks(hb,fb['plane'],fb['field'],env,sr.PARAMS);mn=sr.fp_masks(hn,fn['plane'],fn['field'],env,sr.PARAMS)
 rep['new_water_defects']={k:int((mn[k]&~mb[k]).sum()) for k in ('exposed','env_leak','bed_low','pond_sea','field_dev')}
 if any(rep['new_water_defects'].values()):fail.append('new physical water defect')
 frep=json.loads((a.out/'fp-after/footprint-report.json').read_text());rep['field_checks']=frep['field_checks']
 if any(v['max_wet_seam_m']>1e-5 for v in rep['field_checks']):fail.append('discontinuous wet field seam')
 def pondwet(h,f):
  w=np.full(h.shape,-np.inf);finite=np.isfinite(f['plane'])
  for k,(dr,dc) in enumerate(sr.COFF):
   sl=(slice(dr,dr+sr.NC),slice(dc,dc+sr.NC));w[sl]=np.maximum(w[sl],np.where(finite,f['field'][:,:,k],-np.inf))
  return h<w
 wb,wn=pondwet(hb,fb),pondwet(hn,fn)
 for name,ob,on in [('pond',wb,wn),('pond_dry_complement',~wb,~wn)]:
  top,bad=sr.sea_topology(np.where(ob,0.,1.),np.where(on,0.,1.));rep[name]=top
  if bad:fail.append(name+' topology changed')
 measure={}
 for sid,(sx,sz) in SITES.items():
  r0=int((sr.ZTOP-sz-150)/6);r1=int((sr.ZTOP-sz+150)/6)+1;c0=int((sx-150)/6);c1=int((sx+150)/6)+1;rr,cc=np.mgrid[r0:r1+1,c0:c1+1];xx,zz=sr.vxz(rr,cc);pm=b['platform'][rr,cc];tree=cKDTree(np.c_[xx[pm],zz[pm]]);measure[sid]={}
  for tag,h,f in [('before',hb,fb),('after',hn,fn)]:
   W,fp=sr.corner_water(f['plane'],f['field']);seg=sr.extract_segments(h.astype(float),W,fp,f['plane'],r0,r1,c0,c1);measure[sid][tag]={}
   for pond in (False,True):
    vals=[];pending=0
    for line in sr.chain(sr.subseg(seg,seg['pond']==pond)):
     q,v=sr.wiggle_profile(sr.canonical(line['pts'],line['closed']),line['closed'],12.,.5);near=(tree.query(q)[0]<=30)&np.isfinite(v);disk=np.hypot(q[:,0]-10397.4,q[:,1]-9421.9)<60;pending+=int((near&disk).sum());vals.extend(v[near&~disk].tolist())
    if vals:measure[sid][tag]['pond' if pond else 'sea']={'p90':float(np.percentile(vals,90)),'max':float(max(vals)),'samples':len(vals),'pending_samples':pending}
  bef,aft=measure[sid]['before'],measure[sid]['after']
  if not aft or not set(bef).issubset(aft):fail.append(sid+' missing measured water body')
  for body,v in aft.items():
   if v['p90']>.03:fail.append(f'{sid}/{body} wiggle {v["p90"]} > .03')
 rep['measurements']=measure
 with (a.out/'bury.log').open('w') as f:rc=subprocess.run([sys.executable,'-I',str(P/'tools/water/bury_edges_v31.py'),str(a.after),str(a.before),str(a.cover),str(a.envelope),str(a.out/'fp-before/footprint-report.json'),str(a.out/'buried.npz'),str(a.out/'bury-work'),str(a.out/'bury-report.json')],stdout=f,stderr=subprocess.STDOUT).returncode
 if rc:raise RuntimeError('bury check failed')
 br=json.loads((a.out/'bury-report.json').read_text());rep['bury']={k:br[k] for k in ('final_new_exposed','changed_vs_input')}
 if any(rep['bury'].values()):fail.append('bury still changes terrain or leaves new edges')
 rep['fails']=fail;rep['measurable_sites_pass']=not fail;rep['verdict']='FAIL' if fail else 'PASS_OUTSIDE_PENDING_01545'
 (a.out/'gate.json').write_bytes(json.dumps(rep,indent=2).encode());print(json.dumps({'verdict':rep['verdict'],'fails':fail}));return int(bool(fail))

if __name__=='__main__':sys.exit(main())
