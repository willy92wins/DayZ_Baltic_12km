from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys, tempfile
from pathlib import Path

EV93=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
SRC=EV93/'preflight'; SOURCE=SRC/'ev93_preflight_windows.py'; LEDGER=SRC/'window-ledger.jsonl'
SUMMARY=SRC/'window-summary.json'; PILOT=SRC/'pilot-compare.json'; QUEUE=EV93/'queue/queue.json'
INDEX=EV93/'ev93-face-index/runs/20261010T092417Z-63d4cec3'
INDEX_REPORT=EV93/'review-independent/runs/attempt-01/verification.json'
OUT=EV93/'preflight-segment02'; STAGE=EV93/'.preflight-segment02-stage'
SOURCE_SHA='a5a8537fa8b9caf092d6ba7b3d55f1f168f15e3541c242cdcc288065cb40c1cc'
QUEUE_SHA='cf13887c8de031d65d0a32dab217e8743293103fcd00ea3c07c281c07a6794c9'
PILOT_SHA='e462259614c5006c80a18175a124c29e7fceb4ae2cb9230b6912a0431429a185'
LEDGER_SHA='190d27837c185911d0c6a09440a015153cadd55f6420a038f73337f2c2137d5d'
SUMMARY_SHA='4b10e58865135a0f79eae4001a76c4f38599fdb580338d853e56c63c43dfe8e6'
INDEX_SHA='c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c'
INDEX_REPORT_SHA='b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4'
CAP=['AssertionError','window detail cap 200 MiB reached']; SEGMENT_CAP=200*1024*1024; TOTAL_CAP=400*1024*1024


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def inside(path,root):
    try: return os.path.commonpath([os.path.normcase(os.path.abspath(path)),os.path.normcase(os.path.abspath(root))])==os.path.normcase(os.path.abspath(root))
    except ValueError: return False


def load_frozen():
    if sha(SOURCE)!=SOURCE_SHA: raise AssertionError('frozen preflight source SHA changed')
    spec=importlib.util.spec_from_file_location('ev93_frozen_segment02',SOURCE)
    if spec is None or spec.loader is None: raise ImportError(str(SOURCE))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if Path(mod.__file__).resolve()!=SOURCE.resolve() or mod.OUT.resolve()!=SRC.resolve():
        raise AssertionError('frozen module identity/original OUT mismatch')
    bad=mod.check_pins()
    if bad: raise AssertionError(f'frozen source pins changed: {bad}')
    return mod


def source_inputs(header,summary):
    exact={
      'source':(SOURCE,SOURCE_SHA),'queue':(QUEUE,QUEUE_SHA),'pilot':(PILOT,PILOT_SHA),
      'ledger':(LEDGER,LEDGER_SHA),'summary':(SUMMARY,SUMMARY_SHA),
      'index_manifest':(INDEX/'manifest.json',INDEX_SHA),
      'index_verification':(INDEX_REPORT,INDEX_REPORT_SHA)}
    hashes={}
    for name,(path,want) in exact.items():
        if not path.is_file() or sha(path)!=want: raise AssertionError(f'{name} source hash mismatch')
        hashes[name]=want
    bindings={'source_sha256':'source','queue_sha256':'queue','pilot_sha256':'pilot',
      'index_manifest_sha256':'index_manifest','index_verification_sha256':'index_verification'}
    for field,name in bindings.items():
        if header.get(field)!=hashes[name]: raise AssertionError(f'header {field} differs')
    for field,name in [('source_sha256','source'),('ledger_sha256','ledger'),('index_manifest_sha256','index_manifest'),('index_verification_sha256','index_verification')]:
        if summary.get(field)!=hashes[name]: raise AssertionError(f'summary {field} differs')
    for path,want in header.get('read_set_sha256',{}).items():
        if not Path(path).is_file() or sha(path)!=want: raise AssertionError(f'read-set hash mismatch: {path}')
    return hashes


def safe_detail(source_out,rec,queue_row):
    qid=int(rec['queue_id']); rel=Path(rec.get('detail_path',''))
    expected=f'q{qid:04d}.json'
    if rel.is_absolute() or '..' in rel.parts or rel.parts!=('window-details',expected):
        raise AssertionError(f'noncanonical detail path qid={qid}')
    root=(source_out/'window-details').resolve(strict=True)
    if not inside(root,source_out.resolve(strict=True)):
        raise AssertionError('detail directory escapes original segment')
    path=(source_out/rel).resolve(strict=True)
    if not inside(path,root) or path.parent!=root or path.name!=expected or path.is_symlink():
        raise AssertionError(f'detail escapes original segment qid={qid}')
    if not path.is_file() or sha(path)!=rec.get('detail_sha256'):
        raise AssertionError(f'detail missing/hash mismatch qid={qid}')
    d=json.loads(path.read_text(encoding='utf-8'))
    identity={'queue_id':qid,'seed_id':int(queue_row['seed_id']),
      'center_rc':[queue_row['row'],queue_row['col']],'window17':queue_row['window17']}
    for key,value in identity.items():
        if d.get(key)!=value or rec.get(key)!=value: raise AssertionError(f'detail/ledger/queue {key} mismatch qid={qid}')
    if d.get('preflight',{}).get('status')!=rec.get('state'): raise AssertionError(f'detail state mismatch qid={qid}')
    return path


def _rewrite(line,rec,absolute_path):
    old='"detail_path":'+json.dumps(rec['detail_path'],ensure_ascii=True)
    new='"detail_path":'+json.dumps(absolute_path,ensure_ascii=True)
    if line.count(old)!=1: raise AssertionError(f'cannot isolate detail_path qid={rec["queue_id"]}')
    result=line.replace(old,new,1)
    a=json.loads(line); b=json.loads(result); a.pop('detail_path'); b.pop('detail_path')
    if a!=b or result.replace(new,old,1)!=line: raise AssertionError('non-path ledger bytes changed')
    return result


def inspect_source():
    mod=load_frozen()
    if OUT.exists() or STAGE.exists(): raise FileExistsError('segment02/staging already exists; preserve and inspect')
    raw=LEDGER.read_bytes().splitlines(keepends=True)
    if len(raw)!=705 or any(not line.endswith(b'\n') for line in raw): raise AssertionError('source ledger is not 703 rows plus header/final')
    texts=[line[:-1].decode('utf-8') for line in raw]
    objects=[json.loads(line) for line in texts]
    head,final=objects[0],objects[-1]; summary=json.loads(SUMMARY.read_text(encoding='utf-8'))
    if head.get('event')!='header' or final.get('event')!='final' or head.get('count')!=703:
        raise AssertionError('source ledger header/final/count mismatch')
    if final.get('status')!='INCOMPLETE_READONLY_PREFLIGHT' or (final.get('processed_count'),final.get('remaining_count'),final.get('error_count'))!=(406,297,297):
        raise AssertionError('source final is not the expected cap-limited checkpoint')
    if summary.get('status')!=final['status'] or summary.get('ledger_sha256')!=LEDGER_SHA or summary.get('source_sha256')!=SOURCE_SHA:
        raise AssertionError('source summary does not bind final ledger/source')
    pins=source_inputs(head,summary)
    queue=json.loads(QUEUE.read_text(encoding='utf-8'))
    first=[s for s in queue['seeds'] if s.get('state')=='first_layer']
    if len(first)!=703 or sha(QUEUE)!=QUEUE_SHA: raise AssertionError('frozen queue is not 703 rows')
    byid={}; errors=[]; detail_map=[]; states={}
    for i,(line,rec) in enumerate(zip(texts[1:-1],objects[1:-1])):
        if rec.get('event')!='window': raise AssertionError('unexpected ledger event')
        qid=int(rec.get('queue_id',-1))
        if qid<0 or qid>=703 or qid in byid: raise AssertionError(f'duplicate/invalid qid {qid}')
        byid[qid]=rec
        seed=first[qid]
        if rec.get('seed_id')!=seed['seed_id'] or rec.get('center_rc')!=[seed['row'],seed['col']] or rec.get('window17')!=seed['window17']:
            raise AssertionError(f'ledger queue identity mismatch qid={qid}')
        if rec.get('state')=='PREFLIGHT_ERROR':
            if rec.get('reason')!=CAP: raise AssertionError(f'non-cap error must not retry qid={qid}: {rec.get("reason")}')
            errors.append(qid); continue
        if rec.get('state') not in ('PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW','PREFLIGHT_INFEASIBLE','PREFLIGHT_INCONCLUSIVE'):
            raise AssertionError(f'unexpected completed state qid={qid}')
        states[rec['state']]=states.get(rec['state'],0)+1
        path=safe_detail(SRC,rec,seed)
        detail_map.append({'queue_id':qid,'seed_id':rec['seed_id'],'source_path':str(path),
          'source_relative_path':rec['detail_path'],'sha256':rec['detail_sha256'],
          'source_line_sha256':hashlib.sha256(raw[i+1]).hexdigest()})
    if set(byid)!=set(range(703)) or len(errors)!=297 or len(detail_map)!=406:
        raise AssertionError('ledger qid coverage/count mismatch')
    if sorted(errors)!=final.get('remaining_queue_ids') or set(errors)!=set(range(703))-set(q for q,r in byid.items() if r['state']!='PREFLIGHT_ERROR'):
        raise AssertionError('remaining IDs are not exactly the cap errors')
    expected_states={'PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW':375,'PREFLIGHT_INFEASIBLE':30,'PREFLIGHT_INCONCLUSIVE':1}
    if states!=expected_states or summary.get('state_counts')!=states: raise AssertionError('done state counts mismatch')
    detail_dir=SRC/'window-details'; files=list(detail_dir.glob('*.json')); size=sum(p.stat().st_size for p in files)
    if len(files)!=406 or size>SEGMENT_CAP: raise AssertionError('source segment detail count/cap mismatch')
    if {str(p.resolve()) for p in files}!={x['source_path'] for x in detail_map}: raise AssertionError('unreferenced/missing detail')
    if size+SEGMENT_CAP>TOTAL_CAP: raise AssertionError('segment caps exceed authorized 400 MiB total')
    pins_after=source_inputs(head,summary)
    if pins_after!=pins or sha(LEDGER)!=LEDGER_SHA: raise AssertionError('source mutated during validation')
    return mod,raw,texts,head,final,summary,detail_map,errors,states,pins,size


def _atomic(path,payload):
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('xb') as f: f.write(payload); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)


def prepare_migration():
    mod,raw,texts,head,final,summary,detail_map,errors,states,pins,source_bytes=inspect_source()
    stage=STAGE; stage.mkdir(exist_ok=False)
    maps={x['queue_id']:x for x in detail_map}
    initial={'status':'MIGRATION_STARTED_NO_PREFLIGHT_EXECUTION','segment01':str(SRC.resolve()),
      'segment02':str(OUT.resolve()),'source_script_sha256':pins['source'],
      'source_ledger_sha256':pins['ledger'],'source_summary_sha256':pins['summary'],
      'pilot_sha256':pins['pilot'],'queue_sha256':pins['queue'],'index_manifest_sha256':pins['index_manifest'],
      'index_verification_sha256':pins['index_verification'],'source_detail_bytes':source_bytes,
      'next_segment_detail_cap_bytes':SEGMENT_CAP,'authorized_total_detail_cap_bytes':TOTAL_CAP,
      'source_state_counts':states,'retry_qids_all_200_mib_cap':errors,'done_detail_mapping':detail_map,
      'execution':'NOT_STARTED'}
    initial_path=stage/'migration-initial.json'
    _atomic(initial_path,(json.dumps(initial,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())
    out_lines=[]
    for i,line in enumerate(texts):
        if i==0 or i==len(texts)-1: out_lines.append(line); continue
        rec=json.loads(line)
        if rec['state']=='PREFLIGHT_ERROR': out_lines.append(line); continue
        out_lines.append(_rewrite(line,rec,maps[int(rec['queue_id'])]['source_path']))
    data=('\n'.join(out_lines)+'\n').encode('utf-8')
    ledger=stage/'window-ledger.jsonl'; _atomic(ledger,data)
    reread=ledger.read_bytes().splitlines(keepends=True)
    if reread[0]!=raw[0] or reread[-1]!=raw[-1] or len(reread)!=len(raw): raise AssertionError('header/final not byte-identical')
    for i,(old,new) in enumerate(zip(raw[1:-1],reread[1:-1]),1):
        a=json.loads(old); b=json.loads(new)
        if a['state']=='PREFLIGHT_ERROR':
            if old!=new: raise AssertionError('error row changed')
            continue
        expect=maps[int(a['queue_id'])]['source_path']
        if b.get('detail_path')!=expect or sha(stage/b['detail_path'])!=b['detail_sha256']:
            raise AssertionError(f'resumed original detail hash/path fails qid={a["queue_id"]}')
        if _rewrite(old[:-1].decode(),a,expect).encode()+b'\n'!=new: raise AssertionError('ledger row differs beyond detail_path')
    if sha(LEDGER)!=pins['ledger'] or sha(SOURCE)!=SOURCE_SHA: raise AssertionError('segment01/source changed during migration')
    prepared={'status':'READY_TO_RESUME_SEGMENT02_NO_MAIN_EXECUTED','migration_initial_sha256':sha(initial_path),
      'launcher_sha256':sha(Path(__file__).resolve()),'source_ledger_sha256':pins['ledger'],
      'migrated_ledger_sha256':sha(ledger),'migrated_ledger_bytes':ledger.stat().st_size,
      'header_and_final_byte_identical':True,'done_details_rehashed':len(detail_map),
      'cap_errors_preserved_for_retry':len(errors),'source_segment_unchanged':True,'execution':'NOT_STARTED'}
    _atomic(stage/'migration-prepared.json',(json.dumps(prepared,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())
    if sha(SOURCE)!=SOURCE_SHA or sha(LEDGER)!=pins['ledger']: raise AssertionError('frozen source changed before stage publish')
    stage.replace(OUT)
    return prepared


def run_approved_segment(approved_sha):
    ready=OUT/'migration-prepared.json'
    if not ready.is_file() or sha(ready)!=approved_sha: raise AssertionError('approved migration SHA required')
    rec=json.loads(ready.read_text(encoding='utf-8'))
    if rec.get('status')!='READY_TO_RESUME_SEGMENT02_NO_MAIN_EXECUTED' or rec.get('execution')!='NOT_STARTED':
        raise AssertionError('migration is not runnable or already used')
    if sha(Path(__file__).resolve())!=rec.get('launcher_sha256'):
        raise AssertionError('launcher changed after migration preparation')
    if sha(OUT/'migration-initial.json')!=rec.get('migration_initial_sha256'):
        raise AssertionError('initial migration manifest changed')
    if sha(OUT/'window-ledger.jsonl')!=rec.get('migrated_ledger_sha256'):
        raise AssertionError('migrated ledger changed before execution')
    if (OUT/'migration-final.json').exists(): raise FileExistsError('segment02 already finished')
    if sha(LEDGER)!=LEDGER_SHA: raise AssertionError('source ledger changed before execution')
    mod=load_frozen(); original_out=mod.OUT; original_argv=sys.argv[:]
    with (OUT/'execution-started.json').open('x',encoding='utf-8') as marker:
        json.dump({'approved_migration_sha256':approved_sha,'launcher_sha256':sha(__file__),
                   'source_sha256':SOURCE_SHA,'original_ledger_sha256':LEDGER_SHA},marker)
    mod.OUT=OUT
    if Path(mod.__file__).resolve()!=SOURCE.resolve() or mod.OUT.resolve()!=OUT.resolve(): raise AssertionError('OUT-only redirect failed')
    sys.argv=[str(SOURCE),'--execute-batch-703','--index-run',str(INDEX),'--pilot-receipt',str(PILOT),'--index-verification',str(INDEX_REPORT)]
    try: mod.main()
    finally: sys.argv=original_argv; mod.OUT=original_out
    summary_path=OUT/'window-summary.json'; ledger=OUT/'window-ledger.jsonl'
    summary=json.loads(summary_path.read_text(encoding='utf-8')); new_bytes=sum(p.stat().st_size for p in (OUT/'window-details').glob('*.json'))
    old_bytes=int(json.loads((OUT/'migration-initial.json').read_text(encoding='utf-8'))['source_detail_bytes'])
    if new_bytes>SEGMENT_CAP or old_bytes+new_bytes>TOTAL_CAP: raise AssertionError('detail storage cap exceeded')
    if sha(SOURCE)!=SOURCE_SHA or sha(LEDGER)!=LEDGER_SHA: raise AssertionError('segment01 mutated during resume')
    final={'status':'SEGMENT02_'+summary['status'],'prepared_sha256':approved_sha,'source_sha256':SOURCE_SHA,
      'queue_sha256':QUEUE_SHA,'source_ledger_sha256':LEDGER_SHA,'segment02_ledger_sha256':sha(ledger),
      'segment02_summary_sha256':sha(summary_path),'summary':summary,'source_detail_bytes':old_bytes,
      'segment02_detail_bytes':new_bytes,'combined_detail_bytes':old_bytes+new_bytes,'segment01_unchanged':True}
    target=OUT/'migration-final.json'
    if target.exists(): raise FileExistsError('migration-final already exists')
    _atomic(target,(json.dumps(final,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())
    return final


def fixtures():
    # Negative/positive cases exercise the production path and line-transform predicates only.
    with tempfile.TemporaryDirectory(prefix='ev93-segment02-fixture-') as td:
        root=Path(td); old=root/'segment01'; details=old/'window-details'; details.mkdir(parents=True)
        q={'seed_id':7,'row':10,'col':20,'window17':[2,12,12,22]}
        value={'queue_id':0,'seed_id':7,'center_rc':[10,20],'window17':q['window17'],'preflight':{'status':'PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW'}}
        p=details/'q0000.json'; p.write_text(json.dumps(value)+'\n',encoding='utf-8')
        rec={'event':'window','queue_id':0,'seed_id':7,'center_rc':[10,20],'window17':q['window17'],
          'state':'PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW','detail_path':'window-details\\q0000.json','detail_sha256':sha(p)}
        _=safe_detail(old,rec,q)
        raw=json.dumps(rec,separators=(',',':')); migrated=_rewrite(raw,rec,str(p.resolve())); m=json.loads(migrated)
        if (root/'segment02'/m['detail_path']).resolve(strict=True)!=p.resolve(): raise AssertionError('OUT/absolute lookup fixture')
        bad=copy_record(rec,detail_path=str((root/'outside.json').resolve()))
        (root/'outside.json').write_text('{}',encoding='utf-8')
        try: safe_detail(old,bad,q)
        except AssertionError: pass
        else: raise AssertionError('path traversal/absolute escape accepted')
        for badrec in (copy_record(rec,queue_id=1),copy_record(rec,detail_sha256='0'*64)):
            try: safe_detail(old,badrec,q)
            except AssertionError: pass
            else: raise AssertionError('qid/hash mutation accepted')
        cap={'queue_id':1,'state':'PREFLIGHT_ERROR','reason':CAP}
        if cap['reason']!=CAP: raise AssertionError('exact cap error fixture')
        noncap=copy_record(cap,reason=['ValueError','different']);
        if noncap['reason']==CAP: raise AssertionError('non-cap retry fixture')
        # Import is declarative only; deliberately invalid argv would fail if source main ran at import.
        old_argv=sys.argv[:]; sys.argv=['not-a-preflight-command']
        try: mod=load_frozen()
        finally: sys.argv=old_argv
        if Path(mod.__file__).resolve()!=SOURCE.resolve(): raise AssertionError('__file__ source anchor fixture')
    return {'status':'PASS_SEGMENT02_FIXTURES','path_containment':True,'source_hash_mutation_guard':True,
      'qid_and_detail_hash_mutation_rejected':True,'cap_only_retry_contract':True,
      'OUT_absolute_path_resolution':True,'nonpath_ledger_bytes_preserved':True,'import_does_not_run_main':True}


def copy_record(record,**changes):
    result=dict(record); result.update(changes); return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--fixtures',action='store_true')
    ap.add_argument('--prepare-migration',action='store_true'); ap.add_argument('--run-approved-segment',action='store_true')
    ap.add_argument('--approved-migration-sha',default=''); a=ap.parse_args()
    if a.fixtures: print(json.dumps(fixtures(),indent=2)); return
    if a.prepare_migration: print(json.dumps(prepare_migration(),indent=2)); return
    if a.run_approved_segment:
        if not a.approved_migration_sha: ap.error('--approved-migration-sha is required')
        print(json.dumps(run_approved_segment(a.approved_migration_sha),indent=2)); return
    ap.error('choose --fixtures, --prepare-migration, or --run-approved-segment')

if __name__=='__main__': main()
