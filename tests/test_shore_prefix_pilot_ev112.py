#!/usr/bin/env python3
import copy,hashlib,importlib.util,json,math,subprocess,sys,tempfile
from fractions import Fraction
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def _load(name,rel):
 spec=importlib.util.spec_from_file_location(name,str(W/rel));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
P=_load('prod_ev112','tools/quality/shore_prefix_pilot_ev112.py')
C=_load('cons_ev112','tools/quality/verify_shore_prefix_pilot_ev112.py')
def _strip(r): return {k:v for k,v in r.items() if k!='ops'}
def _assert_raises(fn,exc=Exception):
 try: fn()
 except exc: return
 raise AssertionError('expected raise')
def _pt(st):
 return tuple(Fraction(x[0][0],x[0][1]) for x in st['point'])
def test_straight_old_oracle():
 pts=[[-120,0],[0,0],[120,0]];cache=P.build_cache(pts,False)
 for h in (6,12,24,48,96):
  r=P.query(cache,1,h);assert r['state']=='DEFINED';assert _pt(r['stations']['A'])== (Fraction(-h),Fraction(0));assert _pt(r['stations']['C'])==(Fraction(h),Fraction(0))
  assert _strip(r)==_strip(C.walk(C.verify_cache(pts,False,cache),1,h))
def test_diamond_wrap_reverse_and_h0():
 pts=[[0,0],[1,1],[2,0],[1,-1]];cache=P.build_cache(pts,True);chk=C.verify_cache(pts,True,cache)
 for center in (0,1,2,3):
  for h in (0,1):
   assert _strip(P.query(cache,center,h))==_strip(C.walk(chk,center,h))
 r=P.query(cache,0,0);assert r['state']=='UNDEFINED_ZERO_CHORD' and _pt(r['stations']['B'])==(Fraction(0),Fraction(0)) and _pt(r['stations']['A'])==(Fraction(0),Fraction(0))
 sq=[[0,0],[10,0],[10,10],[0,10]];sc=P.build_cache(sq,True);assert _strip(P.query(sc,0,5))==_strip(C.walk(C.verify_cache(sq,True,sc),0,5))
def test_open_final_and_spike_ac0():
 pts=[[0,0],[3,0],[6,0]];cache=P.build_cache(pts,False);r=P.query(cache,1,3);assert r['state']=='DEFINED';assert _pt(r['stations']['C'])==(Fraction(6),Fraction(0))
 spike=[[-120,0],[0,0],[-120,0]];sc=P.build_cache(spike,False);r=P.query(sc,1,6);assert r['state']=='UNDEFINED_ZERO_CHORD';assert r['features']['chord_ac']['interval']==[[0,1],[0,1]];assert _strip(r)==_strip(C.walk(C.verify_cache(spike,False,sc),1,6))
def test_boundary_uncertainty():
 pts=[[0,0],[1,1],[2,0],[1,-1]];cache=P.build_cache(pts,True);chk=C.verify_cache(pts,True,cache);h=Fraction(796131459065720,281474976710656)
 a=P.query(cache,0,h);b=C.walk(chk,0,h);assert a['state'] in ('SUPPORT_UNCERTAIN','BOUNDARY_UNCERTAIN');assert _strip(a)==_strip(b)
 pts2=[[0,0],[3,0]];c2=P.build_cache(pts2,False)
 # bilateral open support from an endpoint is insufficient for h>0 (Q02B1 semantics)
 assert P.query(c2,0,1)['state']=='INSUFFICIENT_SUPPORT'
def test_small_root_and_bigbits():
 cache=P.build_cache([[0,0],[5e-324,0],[1,0]],False);assert 0 in cache['degenerate_indices']
 _assert_raises(lambda: P.build_cache([[0,0],[10**2000,0],[10**2000,10**2000]],False))
 _assert_raises(lambda: P.build_cache([[0,0],[10**5000,0],[10**5000,10**5000]],False),P.Resource)
def test_cache_mutations_hit_guards():
 pts=[[0,0],[10,0],[10,10],[0,10]];base=P.build_cache(pts,True);C.verify_cache(pts,True,base)
 m=copy.deepcopy(base);m['edges'][0]['lo']+=1;_assert_raises(lambda: C.verify_cache(pts,True,m))
 m=copy.deepcopy(base);m['edges'][0]['lo']+=1;m['pref_lo']=[x+(1 if i>0 else 0) for i,x in enumerate(m['pref_lo'])];m['pref_hi']=list(m['pref_lo']);_assert_raises(lambda: C.verify_cache(pts,True,m))
 m=copy.deepcopy(base);m['pref_lo'][1]+=1;_assert_raises(lambda: C.verify_cache(pts,True,m))
 _assert_raises(lambda: C.verify_cache([[0,0],[11,0],[10,10],[0,10]],True,base))
 _assert_raises(lambda: C.verify_cache(pts,False,base))
 _assert_raises(lambda: C.verify_cache(list(reversed(pts)),True,base))
 m=copy.deepcopy(base);m['points'][0]=[[999,1],[0,1]];_assert_raises(lambda: C.verify_cache(pts,True,m))
 m=copy.deepcopy(base);m['counters']['ops']=4000001;_assert_raises(lambda: C.verify_cache(pts,True,m))
 m=copy.deepcopy(base);m['degenerate_indices']=[0];_assert_raises(lambda: C.verify_cache(pts,True,m))
 m=copy.deepcopy(base);del m['pref_hi'];_assert_raises(lambda: C.verify_cache(pts,True,m))
def _synthetic(tmp):
 import numpy as np
 chains=[([[0.,0.],[10.,0.],[20.,0.]],False,[1],None),([[0.,0.],[0.,10.],[0.,20.],[0.,30.]],False,[0,3],None),([[0.,0.],[10.,0.],[10.,10.],[0.,10.]],True,[0],None),([[0.,0.],[1e-9,0.],[2.,0.]],True,[],'short_segment')]
 pts=[];po=[0];co=[0];closed=[];sels=[]
 for i,(cp,cl,anchors,prior) in enumerate(chains):
  stored=cp+[cp[0]] if cl else cp;pts.extend(stored);po.append(len(pts));co.append(co[-1]+len(stored)-1);closed.append(cl)
  raw=np.array(cp,dtype='<f8').tobytes();sels.append({'label':'c'+str(i),'chain_id':i,'closed':cl,'point_offset':[po[-2],po[-1]],'segment_offset':[co[-2],co[-1]],'core_count':len(cp),'core_float64_le_sha256':hashlib.sha256(raw).hexdigest(),'anchors':anchors,'prior_degenerate_reason':prior})
 arr=np.array(pts,dtype='<f8');npz=tmp/'x.npz';np.savez(str(npz),point_offsets=np.array(po,dtype='<i8'),chain_offsets=np.array(co,dtype='<i8'),chain_points=arr,closed=np.array(closed,dtype=bool))
 helpers={}
 for rel in P.KNOWN: helpers[rel]=hashlib.sha256((W/rel).read_bytes()).hexdigest()
 contract={'schema':'q02b2.v1','scope':'REAL_CONTOUR_NUMERIC_PILOT_ONLY','plan_sha256':'a'*64,'npz_path':str(npz),'npz_sha256':hashlib.sha256(npz.read_bytes()).hexdigest(),'q02a_sha256':'3fc0b5079ed4bd5f475263ba223bd3139bcc7e159fe9adb37736e5c3fb8465d7','selectors':sels,'h':[0,6,12,24,48,96],'queries':24,'p':48,'threshold_ratio':[3022314549036573,302231454903657293676544],'max_bits':4096,'query_ops':100000,'chain_ops':4000000,'max_edges':14000,'read_limits':{'archive_bytes':67108864,'required_uncompressed_bytes':8388608,'header_bytes':16384,'members':32},'output_limits':{'line_bytes':16777216,'query_bytes':262144,'total_bytes':67108864},'helpers':helpers,'human_cases':{'count':9,'state':'GEOMETRY_UNBOUND','resolved':0},'controls':4,'c1':'NOT_REVIEWED','natural_positive_count':0,'calibration_ready':False,'angle_state':'PENDING_CERTIFIED_ANGLE','budgets':{'author_s':240,'review_s':180,'suite_s':120,'capture_s':120,'consumer_s':120,'bytes':536870912}}
 cpath=tmp/'contract.json';cpath.write_bytes(json.dumps(contract).encode());sha=hashlib.sha256(cpath.read_bytes()).hexdigest();return cpath,sha
def _run(script,extra):
 return subprocess.run([sys.executable,'-I',str(script)]+extra,cwd=str(W),capture_output=True,text=True,timeout=60)
def test_synthetic_cli_and_report_mutations():
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td);cpath,sha=_synthetic(tmp);out=tmp/'report.ndjson';vout=tmp/'verify.json'
  r=_run(W/'tools/quality/shore_prefix_pilot_ev112.py',['--root',str(W),'--contract',str(cpath),'--contract-sha',sha,'--output',str(out)]);assert r.returncode==0,r.stderr
  lines=out.read_text().splitlines();recs=[json.loads(x) for x in lines];assert recs[-1]['query_count']==24 and recs[0]['cache_count']==4
  r=_run(W/'tools/quality/verify_shore_prefix_pilot_ev112.py',['--root',str(W),'--contract',str(cpath),'--contract-sha',sha,'--output',str(vout),'--report',str(out)]);assert r.returncode==0,r.stderr;assert json.loads(vout.read_text())['quality_promotion'] is False
  # deep numeric mutation, unchanged cache/certs
  mut=[json.loads(x) for x in lines]
  for rec in mut:
   if rec.get('kind')=='query' and rec['result']['state']=='DEFINED': rec['result']['features']['cross']['interval'][0][0]+=1;break
  mp=tmp/'mut.ndjson';mp.write_text(chr(10).join(json.dumps(x) for x in mut)+chr(10));o2=tmp/'v2.json'
  r=_run(W/'tools/quality/verify_shore_prefix_pilot_ev112.py',['--root',str(W),'--contract',str(cpath),'--contract-sha',sha,'--output',str(o2),'--report',str(mp)]);assert r.returncode!=0 and not o2.exists()
  # missing query row
  mut2=[json.loads(x) for x in lines];del mut2[3];mp.write_text(chr(10).join(json.dumps(x) for x in mut2)+chr(10));o2=tmp/'v3.json'
  r=_run(W/'tools/quality/verify_shore_prefix_pilot_ev112.py',['--root',str(W),'--contract',str(cpath),'--contract-sha',sha,'--output',str(o2),'--report',str(mp)]);assert r.returncode!=0 and not o2.exists()
  # duplicate query + header claim mutation
  mut3=[json.loads(x) for x in lines];mut3.insert(3,copy.deepcopy(mut3[3]));mp.write_text(chr(10).join(json.dumps(x) for x in mut3)+chr(10))
  r=_run(W/'tools/quality/verify_shore_prefix_pilot_ev112.py',['--root',str(W),'--contract',str(cpath),'--contract-sha',sha,'--output',str(o2),'--report',str(mp)]);assert r.returncode!=0
  mut4=[json.loads(x) for x in lines];mut4[0]['natural_positive_count']=1;mp.write_text(chr(10).join(json.dumps(x) for x in mut4)+chr(10))
  r=_run(W/'tools/quality/verify_shore_prefix_pilot_ev112.py',['--root',str(W),'--contract',str(cpath),'--contract-sha',sha,'--output',str(o2),'--report',str(mp)]);assert r.returncode!=0
def test_closed_core_forged_and_counters():
 pts=[[0,0],[10,0],[10,10],[0,10]];base=P.build_cache(pts,True);chk=C.verify_cache(pts,True,base);assert chk.core['points']==base['points'] and len(chk.core['edges'])==4
 m=copy.deepcopy(base);m['counters']['ops']=-1;_assert_raises(lambda: C.verify_cache(pts,True,m),C.Bad)
 m=copy.deepcopy(base);m['counters']['max_bits']=-1;_assert_raises(lambda: C.verify_cache(pts,True,m),C.Bad)
 m=copy.deepcopy(base);m['_checked']=True;m['edges'][0]['lo']+=1;_assert_raises(lambda: C.walk(m,0,1),C.Bad)
 m=copy.deepcopy(base);m['pref_lo'][1]+=1;_assert_raises(lambda: C.verify_cache(pts,True,m),C.Bad)
 m=copy.deepcopy(base);m['edges'][0]['q']=[2,1];_assert_raises(lambda: C.verify_cache(pts,True,m),C.Bad)
def test_old_oracle30_and_2000_edge_cachephase():
 pts=[[x,0] for x in range(-300,301,10)];cache=P.build_cache(pts,False);chk=C.verify_cache(pts,False,cache)
 for ci in range(25,31):
  for h in (6,12,24,48,96):
   r=P.query(cache,ci,h);cx=-300+10*ci;assert _pt(r['stations']['A'])==(Fraction(cx-h),Fraction(0));assert _pt(r['stations']['C'])==(Fraction(cx+h),Fraction(0));assert _strip(r)==_strip(C.walk(chk,ci,h))
 pts2=[[i,0] for i in range(2001)];c2=P.build_cache(pts2,False);chk2=C.verify_cache(pts2,False,c2);assert len(chk2.core['edges'])==2000
def test_query_shared_budget_reject():
 pts=[[0,0],[10,0],[10,10],[0,10]];chk=C.verify_cache(pts,True,P.build_cache(pts,True));C.load_helpers(W);cap=C.V.CapB();cap.n=100000-1;w=C._Walk(cap);_assert_raises(lambda: C._dir_total(w,chk.core,0,1,True),C.Resource)
def test_sealed_real_contract_schema():
 raw=(W/'tests/fixtures/q02b2/contract.json').read_bytes()
 assert hashlib.sha256(raw).hexdigest()=='84534d48ce33e849130cc0e1390ef034391d935d7f7617838f85451bb09204a2'
 obj=json.loads(raw);P._validate_contract(obj);C._validate_contract(obj)
 for module in (P,C):
  m=copy.deepcopy(obj);m['selectors'][2]['core_count']+=1
  _assert_raises(lambda: module._validate_contract(m),module.Bad)
def test_literal_previous_oracles():
 raw=(W/'tests/fixtures/q02b0/oracles.json').read_bytes()
 assert hashlib.sha256(raw).hexdigest()=='083334300732b33b994dd6d97d063a19db08dd58e64a92cffea806848c4bde1b'
 fixtures=json.loads(raw)['fixtures'];count=0
 for f in fixtures:
  cache=P.build_cache(f['points'],f['closed']);chk=C.verify_cache(f['points'],f['closed'],cache)
  for q in f['queries']:
   r=P.query(cache,f['center_index'],q['h']);v=C.walk(chk,f['center_index'],q['h']);count+=1
   assert _strip(r)==_strip(v)
   expected='UNDEFINED_ZERO_CHORD' if q['state']=='COINCIDENT_SUPPORT' else q['state']
   assert r['state']==expected,(f['id'],q['h'],r['state'],expected)
 assert count==30
def test_core_closing_zero_edge_and_context_reset():
 points=[[0,0],[10,0],[0,0]];cache=P.build_cache(points,True)
 assert len(cache['edges'])==3 and cache['degenerate_indices']==[2]
 chk=C.verify_cache(points,True,cache);assert C.walk(chk,0,1)['state']=='DEGENERATE'
 assert P._QB is None
 P.query(P.build_cache([[0,0],[10,0],[20,0]],False),1,2)
 assert P._QB is None
def test_report_types_cannot_alias_numbers():
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td);cpath,sha=_synthetic(tmp);out=tmp/'report.ndjson'
  r=_run(W/'tools/quality/shore_prefix_pilot_ev112.py',['--root',str(W),'--contract',str(cpath),'--contract-sha',sha,'--output',str(out)]);assert r.returncode==0,r.stderr
  contract=json.loads(cpath.read_bytes());chains=C._source_chains(contract,W);data=out.read_bytes();C.verify_report_data(data,contract,sha,chains)
  records=[json.loads(x) for x in data.splitlines()]
  for mutator in ('header','query','points'):
   m=copy.deepcopy(records)
   if mutator=='header': m[0]['calibration_ready']=0
   elif mutator=='query': next(x for x in m if x['kind']=='query')['result']['support']['backward'][0][0]=False
   else: m[1]['cache']['points'][0][0][0]=False
   raw=b''.join(json.dumps(x).encode()+b'\n' for x in m)
   _assert_raises(lambda: C.verify_report_data(raw,contract,sha,chains),C.Bad)
import unittest
class _All(unittest.TestCase): pass
for _n,_f in sorted(list(globals().items())):
 if _n.startswith('test_'): setattr(_All,_n,lambda self,f=_f: f())
if __name__=='__main__': unittest.main(verbosity=2)
