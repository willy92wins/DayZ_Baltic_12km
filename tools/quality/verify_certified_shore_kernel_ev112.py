#!/usr/bin/env python3
import argparse, hashlib, json, math, sys
from fractions import Fraction
from math import isqrt
from pathlib import Path
P=48; SCALE=1<<P; MAXBITS=4096; MAXOPS=100000; MAXREPORT=16*1024*1024; Z=Fraction(0); ONE=Fraction(1)
class Bad(Exception): pass
class Cap(Exception): pass
def bl(x): return abs(int(x)).bit_length()
class CapB:
 def __init__(self): self.n=0; self.events=None
 def tick(self,n=1):
  self.n+=n
  if self.n>MAXOPS: raise Cap('ops')
 def need(self,*v):
  self.tick()
  if sum(bl(x) for x in v)>MAXBITS: raise Cap('bits')
def mk(cap,n,d=1):
 if d==0: raise Bad('den')
 if d<0: n=-n; d=-d
 if bl(n)>MAXBITS or bl(d)>MAXBITS: raise Cap('frac')
 cap.tick(); return Fraction(n,d)
def add(cap,a,b):
 cap.need(a.numerator,b.denominator); cap.need(b.numerator,a.denominator); cap.need(a.denominator,b.denominator)
 if max(bl(a.numerator)+bl(b.denominator),bl(b.numerator)+bl(a.denominator))+1>MAXBITS: raise Cap('add')
 return mk(cap,a.numerator*b.denominator+b.numerator*a.denominator,a.denominator*b.denominator)
def sub(cap,a,b): return add(cap,a,mk(cap,-b.numerator,b.denominator))
def mul(cap,a,b): cap.need(a.numerator,b.numerator); cap.need(a.denominator,b.denominator); return mk(cap,a.numerator*b.numerator,a.denominator*b.denominator)
def div(cap,a,b):
 if b==0: raise Bad('div0')
 return mul(cap,a,mk(cap,b.denominator,b.numerator))
def cmpf(cap,a,b):
 cap.need(a.numerator,b.denominator); cap.need(b.numerator,a.denominator); x=a.numerator*b.denominator; y=b.numerator*a.denominator; return (x>y)-(x<y)
def enc_iv(x): return [[x[0].numerator,x[0].denominator],[x[1].numerator,x[1].denominator]]
def emit(cap,op,inp,out,wlo=None,whi=None):
 if getattr(cap,'events',None) is not None:
  e={'op':op,'input':inp,'output':out}
  if wlo is not None: e['witness_lo']=wlo; e['witness_hi']=whi
  cap.events.append(e)
def iadd(cap,x,y):
 o=(add(cap,x[0],y[0]),add(cap,x[1],y[1])); emit(cap,'add',[enc_iv(x),enc_iv(y)],enc_iv(o)); return o
def isub(cap,x,y):
 o=(sub(cap,x[0],y[1]),sub(cap,x[1],y[0])); emit(cap,'sub',[enc_iv(x),enc_iv(y)],enc_iv(o)); return o
def imul(cap,x,y,_emit=True):
 vs=[mul(cap,x[0],y[0]),mul(cap,x[0],y[1]),mul(cap,x[1],y[0]),mul(cap,x[1],y[1])]; lo=vs[0]; hi=vs[0]
 for v in vs[1:]:
  if cmpf(cap,v,lo)<0: lo=v
  if cmpf(cap,v,hi)>0: hi=v
 o=(lo,hi)
 if _emit: emit(cap,'mul',[enc_iv(x),enc_iv(y)],enc_iv(o))
 return o
def isq(cap,x):
 a=mul(cap,x[0],x[0]); b=mul(cap,x[1],x[1])
 hi=a if cmpf(cap,a,b)>=0 else b
 if cmpf(cap,x[0],Z)<=0 and cmpf(cap,x[1],Z)>=0: o=(Z,hi)
 else: o=(a if cmpf(cap,a,b)<=0 else b,hi)
 emit(cap,'square',enc_iv(x),enc_iv(o)); return o
def idiv(cap,x,y):
 if cmpf(cap,y[0],Z)<=0 and cmpf(cap,y[1],Z)>=0: raise Bad('divinterval')
 r=[div(cap,ONE,y[0]),div(cap,ONE,y[1])]; rec=(r[0],r[1]) if cmpf(cap,r[0],r[1])<=0 else (r[1],r[0]); o=imul(cap,x,rec,False); emit(cap,'divide',[enc_iv(x),enc_iv(y)],enc_iv(o)); return o
def root_interval(cap,x):
 if cmpf(cap,x[0],Z)<0: raise Bad('sqrtneg')
 def fl(f):
  cap.tick(16)
  if bl(f.numerator)+96>MAXBITS: raise Cap('sqrt')
  N=f.numerator<<(2*P); d=f.denominator; j=isqrt(N//d); cap.tick()
  if 2*bl(j+1)+bl(d)>MAXBITS: raise Cap('rootwit')
  if not (j*j*d<=N<(j+1)*(j+1)*d): raise Bad('rootwit')
  return j
 def ce(f):
  j=fl(f); N=f.numerator<<(2*P); d=f.denominator
  if 2*bl(j)+bl(d)>MAXBITS: raise Cap('rootwit')
  return j if j*j*d==N else j+1
 wlo=fl(x[0]); whi=ce(x[1]); o=(mk(cap,wlo,SCALE),mk(cap,whi,SCALE)); emit(cap,'sqrt_interval',enc_iv(x),enc_iv(o),wlo,whi); return o
def no_dup(pairs):
 o={}
 for k,v in pairs:
  if k in o: raise Bad('dup')
  o[k]=v
 return o
def parse(data):
 try: return json.loads(data.decode('utf-8'),object_pairs_hook=no_dup,parse_constant=lambda s:(_ for _ in ()).throw(Bad('const')))
 except Bad: raise
 except Exception as e: raise Bad(str(e))
def keys(o,a):
 if not isinstance(o,dict) or set(o)!=set(a): raise Bad('keys')
def is_num(v): return type(v) is int or (type(v) is float and math.isfinite(v))
def validate_points(v):
 if not isinstance(v,list) or not (2<=len(v)<=512): raise Bad('points')
 for p in v:
  if not isinstance(p,list) or len(p)!=2 or not is_num(p[0]) or not is_num(p[1]): raise Bad('point')
def read_bounded(path,limit=MAXREPORT):
 with open(path,'rb') as fh: data=fh.read(limit+1)
 if len(data)>limit: raise Bad('large')
 return data
def load_pin(path,sha,limit):
 data=read_bounded(path,limit)
 if len(data)>limit: raise Bad('large')
 if hashlib.sha256(data).hexdigest()!=sha.lower(): raise Bad('pin')
 return data
def pair(cap,v):
 if not isinstance(v,list) or len(v)!=2 or type(v[0]) is not int or type(v[1]) is not int or v[1]<=0: raise Bad('pair')
 return mk(cap,v[0],v[1])
def ipair(cap,v):
 if not isinstance(v,list) or len(v)!=2: raise Bad('ipair')
 lo=pair(cap,v[0]); hi=pair(cap,v[1])
 if cmpf(cap,lo,hi)>0: raise Bad('order')
 return (lo,hi)
def dec_pair(v,cap=None): return pair(cap if cap is not None else CapB(),v)
def dec_interval(v,cap=None): return ipair(cap if cap is not None else CapB(),v) if v is not None else None
def encf(f): return [f.numerator,f.denominator]
def strict_eq(a,b):
 if type(a)!=type(b):
  if isinstance(a,(int,float)) and isinstance(b,(int,float)) and type(a) is not bool and type(b) is not bool: return False
  return False
 if isinstance(a,dict): return set(a)==set(b) and all(strict_eq(a[k],b[k]) for k in a)
 if isinstance(a,list): return len(a)==len(b) and all(strict_eq(x,y) for x,y in zip(a,b))
 return a==b
def validate_contract(c):
 keys(c,{'schema','scope','p','max_bits','max_operations','old_oracles','plan_sha256','threshold_binary_ratio','human_cases','controls','c1','calibration_ready','natural_positive_count','angle_state','window_extras','station_extras','interval_extras','invariants','budgets','non_authorizations'})
 if c['schema']!='q02b1-contract.v1' or c['scope']!='NUMERIC_KERNEL_ONLY' or c['p']!=P or c['max_bits']!=MAXBITS or c['max_operations']!=MAXOPS: raise Bad('contract')
 keys(c['old_oracles'],{'path','sha256'})
 if not isinstance(c['old_oracles']['path'],str) or len(c['old_oracles']['sha256'])!=64 or len(c['plan_sha256'])!=64: raise Bad('pins')
 if c['threshold_binary_ratio']!=[3022314549036573,302231454903657293676544]: raise Bad('threshold')
 keys(c['human_cases'],{'count','state','resolved'})
 if c['human_cases']!={'count':9,'state':'GEOMETRY_UNBOUND','resolved':0}: raise Bad('human')
 if c['calibration_ready'] is not False or c['natural_positive_count']!=0 or c['angle_state']!='PENDING_CERTIFIED_ANGLE' or c['c1']!='NOT_REVIEWED': raise Bad('claims')
 if type(c['controls']) is not int or c['controls']!=4: raise Bad('controls')
 keys(c['invariants'],{'old_query_count','old_states','units'})
 if c['invariants']['units']!={'cross':'m^2','dot':'m^2','chord':'m','deficit':'1','deviation':'m','curvature':'1/m'}: raise Bad('units')
 seen=set()
 for name in ('window_extras','station_extras','interval_extras'):
  if not isinstance(c[name],list) or len(c[name])>128: raise Bad(name)
 for e in c['window_extras']:
  keys(e,{'id','points','closed','center_index','h','expected'}); validate_points(e['points'])
  if e['id'] in seen: raise Bad('dupid')
  seen.add(e['id'])
  if type(e['closed']) is not bool or type(e['center_index']) is not int or not (0<=e['center_index']<len(e['points'])): raise Bad('window')
  pair(CapB(),e['h'])
 for e in c['station_extras']:
  keys(e,{'id','points','closed','query','expected'}); validate_points(e['points'])
  if e['id'] in seen: raise Bad('dupid')
  seen.add(e['id'])
  if type(e['closed']) is not bool or not isinstance(e['query'],list) or len(e['query'])!=2: raise Bad('station')
 for e in c['interval_extras']:
  if not isinstance(e,dict) or not {'id','op','x','expected'}<=set(e)<= {'id','op','x','y','exact','expected'}: raise Bad('intervalextra')
  if e['id'] in seen: raise Bad('dupid')
  seen.add(e['id'])
  if e['op'] not in ('sqrt','square','divide'): raise Bad('intervalop')
def validate_terms(v):
 if v is None: return
 if not isinstance(v,list) or len(v)!=2: raise Bad('exact')
 for coord in v:
  if not isinstance(coord,list) or not (1<=len(coord)<=4): raise Bad('terms')
  for t in coord:
   keys(t,{'num','den','radicand'})
   if type(t['num']) is not int or type(t['den']) is not int or type(t['radicand']) is not int or t['den']<=0 or t['radicand']<1: raise Bad('term')
def validate_oracles(o):
 keys(o,{'schema','unit','plane','natural_positive_count','calibration_ready','fixtures'})
 if o['schema']!='q02b0-oracles.v1' or o['unit']!='m' or o['plane']!='XZ' or o['natural_positive_count']!=0 or o['calibration_ready'] is not False: raise Bad('oracles')
 if not isinstance(o['fixtures'],list) or not (1<=len(o['fixtures'])<=16): raise Bad('fixtures')
 total=0; seen=set()
 for f in o['fixtures']:
  keys(f,{'id','points','closed','center_index','queries'}); validate_points(f['points'])
  if f['id'] in seen: raise Bad('dupfixture')
  seen.add(f['id'])
  if type(f['closed']) is not bool or type(f['center_index']) is not int or not (0<=f['center_index']<len(f['points'])): raise Bad('fixture')
  if not isinstance(f['queries'],list) or len(f['queries'])>32: raise Bad('queries')
  total+=len(f['queries'])
  for q in f['queries']:
   keys(q,{'h','state','a_exact','c_exact'})
   if type(q['h']) is not int or q['state'] not in ('DEFINED','COINCIDENT_SUPPORT','INSUFFICIENT_SUPPORT'): raise Bad('query')
   validate_terms(q['a_exact']); validate_terms(q['c_exact'])
 return total
def to_frac(cap,v):
 if type(v) is int: return mk(cap,v)
 if type(v) is float and math.isfinite(v): n,d=v.as_integer_ratio(); return mk(cap,n,d)
 raise Bad('num')
def conv_pts(cap,raw): return [(to_frac(cap,p[0]),to_frac(cap,p[1])) for p in raw]
def degenerate(cap,pts,closed,thr):
 t2=mul(cap,thr,thr); eds=[(pts[i],pts[i+1]) for i in range(len(pts)-1)]+([(pts[-1],pts[0])] if closed else [])
 for a,b in eds:
  dx=sub(cap,b[0],a[0]); dz=sub(cap,b[1],a[1]); q=add(cap,mul(cap,dx,dx),mul(cap,dz,dz))
  if cmpf(cap,q,t2)<0: return True
 return False
def edge_len(cap,a,b): dx=sub(cap,b[0],a[0]); dz=sub(cap,b[1],a[1]); q=add(cap,mul(cap,dx,dx),mul(cap,dz,dz)); return root_interval(cap,(q,q))
def walk_indices(n,center,dirn,closed):
 if closed: return [(center+dirn*i)%n for i in range(n+1)]
 return list(range(center,-1,-1)) if dirn<0 else list(range(center,n))
def make_station(seg,frm,to,t,pt): return {'segment':seg,'from':frm,'to':to,'t':t,'point':pt}
def walk_locate(cap,path,Q,closed_poly):
 if cmpf(cap,Q[0],Z)<0: return 'INVALID_QUERY',None
 if len(path)<2:
  p=path[0]
  if Q[0]==Q[1] and Q[0]==0: return 'DEFINED',make_station(None,p,p,(Z,Z),((p[0],p[0]),(p[1],p[1])))
  return 'OUT_OF_RANGE',None
 if Q[0]==Q[1] and Q[0]==0:
  p=path[0]; return 'DEFINED',make_station(0,p,path[1],(Z,Z),((p[0],p[0]),(p[1],p[1])))
 S=(Z,Z); total=None
 for i in range(len(path)-1):
  L=edge_len(cap,path[i],path[i+1]); N=iadd(cap,S,L); total=N
  if Q[0]==Q[1] and S[0]==S[1] and cmpf(cap,Q[0],S[0])==0:
   p=path[i]; return 'DEFINED',make_station(i,p,path[i+1],(Z,Z),((p[0],p[0]),(p[1],p[1])))
  if cmpf(cap,Q[0],S[1])>0 and cmpf(cap,Q[1],N[0])<0:
   t=idiv(cap,isub(cap,Q,S),L)
   if cmpf(cap,t[0],Z)<0 or cmpf(cap,t[1],ONE)>0: return 'BOUNDARY_UNCERTAIN',None
   pt=[]
   for k in (0,1):
    d=sub(cap,path[i+1][k],path[i][k]); pt.append(iadd(cap,(path[i][k],path[i][k]),imul(cap,t,(d,d))))
   return 'DEFINED',make_station(i,path[i],path[i+1],t,(pt[0],pt[1]))
  S=N
 if total is not None and Q[0]==Q[1] and total[0]==total[1] and cmpf(cap,Q[0],total[0])==0:
  if closed_poly: p=path[0]; return 'DEFINED',make_station(0,p,path[1],(Z,Z),((p[0],p[0]),(p[1],p[1])))
  p=path[-1]; return 'DEFINED',make_station(len(path)-2,path[-2],p,(ONE,ONE),((p[0],p[0]),(p[1],p[1])))
 if total is not None and cmpf(cap,Q[0],total[1])>0: return 'OUT_OF_RANGE',None
 return 'BOUNDARY_UNCERTAIN',None
def path_total(cap,path):
 s=(Z,Z)
 for i in range(len(path)-1): s=iadd(cap,s,edge_len(cap,path[i],path[i+1]))
 return s
def fld(cap,iv,unit): return {'state':'DEFINED','interval':iv,'unit':unit,'width':sub(cap,iv[1],iv[0])}
def qfld(cap,num,den,unit):
 if den==(Z,Z): return {'state':'UNDEFINED_ZERO_CHORD','interval':None,'unit':unit,'width':None}
 if cmpf(cap,den[0],Z)<=0 and cmpf(cap,den[1],Z)>=0: return {'state':'UNDEFINED_CONDITIONING','interval':None,'unit':unit,'width':None}
 return fld(cap,idiv(cap,num,den),unit)
def features(cap,A,B,C,h):
 CA=(isub(cap,C['point'][0],A['point'][0]),isub(cap,C['point'][1],A['point'][1])); BA=(isub(cap,B['point'][0],A['point'][0]),isub(cap,B['point'][1],A['point'][1])); CB=(isub(cap,C['point'][0],B['point'][0]),isub(cap,C['point'][1],B['point'][1]))
 cross=isub(cap,imul(cap,CA[0],BA[1]),imul(cap,CA[1],BA[0])); dot=iadd(cap,imul(cap,CA[0],BA[0]),imul(cap,CA[1],BA[1]))
 def chord(v): return root_interval(cap,iadd(cap,isq(cap,v[0]),isq(cap,v[1])))
 ba=chord(BA); bc=chord(CB); ac=chord(CA); cross2=isub(cap,imul(cap,BA[0],CB[1]),imul(cap,BA[1],CB[0])); two=(mul(cap,mk(cap,2),h),mul(cap,mk(cap,2),h))
 return {'cross':fld(cap,cross,'m^2'),'dot':fld(cap,dot,'m^2'),'chord_ba':fld(cap,ba,'m'),'chord_bc':fld(cap,bc,'m'),'chord_ac':fld(cap,ac,'m'),'deficit':qfld(cap,isub(cap,two,ac),two,'1'),'deviation':qfld(cap,cross,ac,'m'),'curvature':qfld(cap,imul(cap,(mk(cap,2),mk(cap,2)),cross2),imul(cap,imul(cap,ba,bc),ac),'1/m'),'angle':{'state':'PENDING_CERTIFIED_ANGLE','interval':None,'unit':'rad','width':None}}
def expected_window(cap,pts,closed,center,h,thr):
 pts=list(pts)
 if closed and len(pts)>2 and pts[-1]==pts[0]: pts=pts[:-1]
 if type(center) is not int or not (0<=center<len(pts)): return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None}
 if cmpf(cap,h,Z)<0: return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None}
 if degenerate(cap,pts,closed,thr): return {'state':'DEGENERATE','stations':None,'features':None,'support':None}
 bp=[pts[i] for i in walk_indices(len(pts),center,-1,closed)]; fp=[pts[i] for i in walk_indices(len(pts),center,1,closed)]
 bt=path_total(cap,bp); ft=path_total(cap,fp)
 if closed:
  support={'perimeter':ft,'backward':bt,'forward':ft}; two=mul(cap,mk(cap,2),h)
  if ft[0]==ft[1]: supp='SUPPORTED' if cmpf(cap,two,ft[0])<0 else 'INSUFFICIENT_SUPPORT'
  elif cmpf(cap,two,ft[1])>=0: supp='INSUFFICIENT_SUPPORT'
  elif cmpf(cap,two,ft[0])<0: supp='SUPPORTED'
  else: supp='SUPPORT_UNCERTAIN'
 else:
  support={'perimeter':None,'backward':bt,'forward':ft}; supp='SUPPORTED'
  for dist in (bt,ft):
   cur='SUPPORTED' if cmpf(cap,dist[0],h)>=0 else ('INSUFFICIENT_SUPPORT' if cmpf(cap,dist[1],h)<0 else 'SUPPORT_UNCERTAIN')
   if cur=='INSUFFICIENT_SUPPORT': supp=cur
   elif cur=='SUPPORT_UNCERTAIN' and supp=='SUPPORTED': supp=cur
 support['state']=supp
 if supp!='SUPPORTED': return {'state':supp,'stations':None,'features':None,'support':support}
 sa,A=walk_locate(cap,bp,(h,h),False); sc,C=walk_locate(cap,fp,(h,h),False)
 if sa!='DEFINED': return {'state':sa,'stations':None,'features':None,'support':support}
 if sc!='DEFINED': return {'state':sc,'stations':None,'features':None,'support':support}
 cen=pts[center]; B=make_station(None,cen,cen,(Z,Z),((cen[0],cen[0]),(cen[1],cen[1]))); feats=features(cap,A,B,C,h)
 return {'state':'UNDEFINED_ZERO_CHORD' if feats['chord_ac']['interval']==(Z,Z) else 'DEFINED','stations':{'A':A,'B':B,'C':C},'features':feats,'support':support}
def verify_witness(cap,frac,w,is_ceil):
 cap.tick(10)
 if type(w) is not int or w<0 or bl(w)>MAXBITS: raise Bad('witness')
 if bl(frac.numerator)+96>MAXBITS: raise Bad('witnessbits')
 N=frac.numerator<<(2*P); d=frac.denominator
 def sqprod(k):
  if 2*bl(k)+bl(d)>MAXBITS: raise Bad('witnessprod')
  return k*k*d
 if not is_ceil: return sqprod(w)<=N<sqprod(w+1)
 if w==0: return N==0
 return sqprod(w-1)<N<=sqprod(w)
def verify_transcript(rec,cap):
 tr=rec['transcript']; cap.events=None
 if not isinstance(tr,list) or len(tr)>10000: raise Bad('transcript')
 for e in tr:
  if not isinstance(e,dict): raise Bad('entry')
  op=e.get('op')
  if op=='sqrt_interval':
   keys(e,{'op','input','output','witness_lo','witness_hi'}); x=ipair(cap,e['input']); out=ipair(cap,e['output'])
   if not verify_witness(cap,x[0],e['witness_lo'],False): raise Bad('wlo')
   if not verify_witness(cap,x[1],e['witness_hi'],True): raise Bad('whi')
   if out[0]!=mk(cap,e['witness_lo'],SCALE) or out[1]!=mk(cap,e['witness_hi'],SCALE): raise Bad('sqrtout')
  elif op in ('add','sub','mul','divide'):
   keys(e,{'op','input','output'})
   if not isinstance(e['input'],list) or len(e['input'])!=2: raise Bad('bininput')
   x=ipair(cap,e['input'][0]); y=ipair(cap,e['input'][1]); out=ipair(cap,e['output'])
   got={'add':iadd,'sub':isub,'mul':imul,'divide':idiv}[op](cap,x,y)
   if got!=out: raise Bad('opout')
  elif op=='square':
   keys(e,{'op','input','output'}); x=ipair(cap,e['input']); out=ipair(cap,e['output'])
   if isq(cap,x)!=out: raise Bad('sqout')
  else: raise Bad('unknownop')
def expr_parts(terms):
 const=Fraction(0); coeff=Fraction(0); rad=1
 for coord in [terms]: pass
 return const,coeff,rad
def combine_terms(cap,coord):
 const=Z; coeff=Z; rad=None
 for t in coord:
  v=mk(cap,t['num'],t['den'])
  if t['radicand']==1: const=add(cap,const,v)
  elif rad is None or rad==t['radicand']: rad=t['radicand']; coeff=add(cap,coeff,v)
  else: raise Bad('radicals')
 return const,coeff,(rad if rad is not None else 1)
def sign_expr(cap,const,coeff,rad,bound):
 A=sub(cap,const,bound); c=coeff; ac=cmpf(cap,A,Z); cc=cmpf(cap,c,Z)
 if cc==0: return ac
 if ac==0: return cc
 if ac==cc: return ac
 left=mul(cap,A,A); right=mul(cap,mul(cap,c,c),mk(cap,rad)); lc=cmpf(cap,left,right)
 if lc==0: return 0
 if ac>0: return 1 if lc>0 else -1
 return 1 if lc<0 else -1
def encloses(cap,interval,coord):
 const,coeff,rad=combine_terms(cap,coord)
 return sign_expr(cap,const,coeff,rad,interval[0])>=0 and sign_expr(cap,const,coeff,rad,interval[1])<=0
def cmp_station(rep,exp,cap=None):
 cap=cap if cap is not None else CapB()
 if exp is None:
  if rep is not None: raise Bad('stationnull')
  return
 keys(rep,{'segment','from_point','to_point','t','point'})
 if rep['segment']!=exp['segment']: raise Bad('segment')
 for kk in ('from_point','to_point'):
  got=[dec_pair(rep[kk][0],cap),dec_pair(rep[kk][1],cap)]; want=[exp['from'] if kk=='from_point' else exp['to']][0]
  if got[0]!=want[0] or got[1]!=want[1]: raise Bad('endpoint')
 if dec_interval(rep['t'],cap)!=exp['t']: raise Bad('t')
 if dec_interval(rep['point'][0],cap)!=exp['point'][0] or dec_interval(rep['point'][1],cap)!=exp['point'][1]: raise Bad('pointinterval')
def cmp_features(rep,exp,cap=None):
 cap=cap if cap is not None else CapB()
 if exp is None:
  if rep is not None: raise Bad('featuresnull')
  return
 keys(rep,{'cross','dot','chord_ba','chord_bc','chord_ac','deficit','deviation','curvature','angle'})
 for k,v in exp.items():
  f=rep[k]; keys(f,{'state','interval','unit','width'})
  if f['state']!=v['state'] or f['unit']!=v['unit']: raise Bad('fieldmeta')
  if dec_interval(f['interval'],cap)!=v['interval']: raise Bad('fieldinterval')
  w=dec_pair(f['width'],cap) if f['width'] is not None else None
  if w!=v['width']: raise Bad('width')
def cmp_support(rep,exp,cap=None):
 cap=cap if cap is not None else CapB()
 if exp is None:
  if rep is not None: raise Bad('supportnull')
  return
 keys(rep,{'perimeter','backward','forward','state'})
 if rep['state']!=exp['state']: raise Bad('supportstate')
 for k in ('perimeter','backward','forward'):
  if dec_interval(rep[k],cap)!=exp[k]: raise Bad('supportinterval')
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha',required=True); ap.add_argument('--root',required=True); ap.add_argument('--report',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(argv)
 errors=[]; verified=False; contract=None; resource_inconclusive=False
 try:
  cdata=load_pin(a.contract,a.contract_sha,MAXREPORT); contract=parse(cdata); validate_contract(contract)
  root=Path(a.root).resolve(); opath=(root/contract['old_oracles']['path']).resolve()
  if root not in opath.parents: raise Bad('path')
  odata=read_bounded(opath)
  if len(odata)>MAXREPORT or hashlib.sha256(odata).hexdigest()!=contract['old_oracles']['sha256']: raise Bad('oraclepin')
  oracles=parse(odata); total=validate_oracles(oracles)
  if total!=contract['invariants']['old_query_count']: raise Bad('count')
  rdata=read_bounded(a.report)
  if len(rdata)>MAXREPORT: raise Bad('reportlarge')
  report=parse(rdata)
  keys(report,{'schema','contract_sha256','oracles_sha256','p','max_bits','max_operations','threshold','claim_scope','producer_status','calibration_ready','natural_positive_count','human_cases','records'})
  if report['schema']!='q02b1-report.v1' or report['contract_sha256']!=hashlib.sha256(cdata).hexdigest() or report['oracles_sha256']!=hashlib.sha256(odata).hexdigest(): raise Bad('reportpin')
  if report['p']!=P or report['max_bits']!=MAXBITS or report['max_operations']!=MAXOPS or report['claim_scope']!='NUMERIC_KERNEL_ONLY' or report['producer_status']!='PRODUCED_UNVERIFIED': raise Bad('reportmeta')
  if report['calibration_ready'] is not False or report['natural_positive_count']!=0: raise Bad('claims')
  if dec_pair(report['threshold'])!=pair(CapB(),contract['threshold_binary_ratio']): raise Bad('threshold')
  humans=report['human_cases']
  if not isinstance(humans,list) or len(humans)!=contract['human_cases']['count']: raise Bad('humans')
  for i,hh in enumerate(humans):
   keys(hh,{'index','state'})
   if hh['index']!=i or hh['state']!='GEOMETRY_UNBOUND': raise Bad('humanstate')
  thr=pair(CapB(),contract['threshold_binary_ratio']); expected=[]
  for f in oracles['fixtures']:
   for qi,q in enumerate(f['queries']): expected.append(('old',f"old:{f['id']}:{q['h']}",{'fixture':f,'query_index':qi},f,q))
  for e in contract['window_extras']: expected.append(('window',e['id'],e,e,None))
  for e in contract['station_extras']: expected.append(('station',e['id'],e,e,None))
  for e in contract['interval_extras']: expected.append(('interval',e['id'],e,e,None))
  recs=report['records']
  if not isinstance(recs,list) or len(recs)!=len(expected): raise Bad('recordcount')
  mapping=contract['invariants']['old_states']
  for rec,(kind,rid,source,obj,aux) in zip(recs,expected):
   try:
    if not isinstance(rec,dict) or rec.get('id')!=rid or rec.get('kind')!=kind: raise Bad('recordid')
    if not strict_eq(rec.get('source'),source): raise Bad('source')
    cap=CapB()
    verify_transcript(rec,cap)
    cap.events=[]
    if kind in ('old','window'):
     keys(rec,{'id','kind','source','state','transcript','fixture_id','query_index','center_index','h','stations','features','support'})
     if kind=='old':
      ptsraw=obj['points']; closed=obj['closed']; center=obj['center_index']; h=mk(cap,aux['h']); fid=obj['id']
      if rec['fixture_id']!=fid or rec['query_index']!=source['query_index'] or rec['center_index']!=center or dec_pair(rec['h'],cap)!=h: raise Bad('oldmeta')
     else:
      ptsraw=obj['points']; closed=obj['closed']; center=obj['center_index']; h=pair(cap,obj['h']); fid=obj['id']
      if rec['fixture_id']!=fid or rec['query_index'] is not None or rec['center_index']!=center or dec_pair(rec['h'],cap)!=h: raise Bad('windowmeta')
     try: exp=expected_window(cap,conv_pts(cap,ptsraw),closed,center,h,thr)
     except Cap: exp={'state':'RESOURCE_INCONCLUSIVE','stations':None,'features':None,'support':None}
     want= mapping[aux['state']] if kind=='old' else obj['expected']
     # producer state for old DEFINED is exp state; mapped want must agree with exp on trusted data
     if kind=='old' and exp['state']!=want: raise Bad('oracle-state-self')
     if rec['state']!=exp['state']: raise Bad('state')
     if kind=='window' and rec['state']!=obj['expected']: raise Bad('windowexpected')
     if rec['state']!='RESOURCE_INCONCLUSIVE' and exp['state']!='RESOURCE_INCONCLUSIVE':
      req={json.dumps(e,sort_keys=True) for e in cap.events}; rep={json.dumps(e,sort_keys=True) for e in rec['transcript']}
      if req!=rep: raise Bad('proofset')
     cmp_support(rec['support'],exp['support'],cap)
     if exp['stations'] is None:
      if rec['stations'] is not None or rec['features'] is not None: raise Bad('nullstations')
     else:
      keys(rec['stations'],{'A','B','C'})
      for kk in ('A','B','C'): cmp_station(rec['stations'][kk],exp['stations'][kk],cap)
      cmp_features(rec['features'],exp['features'],cap)
      if kind=='old' and aux['state'] in ('DEFINED','COINCIDENT_SUPPORT'):
       A=exp['stations']['A']; C=exp['stations']['C']
       if not encloses(cap,A['point'][0],aux['a_exact'][0]) or not encloses(cap,A['point'][1],aux['a_exact'][1]): raise Bad('aexact')
       if not encloses(cap,C['point'][0],aux['c_exact'][0]) or not encloses(cap,C['point'][1],aux['c_exact'][1]): raise Bad('cexact')
    elif kind=='station':
     keys(rec,{'id','kind','source','state','transcript','query','station'})
     if not strict_eq(rec['query'],obj['query']): raise Bad('query')
     try:
      Q=ipair(cap,obj['query']); expst=None; station=None
      if cmpf(cap,Q[0],Z)<0: expst='INVALID_QUERY'
      else:
       pts=conv_pts(cap,obj['points'])
       if obj['closed'] and len(pts)>2 and pts[-1]==pts[0]: pts=pts[:-1]
       if degenerate(cap,pts,obj['closed'],thr): expst='DEGENERATE'
       else:
        idx=[i%len(pts) for i in range(len(pts)+1)] if obj['closed'] else list(range(len(pts)))
        path=[pts[i] for i in idx]; path_total(cap,path); expst,station=walk_locate(cap,path,Q,obj['closed'])
     except Cap: expst='RESOURCE_INCONCLUSIVE'; station=None
     if rec['state']!=expst or rec['state']!=obj['expected']: raise Bad('stationstate')
     if rec['state']!='RESOURCE_INCONCLUSIVE' and expst!='RESOURCE_INCONCLUSIVE':
      req={json.dumps(e,sort_keys=True) for e in cap.events}; rep={json.dumps(e,sort_keys=True) for e in rec['transcript']}
      if req!=rep: raise Bad('proofset')
     cmp_station(rec['station'],station,cap)
    else:
     keys(rec,{'id','kind','source','state','transcript','op','x','y','result_interval'})
     if rec['op']!=obj['op'] or not strict_eq(rec['x'],obj['x']) or not strict_eq(rec['y'],obj.get('y')): raise Bad('intervalmeta')
     try:
      x=ipair(cap,obj['x']); y=ipair(cap,obj['y']) if obj.get('y') is not None else None
      if obj['op']=='sqrt': expst='DEFINED'; res=root_interval(cap,x)
      elif obj['op']=='square': expst='DEFINED'; res=isq(cap,x)
      elif obj['op']=='divide':
       f=qfld(cap,x,y,'1'); expst=f['state']; res=f['interval']
      else: raise Bad('op')
     except Cap: expst='RESOURCE_INCONCLUSIVE'; res=None
     if rec['state']!=expst or rec['state']!=obj['expected']: raise Bad('intervalstate')
     if rec['state']!='RESOURCE_INCONCLUSIVE' and expst!='RESOURCE_INCONCLUSIVE':
      req={json.dumps(e,sort_keys=True) for e in cap.events}; rep={json.dumps(e,sort_keys=True) for e in rec['transcript']}
      if req!=rep: raise Bad('proofset')
     if dec_interval(rec['result_interval'],cap)!=res: raise Bad('result')
     if 'exact' in obj and dec_interval(rec['result_interval'],cap)!=ipair(cap,obj['exact']): raise Bad('literalexact')
   except Cap: resource_inconclusive=True
   except (Bad,KeyError,TypeError,ValueError,ZeroDivisionError,IndexError) as e: errors.append(f'{rid}: {e}')
  verified=not errors and not resource_inconclusive
 except (Bad,OSError,ValueError,KeyError,TypeError) as e: errors.append(str(e))
 out={'schema':'q02b1-verification.v1','status':'VERIFIED_NUMERIC_KERNEL_ONLY' if verified else ('RESOURCE_INCONCLUSIVE' if resource_inconclusive and not errors else 'REJECTED'),'errors':errors[:50],'calibration_ready':False,'natural_positive_count':0,'human_cases_state':'GEOMETRY_UNBOUND','angle_state':'PENDING_CERTIFIED_ANGLE','c1':contract.get('c1','NOT_REVIEWED') if isinstance(contract,dict) else 'NOT_REVIEWED','controls':contract.get('controls') if isinstance(contract,dict) else None,'human_cases_resolved':contract.get('human_cases',{}).get('resolved',0) if isinstance(contract,dict) and isinstance(contract.get('human_cases'),dict) else 0,'scope':contract.get('scope') if isinstance(contract,dict) else None}
 if verified:
  out['record_count']=len(recs)
  out['expected_resource_case_ids']=[r['id'] for r in recs if r['state']=='RESOURCE_INCONCLUSIVE']
  out['all_records_numerically_defined']=all(r['state']=='DEFINED' for r in recs)
  out['verification_meaning']='Kernel behavior including declared resource-limit negative controls; no map acceptance'
 try:
  with open(a.output,'x',encoding='utf-8') as fh: fh.write(json.dumps(out,indent=2)+'\n')
 except OSError as e:
  print(str(e),file=sys.stderr); return 2
 return 0 if verified else 3
if __name__=='__main__': raise SystemExit(main())
