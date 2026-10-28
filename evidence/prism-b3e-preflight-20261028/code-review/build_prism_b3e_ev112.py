"""One fresh control/candidate pair; no full package, deployment or DayZ."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,os,subprocess,sys,time,traceback
HERE=Path(__file__).resolve().parent;W=HERE.parent.parent
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
sys.path[:0]=[str(HERE),str(HERE.parent/'water'),str(HERE.parent/'playtest')]
sys.path.append(str(R/'dry-road-build-dependencies-20261028'))
import psutil
import prism_b3e_compiled_ev112 as gate
from continuous_stream_pilot_v31 import model_config
meter=gate.meter
sha=meter.sha
dump=meter.dump

def run_tree(command,cwd,log,seconds,limit=2*1024**3):
    """Sample and bound only descendants of this Popen; never match by name."""
    borns={};observed={};peak=0;start=time.monotonic();reason=None
    def live_owned():
        live=[]
        for pid,born in list(borns.items()):
            try:
                p=psutil.Process(pid)
                if p.create_time()!=born or not p.is_running():continue
                live.append(p)
            except psutil.NoSuchProcess:pass
        return live
    def stop_owned():
        for p in reversed(live_owned()):
            try:
                if p.create_time()==borns[p.pid]:p.kill()
            except psutil.NoSuchProcess:pass
    with log.open('wb') as out:
        child=subprocess.Popen(command,cwd=cwd,stdout=out,stderr=subprocess.STDOUT,creationflags=0x08000000)
        parent=psutil.Process(child.pid);borns[parent.pid]=parent.create_time()
        dump(log.with_suffix('.running.json'),dict(pid=parent.pid,create_time=borns[parent.pid],command=command,max_seconds=seconds,max_sampled_tree_rss_bytes=limit))
        try:
            while True:
                for p in live_owned():
                    try:
                        for d in p.children(recursive=True):borns.setdefault(d.pid,d.create_time())
                    except psutil.NoSuchProcess:pass
                live=live_owned();rss=0
                for p in live:
                    try:
                        rss+=p.memory_info().rss
                        if p.pid not in observed:
                            exe=p.exe();observed[p.pid]=dict(executable=exe,sha256=sha(exe),create_time=p.create_time())
                    except (psutil.NoSuchProcess,FileNotFoundError):pass
                peak=max(peak,rss)
                if time.monotonic()-start>seconds or peak>limit:
                    reason='timeout' if time.monotonic()-start>seconds else 'sampled_tree_memory';stop_owned();child.wait(timeout=10);break
                if child.poll() is not None and not live:break
                time.sleep(.1)
        except BaseException:
            stop_owned();child.wait(timeout=10);raise
    result=dict(returncode=child.returncode,stop_reason=reason,seconds=time.monotonic()-start,peak_sampled_tree_rss_bytes=peak,observed_processes=observed,
                observation_limit='Sampled descendants only. Installed hashes do not prove unobserved short-lived children executed.')
    dump(log.with_suffix('.receipt.json'),result)
    if child.returncode or reason:raise RuntimeError('owned_process_failed:'+str(result))
    return result

def preflight(output):
    output.mkdir(exist_ok=False);meter.STARTED=time.monotonic();meter.MAX_SECONDS=60;stop=meter.bounded(output)
    try:
        old=json.loads((R/'dry-road-build-preflight-20261028/report.json').read_bytes());src=Path(old['original_source']);fixed=R/'dry-road-build-preflight-20261028/preflight_syntax_repaired.py'
        gate.bind(sha(src)==old['original_sha256'] and sha(fixed)==old['local_sha256']=='5fb698727b6c70e8dfa21267963b54cafa60b1ade8b4df3ebfe6b8124e5fc7f2','preflight_sources')
        a=src.read_text();b=fixed.read_text();gate.bind(b.replace("        r'subst P:","        'subst P:")==a,'preflight_literal_only')
        try:compile(a,str(src),'exec');syntax='original_compiles'
        except SyntaxError as e:syntax=f'{type(e).__name__}:line{e.lineno}:{e.msg}'
        spec=importlib.util.spec_from_file_location('b3e_official_preflight',fixed);pf=importlib.util.module_from_spec(spec);spec.loader.exec_module(pf)
        log=io.StringIO()
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):code=pf.main();mods=pf.validate_p_mods();tools=pf.find_dayz_tools()
        (output/'official-checks.log').write_text(log.getvalue(),encoding='utf-8')
        gate.bind(code==0 and mods is None and str(tools)==old['tools_root'],'preflight_failed')
        for p in ('P:/DZ','P:/bin','P:/core','P:/scripts'):gate.bind(Path(p).is_dir(),'dependency_missing:'+p)
        pins={str(src):sha(src),str(fixed):sha(fixed)}
        for p,h in old['tools_sha256'].items():gate.bind(sha(p)==h,'tool_changed:'+p);pins[p]=h
        prior=json.loads((R/'prism-b3-binary-replay-20261028/contract-r1.json').read_bytes())
        for p in [tools/'Bin/Binarize/Binarize.exe',Path('P:/bin/config.cpp')]:
            key=str(p);gate.bind(key in prior['pins'] and sha(p)==prior['pins'][key],'prior_tool_or_config:'+key);pins[key]=sha(p)
        result=dict(status='FRESH_PREFLIGHT_B3E',tools_root=str(tools),pins=pins,original_parse=syntax,
                    installed_skill_modified=False,repair='Archived display-literal raw-prefix only; exact source/diff binding verified.',native_environment_certified=False,measurement=meter.memory())
        dump(output/'report.json',result);return result
    finally:stop.set()

def sequence(build_control,check_control,build_candidate,check_candidate):
    build_control();check_control();build_candidate();check_candidate()

def execute(output):
    output.mkdir(exist_ok=False)
    gate.bind(psutil.__version__=='7.2.2' and Path(psutil.__file__).resolve().is_relative_to(R/'dry-road-build-dependencies-20261028'),'psutil_binding')
    # Human-reviewed code and final tests are required before this entry point.
    approval=R/'prism-b3e-execution-approval-20261028.json';approval_data=json.loads(approval.read_bytes())
    gate.bind(approval_data['status']=='REVIEW_ADJUDICATED_TESTS_PASS','execution_not_ready')
    for p in [Path(__file__),Path(gate.__file__),HERE/'test_prism_b3e_ev112.py',W/'plans/ev112-prism-b3e-compiled-witness-20261028.md']:
        gate.bind(str(p) in approval_data['pins'],'approval_unpinned:'+str(p))
    for p,h in approval_data['pins'].items():gate.bind(sha(p)==h,'approval_postimage_changed:'+p)
    pre=preflight(output/'preflight')
    dpath=R/'prism-b3d-execution-20261028/contract.json';ppath=R/'prism-b3d-consumer-20261028/report.json';priorpath=R/'prism-b3-binary-replay-20261028/contract-r1.json'
    gate.bind(sha(dpath)==gate.OFFLINE and sha(ppath)==gate.PROOF and sha(priorpath)==gate.PRIOR,'ancestry_hash')
    d=json.loads(dpath.read_bytes());prior=json.loads(priorpath.read_bytes());pins=dict(d['pins'])
    for p,h in pins.items():gate.bind(sha(p)==h,'inherited_pin_changed:'+p)
    historic=json.loads((R/'dry-road-compile-pair-20261028/inputs.json').read_bytes())
    for p,h in historic.items():
        if 'dry-road-build-dependencies-20261028' in p:gate.bind(sha(p)==h,'dependency_changed:'+p);pins[p]=h
    for p,h in pre['pins'].items():gate.bind(p not in pins or pins[p]==h,'preflight_ancestry_mismatch:'+p);pins[p]=h
    files=[dpath,ppath,priorpath,R/'prism-b3d-candidate-20261028/candidate.p3d',output/'preflight/report.json',approval,Path(__file__),HERE/'prism_b3e_compiled_ev112.py',HERE/'test_prism_b3e_ev112.py',W/'plans/ev112-prism-b3e-compiled-witness-20261028.md']
    for p in files:pins[str(p)]=sha(p)
    for p,h in approval_data['pins'].items():gate.bind(p not in pins or pins[p]==h,'approval_inherited_mismatch');pins[p]=h
    config=model_config([dict(model='baltic_stream_pilot\\'+gate.old.NAME)]).encode('ascii')
    c=dict(schema='B3E_COMPILED_V1',offline_contract=str(dpath),offline_proof=str(ppath),prior_contract=str(priorpath),source_control=d['reference'],candidate_mlod=str(R/'prism-b3d-candidate-20261028/candidate.p3d'),original_result=d['original_result'],pins=pins,config_sha256=hashlib.sha256(config).hexdigest())
    for k in ('origin','matrix','centre','targets','selected_components'):c[k]=d[k]
    for k in ('baseline_odol','baseline_pbo','poses'):c[k]=prior[k]
    contract=output/'contract.json';dump(contract,c);contract_sha=sha(contract);gate.context(contract)
    reader='C:/temp/moto_lanes/review_g3/tools';receipts=[]
    def stable():gate.check_pins(c);gate.bind(sha(contract)==contract_sha,'contract_changed')
    def build(side):
        stable();folder=output/side/'source/baltic_stream_pilot';folder.mkdir(parents=True,exist_ok=False)
        source=Path(c['source_control'] if side=='control' else c['candidate_mlod']);(folder/gate.old.NAME).write_bytes(source.read_bytes());(folder/'config.cpp').write_bytes(config);(folder/'$PBOPREFIX$').write_bytes(b'baltic_stream_pilot')
        gate.bind(sha(folder/gate.old.NAME)==c['pins'][str(source)],'copied_source')
        result=run_tree(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/water/pack_continuous_stream_pilot_v31.ps1'),'-Pilot',str(output/side)],W,output/side/'driver.log',150)
        _,props,entries=gate.old.read_pbo(output/side/'packed/baltic_stream_pilot.pbo')
        gate.bind(set(entries)=={gate.old.NAME,'config.bin'} and props['prefix']=='baltic_stream_pilot' and entries[gate.old.NAME].startswith(b'ODOL'),'build_payload')
        (output/side/'saved-odol.p3d').write_bytes(entries[gate.old.NAME]);stable()
        result.update(side=side,odol_sha256=sha(output/side/'saved-odol.p3d'),pbo_sha256=sha(output/side/'packed/baltic_stream_pilot.pbo'),config_sha256=hashlib.sha256(entries['config.bin']).hexdigest());dump(output/side/'receipt.json',result);receipts.append(result)
    def check(side):
        dest=output/('control-gate' if side=='control' else 'candidate-gate')
        run_tree([sys.executable,'-I',str(HERE/'prism_b3e_compiled_ev112.py'),side,str(contract),str(output),reader,str(dest)],W,output/(side+'-gate.log'),180)
        report=json.loads((dest/'report.json').read_bytes());gate.bind(report['contract_sha256']==contract_sha and report['status']==('CONTROL_B3E_CERTIFIED' if side=='control' else 'COMPILED_B3E_CONDITIONAL'),'gate_result');stable()
    sequence(lambda:build('control'),lambda:check('control'),lambda:build('candidate'),lambda:check('candidate'))
    gate.bind(receipts[0]['config_sha256']==receipts[1]['config_sha256'],'pair_config_changed')
    dump(output/'completion.json',dict(status='COMPILED_B3E_CONDITIONAL',contract_sha256=contract_sha,proof_sha256=sha(output/'candidate-gate/report.json'),builds=receipts,no_package201_or_dayz=True));print('COMPILED_B3E_CONDITIONAL')

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
    try:execute(a.output)
    except Exception as e:
        if a.output.exists():dump(a.output/'execution-failure.json',dict(status='INCONCLUSIVE_EXECUTION',type=type(e).__name__,reason=str(e),traceback=traceback.format_exc(),note='See child gate reports for any geometric rejection; this wrapper does not reclassify them.'))
        raise

if __name__=='__main__':main()
