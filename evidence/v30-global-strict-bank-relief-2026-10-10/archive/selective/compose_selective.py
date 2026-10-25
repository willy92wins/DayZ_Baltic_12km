"""Integrate a conservative subset of frozen EV87 directions, with no new solve."""
import hashlib,json,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;EV=HERE.parent;ROOT=EV.parent
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
H=EV/'candidate-terrain.npz';LEDGER=EV/'queue-ledger.jsonl';DIR=EV/'directions.npz'
INDEX=EV/'direction-index.json';PLAN=EV/'selective-integration-plan.md'
INVENTORY=EV/'review-independent/incremental-conflict-inventory.json'
P=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
WRP=ROOT/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
EXPECTED={B:'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
H:'a7146c27a634d3ee59bc4c2763d71050da3172724c4f2620a17fce0775fcf020',
LEDGER:'ac87b33eb999f1250e2fa34ac9368f30a788fd1110dac9c0d138c7255ab69e76',
DIR:'4ce901a0d43989dd6baeac0c4d2d74c2781b41ce5432fe31032aad0c4924df92',
INDEX:'c1fb1f6fcc1a576be662579a730347bac1cce43d91d7e83fe549722ce96d5ba3',
P:'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
F:'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
WRP:'3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'}
MANDATORY={79,398,470,565,575,848}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(4194304),b''):h.update(block)
 return h.hexdigest()
def npz(p):
 with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def cells(nodes):return {(int(r)+dr,int(c)+dc) for r,c in nodes for dr in (-1,0) for dc in (-1,0)}
def main():
 start=time.monotonic();target=HERE/'candidate-terrain.npz';receipt=HERE/'integration-receipt.json'
 assert not target.exists() and not receipt.exists(),'Preserve previous composition'
 for path,digest in EXPECTED.items():assert sha(path)==digest,('input drift',path)
 inv=json.loads(INVENTORY.read_text(encoding='utf-8'))
 assert inv['status']=='COMPLETE_READ_ONLY_CONFLICT_INVENTORY' and inv['acceptance'] is False and inv['scan_cells']==41008
 for path,digest in inv['inputs'].items():assert sha(path)==digest,('inventory input drift',path)
 inputs={str(p):sha(p) for p in (*EXPECTED,INVENTORY,PLAN,Path(__file__))}
 events=[json.loads(s) for s in LEDGER.read_text(encoding='utf-8').splitlines()]
 events=[e for e in events if e.get('event')=='patch' and e['state']=='accepted']
 assert len(events)==718
 marked={tuple(x['cell']) for x in inv['conflict_cells']}
 excluded={e['queue_id'] for e in events if cells(e['mutable_nodes'])&marked}|MANDATORY
 assert {int(x) for x in inv['suggested_rejected_patches']} <= excluded
 source=npz(B);original=npz(H);hb=source['heights'];all_h=hb.copy();result=hb.copy()
 dirs=np.load(DIR,allow_pickle=False);seen=set();records=[];retained=[]
 for e in sorted(events,key=lambda x:x['queue_id']):
  nodes=[tuple(v) for v in e['mutable_nodes']];q=e['queue_id'];direction=dirs[e['direction_key']]
  assert len(nodes)==len(direction) and not seen.intersection(nodes);seen.update(nodes)
  assert hashlib.sha256(np.asarray(direction,dtype='<f4').tobytes()).hexdigest()==e['direction_sha256']
  for v,rv in zip(nodes,direction):
   # Match the frozen author expression exactly, with one float32 serialization.
   value=np.float32(float(hb[v])+(float(rv)-float(hb[v]))*.5)
   all_h[v]=value
   if q not in excluded:result[v]=value
  if q in excluded:
   hit=sorted(cells(nodes)&marked)
   records.append({'queue_id':q,'reason':'compiled_water_conflict' if hit else 'mandatory_footprint_diagnosis',
      'conflict_cells':[list(v) for v in hit],'center':e['center'],'mutable_nodes':e['mutable_nodes']})
  else:retained.append(q)
 assert np.array_equal(all_h,original['heights']),'Frozen directions fail to reconstruct raw EV87 exactly'
 assert source.keys()==original.keys()
 for k in source:
  if k!='heights':assert np.array_equal(source[k],original[k],equal_nan=True),('metadata',k)
 for r,c in marked:
  assert np.array_equal(result[r:r+2,c:c+2],hb[r:r+2,c:c+2]),('marked cell not B exact',r,c)
 diff=result!=original['heights'];restored=np.zeros(hb.shape,dtype=bool)
 for rec in records:
  for v in rec['mutable_nodes']:restored[tuple(v)]=True
 assert not np.any(diff&~restored) and np.array_equal(result[restored],hb[restored])
 source['heights']=result
 np.savez_compressed(target,**source)
 check=npz(target)
 for k in source:assert np.array_equal(source[k],check[k],equal_nan=True)
 for path,digest in inputs.items():assert sha(path)==digest,('end drift',path)
 out={'status':'COMPOSED_COMPLETE','acceptance':False,'inputs':inputs,
  'candidate_path':str(target),'candidate_sha256':sha(target),
  'source_B_path':str(B),'source_B_sha256':sha(B),'source_EV87_path':str(H),'source_EV87_sha256':sha(H),
  'ledger_path':str(LEDGER),'directions_path':str(DIR),'direction_index_path':str(INDEX),'inventory_path':str(INVENTORY),
  'ledger_sha256':sha(LEDGER),'directions_sha256':sha(DIR),'direction_index_sha256':sha(INDEX),
  'conflict_inventory_path':str(INVENTORY),'conflict_inventory_sha256':sha(INVENTORY),
  'selective_integration_plan_sha256':sha(PLAN),'P_sha256':sha(P),'F_sha256':sha(F),'WRP_sha256':sha(WRP),
  'excluded_patches':records,'retained_queue_ids':retained,'conflict_cells':[list(v) for v in sorted(marked)],
  'modified_vertices':int(np.count_nonzero(result!=hb)),'comparison_to_EV87':{'raw_reconstructed_exact':True,
   'differences_only_in_excluded_patches':True,'restored_vertices':int(np.count_nonzero(diff))},
  'seconds':time.monotonic()-start,'limits':['Not validated yet','No new solve','Inherited water discrepancies remain open']}
 receipt.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({k:out[k] for k in ('status','candidate_sha256','modified_vertices','seconds')}))
 print(json.dumps({'retained':len(retained),'excluded':len(excluded),'receipt_sha256':sha(receipt)}))
if __name__=='__main__':main()
