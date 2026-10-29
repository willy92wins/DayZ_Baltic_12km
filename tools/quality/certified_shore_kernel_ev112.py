#!/usr/bin/env python3
import argparse, hashlib, json, math, sys
from fractions import Fraction
from math import isqrt
from pathlib import Path
P=48; SCALE=1<<P; MAXBITS=4096; MAXOPS=100000; MAXIN=16*1024*1024; Z=Fraction(0); ONE=Fraction(1)
class Bad(Exception): pass
class Res(Exception): pass
def bits(x): return abs(int(x)).bit_length()
class Budget:
 def __init__(self): self.ops=0
 def tick(self,n=1):
  self.ops+=n
  if self.ops>MAXOPS: raise Res('ops')
 def est(self,*vals):
  self.tick()
  if sum(bits(v) for v in vals)>MAXBITS: raise Res('bits')
def fmake(b,n,d=1):
 if d==0: raise Bad('den0')
 if d<0: n=-n; d=-d
 if bits(n)>MAXBITS or bits(d)>MAXBITS: raise Res('fracbits')
 b.tick(); return Fraction(n,d)
def fadd(b,a,c):
 b.est(a.numerator,c.denominator); b.est(c.numerator,a.denominator); b.est(a.denominator,c.denominator)
 if max(bits(a.numerator)+bits(c.denominator),bits(c.numerator)+bits(a.denominator))+1>MAXBITS: raise Res('addbits')
 return fmake(b,a.numerator*c.denominator+c.numerator*a.denominator,a.denominator*c.denominator)
def fsub(b,a,c): return fadd(b,a,fmake(b,-c.numerator,c.denominator))
def fmul(b,a,c):
 b.est(a.numerator,c.numerator); b.est(a.denominator,c.denominator)
 return fmake(b,a.numerator*c.numerator,a.denominator*c.denominator)
def fdiv(b,a,c):
 if c==0: raise Bad('div0')
 return fmul(b,a,fmake(b,c.denominator,c.numerator))
def fcmp(b,a,c):
 b.est(a.numerator,c.denominator); b.est(c.numerator,a.denominator)
 x=a.numerator*c.denominator; y=c.numerator*a.denominator
 return (x>y)-(x<y)
def encf(f): return [f.numerator,f.denominator]
def enci(x): return [encf(x[0]),encf(x[1])]
def logop(log,op,inp,out,wlo=None,whi=None):
 if log is not None:
  e={'op':op,'input':inp,'output':out}
  if wlo is not None: e['witness_lo']=wlo; e['witness_hi']=whi
  log.append(e)
def iadd(b,x,y,log=None):
 o=(fadd(b,x[0],y[0]),fadd(b,x[1],y[1])); logop(log,'add',[enci(x),enci(y)],enci(o)); return o
def isub(b,x,y,log=None):
 o=(fsub(b,x[0],y[1]),fsub(b,x[1],y[0])); logop(log,'sub',[enci(x),enci(y)],enci(o)); return o
def imul(b,x,y,log=None):
 vals=[fmul(b,x[0],y[0]),fmul(b,x[0],y[1]),fmul(b,x[1],y[0]),fmul(b,x[1],y[1])]
 lo=vals[0]; hi=vals[0]
 for v in vals[1:]:
  if fcmp(b,v,lo)<0: lo=v
  if fcmp(b,v,hi)>0: hi=v
 o=(lo,hi); logop(log,'mul',[enci(x),enci(y)],enci(o)); return o
def isquare(b,x,log=None):
 a=fmul(b,x[0],x[0]); c=fmul(b,x[1],x[1])
 if fcmp(b,x[0],Z)<=0 and fcmp(b,x[1],Z)>=0: o=(Z,a if fcmp(b,a,c)>=0 else c)
 else: o=(a if fcmp(b,a,c)<=0 else c,a if fcmp(b,a,c)>=0 else c)
 logop(log,'square',enci(x),enci(o)); return o
def idiv(b,x,y,log=None):
 if fcmp(b,y[0],Z)<=0 and fcmp(b,y[1],Z)>=0: raise Bad('divzerointerval')
 r1=fdiv(b,ONE,y[0]); r2=fdiv(b,ONE,y[1]); rec=(r1 if fcmp(b,r1,r2)<=0 else r2,r2 if fcmp(b,r1,r2)<=0 else r1)
 o=imul(b,x,rec);
 logop(log,'divide',[enci(x),enci(y)],enci(o))
 return o
def sqrt_witnesses(b,f):
 b.tick(16) # charge the bounded root primitive before shift/divide/isqrt/products
 if bits(f.numerator)+2*P>MAXBITS: raise Res('sqrtbits')
 n=f.numerator<<(2*P); d=f.denominator; j=isqrt(n//d)
 if 2*bits(j+1)+bits(d)>MAXBITS: raise Res('witnessbits')
 if not (j*j*d<=n<(j+1)*(j+1)*d): raise Bad('witness')
 exact=(j*j*d==n); whi=j if exact else j+1
 return j,whi
def sqrt_interval(b,x,log=None):
 if fcmp(b,x[0],Z)<0: raise Bad('sqrtneg')
 wlo,_=sqrt_witnesses(b,x[0]); _,whi=sqrt_witnesses(b,x[1])
 o=(fmake(b,wlo,SCALE),fmake(b,whi,SCALE)); logop(log,'sqrt_interval',enci(x),enci(o),wlo,whi); return o
def num_frac(b,v):
 if type(v) is int: return fmake(b,v)
 if type(v) is float:
  if not math.isfinite(v): raise Bad('nonfinite')
  n,d=v.as_integer_ratio(); return fmake(b,n,d)
 raise Bad('number')
def pair_frac(b,v):
 if not isinstance(v,list) or len(v)!=2 or type(v[0]) is not int or type(v[1]) is not int or v[1]<=0: raise Bad('pair')
 return fmake(b,v[0],v[1])
def interval_pair(b,v):
 if not isinstance(v,list) or len(v)!=2: raise Bad('interval')
 lo=pair_frac(b,v[0]); hi=pair_frac(b,v[1])
 if fcmp(b,lo,hi)>0: raise Bad('intervalorder')
 return (lo,hi)
def no_dup(pairs):
 o={}
 for k,v in pairs:
  if k in o: raise Bad('dupkey')
  o[k]=v
 return o
def bad_const(x): raise Bad('constant')
def load_bytes(path,limit=MAXIN):
 with open(path,'rb') as fh: data=fh.read(limit+1)
 if len(data)>limit: raise Bad('toolarge')
 return data
def parse_json(data):
 try: return json.loads(data.decode('utf-8'),object_pairs_hook=no_dup,parse_constant=bad_const)
 except Bad: raise
 except Exception as e: raise Bad(str(e))
def keys(o,allowed):
 if not isinstance(o,dict) or set(o)!=set(allowed): raise Bad('keys')
def is_num(v): return type(v) is int or (type(v) is float and math.isfinite(v))
def validate_points(v):
 if not isinstance(v,list) or not (2<=len(v)<=512): raise Bad('points')
 for p in v:
  if not isinstance(p,list) or len(p)!=2 or not is_num(p[0]) or not is_num(p[1]): raise Bad('point')
def validate_terms(v):
 if v is None: return
 if not isinstance(v,list) or len(v)!=2: raise Bad('exact')
 for coord in v:
  if not isinstance(coord,list) or not (1<=len(coord)<=4): raise Bad('terms')
  for t in coord:
   keys(t,{'num','den','radicand'})
   if type(t['num']) is not int or type(t['den']) is not int or type(t['radicand']) is not int or t['den']<=0 or t['radicand']<1: raise Bad('term')
def validate_contract(c):
 keys(c,{'schema','scope','p','max_bits','max_operations','old_oracles','plan_sha256','threshold_binary_ratio','human_cases','controls','c1','calibration_ready','natural_positive_count','angle_state','window_extras','station_extras','interval_extras','invariants','budgets','non_authorizations'})
 if c['schema']!='q02b1-contract.v1' or c['scope']!='NUMERIC_KERNEL_ONLY' or c['p']!=P or c['max_bits']!=MAXBITS or c['max_operations']!=MAXOPS: raise Bad('contract')
 keys(c['old_oracles'],{'path','sha256'})
 if not isinstance(c['old_oracles']['path'],str) or len(c['old_oracles']['sha256'])!=64: raise Bad('oraclepin')
 if len(c['plan_sha256'])!=64: raise Bad('plansha')
 pair_frac(Budget(),c['threshold_binary_ratio'])
 keys(c['human_cases'],{'count','state','resolved'})
 if c['human_cases']!={'count':9,'state':'GEOMETRY_UNBOUND','resolved':0}: raise Bad('human')
 if type(c['controls']) is not int or c['controls']!=4: raise Bad('controls')
 if c['threshold_binary_ratio']!=[3022314549036573,302231454903657293676544]: raise Bad('threshold')
 if c['calibration_ready'] is not False or c['natural_positive_count']!=0 or c['angle_state']!='PENDING_CERTIFIED_ANGLE' or c['c1']!='NOT_REVIEWED': raise Bad('claims')
 for name in ('window_extras','station_extras','interval_extras'):
  if not isinstance(c[name],list) or len(c[name])>128: raise Bad(name)
 for e in c['window_extras']:
  keys(e,{'id','points','closed','center_index','h','expected'}); validate_points(e['points'])
  if type(e['closed']) is not bool or type(e['center_index']) is not int or not (0<=e['center_index']<len(e['points'])): raise Bad('window')
  if not isinstance(e['h'],list): raise Bad('h')
 for e in c['station_extras']:
  keys(e,{'id','points','closed','query','expected'}); validate_points(e['points'])
  if type(e['closed']) is not bool: raise Bad('station')
 for e in c['interval_extras']:
  if not isinstance(e,dict) or 'id' not in e or 'op' not in e or 'x' not in e or 'expected' not in e: raise Bad('intervalextra')
  extra=set(e)-{'id','op','x','y','exact','expected'}
  if extra: raise Bad('intervalkeys')
 keys(c['invariants'],{'old_query_count','old_states','units'})
 if c['invariants']['units']!={'cross':'m^2','dot':'m^2','chord':'m','deficit':'1','deviation':'m','curvature':'1/m'}: raise Bad('units')
def validate_oracles(o):
 keys(o,{'schema','unit','plane','natural_positive_count','calibration_ready','fixtures'})
 if o['schema']!='q02b0-oracles.v1' or o['unit']!='m' or o['plane']!='XZ' or o['natural_positive_count']!=0 or o['calibration_ready'] is not False: raise Bad('oracles')
 if not isinstance(o['fixtures'],list) or not (1<=len(o['fixtures'])<=16): raise Bad('fixtures')
 total=0
 for f in o['fixtures']:
  keys(f,{'id','points','closed','center_index','queries'}); validate_points(f['points'])
  if type(f['closed']) is not bool or type(f['center_index']) is not int or not (0<=f['center_index']<len(f['points'])): raise Bad('fixture')
  if not isinstance(f['queries'],list) or len(f['queries'])>32: raise Bad('queries')
  total+=len(f['queries'])
  for q in f['queries']:
   keys(q,{'h','state','a_exact','c_exact'})
   if type(q['h']) is not int or q['state'] not in ('DEFINED','COINCIDENT_SUPPORT','INSUFFICIENT_SUPPORT'): raise Bad('query')
   validate_terms(q['a_exact']); validate_terms(q['c_exact'])
 return total
def pts_frac(b,raw): return [(num_frac(b,p[0]),num_frac(b,p[1])) for p in raw]
def edges_of(pts,closed):
 e=[(pts[i],pts[i+1]) for i in range(len(pts)-1)]
 if closed: e.append((pts[-1],pts[0]))
 return e
def is_degenerate(b,pts,closed,thr):
 t2=fmul(b,thr,thr)
 for a,c in edges_of(pts,closed):
  dx=fsub(b,c[0],a[0]); dz=fsub(b,c[1],a[1]); q=fadd(b,fmul(b,dx,dx),fmul(b,dz,dz))
  if fcmp(b,q,t2)<0: return True
 return False
def build_path(b,log,pts,indices):
 path=[pts[i] for i in indices]; lengths=[]; prefs=[(Z,Z)]; s=(Z,Z)
 for i in range(len(path)-1):
  dx=fsub(b,path[i+1][0],path[i][0]); dz=fsub(b,path[i+1][1],path[i][1]); q=fadd(b,fmul(b,dx,dx),fmul(b,dz,dz))
  L=sqrt_interval(b,(q,q),log); lengths.append(L); s=iadd(b,s,L,log); prefs.append(s)
 return path,lengths,prefs
def station_obj(seg,frm,to,t,point): return {'segment':seg,'from':frm,'to':to,'t':t,'point':point}
def locate(b,log,path,lengths,prefs,Q,closed_poly):
 total=prefs[-1]
 if fcmp(b,Q[0],Z)<0: return 'INVALID_QUERY',None
 if len(path)<2:
  p=path[0]
  if Q[0]==Q[1] and Q[0]==0: return 'DEFINED',station_obj(None,p,p,(Z,Z),((p[0],p[0]),(p[1],p[1])))
  return 'OUT_OF_RANGE',None
 if Q[0]==Q[1] and Q[0]==0: return 'DEFINED',station_obj(0,path[0],path[1],(Z,Z),( (path[0][0],path[0][0]),(path[0][1],path[0][1])))
 for i in range(len(lengths)):
  S=prefs[i]; N=prefs[i+1]
  if Q[0]==Q[1] and S[0]==S[1] and fcmp(b,Q[0],S[0])==0:
   p=path[i]; return 'DEFINED',station_obj(i,p,path[i+1],(Z,Z),((p[0],p[0]),(p[1],p[1])))
  if fcmp(b,Q[0],S[1])>0 and fcmp(b,Q[1],N[0])<0:
   t=idiv(b,isub(b,Q,S,log),lengths[i],log)
   if fcmp(b,t[0],Z)<0 or fcmp(b,t[1],ONE)>0: return 'BOUNDARY_UNCERTAIN',None
   frm=path[i]; to=path[i+1]; pt=[]
   for k in (0,1):
    d=fsub(b,to[k],frm[k]); prod=imul(b,t,(d,d),log); pt.append(iadd(b,(frm[k],frm[k]),prod,log))
   return 'DEFINED',station_obj(i,frm,to,t,(pt[0],pt[1]))
 if Q[0]==Q[1] and total[0]==total[1] and fcmp(b,Q[0],total[0])==0:
  if closed_poly: p=path[0]; return 'DEFINED',station_obj(0,p,path[1],(Z,Z),((p[0],p[0]),(p[1],p[1])))
  p=path[-1]; return 'DEFINED',station_obj(len(lengths)-1,path[-2],p,(ONE,ONE),((p[0],p[0]),(p[1],p[1])))
 if fcmp(b,Q[0],total[1])>0: return 'OUT_OF_RANGE',None
 return 'BOUNDARY_UNCERTAIN',None
def path_indices(n,center,direction,closed):
 if closed: return [(center+direction*i)%n for i in range(n+1)]
 return list(range(center,-1,-1)) if direction<0 else list(range(center,n))
def field(b,interval,unit): return {'state':'DEFINED','interval':interval,'unit':unit,'width':fsub(b,interval[1],interval[0])}
def qfield(b,num,den,unit,log=None):
 if den[0]==0 and den[1]==0: return {'state':'UNDEFINED_ZERO_CHORD','interval':None,'unit':unit,'width':None}
 if fcmp(b,den[0],Z)<=0 and fcmp(b,den[1],Z)>=0: return {'state':'UNDEFINED_CONDITIONING','interval':None,'unit':unit,'width':None}
 return field(b,idiv(b,num,den,log),unit)
def compute_features(b,log,A,B,C,h):
 Ax,Ay=A['point']; Bx,By=B['point']; Cx,Cy=C['point']
 CA=(isub(b,Cx,Ax,log),isub(b,Cy,Ay,log)); BA=(isub(b,Bx,Ax,log),isub(b,By,Ay,log)); CB=(isub(b,Cx,Bx,log),isub(b,Cy,By,log))
 cross=isub(b,imul(b,CA[0],BA[1],log),imul(b,CA[1],BA[0],log),log)
 dot=iadd(b,imul(b,CA[0],BA[0],log),imul(b,CA[1],BA[1],log),log)
 def chord(v):
  sq=iadd(b,isquare(b,v[0],log),isquare(b,v[1],log),log); return sqrt_interval(b,sq,log)
 chBA=chord(BA); chBC=chord(CB); chAC=chord(CA)
 cross2=isub(b,imul(b,BA[0],CB[1],log),imul(b,BA[1],CB[0],log),log)
 twoh=(fmul(b,fmake(b,2),h),fmul(b,fmake(b,2),h))
 deficit=qfield(b,isub(b,twoh,chAC,log),twoh,'1',log)
 deviation=qfield(b,cross,chAC,'m',log)
 denom=imul(b,imul(b,chBA,chBC,log),chAC,log)
 curvature=qfield(b,imul(b,(fmake(b,2),fmake(b,2)),cross2,log),denom,'1/m',log)
 return {'cross':field(b,cross,'m^2'),'dot':field(b,dot,'m^2'),'chord_ba':field(b,chBA,'m'),'chord_bc':field(b,chBC,'m'),'chord_ac':field(b,chAC,'m'),'deficit':deficit,'deviation':deviation,'curvature':curvature,'angle':{'state':'PENDING_CERTIFIED_ANGLE','interval':None,'unit':'rad','width':None}}
def compute_window_core(b,log,pts,closed,center,h,thr):
 pts=list(pts)
 if closed and len(pts)>2 and pts[-1]==pts[0]: pts=pts[:-1]
 if type(center) is not int or not (0<=center<len(pts)): return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None}
 if fcmp(b,h,Z)<0: return {'state':'INVALID_QUERY','stations':None,'features':None,'support':None}
 if is_degenerate(b,pts,closed,thr): return {'state':'DEGENERATE','stations':None,'features':None,'support':None}
 bi=path_indices(len(pts),center,-1,closed); fi=path_indices(len(pts),center,1,closed)
 bpath,blen,bpref=build_path(b,log,pts,bi); fpath,flen,fpref=build_path(b,log,pts,fi)
 if closed:
  per=fpref[-1]; support={'perimeter':per,'backward':bpref[-1],'forward':per}
  two=fmul(b,fmake(b,2),h)
  if per[0]==per[1]: ok=fcmp(b,two,per[0])<0; supp='SUPPORTED' if ok else 'INSUFFICIENT_SUPPORT'
  elif fcmp(b,two,per[1])>=0: supp='INSUFFICIENT_SUPPORT'
  elif fcmp(b,two,per[0])<0: supp='SUPPORTED'
  else: supp='SUPPORT_UNCERTAIN'
 else:
  support={'perimeter':None,'backward':bpref[-1],'forward':fpref[-1]}; supp='SUPPORTED'
  for dist in (bpref[-1],fpref[-1]):
   if fcmp(b,dist[0],h)>=0: cur='SUPPORTED'
   elif fcmp(b,dist[1],h)<0: cur='INSUFFICIENT_SUPPORT'
   else: cur='SUPPORT_UNCERTAIN'
   if cur=='INSUFFICIENT_SUPPORT': supp=cur
   elif cur=='SUPPORT_UNCERTAIN' and supp=='SUPPORTED': supp=cur
 support['state']=supp
 if supp!='SUPPORTED': return {'state':supp,'stations':None,'features':None,'support':support}
 sa,A=locate(b,log,bpath,blen,bpref,(h,h),False); sc,C=locate(b,log,fpath,flen,fpref,(h,h),False)
 if sa!='DEFINED': return {'state':sa,'stations':None,'features':None,'support':support}
 if sc!='DEFINED': return {'state':sc,'stations':None,'features':None,'support':support}
 cen=pts[center]; B=station_obj(None,cen,cen,(Z,Z),((cen[0],cen[0]),(cen[1],cen[1])))
 feats=compute_features(b,log,A,B,C,h)
 state='UNDEFINED_ZERO_CHORD' if feats['chord_ac']['interval']==(Z,Z) else 'DEFINED'
 return {'state':state,'stations':{'A':A,'B':B,'C':C},'features':feats,'support':support}
def enc_station(s):
 if s is None: return None
 return {'segment':s['segment'],'from_point':[encf(s['from'][0]),encf(s['from'][1])],'to_point':[encf(s['to'][0]),encf(s['to'][1])],'t':enci(s['t']),'point':[enci(s['point'][0]),enci(s['point'][1])]}
def enc_field(f): return {'state':f['state'],'interval':enci(f['interval']) if f['interval'] is not None else None,'unit':f['unit'],'width':encf(f['width']) if f['width'] is not None else None}
def enc_support(s):
 if s is None: return None
 return {'perimeter':enci(s['perimeter']) if s['perimeter'] else None,'backward':enci(s['backward']) if s['backward'] else None,'forward':enci(s['forward']) if s['forward'] else None,'state':s['state']}
def finish_window(rid,kind,source,core,extra=None):
 r={'id':rid,'kind':kind,'source':source,'state':core['state'],'transcript':extra if extra is not None else [],'fixture_id':rid,'query_index':None,'center_index':None,'h':None,'stations':None,'features':None,'support':enc_support(core.get('support'))}
 if core.get('stations'): r['stations']={k:enc_station(v) for k,v in core['stations'].items()}
 if core.get('features'): r['features']={k:enc_field(v) for k,v in core['features'].items()}
 return r
def compute_window_case(points,closed,center,h):
 b=Budget(); log=[]; pts=pts_frac(b,points); hh=fmake(b,h.numerator,h.denominator) if isinstance(h,Fraction) else fmake(b,h)
 thr=fmake(b,3022314549036573,302231454903657293676544); core=compute_window_core(b,log,pts,closed,center,hh,thr)
 r=finish_window('adhoc','window',{},core,log); return r
def new_budget(): return Budget()
def eval_interval_op(b,log,op,x,y=None):
 if op=='sqrt': return 'DEFINED',sqrt_interval(b,x,log)
 if op=='square': return 'DEFINED',isquare(b,x,log)
 if op=='divide':
  f=qfield(b,x,y,'1',log); return f['state'],f['interval']
 raise Bad('op')
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha',required=True); ap.add_argument('--root',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(argv)
 try:
  cdata=load_bytes(a.contract)
  if hashlib.sha256(cdata).hexdigest()!=a.contract_sha.lower(): print('contract pin mismatch',file=sys.stderr); return 2
  contract=parse_json(cdata); validate_contract(contract)
  root=Path(a.root).resolve(); opath=(root/contract['old_oracles']['path']).resolve()
  if root not in opath.parents and opath!=root: print('oracle path escape',file=sys.stderr); return 2
  odata=load_bytes(opath)
  if hashlib.sha256(odata).hexdigest()!=contract['old_oracles']['sha256']: print('oracle pin mismatch',file=sys.stderr); return 2
  oracles=parse_json(odata); total=validate_oracles(oracles)
  if total!=contract['invariants']['old_query_count']: raise Bad('oldcount')
  thr=pair_frac(Budget(),contract['threshold_binary_ratio']); records=[]
  for f in oracles['fixtures']:
   for qi,q in enumerate(f['queries']):
    b=Budget(); log=[]; rid=f"old:{f['id']}:{q['h']}"
    try:
     pts=pts_frac(b,f['points']); core=compute_window_core(b,log,pts,f['closed'],f['center_index'],fmake(b,q['h']),thr)
     r=finish_window(rid,'old',{'fixture':f,'query_index':qi},core,log)
    except Res:
     r=finish_window(rid,'old',{'fixture':f,'query_index':qi},{'state':'RESOURCE_INCONCLUSIVE','stations':None,'features':None,'support':None},log)
    r['fixture_id']=f['id']; r['query_index']=qi; r['center_index']=f['center_index']; r['h']=encf(fmake(Budget(),q['h'])); records.append(r)
  for e in contract['window_extras']:
   b=Budget(); log=[]
   try:
    pts=pts_frac(b,e['points']); h=pair_frac(b,e['h']); core=compute_window_core(b,log,pts,e['closed'],e['center_index'],h,thr); r=finish_window(e['id'],'window',e,core,log)
   except Res: r=finish_window(e['id'],'window',e,{'state':'RESOURCE_INCONCLUSIVE','stations':None,'features':None,'support':None},log)
   r['fixture_id']=e['id']; r['center_index']=e['center_index']; r['h']=encf(pair_frac(Budget(),e['h'])); records.append(r)
  for e in contract['station_extras']:
   b=Budget(); log=[]; base={'id':e['id'],'kind':'station','source':e,'state':'RESOURCE_INCONCLUSIVE','transcript':log,'query':e['query'],'station':None}
   try:
    Q=interval_pair(b,e['query'])
    if fcmp(b,Q[0],Z)<0: base['state']='INVALID_QUERY'
    else:
     pts=pts_frac(b,e['points'])
     if e['closed'] and len(pts)>2 and pts[-1]==pts[0]: pts=pts[:-1]
     if is_degenerate(b,pts,e['closed'],thr): base['state']='DEGENERATE'
     else:
      idx=list(range(len(pts)+1)) if e['closed'] else list(range(len(pts)))
      if e['closed']: idx=[i%len(pts) for i in range(len(pts)+1)]
      path,lengths,prefs=build_path(b,log,pts,idx); st,station=locate(b,log,path,lengths,prefs,Q,e['closed']); base['state']=st; base['station']=enc_station(station)
   except Res: base['state']='RESOURCE_INCONCLUSIVE'
   records.append(base)
  for e in contract['interval_extras']:
   b=Budget(); log=[]; base={'id':e['id'],'kind':'interval','source':e,'state':'RESOURCE_INCONCLUSIVE','transcript':log,'op':e['op'],'x':e['x'],'y':e.get('y'),'result_interval':None}
   try:
    x=interval_pair(b,e['x']); y=interval_pair(b,e['y']) if e.get('y') is not None else None; st,res=eval_interval_op(b,log,e['op'],x,y); base['state']=st; base['result_interval']=enci(res) if res is not None else None
   except Res: base['state']='RESOURCE_INCONCLUSIVE'
   records.append(base)
  report={'schema':'q02b1-report.v1','contract_sha256':hashlib.sha256(cdata).hexdigest(),'oracles_sha256':hashlib.sha256(odata).hexdigest(),'p':P,'max_bits':MAXBITS,'max_operations':MAXOPS,'threshold':encf(thr),'claim_scope':'NUMERIC_KERNEL_ONLY','producer_status':'PRODUCED_UNVERIFIED','calibration_ready':False,'natural_positive_count':0,'human_cases':[{'index':i,'state':'GEOMETRY_UNBOUND'} for i in range(contract['human_cases']['count'])],'records':records}
  text=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
  if len(text.encode('utf-8'))>MAXIN: raise Res('reportlarge')
  with open(a.output,'x',encoding='utf-8') as fh: fh.write(text)
  return 0
 except (Bad,Res,OSError,ValueError) as e:
  print(f'error: {e}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
