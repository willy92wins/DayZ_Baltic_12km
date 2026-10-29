#!/usr/bin/env python3
import argparse,copy,hashlib,importlib.util,json,math,sys
from fractions import Fraction
from pathlib import Path
P=48;SCALE=1<<P;MAXBITS=4096;QOPS=100000;COPS=4000000;MAXE=14000;THR=Fraction(3022314549036573,302231454903657293676544)
KP='tools/quality/certified_shore_kernel_ev112.py';TP='tools/quality/shore_numeric_discovery_ev112.py'
KNOWN={KP:'ef844931862c1aa2d181caa5000b4843a4b1587da7149fb033a8efa5248abe64','tools/quality/verify_certified_shore_kernel_ev112.py':'ab1977bc1ed283d00cb9aedab56ad1b83d2596a17f49c3558825aeec3ec8f2ca',TP:'3264f82294a2411e4f1d902c42173a01ef1f72244d6b220bba91e49a4596b696'}
class Bad(Exception): pass
class Resource(Exception): pass
K=None;TR=None;_ROOT=None;_QB=None
def _load_mod(root,rel,helpers=None):
 p=Path(root)/rel
 try:
  with open(p,'rb') as fh: data=fh.read(17*1024*1024)
 except Exception as e: raise Bad('helperread:'+str(e))
 if len(data)>=17*1024*1024: raise Bad('helperlarge')
 sha=hashlib.sha256(data).hexdigest()
 if sha!=KNOWN[rel]: raise Bad('helperpin:'+rel)
 if helpers is not None and helpers.get(rel)!=sha: raise Bad('contracthelperpin:'+rel)
 spec=importlib.util.spec_from_file_location('sealed_p_'+sha[:12],str(p))
 mod=importlib.util.module_from_spec(spec);mod.__file__=str(p);exec(compile(data,str(p),'exec'),mod.__dict__);return mod
def load_helpers(root,helpers=None):
 global K,TR,_ROOT
 root=Path(root)
 if helpers is not None and helpers!=KNOWN: raise Bad('contracthelperpin')
 if K is not None and _ROOT is not None and root.resolve()!=_ROOT: K=None;TR=None
 if K is None: K=_load_mod(root,KP,helpers)
 if TR is None: TR=_load_mod(root,TP,helpers)
 _ROOT=root.resolve();return K
def _ensure():
 if K is None: load_helpers(Path(__file__).resolve().parents[2])
class _Prepared:
 __slots__=('cache','pts')
 def __init__(self,cache,pts): self.cache=cache;self.pts=pts
def _cbudget():
 class CB(K.Budget):
  def __init__(self,limit=COPS):
   super().__init__();self.limit=limit
  def tick(self,n=1):
   self.ops+=n
   if self.ops>self.limit: raise Resource('chainops')
 return CB()
def _itick(bud,a,b):
 if _bits(a)>MAXBITS or _bits(b)>MAXBITS or max(_bits(a),_bits(b))+1>MAXBITS: raise Resource('intbits')
 try: bud.tick()
 except Exception as e:
  if e.__class__.__name__=='Res': raise Resource('queryops')
  raise
def _iadd(a,b,bud): _itick(bud,a,b);return a+b
def _isub(a,b,bud): _itick(bud,a,b);return a-b
def _bits(x): return abs(int(x)).bit_length()
def _frac(v):
 if isinstance(v,Fraction): return v
 if type(v) is int:
  if _bits(v)>MAXBITS: raise Resource('bits')
  return Fraction(v)
 if type(v) is float:
  if not math.isfinite(v): raise Bad('nonfinite')
  n,d=v.as_integer_ratio();return Fraction(n,d)
 if isinstance(v,list) and len(v)==2 and type(v[0]) is int and type(v[1]) is int and v[1]>0:
  if _bits(v[0])>MAXBITS or _bits(v[1])>MAXBITS: raise Resource('bits')
  return Fraction(v[0],v[1])
 raise Bad('number')
def _encf(f): return [f.numerator,f.denominator]
def _points_frac(points):
 if not isinstance(points,list) or not (2<=len(points)<=MAXE+1): raise Bad('points')
 out=[]
 for p in points:
  if not isinstance(p,list) or len(p)!=2: raise Bad('point')
  out.append((_frac(p[0]),_frac(p[1])))
 return out
def build_cache(points,closed,meta=None):
 _ensure()
 if type(closed) is not bool: raise Bad('closed')
 if meta is not None and not isinstance(meta,dict): raise Bad('meta')
 pts=_points_frac(points)
 n=len(pts);m=n if closed else n-1
 if m<1 or m>MAXE: raise Bad('edges')
 edges=[];pref_lo=[0];pref_hi=[0];deg=[];maxb=0;bud=_cbudget();t2=K.fmul(bud,THR,THR)
 for i in range(m):
  a=pts[i];b=pts[(i+1)%n]
  try:
   dx=K.fsub(bud,b[0],a[0]);dz=K.fsub(bud,b[1],a[1]);q=K.fadd(bud,K.fmul(bud,dx,dx),K.fmul(bud,dz,dz));lo,hi=K.sqrt_witnesses(bud,q);isdeg=K.fcmp(bud,q,t2)<0
  except Resource: raise
  except Exception as e:
   if e.__class__.__name__=='Res': raise Resource('chainops')
   raise Bad('witness:'+str(e))
  if _bits(lo)>MAXBITS or _bits(hi)>MAXBITS or hi-lo not in (0,1): raise Bad('witnesscanon')
  maxb=max(maxb,_bits(q.numerator),_bits(q.denominator))
  nlo=_iadd(pref_lo[-1],lo,bud);nhi=_iadd(pref_hi[-1],hi,bud)
  pref_lo.append(nlo);pref_hi.append(nhi);edges.append({'q':_encf(q),'lo':lo,'hi':hi})
  if isdeg: deg.append(i)
 cache={'meta':copy.deepcopy(meta) if meta is not None else {},'closed':closed,'points':[[_encf(c) for c in p] for p in pts],'edges':edges,'pref_lo':pref_lo,'pref_hi':pref_hi,'degenerate_indices':deg,'counters':{'edges':m,'ops':bud.ops,'max_bits':maxb}}
 return cache
def _val_cache(cache):
 if not isinstance(cache,dict) or set(cache)!={'meta','closed','points','edges','pref_lo','pref_hi','degenerate_indices','counters'}: raise Bad('cachekeys')
 if not isinstance(cache['meta'],dict) or type(cache['closed']) is not bool: raise Bad('cachemeta')
 pts=_points_frac(cache['points'])
 rawpts=[]
 for p in cache['points']:
  for c in p:
   if not isinstance(c,list) or len(c)!=2 or type(c[0]) is not int or type(c[1]) is not int or c[1]<=0 or Fraction(c[0],c[1]).numerator!=c[0] or Fraction(c[0],c[1]).denominator!=c[1]: raise Bad('pointratio')
 n=len(pts);m=n if cache['closed'] else n-1
 if not isinstance(cache['edges'],list) or len(cache['edges'])!=m or m>MAXE: raise Bad('edgecount')
 for e in cache['edges']:
  if not isinstance(e,dict) or set(e)!={'q','lo','hi'}: raise Bad('edgekeys')
  if not isinstance(e['q'],list) or len(e['q'])!=2 or type(e['q'][0]) is not int or type(e['q'][1]) is not int or e['q'][1]<=0: raise Bad('q')
  if type(e['lo']) is not int or type(e['hi']) is not int or e['lo']<0 or e['hi']<e['lo'] or e['hi']-e['lo']>1: raise Bad('witnessrange')
  if max(_bits(e['q'][0]),_bits(e['q'][1]),_bits(e['lo']),_bits(e['hi']))>MAXBITS: raise Resource('edgebits')
 for name in ('pref_lo','pref_hi'):
  v=cache[name]
  if not isinstance(v,list) or len(v)!=m+1 or v[0]!=0 or any(type(x) is not int or x<0 for x in v) or any(v[i]>v[i+1] for i in range(m)): raise Bad(name)
  if any(_bits(x)>MAXBITS for x in v): raise Resource('prefixbits')
 if not isinstance(cache['degenerate_indices'],list) or any(type(x) is not int for x in cache['degenerate_indices']): raise Bad('deg')
 c=cache['counters']
 if not isinstance(c,dict) or set(c)!={'edges','ops','max_bits'} or c['edges']!=m or type(c['ops']) is not int or not (0<=c['ops']<=COPS) or type(c['max_bits']) is not int or c['max_bits']<0 or c['max_bits']>MAXBITS: raise Bad('counters')
 bud=_cbudget();t2=K.fmul(bud,THR,THR);deg=[];pl=[0];ph=[0]
 for i,e in enumerate(cache['edges']):
  a=pts[i];b=pts[(i+1)%n]
  try:
   dx=K.fsub(bud,b[0],a[0]);dz=K.fsub(bud,b[1],a[1]);q=K.fadd(bud,K.fmul(bud,dx,dx),K.fmul(bud,dz,dz));lo,hi=K.sqrt_witnesses(bud,q);isdeg=K.fcmp(bud,q,t2)<0
  except Resource: raise
  except Exception as ex:
   if ex.__class__.__name__=='Res': raise Resource('chainops')
   raise Bad('witness:'+str(ex))
  if q!=Fraction(e['q'][0],e['q'][1]) or lo!=e['lo'] or hi!=e['hi']: raise Bad('edgerecompute')
  pl.append(_iadd(pl[-1],lo,bud));ph.append(_iadd(ph[-1],hi,bud))
  if isdeg: deg.append(i)
 if pl!=cache['pref_lo'] or ph!=cache['pref_hi']: raise Bad('prefix')
 if deg!=cache['degenerate_indices']: raise Bad('degenerate')
 return _Prepared(cache,pts)
def _range(cache,a,b):
 if _QB is not None: return (Fraction(_isub(cache['pref_lo'][b],cache['pref_lo'][a],_QB),SCALE),Fraction(_isub(cache['pref_hi'][b],cache['pref_hi'][a],_QB),SCALE))
 return (Fraction(cache['pref_lo'][b]-cache['pref_lo'][a],SCALE),Fraction(cache['pref_hi'][b]-cache['pref_hi'][a],SCALE))
def _idx(n,center,direction,k,closed): return (center+direction*k)%n if closed else center+direction*k
def _dir_pref(cache,center,direction,closed,k):
 if k==0: return (Fraction(0),Fraction(0))
 pl=cache['pref_lo'];ph=cache['pref_hi'];m=len(cache['edges']);n=len(cache['points'])
 def rs(a,b): return ((_isub(pl[b],pl[a],_QB),_isub(ph[b],ph[a],_QB)) if _QB is not None else (pl[b]-pl[a],ph[b]-ph[a]))
 if direction>0:
  if not closed: v=rs(center,center+k)
  elif center+k<=m: v=rs(center,center+k)
  else:
   x=rs(center,m);y=rs(0,(center+k)%m);v=(_iadd(x[0],y[0],_QB),_iadd(x[1],y[1],_QB))
 else:
  if not closed: v=rs(center-k,center)
  elif center-k>=0: v=rs(center-k,center)
  else:
   x=rs(0,center);y=rs(m+(center-k),m);v=(_iadd(x[0],y[0],_QB),_iadd(x[1],y[1],_QB))
 return (Fraction(v[0],SCALE),Fraction(v[1],SCALE))
def _dir_edge(cache,center,direction,k,closed):
 n=len(cache['points']);frm=_idx(n,center,direction,k,closed);to=_idx(n,center,direction,k+1,closed)
 ei=frm if direction>0 else to
 if closed: ei%=n
 return ei,frm,to
def _station(b,cache,pts,center,direction,closed,seg,frm,to,t):
 pt=[]
 for kk in (0,1):
  d=K.fsub(b,pts[to][kk],pts[frm][kk])
  try: prod=K.imul(b,t,(d,d));v=K.iadd(b,(pts[frm][kk],pts[frm][kk]),prod)
  except Exception as e:
   if e.__class__.__name__=='Res': raise Resource('station')
   raise
  pt.append(v)
 return {'segment':seg,'from':pts[frm],'to':pts[to],'t':t,'point':(pt[0],pt[1])}
def _locate(b,cache,pts,center,direction,closed,h):
 n=len(pts);steps=(n if closed else (center if direction<0 else n-1-center))
 cen=pts[center]
 if steps==0:
  if K.fcmp(b,h,Fraction(0))==0: return {'segment':None,'from':cen,'to':cen,'t':(Fraction(0),Fraction(0)),'point':((cen[0],cen[0]),(cen[1],cen[1]))}
  return 'OUT_OF_RANGE'
 if K.fcmp(b,h,Fraction(0))==0:
  ei,frm,to=_dir_edge(cache,center,direction,0,closed);return _station(b,cache,pts,center,direction,closed,0,frm,to,(Fraction(0),Fraction(0)))
 total=_dir_pref(cache,center,direction,closed,steps)
 if K.fcmp(b,total[0],total[1])==0 and K.fcmp(b,h,total[0])==0 and not closed:
  ei,frm,to=_dir_edge(cache,center,direction,steps-1,closed);return _station(b,cache,pts,center,direction,closed,steps-1,frm,to,(Fraction(1),Fraction(1)))
 lo_i=0;hi_i=steps
 while lo_i<hi_i:
  mid=(lo_i+hi_i)//2;b.tick()
  if K.fcmp(b,_dir_pref(cache,center,direction,closed,mid+1)[0],h)<=0: lo_i=mid+1
  else: hi_i=mid
 cand=lo_i
 for i in range(max(0,cand-2),min(steps,cand+3)):
  b.tick();S=_dir_pref(cache,center,direction,closed,i);N=_dir_pref(cache,center,direction,closed,i+1)
  ei,frm,to=_dir_edge(cache,center,direction,i,closed)
  if K.fcmp(b,S[0],S[1])==0 and K.fcmp(b,h,S[0])==0: return _station(b,cache,pts,center,direction,closed,i,frm,to,(Fraction(0),Fraction(0)))
  if K.fcmp(b,S[1],h)<0 and K.fcmp(b,h,N[0])<0:
   e=cache['edges'][ei];L=(Fraction(e['lo'],SCALE),Fraction(e['hi'],SCALE))
   try: t=K.idiv(b,K.isub(b,(h,h),S),L)
   except Exception as ex:
    if ex.__class__.__name__=='Res': raise Resource('t')
    raise Bad('t:'+str(ex))
   if K.fcmp(b,t[0],Fraction(0))<0 or K.fcmp(b,t[1],Fraction(1))>0: return 'BOUNDARY_UNCERTAIN'
   return _station(b,cache,pts,center,direction,closed,i,frm,to,t)
 if K.fcmp(b,h,total[1])>0: return 'OUT_OF_RANGE'
 return 'BOUNDARY_UNCERTAIN'
def query(cache,center,h):
 global _QB
 previous=_QB
 try: return _query(cache,center,h)
 except Exception as e:
  if e.__class__.__name__=='Res': raise Resource('queryops') from e
  raise
 finally: _QB=previous

def _query(cache,center,h):
 _ensure();prepared=cache if isinstance(cache,_Prepared) else _val_cache(cache);cache=prepared.cache;pts=prepared.pts;closed=cache['closed']
 if type(center) is not int or not (0<=center<len(pts)): return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None,'ops':0}
 try: hh=_frac(h)
 except Exception: return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None,'ops':0}
 b=K.Budget();globals().__setitem__('_QB',b)
 if K.fcmp(b,hh,Fraction(0))<0: return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None,'ops':0}
 if cache['degenerate_indices']: return {'state':'DEGENERATE','stations':None,'features':None,'support':None,'ops':0}
 m=len(cache['edges'])
 if closed:
  per=_range(cache,0,m);support={'perimeter':per,'backward':per,'forward':per};two=K.fmul(b,Fraction(2),hh)
  if K.fcmp(b,per[0],per[1])==0: supp='SUPPORTED' if K.fcmp(b,two,per[0])<0 else 'INSUFFICIENT_SUPPORT'
  elif K.fcmp(b,two,per[1])>=0: supp='INSUFFICIENT_SUPPORT'
  elif K.fcmp(b,two,per[0])<0: supp='SUPPORTED'
  else: supp='SUPPORT_UNCERTAIN'
 else:
  back=_range(cache,0,center);fwd=_range(cache,center,m);support={'perimeter':None,'backward':back,'forward':fwd};supp='SUPPORTED'
  for dist in (back,fwd):
   cur='SUPPORTED' if K.fcmp(b,dist[0],hh)>=0 else ('INSUFFICIENT_SUPPORT' if K.fcmp(b,dist[1],hh)<0 else 'SUPPORT_UNCERTAIN')
   if cur=='INSUFFICIENT_SUPPORT': supp=cur
   elif cur=='SUPPORT_UNCERTAIN' and supp=='SUPPORTED': supp=cur
 support['state']=supp;sup_enc=K.enc_support(support)
 if supp!='SUPPORTED': return {'state':supp,'stations':None,'features':None,'support':sup_enc,'ops':b.ops}
 try:
  A=_locate(b,cache,pts,center,-1,closed,hh)
  if isinstance(A,str): return {'state':A,'stations':None,'features':None,'support':sup_enc,'ops':b.ops}
  C=_locate(b,cache,pts,center,1,closed,hh)
  if isinstance(C,str): return {'state':C,'stations':None,'features':None,'support':sup_enc,'ops':b.ops}
  cen=pts[center];B={'segment':None,'from':cen,'to':cen,'t':(Fraction(0),Fraction(0)),'point':((cen[0],cen[0]),(cen[1],cen[1]))}
  feats=K.compute_features(b,None,A,B,C,hh)
 except Resource: raise
 except Exception as e:
  if e.__class__.__name__=='Res': raise Resource('queryops')
  raise
 state='UNDEFINED_ZERO_CHORD' if feats['chord_ac']['interval']==(Fraction(0),Fraction(0)) else 'DEFINED'
 return {'state':state,'stations':{'A':K.enc_station(A),'B':K.enc_station(B),'C':K.enc_station(C)},'features':{k:K.enc_field(v) for k,v in feats.items()},'support':sup_enc,'ops':b.ops}
# CLI
def _keys(o,s):
 if not isinstance(o,dict) or set(o)!=set(s): raise Bad('keys')
def _ishex(s): return isinstance(s,str) and len(s)==64 and all(c in '0123456789abcdef' for c in s)
def _validate_contract(c):
 _keys(c,{'schema','scope','plan_sha256','npz_path','npz_sha256','q02a_sha256','selectors','h','queries','p','threshold_ratio','max_bits','query_ops','chain_ops','max_edges','read_limits','output_limits','helpers','human_cases','controls','c1','natural_positive_count','calibration_ready','angle_state','budgets'})
 if c['schema']!='q02b2.v1' or c['scope']!='REAL_CONTOUR_NUMERIC_PILOT_ONLY' or c['p']!=48 or c['max_bits']!=4096 or c['query_ops']!=100000 or c['chain_ops']!=4000000 or c['max_edges']!=14000: raise Bad('contract')
 if c['h']!=[0,6,12,24,48,96] or c['threshold_ratio']!=[3022314549036573,302231454903657293676544]: raise Bad('hthr')
 if not _ishex(c['plan_sha256']) or not _ishex(c['npz_sha256']) or not _ishex(c['q02a_sha256']) or not isinstance(c['npz_path'],str): raise Bad('pins')
 if c['helpers']!=KNOWN: raise Bad('helpers')
 if c['human_cases']!={'count':9,'state':'GEOMETRY_UNBOUND','resolved':0} or c['controls']!=4 or c['c1']!='NOT_REVIEWED' or c['natural_positive_count']!=0 or c['calibration_ready'] is not False or c['angle_state']!='PENDING_CERTIFIED_ANGLE': raise Bad('claims')
 _keys(c['read_limits'],{'archive_bytes','required_uncompressed_bytes','header_bytes','members'});_keys(c['output_limits'],{'line_bytes','query_bytes','total_bytes'})
 _keys(c['budgets'],{'author_s','review_s','suite_s','capture_s','consumer_s','bytes'})
 for _v in list(c['read_limits'].values())+list(c['output_limits'].values())+list(c['budgets'].values()):
  if type(_v) is not int or _v<=0: raise Bad('limits')
 if c['read_limits']['archive_bytes']>67108864 or c['read_limits']['required_uncompressed_bytes']>8388608 or c['read_limits']['header_bytes']>16384 or c['read_limits']['members']>32 or c['output_limits']['line_bytes']>16777216 or c['output_limits']['query_bytes']>262144 or c['output_limits']['total_bytes']>67108864: raise Bad('limits')
 if not isinstance(c['selectors'],list) or len(c['selectors'])!=4: raise Bad('selectors')
 exp=0
 for s in c['selectors']:
  _keys(s,{'label','chain_id','closed','point_offset','segment_offset','core_count','core_float64_le_sha256','anchors','prior_degenerate_reason'})
  if not isinstance(s['label'],str) or type(s['chain_id']) is not int or type(s['closed']) is not bool: raise Bad('selector')
  for off in (s['point_offset'],s['segment_offset']):
   if not isinstance(off,list) or len(off)!=2 or any(type(x) is not int for x in off) or not (0<=off[0]<off[1]): raise Bad('offset')
  if s['core_count']!=(s['point_offset'][1]-s['point_offset'][0])-(1 if s['closed'] else 0) or not _ishex(s['core_float64_le_sha256']): raise Bad('core')
  if not isinstance(s['anchors'],list) or any(type(x) is not int for x in s['anchors']) or s['anchors']!=sorted(set(s['anchors'])) or any(not (0<=x<s['core_count']) for x in s['anchors']): raise Bad('anchors')
  if s['prior_degenerate_reason'] not in (None,'short_segment'): raise Bad('prior')
  if s['prior_degenerate_reason'] is None: exp+=len(s['anchors'])*len(c['h'])
  elif s['anchors']: raise Bad('deganchors')
 if len({s['label'] for s in c['selectors']})!=4 or len({s['chain_id'] for s in c['selectors']})!=4: raise Bad('selectorunique')
 if any(type(s['core_count']) is not int or type(s['chain_id']) is not int for s in c['selectors']): raise Bad('selectortype')
 if c['queries']!=exp: raise Bad('querycount')
 return c
def _read_file_bounded(path,limit):
 with open(path,'rb') as fh: data=fh.read(limit+1)
 if len(data)>limit: raise Bad('largefile')
 return data
def _load_contract(root,cpath,csha):
 data=_read_file_bounded(cpath,1024*1024)
 if hashlib.sha256(data).hexdigest()!=csha.lower(): raise Bad('contractsha')
 _ensure();c=K.parse_json(data);_validate_contract(c);return c,hashlib.sha256(data).hexdigest()
def _source_chains(contract,root):
 load_helpers(root,contract['helpers'])
 tc={'npz_path':contract['npz_path'],'npz_sha256':contract['npz_sha256'],'limits':contract['read_limits']}
 try: arrays,meta,other,before,after=TR._read_npz(tc)
 except Exception as e: raise Bad('npz:'+str(e))
 if set(arrays)!={'point_offsets','chain_offsets','chain_points','closed'}: raise Bad('arrays')
 po=arrays['point_offsets'];co=arrays['chain_offsets'];cp=arrays['chain_points'];cl=arrays['closed']
 pol=po.tolist();col=co.tolist();cll=cl.tolist()
 if str(po.dtype) not in ('int64','<i8') or str(co.dtype) not in ('int64','<i8') or str(cp.dtype) not in ('<f8','float64'): raise Bad('dtypes')
 if str(cl.dtype)!='bool' or len(cp.shape)!=2 or cp.shape[1]!=2: raise Bad('shapes')
 if len(pol)!=len(cll)+1 or len(col)!=len(cll)+1 or pol[0]!=0 or col[0]!=0 or pol[-1]!=cp.shape[0] or pol!=sorted(pol) or col!=sorted(col) or any(col[i+1]-col[i]!=pol[i+1]-pol[i]-1 for i in range(len(cll))) or len(cll)<1: raise Bad('monotonic')
 chains={}
 for s in contract['selectors']:
  ci=s['chain_id']
  if not (0<=ci<len(cll)) or ci+1>=len(pol): raise Bad('chainid')
  if pol[ci]!=s['point_offset'][0] or pol[ci+1]!=s['point_offset'][1]: raise Bad('pointoffset')
  if col[ci]!=s['segment_offset'][0] or col[ci+1]!=s['segment_offset'][1]: raise Bad('segmentoffset')
  if bool(cll[ci])!=s['closed']: raise Bad('closedflag')
  if s['core_count']!=(pol[ci+1]-pol[ci])-(1 if s['closed'] else 0) or (col[ci+1]-col[ci])!=(pol[ci+1]-pol[ci])-1: raise Bad('corecount')
  sub=cp[s['point_offset'][0]:s['point_offset'][1]];core=sub[:-1] if s['closed'] else sub
  if s['closed'] and (len(sub)<2 or sub[-1].astype('<f8').tobytes()!=sub[0].astype('<f8').tobytes()): raise Bad('closedrepeat')
  raw=core.astype('<f8').tobytes()
  if hashlib.sha256(raw).hexdigest()!=s['core_float64_le_sha256']: raise Bad('corehash')
  pts=[]
  for row in core.tolist():
   x=float(row[0]);z=float(row[1])
   if not math.isfinite(x) or not math.isfinite(z): raise Bad('finite')
   pts.append([x,z])
  meta={'label':s['label'],'chain_id':ci,'closed':s['closed'],'point_offset':s['point_offset'],'segment_offset':s['segment_offset'],'core_count':s['core_count'],'core_float64_le_sha256':s['core_float64_le_sha256'],'npz_sha256':contract['npz_sha256'],'kernel_sha256':KNOWN[KP]}
  chains[s['label']]={'selector':s,'points':pts,'closed':s['closed'],'meta':meta}
 return chains
def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--contract',required=True);ap.add_argument('--contract-sha',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(argv)
 try:
  contract,csha=_load_contract(a.root,a.contract,a.contract_sha);chains=_source_chains(contract,Path(a.root))
  lines=[];qcount=0;degcount=0;state='REAL_CONTOUR_NUMERIC_PILOT_ONLY'
  header={'kind':'header','schema':'q02b2.v1','scope':'REAL_CONTOUR_NUMERIC_PILOT_ONLY','contract_sha256':csha,'npz_sha256':contract['npz_sha256'],'kernel_sha256':KNOWN[KP],'cache_count':4,'query_count':contract['queries'],'human_cases':contract['human_cases'],'controls':4,'c1':'NOT_REVIEWED','natural_positive_count':0,'calibration_ready':False,'angle_state':'PENDING_CERTIFIED_ANGLE'}
  lines.append(header)
  for s in contract['selectors']:
   ch=chains[s['label']];cache=build_cache(ch['points'],ch['closed'],dict(ch['meta'],contract_sha256=csha));prepared=_Prepared(cache,_points_frac(cache['points']))
   lines.append({'kind':'cache','label':s['label'],'chain_id':s['chain_id'],'cache':cache})
   actual=bool(cache['degenerate_indices']);expected=s['prior_degenerate_reason'] is not None
   if actual: degcount+=1
   if actual!=expected:
    state='INCONCLUSIVE_CHAIN_CLASS';lines.append({'kind':'chain_class','label':s['label'],'chain_id':s['chain_id'],'state':'INCONCLUSIVE_CHAIN_CLASS','degenerate_indices':cache['degenerate_indices'],'query_count':0});continue
   if actual:
    lines.append({'kind':'chain_class','label':s['label'],'chain_id':s['chain_id'],'state':'DEGENERATE','degenerate_indices':cache['degenerate_indices'],'query_count':0});continue
   for center in s['anchors']:
    for h in contract['h']:
     r=query(prepared,center,h);rec={'kind':'query','label':s['label'],'chain_id':s['chain_id'],'center_index':center,'h':h,'result':r}
     if len(json.dumps(rec,sort_keys=True,separators=(',',':')).encode())>contract['output_limits']['query_bytes']: raise Resource('querybytes')
     lines.append(rec);qcount+=1
  lines.append({'kind':'summary','state':state,'cache_count':4,'query_count':qcount,'degenerate_count':degcount})
  blob=b''
  for rec in lines:
   line=json.dumps(rec,sort_keys=True,separators=(',',':')).encode()+chr(10).encode()
   if len(line)>contract['output_limits']['line_bytes']: raise Resource('linebytes')
   if len(blob)+len(line)>contract['output_limits']['total_bytes']: raise Resource('totalbytes')
   blob+=line
  if len(blob)>contract['output_limits']['total_bytes']: raise Resource('totalbytes')
  with open(a.output,'xb') as fh: fh.write(blob)
  print(state);return 0 if state=='REAL_CONTOUR_NUMERIC_PILOT_ONLY' and qcount==contract['queries'] else 2
 except Resource as e: print('INCONCLUSIVE_RESOURCE:'+str(e),file=sys.stderr);return 2
 except Exception as e: print('INCONCLUSIVE:'+str(e),file=sys.stderr);return 2
if __name__=='__main__': raise SystemExit(main())
