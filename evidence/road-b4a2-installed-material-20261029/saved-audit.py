"""Independent read-only audit of consumed B4A2 partial, never opens PBOs."""
from pathlib import Path
import json,hashlib,copy
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-b4a2-saved-audit-20261029';D.mkdir();C=R/'road-b4a2-capture-20261029';sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(C/'report.json').read_bytes();pin=json.loads((R/'road-b4a2-stream-fix-20261029/fix.json').read_bytes())['historical_report_unchanged'];assert sha(raw)==pin
contract_bytes=(R/'road-b4a2-inputs-20261029/contract.json').read_bytes();ch='dc7077e5deed2930f3bb1189df79a1856ff1e70d20bf25e626710b3e84d8edaa';assert sha(contract_bytes)==ch;c=json.loads(contract_bytes);r=json.loads(raw)
def check(r):
 assert r['status']=='INCONCLUSIVE_INITIAL_DISCOVERY' and r['error']=='DiscoveryError:conversion_stream_missing' and r['build_ready'] is False
 assert r['contract_sha256']==ch and r['dependency_closure']=='NOT_EVALUATED'
 assets=r['assets'];assert len(assets)==8 and len({a['virtual_path'] for a in assets})==8
 by={a['virtual_path']:a for a in assets};wanted={s['virtual_path'] for s in c['selected']}|set(c['external']);assert set(by)==wanted
 for s in c['selected']:assert by[s['virtual_path']]['sha256']==s['sha256'] and by[s['virtual_path']]['provider']=='roads'
 ext=r['external'];assert len(ext)==1 and ext[0]['status']=='RESOLVED' and ext[0]['providers']==['surfaces'] and ext[0]['virtual_path']==c['external'][0]
 assert by[c['external'][0]]['sha256']==ext[0]['sha256'] and by[c['external'][0]]['provider']=='surfaces'
 for k,t in r['tables'].items():
  assert t['sha256_after']==t['sha256_observed']==t['sha256_observed_now'] and t['stat_before']==t['stat_after']
  assert t['size']==c['pbos'][k]['bytes'] and t['stat_before'][2]==t['size']
 assert r['tables']['roads']['sha256_after']==c['pbos']['roads']['sha256']
 return by
by=check(r);originals={}
for vp,a in by.items():
 rel=Path(a['local_path']);assert not rel.is_absolute() and '..' not in rel.parts
 b=(C/rel).read_bytes();assert sha(b)==a['sha256'] and len(b)==a['size'] and b[:16].hex()==a['prefix16'];originals[vp]={'sha256':sha(b),'size':len(b)}
rp=C/'receipts/conversion_1';run=json.loads((rp/'running.json').read_bytes());done=json.loads((rp/'completion.json').read_bytes());assert done['rc']==0 and done['reason'] is None and done['identities'][str(run['pid'])]==run['birth'];assert run['input_sha']==by['dz/structures/roads/parts/data/asf1_dashedline.rvmat']['sha256'] and run['executable']==c['cfgconvert']
for s in ['stdout','stderr']:assert sha((rp/s).read_bytes())==done[s+'_sha']
texts=list((C/'decoded').rglob('*.txt'));assert len(texts)==1 and 0<texts[0].stat().st_size<c['limits']['resource_bytes'];assert not (C/'receipts/conversion_2').exists()
neg=[]
for name,mut in [('omittedasset',lambda x:x['assets'].pop()),('promotepartial',lambda x:x.update(status='INITIAL_DISCOVERY_ONLY')),('foreignprovider',lambda x:x['external'][0].update(providers=['surfaces','surfaces_bliss'])),('changedhash',lambda x:x['assets'][0].update(sha256='0'*64)),('changedfileidentity',lambda x:x['tables']['surfaces']['stat_after'].__setitem__(1,0))]:
 x=copy.deepcopy(r);mut(x)
 try:check(x)
 except AssertionError:neg.append(name)
 else:raise AssertionError('mutant passed:'+name)
out={'status':'SAVED_EXTRACTIONS_VERIFIED_PARTIAL_NOT_PROMOTED','report_sha256':pin,'contract_sha256':ch,'assets':originals,'three_pbo_snapshots_hash_stable':True,'conversion_1':{'rc':0,'seconds':done['seconds'],'decoded_sha256':sha(texts[0].read_bytes()),'decoded_bytes':texts[0].stat().st_size,'receipt_identity_verified':True},'conversion_2':'NOT_LAUNCHED','mutants_rejected':neg,'build_ready':False,'material_semantics':'NOT_EVALUATED','map_acceptance':'NOT_EVALUATED','sources_reopened':'saved files only, no PBO or installed vanilla reread'}
(D/'report.json').write_bytes(json.dumps(out,indent=2).encode());assert sha((C/'report.json').read_bytes())==pin;print(json.dumps(out))
