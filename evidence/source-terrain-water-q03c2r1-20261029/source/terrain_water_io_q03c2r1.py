"""Pinned shared input, accounting and terminal schema. No polygon geometry."""
from pathlib import Path
from fractions import Fraction as F
import sys,types,json,hashlib,math,argparse
import numpy as np
ROOT=Path('E:/DayZ-Baltic-Build/shape-repair-20261025/q03c1-local-author-20261029')
PINS={'selected_water_io_q03c1.py':'5f2655572c2f49a3c33d2d43ea8ac4b296d48625cfbcc03967a541ba0ccf0a26','selected_water_producer_q03c1.py':'139691de5c462a195b65cd0b689d8883334ff97053adef334dfe942e15b7b94f','selected_water_consumer_q03c1.py':'912f4f7b86b2e097c6da13d9cf8105a2746e8f1b07a4f8b6f1e69b09c582f301'}
def sealed(name):
 p=ROOT/name;b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=PINS[name]:raise RuntimeError('sealed dependency identity')
 m=types.ModuleType(name[:-3]);m.__file__=str(p);sys.modules[name[:-3]]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m
I=sealed('selected_water_io_q03c1.py')
def geometry(name):return sealed(name)
LIMITS={'bits':4096,'ops':100000,'pieces':1024,'vertices':8192,'lines':1024,'cells':1024,'output':33554432,'retained':67108864}
CLAIMS={'compiled_terrain_evaluated':False,'exposure_evaluated':False,'native_acceptance':False,'map_repaired':False,'human_resolved':0,'C1':'NOT_REVIEWED','terrain_convention':'SOURCE_GRID_NW_SE_ASSUMPTION'}
class Budget(I.Budget):
 def __init__(self,limits=None):super().__init__(limits);self.held=(0,0)
 def hold(self,p,v):
  super().reserve(p,v);self.held=(p,v)
 def reserve(self,p,v):super().reserve(p+self.held[0],v+self.held[1])
class Grid:
 def __init__(self,h,step):
  I.need(type(step) is int and step==6 and isinstance(h,np.ndarray) and h.dtype==np.dtype('<f4') and h.ndim==2 and h.shape[0]==h.shape[1] and 2<=h.shape[0]<=2048,'GEOMETRY','grid descriptor')
  # Row-sized finite mask, not a whole-grid promoted copy.
  I.need(all(np.isfinite(row).all() for row in h),'GEOMETRY','nonfinite height')
  self.h=h;self.n=len(h);self.step=step;self.top=(self.n-1)*step
def config(path,sha):
 c=I.parse(I.read(path,{'sha256':sha}));I.need(c['schema']=='q03c2r1-terrain-water-partition-v1' and I.exact(c['limits'],LIMITS) and I.exact(c['claims'],CLAIMS),'SCHEMA')
 for name,p in c['geometry_sources'].items():I.need(p['sha256']==PINS[name],'IDENTITY');I.read(p['path'],p)
 for key in ('plan','original_plan','oracle','view_contract','view_approval','water_consumer'):I.read(c[key]['path'],c[key])
 for p in c['view_final_sources'].values():I.read(p['path'],p)
 for p in c['view_receipts']:
  v=I.parse(I.read(p['path'],p));I.need(v['rc']==0 and v['reason'] is None,'IDENTITY','view completion')
 proof=I.parse(I.read(c['view_consumer']['path'],c['view_consumer']));r=I.parse(I.read(c['view_report']['path'],c['view_report']))
 validate_view_binding(c,proof,r)
 old,m=I.config(c['water_contract']['path'],c['water_contract']['sha256']);I.need(I.exact(old['archive_limits'],c['archive_limits']),'IDENTITY')
 return c,old,m
def validate_view_binding(c,proof,r):
 I.need(proof['status']=='VERIFIED_SINGLE_HEIGHT_MEMBER_VIEW_ONLY' and r['status']=='SINGLE_HEIGHT_MEMBER_VIEW_UNVERIFIED' and proof['fixture'] is False and r['fixture'] is False,'IDENTITY','view proof')
 expected={'whole_source_archive_validated':False,'other_payloads_decoded':False,'terrain_geometry_evaluated':False,'map_repaired':False}
 I.need(I.exact(proof['claims'],expected) and I.exact(r['claims'],expected),'IDENTITY','claims')
 I.need(proof['report_sha256']==c['view_report']['sha256'] and proof['contract_sha256']==r['contract_sha256']==c['view_contract']['sha256'] and proof['view_sha256']==r['view_sha256']==c['view']['sha256'] and r['view_bytes']==c['view']['bytes'],'IDENTITY','binding')
 I.need(proof['npy_sha256']==r['npy_sha256'] and proof['source_sha256']==r['source_sha256']=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40','IDENTITY')
 I.need(I.exact({k:r[k] for k in c['view_expected']},c['view_expected']),'IDENTITY','member pins')
def view_input(c,path):
 # Canonical input guard before any ZIP or array call; original cannot enter this path.
 I.need(str(Path(path))==str(Path(c['view']['path'])),'IDENTITY','view path')
 return c['view']
def historical(c,old,m):
 scene=m.parse(m.read_small(old['scene']['path'],old['scene']));cc=m.parse(m.read_small(old['index_contract']['path'],old['index_contract']));idx=m.parse(m.read_small(old['index']['path'],old['index']));proof=m.parse(m.read_small(old['index_consumer']['path'],old['index_consumer']))
 I.need(proof['status']==idx['status']=='VERIFIED_SAVED_SELECTED_SURFACE_INDEX_ONLY' and proof['files_read']==204 and proof['contract_sha256']==idx['contract_sha256']==old['index_contract']['sha256'] and I.exact(scene['epoch'],old['epoch']),'IDENTITY','selected scene')
 for p in old['receipts']:
  v=m.parse(m.read_small(p['path'],p));I.need(v['rc']==0 and v['reason'] is None,'IDENTITY')
 for p in scene['pins'].values():m.read_small(p['path'],p)
 specs={p['relative']:p for p in scene['arrays'] if p['kind']=='pilot'};pilots={p['model_index']:p for p in idx['pilots']};I.need(len(specs)==len(pilots)==201,'IDENTITY')
 reservation=c['reservations'];I.need(sum(p['expanded_bound'] for p in specs.values())==reservation['pilot_expanded_bound_sum'] and reservation['session_expanded_bound_sum']==reservation['pilot_expanded_bound_sum']+16777344<=262434599,'IDENTITY','session reservations')
 I.need(reservation['height_load_peak_charge']==(1520+4760)*1024+16777216*3+65536<=LIMITS['retained'],'IDENTITY','retained reservation')
 rd=m.Reader(cc);bed=[];water=[];inventory=[];retained=0
 for mi,pilot in sorted(pilots.items()):
  I.need(pilot['archive'] in specs,'IDENTITY');spec=specs[pilot['archive']];desc=pilot['arraydigestmap']
  def pred(heads):I.need(I.exact(heads,{n:{'dtype':d['descriptor'],'shape':d['shape']} for n,d in desc.items()}),'IDENTITY')
  I.need(retained+3*spec['expanded_bound']+spec['bytes']+65536<=LIMITS['retained'],'RESOURCE_INCONCLUSIVE','pilot retained')
  with rd.open(spec,[n[:-4] for n in desc],pred) as (arrays,actual):
   I.need(I.exact(desc,actual),'IDENTITY','pilot digests')
   for group in (['water','bed'] if mi==3579 else ['water']):
    v=arrays[group];ids=arrays[group+'_source_ids'];counts=arrays[group+'_n'];flags=arrays[group+'_flags'];n=len(v)
    I.need(v.dtype==np.dtype('<f8') and ids.dtype.kind in 'iu' and v.shape==(n,4,3) and ids.shape==(n,2) and counts.shape==flags.shape==(n,) and np.isfinite(v).all() and np.all(counts==3) and not np.any(flags) and not np.any(v[:,3,:].view('<u8')),'GEOMETRY')
    I.need(retained+n*1024<=16777216,'RESOURCE_INCONCLUSIVE','geometry retained');retained+=n*1024;target=water if group=='water' else bed
    for j in range(n):target.append({'key':[mi,j,[int(x) for x in ids[j]]],'triangle':v[j,:3].tolist()})
   inventory.append({'archive':pilot['archive'],'sha256':spec['sha256'],'members':actual})
  del arrays,v,ids,counts,flags
 I.need(len(bed)==1520 and len(water)==4760 and all(pilots[3579][k]==old['target'][k] for k in ('model_index','model','instance_id','pose_row')),'IDENTITY')
 spec=view_input(c,c['view']['path']);wanted={'heights.npy':{'dtype':'<f4','shape':[2048,2048]}}
 def height_pred(h):I.need(I.exact(h,wanted),'IDENTITY','height descriptor')
 I.need(retained+3*16777216+65536<=LIMITS['retained'],'RESOURCE_INCONCLUSIVE','height retained')
 with rd.open(spec,['heights'],height_pred) as (arrays,actual):
  heights=arrays['heights'];d=actual['heights.npy'];I.need(d['data_sha256']==c['view_expected']['payload']['sha256'] and d['bytes']==16777216 and heights.dtype==np.dtype('<f4'),'IDENTITY','height payload');grid=Grid(heights,6)
 metrics=I.parse(I.read(c['metrics']['path'],c['metrics'],33554432));I.need(len(metrics['faces'])==len(bed),'IDENTITY')
 marg=[]
 for face,saved in zip(bed,metrics['faces']):
  I.need(I.exact(face['key'],saved['key']) and saved['status']=='DEFINED','IDENTITY','marginal key');marg.append(saved['areas'])
 return bed,water,grid,{'mode':'HISTORICAL','pilots':inventory,'height_view':c['view'],'retained_charge':retained+16777216,'session_expanded_reserved':rd.session.cumulative_expanded_reserved},marg
def fixture(path,sha):
 data=I.parse(I.read(path,{'sha256':sha},1048576));I.need(type(data) is dict and set(data)=={'bed','water','heights','step'},'SCHEMA')
 for kind in ('bed','water'):
  I.need(type(data[kind]) is list and len(data[kind])<=128,'SCHEMA');seen=set()
  for r in data[kind]:
   I.need(set(r)=={'key','triangle'},'SCHEMA');I.key_ok(r['key']);I.validate_face(r['triangle']);key=I.canonical(r['key']);I.need(key not in seen,'IDENTITY');seen.add(key)
 h=data['heights'];I.need(type(h) is list and 2<=len(h)<=16 and all(type(r) is list and len(r)==len(h) and all(type(v) in (int,float) and math.isfinite(v) for v in r) for r in h),'GEOMETRY')
 return data['bed'],data['water'],Grid(np.asarray(h,dtype='<f4'),data['step']),{'mode':'FIXTURE','sha256':sha},None
def record(key,q,status,areas=None,parts=None,terrain_contacts=None,water_contacts=None,detail=None,water_marginal=None):
 return {'key':key,'status':status,'areas':areas,'water_marginal':water_marginal,'parts':parts or [],'terrain_contacts':terrain_contacts or [],'water_contacts':water_contacts or [],'detail':detail,'stats':q.stats()}
def semantic(r):
 I.need(type(r) is dict and set(r)=={'key','status','areas','water_marginal','parts','terrain_contacts','water_contacts','detail','stats'},'REPORT');I.key_ok(r['key']);I.need(r['status'] in ('DEFINED','RESOURCE_INCONCLUSIVE','DEGENERATE_PROJECTION','INCONCLUSIVE_GEOMETRY'),'REPORT')
 I.need((r['status']=='DEFINED')==(r['areas'] is not None)==(r['water_marginal'] is not None),'REPORT')
 if r['water_marginal'] is not None:I.need(type(r['water_marginal']) is list and len(r['water_marginal'])==3 and all(I.unpack(x)>=0 for x in r['water_marginal']),'REPORT')
 if r['areas'] is not None:I.need(type(r['areas']) is list and len(r['areas'])==9 and all(I.unpack(x)>=0 for x in r['areas']),'REPORT')
 for p in r['parts']:
  I.need(type(p) is dict and set(p)=={'cell','area','min_B_H','max_B_H'},'REPORT');I.need(type(p['cell']) is list and len(p['cell'])==3 and all(type(x) is int and x>=0 for x in p['cell']) and p['cell'][2]<2,'REPORT');I.need(I.unpack(p['area'])>0 and I.unpack(p['min_B_H'])<=I.unpack(p['max_B_H']),'REPORT')
 for v in r['terrain_contacts']:I.need(type(v) is list and len(v)==3 and all(type(x) is int and x>=0 for x in v) and v[2]<2,'REPORT')
 for v in r['water_contacts']:I.key_ok(v)
 st=r['stats'];I.need(type(st) is dict and set(st)=={'ops','peak_pieces','peak_vertices'} and all(type(v) is int and v>=0 for v in st.values()) and st['ops']<=100000 and st['peak_pieces']<=1024 and st['peak_vertices']<=8192,'REPORT')
 return {k:v for k,v in r.items() if k!='stats'}
def check_marginal(r,expected):
 if r['status']=='DEFINED' and expected is not None:
  I.need(I.exact(r['water_marginal'],expected),'REPORT','Q03C1 marginal')
def arguments(consumer=False):
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--out',required=True);p.add_argument('--fixture');p.add_argument('--fixture-sha')
 if consumer:p.add_argument('--capture',required=True)
 return p.parse_args()
def data(c,old,m,a):return fixture(a.fixture,a.fixture_sha) if a.fixture else historical(c,old,m)
def header(sha,inventory,n,w,fixture):return {'schema':'q03c2r1-capture-v1','contract_sha256':sha,'inventory':inventory,'bed_count':n,'water_count':w,'fixture':fixture,'claims':dict(CLAIMS)}
