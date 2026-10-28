"""B3E2 continuation: fresh approval/output, isolated preflight, same binary gates."""
from pathlib import Path
import hashlib,json,os,sys,time,traceback
HERE=Path(__file__).resolve().parent;W=HERE.parent.parent;sys.path.insert(0,str(HERE))
import build_prism_b3e_ev112 as base
import preflight_b3e2_ev112 as flight
import preflight_read_discovery_ev112 as reads
gate=base.gate;R=base.R;sha=base.sha;dump=reads.dump
READER=Path('C:/temp/moto_lanes/review_g3/tools')
EXTRA={'lzo_decompress.py':'5ecb852cca9f38258121e2b5246ff8ba438d672b04390442e2e536bc080b8658','lzss_decompress.py':'be3fdf6d38794494cc657639215823fb64035e8d0b26701a6fa0122b0f613898'}
HELPERS={HERE/'build_prism_b3e_ev112.py':'914bef55add8016bec4e82996863a647520d1aa016a67bf7529b5fca94861eaa',HERE/'prism_b3e_compiled_ev112.py':'36bce0d822621e5879179243591d028ed9ae9c09f40c624d6b755db768b9a5eb',HERE/'water_constraint_diagnostic_ev112.py':'a3fe3afd08a516428a7de72251bdad6b175fd6f9d469306d9dcbf11cb709ff45',HERE/'preflight_read_discovery_ev112.py':'308438e6aee0a0a744e2f7f83e5c0c22efe1c15f46f057052a8638bfd40be6a6'}
HELPERS[HERE/'road_asset_catalog_ev112.py']='fb8ac8972e834c21084b2f22c6dd7409daeb052c6c466d97a6ea4929ad5f0427'

def checked_approval(path,output):
    a=json.loads(path.read_bytes());gate.bind(a['schema']=='B3E2_EXECUTION_V1' and a['status']=='REVIEW_ADJUDICATED_TESTS_PASS','approval_schema')
    gate.bind(Path(a['output']).resolve()==output.resolve(),'approval_output')
    required=[Path(__file__),HERE/'preflight_b3e2_ev112.py',HERE/'consume_prism_b3e2_ev112.py',HERE/'test_prism_b3e2_ev112.py',W/'plans/ev112-b3e-build-continuation-20261028.md']
    for p in required:gate.bind(str(p) in a['pins'],'approval_missing:'+str(p))
    for p,h in a['pins'].items():gate.bind(sha(p)==h,'approval_changed:'+p)
    for p,h in HELPERS.items():gate.bind(sha(p)==h,'helper_changed:'+str(p))
    for key in ('review_adjudication','tests'):
        gate.bind(a[key] in a['pins'],'approval_receipt:'+key)
    suite=flight.pinned_json(Path(a['tests']),a['pins'][a['tests']])
    gate.bind(suite['status']=='TESTS_PASS' and suite['tests']>0 and suite['seconds']<=120,'approval_tests')
    for p in required[:-1]:gate.bind(suite['postimages'].get(str(p))==a['pins'][str(p)],'suite_postimage:'+str(p))
    return a

def enforce_receipt(result,elapsed,limit):
    gate.bind(result['returncode']==0 and result['stop_reason'] is None,'process_failed')
    gate.bind(elapsed<=limit and result['seconds']<=limit,'process_deadline')
    gate.bind(result['peak_sampled_tree_rss_bytes']<=2*1024**3,'process_memory')

def run_process(command,log,seconds):
    start=time.monotonic();result=base.run_tree(command,W,log,seconds);enforce_receipt(result,time.monotonic()-start,seconds);return result

def linked_failure(output,exc,phase):
    child=output/phase/'report.json';link=None
    if child.is_file():
        raw=child.read_bytes();link=dict(path=str(child),sha256=hashlib.sha256(raw).hexdigest())
        try:link['status']=json.loads(raw)['status']
        except Exception as error:link['read_error']=type(error).__name__+':'+str(error)
    dump(output/'execution-failure.json',dict(status='INCONCLUSIVE_EXECUTION',phase=phase,type=type(exc).__name__,reason=str(exc),gate_or_preflight=link,traceback=traceback.format_exc(),note='Child status is preserved, not reclassified.'))

def make_contract(pre,approval,approval_path,pre_path):
    dpath=R/'prism-b3d-execution-20261028/contract.json';ppath=R/'prism-b3d-consumer-20261028/report.json';priorpath=R/'prism-b3-binary-replay-20261028/contract-r1.json'
    d=flight.pinned_json(dpath,gate.OFFLINE);flight.pinned_json(ppath,gate.PROOF);prior=flight.pinned_json(priorpath,gate.PRIOR)
    pins=dict(d['pins']);gate.check_pins(dict(pins=pins))
    extra={**pre['pins'],**{str(p):h for p,h in HELPERS.items()},**{str(READER/n):h for n,h in EXTRA.items()},**approval['pins']}
    # The sealed B3D contract already includes the psutil package bytes.
    gate.bind(any('dry-road-build-dependencies-20261028' in p for p in pins),'missing_dependency_pins')
    for p in [dpath,ppath,priorpath,R/'prism-b3d-candidate-20261028/candidate.p3d',pre_path,approval_path]:extra[str(p)]=sha(p)
    for p,h in extra.items():gate.bind(p not in pins or pins[p]==h,'inherited_pin_conflict:'+p);gate.bind(sha(p)==h,'input_changed:'+p);pins[p]=h
    config=base.model_config([dict(model='baltic_stream_pilot\\'+gate.old.NAME)]).encode('ascii')
    c=dict(schema='B3E_COMPILED_V1',offline_contract=str(dpath),offline_proof=str(ppath),prior_contract=str(priorpath),source_control=d['reference'],candidate_mlod=str(R/'prism-b3d-candidate-20261028/candidate.p3d'),original_result=d['original_result'],pins=pins,config_sha256=hashlib.sha256(config).hexdigest())
    for k in ('origin','matrix','centre','targets','selected_components'):c[k]=d[k]
    for k in ('baseline_odol','baseline_pbo','poses'):c[k]=prior[k]
    return c,config

def sequence(build,check):
    build('control');check('control');build('candidate');check('candidate')

def execute(approval_path,output):
    approval=checked_approval(approval_path,output);output.mkdir(exist_ok=False);phase='preflight';emit=reads.Events(output/'events.jsonl')
    try:
        gate.bind(base.psutil.__version__=='7.2.2' and Path(base.psutil.__file__).resolve().is_relative_to(R/'dry-road-build-dependencies-20261028'),'psutil_binding')
        emit(phase);image=reads.interpreter_image()
        run_process([str(image),'-I','-S',str(HERE/'preflight_b3e2_ev112.py'),str(output/'preflight')],output/'preflight-driver.log',60)
        pre=json.loads((output/'preflight/report.json').read_bytes());gate.bind(pre['status']=='FRESH_PREFLIGHT_B3E2','preflight_status')
        identity=json.loads((output/'preflight-driver.running.json').read_bytes());gate.bind(pre['measurement']['pid']==identity['pid'],'preflight_process_identity')
        checked_approval(approval_path,output)
        c,config=make_contract(pre,approval,approval_path,output/'preflight/report.json');contract=output/'contract.json';dump(contract,c);contract_sha=sha(contract);gate.context(contract)
        receipts=[]
        def stable():gate.check_pins(c);gate.bind(sha(contract)==contract_sha,'contract_changed')
        def build(side):
            nonlocal phase
            phase=side;emit('build',side=side);stable();folder=output/side/'source/baltic_stream_pilot';folder.mkdir(parents=True,exist_ok=False)
            source=Path(c['source_control'] if side=='control' else c['candidate_mlod']);(folder/gate.old.NAME).write_bytes(source.read_bytes());(folder/'config.cpp').write_bytes(config);(folder/'$PBOPREFIX$').write_bytes(b'baltic_stream_pilot')
            gate.bind(sha(folder/gate.old.NAME)==c['pins'][str(source)],'copied_source')
            result=run_process(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/water/pack_continuous_stream_pilot_v31.ps1'),'-Pilot',str(output/side)],output/side/'driver.log',150)
            _,props,entries=gate.old.read_pbo(output/side/'packed/baltic_stream_pilot.pbo')
            gate.bind(set(entries)=={gate.old.NAME,'config.bin'} and props['prefix']=='baltic_stream_pilot' and entries[gate.old.NAME].startswith(b'ODOL'),'build_payload')
            (output/side/'saved-odol.p3d').write_bytes(entries[gate.old.NAME]);stable()
            result.update(side=side,odol_sha256=sha(output/side/'saved-odol.p3d'),pbo_sha256=sha(output/side/'packed/baltic_stream_pilot.pbo'),config_sha256=hashlib.sha256(entries['config.bin']).hexdigest());dump(output/side/'receipt.json',result);receipts.append(result)
        def check(side):
            nonlocal phase
            phase=side+'-gate';emit('gate',side=side);stable();dest=output/phase
            run_process([sys.executable,'-I',str(HERE/'consume_prism_b3e2_ev112.py'),side,str(contract),str(output),str(READER),str(dest)],output/(phase+'.log'),180)
            report=json.loads((dest/'report.json').read_bytes());gate.bind(report['contract_sha256']==contract_sha and report['status']==('CONTROL_B3E_CERTIFIED' if side=='control' else 'COMPILED_B3E_CONDITIONAL'),'gate_result');stable()
        sequence(build,check)
        gate.bind(receipts[0]['config_sha256']==receipts[1]['config_sha256'],'pair_config_changed')
        dump(output/'completion.json',dict(status='COMPILED_B3E_CONDITIONAL',contract_sha256=contract_sha,proof_sha256=sha(output/'candidate-gate/report.json'),builds=receipts,no_package201_or_dayz=True))
    except Exception as exc:linked_failure(output,exc,phase);raise

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('approval',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();execute(a.approval,a.output)

if __name__=='__main__':main()
