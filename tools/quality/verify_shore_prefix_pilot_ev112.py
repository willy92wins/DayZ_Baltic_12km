#!/usr/bin/env python3
import argparse,copy,hashlib,importlib.util,json,math,sys
from fractions import Fraction
from pathlib import Path
P=48;SCALE=1<<P;MAXBITS=4096;QOPS=100000;COPS=4000000;MAXE=14000;THR=Fraction(3022314549036573,302231454903657293676544)
KP='tools/quality/certified_shore_kernel_ev112.py';VP='tools/quality/verify_certified_shore_kernel_ev112.py';TP='tools/quality/shore_numeric_discovery_ev112.py'
KNOWN={KP:'ef844931862c1aa2d181caa5000b4843a4b1587da7149fb033a8efa5248abe64',VP:'ab1977bc1ed283d00cb9aedab56ad1b83d2596a17f49c3558825aeec3ec8f2ca',TP:'3264f82294a2411e4f1d902c42173a01ef1f72244d6b220bba91e49a4596b696'}
class Bad(Exception): pass
class Resource(Exception): pass
V=None;TR=None;_ROOT=None
def _load_mod(root,rel,helpers=None):
 p=Path(root)/rel
 with open(p,'rb') as fh: data=fh.read(17*1024*1024)
 sha=hashlib.sha256(data).hexdigest()
 if sha!=KNOWN[rel]: raise Bad('helperpin:'+rel)
 if helpers is not None and helpers.get(rel)!=sha: raise Bad('contracthelperpin:'+rel)
 spec=importlib.util.spec_from_file_location('sealed_c_'+sha[:12],str(p));mod=importlib.util.module_from_spec(spec);mod.__file__=str(p);exec(compile(data,str(p),'exec'),mod.__dict__);return mod
def load_helpers(root,helpers=None):
 global V,TR,_ROOT
 root=Path(root)
 if helpers is not None and helpers!=KNOWN: raise Bad('contracthelperpin')
 if V is not None and _ROOT is not None and root.resolve()!=_ROOT: V=None;TR=None
 if V is None: V=_load_mod(root,VP,helpers)
 if TR is None: TR=_load_mod(root,TP,helpers)
 _ROOT=root.resolve();return V
def _ensure():
 if V is None: load_helpers(Path(__file__).resolve().parents[2])
class _Prepared:
 __slots__=('core','pts')
 def __init__(self,core,pts): self.core=core;self.pts=pts
def _cap(limit):
 class CB(V.CapB):
  def __init__(self):
   super().__init__();self.limit=limit
  def tick(self,n=1):
   self.n+=n
   if self.n>self.limit: raise Resource('chainops')
 return CB()
def _padd(cap,a,b):
 if _bits(a)>MAXBITS or _bits(b)>MAXBITS or max(_bits(a),_bits(b))+1>MAXBITS: raise Resource('intbits')
 try: cap.tick()
 except Exception as e:
  if e.__class__.__name__=='Cap': raise Resource('chainops')
  raise
 return a+b
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
def _pts(points):
 if not isinstance(points,list) or not (2<=len(points)<=MAXE+1): raise Bad('points')
 out=[]
 for p in points:
  if not isinstance(p,list) or len(p)!=2: raise Bad('point')
  out.append((_frac(p[0]),_frac(p[1])))
 return out
def _schema(cache):
 if isinstance(cache,_Prepared): return cache.core
 if not isinstance(cache,dict): raise Bad('cachekeys')
 if any(not isinstance(k,str) or k.startswith('_') for k in cache): raise Bad('underscorefield')
 if set(cache)!={'meta','closed','points','edges','pref_lo','pref_hi','degenerate_indices','counters'}: raise Bad('cachekeys')
 return cache
def _same(a,b):
 if type(a) is not type(b): return False
 if isinstance(a,dict): return a.keys()==b.keys() and all(_same(a[k],b[k]) for k in a)
 if isinstance(a,list): return len(a)==len(b) and all(_same(x,y) for x,y in zip(a,b))
 return a==b

def verify_cache(points,closed,cache):
 _ensure();core=_schema(cache)
 if type(closed) is not bool or type(core['closed']) is not bool or core['closed']!=closed: raise Bad('closed')
 src=_pts(points);pts=_pts(core['points'])
 if pts!=src: raise Bad('pointsbind')
 if not _same(core['points'],[[[v.numerator,v.denominator] for v in p] for p in pts]): raise Bad('pointencoding')
 n=len(pts);m=n if closed else n-1
 if not isinstance(core['edges'],list) or len(core['edges'])!=m or m>MAXE: raise Bad('edgecount')
 for name in ('pref_lo','pref_hi'):
  v=core[name]
  if not isinstance(v,list) or len(v)!=m+1 or v[0]!=0 or any(type(x) is not int or x<0 for x in v): raise Bad(name)
  if any(_bits(x)>MAXBITS for x in v): raise Resource('prefixbits')
 cap=_cap(COPS);deg=[];pl=[0];ph=[0];t2=V.mul(cap,THR,THR)
 for i,e in enumerate(core['edges']):
  if cap.n> COPS: raise Resource('chainops')
  if not isinstance(e,dict) or set(e)!={'q','lo','hi'}: raise Bad('edgekeys')
  if not isinstance(e['q'],list) or len(e['q'])!=2 or type(e['q'][0]) is not int or type(e['q'][1]) is not int or e['q'][1]<=0: raise Bad('q')
  if type(e['lo']) is not int or type(e['hi']) is not int or e['lo']<0 or e['hi']<e['lo'] or e['hi']-e['lo']>1: raise Bad('witnessrange')
  if max(_bits(e['q'][0]),_bits(e['q'][1]),_bits(e['lo']),_bits(e['hi']))>MAXBITS: raise Resource('edgebits')
  a=pts[i];b=pts[(i+1)%n]
  try:
   dx=V.sub(cap,b[0],a[0]);dz=V.sub(cap,b[1],a[1]);q=V.add(cap,V.mul(cap,dx,dx),V.mul(cap,dz,dz))
  except Exception as ex:
   if ex.__class__.__name__=='Cap': raise Resource('edgeops')
   raise
  if q!=Fraction(e['q'][0],e['q'][1]): raise Bad('qrecompute')
  try:
   if not V.verify_witness(cap,q,e['lo'],False): raise Bad('floorwitness')
   if not V.verify_witness(cap,q,e['hi'],True): raise Bad('ceilwitness')
  except Resource: raise
  except Bad: raise
  except Exception as ex:
   if ex.__class__.__name__=='Cap': raise Resource('chainops')
   raise Bad('witness:'+str(ex))
  pl.append(_padd(cap,pl[-1],e['lo']));ph.append(_padd(cap,ph[-1],e['hi']))
  if _bits(pl[-1])>MAXBITS or _bits(ph[-1])>MAXBITS: raise Resource('prefixbits')
  if V.cmpf(cap,q,t2)<0: deg.append(i)
 if pl!=core['pref_lo'] or ph!=core['pref_hi']: raise Bad('prefix')
 if deg!=core['degenerate_indices']: raise Bad('degenerate')
 c=core['counters']
 if not isinstance(c,dict) or set(c)!={'edges','ops','max_bits'} or c['edges']!=m or type(c['ops']) is not int or not (0<=c['ops']<=COPS) or type(c['max_bits']) is not int or c['max_bits']<0 or c['max_bits']>MAXBITS: raise Bad('counters')
 return _Prepared(copy.deepcopy(core),pts)
def _enc_interval(iv): return [[iv[0].numerator,iv[0].denominator],[iv[1].numerator,iv[1].denominator]] if iv is not None else None
def _enc_station(s):
 if s is None: return None
 return {'segment':s['segment'],'from_point':[[s['from'][0].numerator,s['from'][0].denominator],[s['from'][1].numerator,s['from'][1].denominator]],'to_point':[[s['to'][0].numerator,s['to'][0].denominator],[s['to'][1].numerator,s['to'][1].denominator]],'t':_enc_interval(s['t']),'point':[_enc_interval(s['point'][0]),_enc_interval(s['point'][1])]}
def _enc_field(f): return {'state':f['state'],'interval':_enc_interval(f['interval']),'unit':f['unit'],'width':[f['width'].numerator,f['width'].denominator] if f['width'] is not None else None}
class _Walk:
 def __init__(self,cap): self.cap=cap
 @property
 def ops(self): return 0
 def tick(self,n=1):
  try: self.cap.tick(n)
  except Exception as e:
   if e.__class__.__name__=='Cap': raise Resource('walkops')
   raise
def _dir_steps(cache,center,direction,closed):
 n=len(cache['points']);return n if closed else (center if direction<0 else n-1-center)
def _edge_at(cache,center,direction,k,closed):
 n=len(cache['points']);frm=(center+direction*k)%n if closed else center+direction*k;to=(center+direction*(k+1))%n if closed else center+direction*(k+1);ei=frm if direction>0 else to
 return cache['edges'][ei%n if closed else ei],frm,to
def _dir_total(w,cache,center,direction,closed):
 lo=0;hi=0;steps=_dir_steps(cache,center,direction,closed)
 for k in range(steps):
  w.tick();e,frm,to=_edge_at(cache,center,direction,k,closed)
  if max(_bits(lo),_bits(e['lo']))+1>MAXBITS or max(_bits(hi),_bits(e['hi']))+1>MAXBITS: raise Resource('intbits')
  lo=_padd(w.cap,lo,e['lo']);hi=_padd(w.cap,hi,e['hi'])
 return (Fraction(lo,SCALE),Fraction(hi,SCALE))
def _locate_walk(cap,w,cache,pts,center,direction,closed,h):
 n=len(pts);steps=_dir_steps(cache,center,direction,closed);cen=pts[center]
 if steps==0:
  if V.cmpf(cap,h,Fraction(0))==0: return {'segment':None,'from':cen,'to':cen,'t':(Fraction(0),Fraction(0)),'point':((cen[0],cen[0]),(cen[1],cen[1]))}
  return 'OUT_OF_RANGE'
 if V.cmpf(cap,h,Fraction(0))==0:
  e,frm,to=_edge_at(cache,center,direction,0,closed);return _make_station(cap,cache,pts,0,frm,to,(Fraction(0),Fraction(0)))
 slo=0;shi=0;total=None
 for i in range(steps):
  w.tick();e,frm,to=_edge_at(cache,center,direction,i,closed);nlo=_padd(cap,slo,e['lo']);nhi=_padd(cap,shi,e['hi']);S=(Fraction(slo,SCALE),Fraction(shi,SCALE));N=(Fraction(nlo,SCALE),Fraction(nhi,SCALE));total=N
  if V.cmpf(cap,S[0],S[1])==0 and V.cmpf(cap,h,S[0])==0: return _make_station(cap,cache,pts,i,frm,to,(Fraction(0),Fraction(0)))
  if V.cmpf(cap,S[1],h)<0 and V.cmpf(cap,h,N[0])<0:
   L=(Fraction(e['lo'],SCALE),Fraction(e['hi'],SCALE))
   try: t=V.idiv(cap,V.isub(cap,(h,h),S),L)
   except Exception as ex:
    if ex.__class__.__name__=='Cap': raise Resource('t')
    raise Bad('t:'+str(ex))
   if V.cmpf(cap,t[0],Fraction(0))<0 or V.cmpf(cap,t[1],Fraction(1))>0: return 'BOUNDARY_UNCERTAIN'
   return _make_station(cap,cache,pts,i,frm,to,t)
  slo,shi=nlo,nhi
 if total is not None and V.cmpf(cap,total[0],total[1])==0 and V.cmpf(cap,h,total[0])==0 and not closed:
  e,frm,to=_edge_at(cache,center,direction,steps-1,closed);return _make_station(cap,cache,pts,steps-1,frm,to,(Fraction(1),Fraction(1)))
 if total is not None and V.cmpf(cap,h,total[1])>0: return 'OUT_OF_RANGE'
 return 'BOUNDARY_UNCERTAIN'
def _make_station(cap,cache,pts,seg,frm,to,t):
 pt=[]
 for kk in (0,1):
  d=V.sub(cap,pts[to][kk],pts[frm][kk]);pt.append(V.iadd(cap,(pts[frm][kk],pts[frm][kk]),V.imul(cap,t,(d,d))))
 return {'segment':seg,'from':pts[frm],'to':pts[to],'t':t,'point':(pt[0],pt[1])}
def walk(cache,center,h):
 try: return _walk(cache,center,h)
 except Exception as e:
  if e.__class__.__name__=='Cap': raise Resource('queryops') from e
  raise

def _walk(cache,center,h):
 _ensure()
 if isinstance(cache,_Prepared): checked=cache
 elif isinstance(cache,dict): checked=verify_cache(cache['points'],cache['closed'],cache)
 else: raise Bad('cache')
 core=_schema(checked);pts=_pts(core['points']);closed=core['closed']
 if type(center) is not int or not (0<=center<len(pts)): return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None,'ops':0}
 hh=_frac(h);cap=V.CapB();w=_Walk(cap)
 if V.cmpf(cap,hh,Fraction(0))<0: return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None,'ops':0}
 if core['degenerate_indices']: return {'state':'DEGENERATE','stations':None,'features':None,'support':None,'ops':0}
 if closed:
  per=_dir_total(w,core,center,1,closed);support={'perimeter':per,'backward':per,'forward':per};two=V.mul(cap,Fraction(2),hh)
  if V.cmpf(cap,per[0],per[1])==0: supp='SUPPORTED' if V.cmpf(cap,two,per[0])<0 else 'INSUFFICIENT_SUPPORT'
  elif V.cmpf(cap,two,per[1])>=0: supp='INSUFFICIENT_SUPPORT'
  elif V.cmpf(cap,two,per[0])<0: supp='SUPPORTED'
  else: supp='SUPPORT_UNCERTAIN'
 else:
  back=_dir_total(w,core,center,-1,closed);fwd=_dir_total(w,core,center,1,closed);support={'perimeter':None,'backward':back,'forward':fwd};supp='SUPPORTED'
  for dist in (back,fwd):
   cur='SUPPORTED' if V.cmpf(cap,dist[0],hh)>=0 else ('INSUFFICIENT_SUPPORT' if V.cmpf(cap,dist[1],hh)<0 else 'SUPPORT_UNCERTAIN')
   if cur=='INSUFFICIENT_SUPPORT': supp=cur
   elif cur=='SUPPORT_UNCERTAIN' and supp=='SUPPORTED': supp=cur
 sup_enc={'perimeter':_enc_interval(support['perimeter']),'backward':_enc_interval(support['backward']),'forward':_enc_interval(support['forward']),'state':supp}
 if supp!='SUPPORTED': return {'state':supp,'stations':None,'features':None,'support':sup_enc,'ops':w.ops+cap.n}
 A=_locate_walk(cap,w,core,pts,center,-1,closed,hh)
 if isinstance(A,str): return {'state':A,'stations':None,'features':None,'support':sup_enc,'ops':w.ops+cap.n}
 C=_locate_walk(cap,w,core,pts,center,1,closed,hh)
 if isinstance(C,str): return {'state':C,'stations':None,'features':None,'support':sup_enc,'ops':w.ops+cap.n}
 cen=pts[center];B={'segment':None,'from':cen,'to':cen,'t':(Fraction(0),Fraction(0)),'point':((cen[0],cen[0]),(cen[1],cen[1]))}
 try: feats=V.features(cap,A,B,C,hh)
 except Exception as e:
  if e.__class__.__name__=='Cap': raise Resource('features')
  raise
 state='UNDEFINED_ZERO_CHORD' if feats['chord_ac']['interval']==(Fraction(0),Fraction(0)) else 'DEFINED'
 return {'state':state,'stations':{'A':_enc_station(A),'B':_enc_station(B),'C':_enc_station(C)},'features':{k:_enc_field(v) for k,v in feats.items()},'support':sup_enc,'ops':w.ops+cap.n}
# CLI shared contract/source/report validation
def _keys(o,s):
 if not isinstance(o,dict) or set(o)!=set(s): raise Bad('keys')
def _ishex(s): return isinstance(s,str) and len(s)==64 and all(c in '0123456789abcdef' for c in s)
def _validate_contract(c):
 _keys(c,{'schema','scope','plan_sha256','npz_path','npz_sha256','q02a_sha256','selectors','h','queries','p','threshold_ratio','max_bits','query_ops','chain_ops','max_edges','read_limits','output_limits','helpers','human_cases','controls','c1','natural_positive_count','calibration_ready','angle_state','budgets'})
 if c['schema']!='q02b2.v1' or c['scope']!='REAL_CONTOUR_NUMERIC_PILOT_ONLY' or c['p']!=48 or c['max_bits']!=4096 or c['query_ops']!=100000 or c['chain_ops']!=4000000 or c['max_edges']!=14000: raise Bad('contract')
 if c['h']!=[0,6,12,24,48,96] or c['threshold_ratio']!=[3022314549036573,302231454903657293676544]: raise Bad('hthr')
 if not _ishex(c['plan_sha256']) or not _ishex(c['npz_sha256']) or not _ishex(c['q02a_sha256']): raise Bad('pins')
 if c['helpers']!=KNOWN: raise Bad('helpers')
 if c['human_cases']!={'count':9,'state':'GEOMETRY_UNBOUND','resolved':0} or c['controls']!=4 or c['c1']!='NOT_REVIEWED' or c['natural_positive_count']!=0 or c['calibration_ready'] is not False or c['angle_state']!='PENDING_CERTIFIED_ANGLE': raise Bad('claims')
 _keys(c['read_limits'],{'archive_bytes','required_uncompressed_bytes','header_bytes','members'});_keys(c['output_limits'],{'line_bytes','query_bytes','total_bytes'})
 _keys(c['budgets'],{'author_s','review_s','suite_s','capture_s','consumer_s','bytes'})
 for _v in list(c['read_limits'].values())+list(c['output_limits'].values())+list(c['budgets'].values()):
  if type(_v) is not int or _v<=0: raise Bad('limits')
 if not isinstance(c['npz_path'],str) or not _ishex(c['npz_sha256']): raise Bad('pins')
 if c['read_limits']['archive_bytes']>67108864 or c['read_limits']['required_uncompressed_bytes']>8388608 or c['read_limits']['header_bytes']>16384 or c['read_limits']['members']>32 or c['output_limits']['line_bytes']>16777216 or c['output_limits']['query_bytes']>262144 or c['output_limits']['total_bytes']>67108864: raise Bad('limits')
 if not isinstance(c['selectors'],list) or len(c['selectors'])!=4: raise Bad('selectors')
 exp=0
 for s in c['selectors']:
  _keys(s,{'label','chain_id','closed','point_offset','segment_offset','core_count','core_float64_le_sha256','anchors','prior_degenerate_reason'})
  if not isinstance(s['label'],str) or type(s['chain_id']) is not int or type(s['closed']) is not bool or type(s['core_count']) is not int: raise Bad('selector')
  for off in (s['point_offset'],s['segment_offset']):
   if not isinstance(off,list) or len(off)!=2 or any(type(x) is not int for x in off) or not (0<=off[0]<off[1]): raise Bad('offset')
  if not isinstance(s['anchors'],list) or any(type(x) is not int for x in s['anchors']) or s['anchors']!=sorted(set(s['anchors'])) or any(not (0<=x<s['core_count']) for x in s['anchors']): raise Bad('anchors')
  if s['core_count']!=(s['point_offset'][1]-s['point_offset'][0])-(1 if s['closed'] else 0): raise Bad('core')
  if s['prior_degenerate_reason'] is None: exp+=len(s['anchors'])*len(c['h'])
  elif s['anchors']: raise Bad('deganchors')
 if len({s['label'] for s in c['selectors']})!=4 or len({s['chain_id'] for s in c['selectors']})!=4: raise Bad('selectorunique')
 if c['queries']!=exp: raise Bad('querycount')
 return c
def _read_bounded(path,limit):
 with open(path,'rb') as fh: data=fh.read(limit+1)
 if len(data)>limit: raise Bad('large')
 return data
def _load_contract(root,cpath,csha):
 data=_read_bounded(cpath,1024*1024)
 if hashlib.sha256(data).hexdigest()!=csha.lower(): raise Bad('contractsha')
 _ensure();c=V.parse(data);_validate_contract(c);return c,hashlib.sha256(data).hexdigest()
def _source_chains(contract,root):
 load_helpers(root,contract['helpers']);tc={'npz_path':contract['npz_path'],'npz_sha256':contract['npz_sha256'],'limits':contract['read_limits']}
 try: arrays,meta,other,before,after=TR._read_npz(tc)
 except Exception as e: raise Bad('npz:'+str(e))
 if set(arrays)!={'point_offsets','chain_offsets','chain_points','closed'}: raise Bad('arrays')
 po=arrays['point_offsets'];co=arrays['chain_offsets'];cp=arrays['chain_points'];cl=arrays['closed'];pol=po.tolist();col=co.tolist();cll=cl.tolist()
 if str(po.dtype) not in ('int64','<i8') or str(co.dtype) not in ('int64','<i8') or str(cp.dtype) not in ('<f8','float64'): raise Bad('dtypes')
 if len(cp.shape)!=2 or cp.shape[1]!=2 or str(cl.dtype)!='bool' or len(pol)!=len(cll)+1 or len(col)!=len(cll)+1 or pol[0]!=0 or col[0]!=0 or pol[-1]!=cp.shape[0] or pol!=sorted(pol) or col!=sorted(col) or any(col[i+1]-col[i]!=pol[i+1]-pol[i]-1 for i in range(len(cll))): raise Bad('arrayshape')
 chains={}
 for s in contract['selectors']:
  ci=s['chain_id']
  if not (0<=ci<len(cll)) or pol[ci]!=s['point_offset'][0] or pol[ci+1]!=s['point_offset'][1]: raise Bad('pointoffset')
  if col[ci]!=s['segment_offset'][0] or col[ci+1]!=s['segment_offset'][1]: raise Bad('segmentoffset')
  if bool(cll[ci])!=s['closed']: raise Bad('closedflag')
  if s['core_count']!=(pol[ci+1]-pol[ci])-(1 if s['closed'] else 0) or (col[ci+1]-col[ci])!=(pol[ci+1]-pol[ci])-1: raise Bad('corecount')
  sub=cp[s['point_offset'][0]:s['point_offset'][1]];core=sub[:-1] if s['closed'] else sub
  if s['closed'] and (len(sub)<2 or sub[-1].astype('<f8').tobytes()!=sub[0].astype('<f8').tobytes()): raise Bad('closedrepeat')
  if hashlib.sha256(core.astype('<f8').tobytes()).hexdigest()!=s['core_float64_le_sha256']: raise Bad('corehash')
  pts=[]
  for r in core.tolist():
   if not math.isfinite(float(r[0])) or not math.isfinite(float(r[1])): raise Bad('finite')
   pts.append([float(r[0]),float(r[1])])
  meta={'label':s['label'],'chain_id':ci,'closed':s['closed'],'point_offset':s['point_offset'],'segment_offset':s['segment_offset'],'core_count':s['core_count'],'core_float64_le_sha256':s['core_float64_le_sha256'],'npz_sha256':contract['npz_sha256'],'kernel_sha256':KNOWN[KP],'contract_sha256':None}
  chains[s['label']]={'selector':s,'points':pts,'closed':s['closed'],'meta':meta}
 return chains
def _deg_indices_removed(): pass
def _read_report_stream(path,limit):
 chunks=[];total=0
 with open(path,'rb') as fh:
  while True:
   chunk=fh.read(65536)
   if not chunk: break
   total+=len(chunk)
   if total>limit: raise Bad('reportlarge')
   chunks.append(chunk)
 return b''.join(chunks)
def _strip_ops(r):
 if not isinstance(r,dict) or 'ops' not in r or type(r['ops']) is not int or not (0<=r['ops']<=QOPS): raise Bad('ops')
 return {k:v for k,v in r.items() if k!='ops'}
def verify_report_data(data,contract,csha,chains):
 if len(data)>contract['output_limits']['total_bytes'] or not data.endswith(chr(10).encode()): raise Bad('reporteof')
 raw=data.split(chr(10).encode())[:-1]
 if any(len(x)+1>contract['output_limits']['line_bytes'] or (b'"kind":"query"' in x and len(x)+1>contract['output_limits']['query_bytes']) for x in raw): raise Bad('linebytes')
 recs=[]
 for line in raw:
  try: recs.append(V.parse(line))
  except Exception as e: raise Bad('reportjson:'+str(e))
 header={'kind':'header','schema':'q02b2.v1','scope':'REAL_CONTOUR_NUMERIC_PILOT_ONLY','contract_sha256':csha,'npz_sha256':contract['npz_sha256'],'kernel_sha256':KNOWN[KP],'cache_count':4,'query_count':contract['queries'],'human_cases':contract['human_cases'],'controls':4,'c1':'NOT_REVIEWED','natural_positive_count':0,'calibration_ready':False,'angle_state':'PENDING_CERTIFIED_ANGLE'}
 if not recs or not _same(recs[0],header): raise Bad('header')
 idx=1;qcount=0
 for s in contract['selectors']:
  ch=chains[s['label']]
  if idx>=len(recs): raise Bad('missingcache')
  rec=recs[idx];idx+=1
  if not isinstance(rec,dict) or set(rec)!={'kind','label','chain_id','cache'} or rec['kind']!='cache' or rec['label']!=s['label'] or rec['chain_id']!=s['chain_id']: raise Bad('cacheorder')
  expmeta=dict(ch['meta']);expmeta['contract_sha256']=csha
  if not _same(rec['cache'].get('meta'),expmeta): raise Bad('cachemeta')
  checked=verify_cache(ch['points'],ch['closed'],rec['cache'])
  if not _same(_schema(checked),rec['cache']): raise Bad('cacheexact')
  actual=bool(checked.core['degenerate_indices']);expected=s['prior_degenerate_reason'] is not None
  if actual!=expected: raise Bad('INCONCLUSIVE_CHAIN_CLASS')
  if actual:
   if idx>=len(recs): raise Bad('missingclass')
   cr=recs[idx];idx+=1
   if cr!={'kind':'chain_class','label':s['label'],'chain_id':s['chain_id'],'state':'DEGENERATE','degenerate_indices':checked.core['degenerate_indices'],'query_count':0}: raise Bad('classrecord')
   continue
  for center in s['anchors']:
   for h in contract['h']:
    if idx>=len(recs): raise Bad('missingquery')
    qr=recs[idx];idx+=1;qcount+=1
    if not isinstance(qr,dict) or set(qr)!={'kind','label','chain_id','center_index','h','result'} or qr['kind']!='query' or qr['label']!=s['label'] or qr['chain_id']!=s['chain_id'] or qr['center_index']!=center or qr['h']!=h: raise Bad('queryorder')
    if len(json.dumps(qr,sort_keys=True,separators=(',',':')).encode())>contract['output_limits']['query_bytes']: raise Bad('querybytes')
    exp=walk(checked,center,h)
    if not _same(_strip_ops(qr['result']),_strip_ops(exp)): raise Bad('querymismatch')
 if idx>=len(recs): raise Bad('missingsummary')
 summ=recs[idx];idx+=1
 if not _same(summ,{'kind':'summary','state':'REAL_CONTOUR_NUMERIC_PILOT_ONLY','cache_count':4,'query_count':qcount,'degenerate_count':sum(1 for s in contract['selectors'] if s['prior_degenerate_reason'] is not None)}): raise Bad('summary')
 if idx!=len(recs) or qcount!=contract['queries']: raise Bad('trailing')
 return {'cache_count':4,'query_count':qcount}
def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--contract',required=True);ap.add_argument('--contract-sha',required=True);ap.add_argument('--output',required=True);ap.add_argument('--report',required=True);a=ap.parse_args(argv)
 try:
  contract,csha=_load_contract(a.root,a.contract,a.contract_sha);chains=_source_chains(contract,Path(a.root))
  # degeneracy is verified once per source-bound cache in verify_report_data
  data=_read_report_stream(a.report,contract['output_limits']['total_bytes']);res=verify_report_data(data,contract,csha,chains)
  out={'schema':'q02b2-consumer.v1','state':'VERIFIED','pilot_state':'REAL_CONTOUR_NUMERIC_PILOT_ONLY','scope':'REAL_CONTOUR_NUMERIC_PILOT_ONLY','contract_sha256':csha,'report_sha256':hashlib.sha256(data).hexdigest(),'cache_count':res['cache_count'],'query_count':res['query_count'],'human_cases':contract['human_cases'],'controls':4,'c1':'NOT_REVIEWED','natural_positive_count':0,'calibration_ready':False,'angle_state':'PENDING_CERTIFIED_ANGLE','quality_promotion':False}
  blob=json.dumps(out,sort_keys=True,separators=(',',':')).encode()+chr(10).encode()
  with open(a.output,'xb') as fh: fh.write(blob)
  print('VERIFIED');return 0
 except Resource as e: print('INCONCLUSIVE_RESOURCE:'+str(e),file=sys.stderr);return 2
 except Exception as e: print('INCONCLUSIVE:'+str(e),file=sys.stderr);return 2
if __name__=='__main__': raise SystemExit(main())
