from pathlib import Path
import copy,json,hashlib,ntpath,stat
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-b4a1-saved-audit-20261029';D.mkdir(exist_ok=False)
C=R/'road-b4a1-inputs-20261029/contract.json';P=R/'road-b4a1-capture-20261029/report.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(C)=='0559c769522b3f74d4fe15ae55a46094207f2a7c49972b41c9c41f8629d85ace'
c=json.loads(C.read_bytes());r=json.loads(P.read_bytes())
def check(d):
 assert d['contract_sha256']==sha(C) and d['status']=='DISCOVERY_ONLY' and d['source_stability']=='STABLE_CAPTURE' and d['build_ready'] is False
 assert len(d['files'])==7 and {f['name'] for f in d['files']}=={f['name'] for f in c['files']}
 assert d['external_references']==[{'normalized':x,'status':'UNRESOLVED_EXTERNAL'} for x in c['external_references']]
 keys=['st_dev','st_ino','st_size','st_mtime_ns'];full=keys+['st_ctime_ns']
 ident=lambda v:tuple(v[k] for k in keys);entire=lambda v:tuple(v[k] for k in full)
 ordinary=lambda v:not (v['st_file_attributes']&0x400) and not stat.S_ISLNK(v['st_mode'])
 for f in d['files']:
  t=next(x for x in c['files'] if x['name']==f['name']);assert f['path']==t['path'] and f['reference_sha256']==t['reference_sha256']
  assert f['stable'] is True and f['status']=='OK' and not f['errors']
  a,b,z=f['fstat_before'],f['fstat_between'],f['fstat_after'];sb,sa,lb,la=[f[x] for x in ['stat_before','stat_after','lstat_before','lstat_after']]
  assert entire(a)==entire(b)==entire(z) and ident(sb)==ident(a) and ident(sa)==ident(z) and ident(la)==ident(z)
  assert entire(sb)==entire(sa) and entire(lb)==entire(la) and ordinary(la)
  assert f['read1']==f['read2'] and f['sha256']==f['read2']['sha256']
  assert f['read1']['size']==a['st_size']==b['st_size']==z['st_size']
  assert all(ident(x['stat'])==ident(x['final_stat']) and ordinary(x['stat']) and ordinary(x['final_stat']) for x in f['ancestors'])
  expected=chr(92)+'??'+chr(92)+ntpath.normpath(c['root'])
  assert all(ntpath.normcase(ntpath.normpath(f[m]['raw_first']))==ntpath.normcase(expected) for m in ['mapping_before','mapping_after'])
  assert len(f['predicates'])==19 and len({p['name'] for p in f['predicates']})==19 and all(p['value'] is True for p in f['predicates'])
  assert f['reference_status']==('MATCH' if f['sha256']==t['reference_sha256'] else 'BYTES_DIFFER_REFERENCE_FORMAT_UNKNOWN')
check(r)
negative=[]
for name,edit in [('omit_file',lambda x:x['files'].pop()),('co_mutated_wrong_fstat_id',lambda x:x['files'][0]['fstat_before'].update(st_ino=42)),('promote_external',lambda x:x['external_references'][0].update(status='MATCH')),('false_reference_match',lambda x:x['files'][0].update(reference_status='MATCH')),('hash_read_disagreement',lambda x:x['files'][0]['read1'].update(sha256='0'*64))]:
 bad=copy.deepcopy(r);edit(bad)
 try:check(bad)
 except AssertionError:negative.append(name)
 else:raise AssertionError('mutant_accepted:'+name)
out={'status':'SAVED_OBSERVATIONS_CONSISTENT','scope':'Independent raw-field arithmetic and identity comparison; no repeat of source capture and no global/build acceptance.','report_sha256':sha(P),'contract_sha256':sha(C),'files':7,'predicates_per_file':19,'negative_cases_rejected':negative,'reference_match':2,'reference_bytes_different_format_unknown':5,'r0_history_reinterpreted':False}
(D/'report.json').write_bytes(json.dumps(out,indent=2).encode());print(out)
