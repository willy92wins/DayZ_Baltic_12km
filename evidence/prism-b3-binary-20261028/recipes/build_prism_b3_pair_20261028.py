"""One B3B pair, followed by independent saved consumer and conditional package."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
PY='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe'
sys.path[:0]=[str(W/'tools/quality'),str(W/'tools/water'),str(W/'tools/playtest')]
sys.path.append(str(R/'dry-road-build-dependencies-20261028'))
import psutil,numpy as np
import prism_b3_binary_ev112 as gate
from continuous_stream_pilot_v31 import model_config
from attach_navmesh import read_pbo
O=R/'prism-b3-binary-pair-20261028'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def execute(cmd,cwd,out,seconds,limit=2*1024**3):
    start=time.monotonic();peak=0;owned={};stop_reason=None
    with out.open('wb') as log:
        child=subprocess.Popen(cmd,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,creationflags=0x08000000)
        parent=psutil.Process(child.pid);owned[parent.pid]=parent.create_time()
        dump(out.with_suffix('.running.json'),dict(pid=parent.pid,create_time=owned[parent.pid],max_seconds=seconds,max_tree_rss=limit))
        while True:
            live=[]
            for pid,born in list(owned.items()):
                try:
                    p=psutil.Process(pid)
                    if p.create_time()!=born or not p.is_running():continue
                    live.append(p)
                    for d in p.children(recursive=True):owned.setdefault(d.pid,d.create_time())
                except psutil.NoSuchProcess:pass
            rss=0
            for p in live:
                try:rss+=p.memory_info().rss
                except psutil.NoSuchProcess:pass
            peak=max(peak,rss)
            if time.monotonic()-start>seconds or peak>limit:
                stop_reason='timeout' if time.monotonic()-start>seconds else 'tree_memory'
                for pid,born in reversed(list(owned.items())):
                    try:
                        p=psutil.Process(pid)
                        if p.create_time()==born:p.kill()
                    except psutil.NoSuchProcess:pass
                child.wait(timeout=10);break
            if child.poll() is not None and not live:break
            time.sleep(.2)
    result=dict(returncode=child.returncode,stop_reason=stop_reason,seconds=time.monotonic()-start,peak_tree_rss_bytes=peak,owned_pids=owned)
    dump(out.with_suffix('.receipt.json'),result)
    if child.returncode or stop_reason:raise RuntimeError(str(result))
    return result

def main():
    O.mkdir(exist_ok=False)
    assert psutil.__version__=='7.2.2'
    assert Path(psutil.__file__).resolve().is_relative_to(R/'dry-road-build-dependencies-20261028')
    pre_path=R/'prism-b3-binary-preflight-20261028/report.json';pre=json.loads(pre_path.read_bytes())
    assert pre['status']=='FRESH_OFFICIAL_CHECKS_PASS_WITH_ARCHIVED_LITERAL_REPAIR'
    pins=dict(pre['pins']);pins[str(pre_path)]=sha(pre_path)
    # Dependencies are explicit recorded files: never recurse source/DZ junctions.
    historic=json.loads((R/'dry-road-compile-pair-20261028/inputs.json').read_bytes())
    for p,h in historic.items():
        if 'dry-road-build-dependencies-20261028' in p:assert sha(p)==h;pins[p]=h
    sources={'control':R/'dry-road-mlod-candidate-r2-20261028/source/baltic_stream_pilot/cs_kit_118_0000.p3d','candidate':R/'prism-contact-b3-candidate-20261028/candidate.p3d'}
    assert sha(sources['control'])=='d13069d5ec2816cdacc90891a83e5f92f517c4c33703380d534d3f7538baddef'
    assert sha(sources['candidate'])=='c769dd9a0631156075ec61586dc8f5a1471964899e21bdf34e8d13adad8233ad'
    old_contract=R/'prism-contact-b3-execution-20261028/contract-r1.json';assert sha(old_contract)=='447d4a767183bdf95064387a7e0ef45d14a5e040aba6941c5584428e0829ff48'
    context=json.loads(old_contract.read_bytes())
    baseline=R/'dry-road-compile-pair-20261028/candidate/saved-odol.p3d';pbo=R/'dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo'
    assert sha(baseline)=='351424ab535a3e3eb40fc460a22360ab442776446055b116e10c0ba6134579f5' and sha(pbo)=='ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84'
    poses=R/'deployed-surface-prototypes-20261028/instances.npz';assert sha(poses)=='6c0ae3b5b9dc9bbcbb9333bd8c6877ac0ed914a3508ea543d0af5f01829f6e37'
    reader=Path('C:/temp/moto_lanes/review_g3/tools')
    paths=[*sources.values(),old_contract,baseline,pbo,poses,Path(context['original_result']),R/'prism-contact-b3-consumer-20261028/report.json',Path(__file__),W/'plans/ev112-prism-contact-b3-binary-20261028.md']
    paths += [W/'tools/quality'/x for x in ('prism_b3_binary_ev112.py','test_prism_b3_binary_ev112.py','compiled_dry_road_gate_ev112.py','deployed_surface_inventory_ev112.py','verify_prism_contact_b3_ev112.py','water_constraint_diagnostic_ev112.py')]
    paths += [W/'tools/water'/x for x in ('pack_continuous_stream_pilot_v31.ps1','continuous_stream_pilot_v31.py','review_compact_collision_v31.py','compare_non_geometry_lods_v31.py','mesh_quality_v31.py','collision_contact_union_v31.py')]
    paths += [W/'tools/playtest/attach_navmesh.py']+[reader/x for x in gate.old.READER_HASHES]
    # All py3d sources are the explicitly frozen list from the B3 contract.
    paths += [Path(p) for p in context['pins'] if '/py3d/' in p.replace('\\','/')]
    for p in paths:pins[str(p)]=sha(p)
    for p,h in pins.items():assert sha(p)==h,p
    npz=np.load(poses);ix=np.flatnonzero(npz['ids']==19394363);assert len(ix)==1
    c=dict(offline_contract=str(old_contract),source_control=str(sources['control']),candidate_mlod=str(sources['candidate']),candidate_sha256=sha(sources['candidate']),baseline_odol=str(baseline),baseline_pbo=str(pbo),poses=str(poses),original_result=context['original_result'],offline_proof=str(R/'prism-contact-b3-consumer-20261028/report.json'),targets=context['targets'],origin=context['origin'],matrix=npz['matrix'][ix[0]].tolist(),selected_components=context['selected_components'],pins=pins)
    contract=O/'contract.json';dump(contract,c)
    ODOL=gate.old.read_backend(reader);historical=ODOL.from_file(str(baseline),strict=True)
    config=model_config([dict(model='baltic_stream_pilot\\'+gate.NAME)]);results=[]
    for side,source in sources.items():
        directory=O/side;folder=directory/'source/baltic_stream_pilot';folder.mkdir(parents=True)
        (folder/gate.NAME).write_bytes(source.read_bytes());(folder/'config.cpp').write_text(config,encoding='ascii');(folder/'$PBOPREFIX$').write_text('baltic_stream_pilot',encoding='ascii')
        receipt=execute(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/water/pack_continuous_stream_pilot_v31.ps1'),'-Pilot',str(directory)],W,directory/'driver.log',150)
        _,props,entries=read_pbo(directory/'packed/baltic_stream_pilot.pbo');assert props['prefix']=='baltic_stream_pilot' and set(entries)=={gate.NAME,'config.bin'}
        odol=directory/'saved-odol.p3d';odol.write_bytes(entries[gate.NAME]);assert entries[gate.NAME].startswith(b'ODOL')
        if side=='control':
            fresh=ODOL.from_file(str(odol),strict=True);gate.control_identity(historical,fresh)
            _,control_mlods,_=gate.load(source)
            control=gate.control_surface(control_mlods[1],fresh.lods[1],c['origin'],c['matrix'],gate.old.xyz([fresh.model_info.bounding_center])[0],c['targets'])
            dump(directory/'surface-control.json',control)
        receipt.update(odol_sha256=sha(odol),pbo_sha256=sha(directory/'packed/baltic_stream_pilot.pbo'),config_sha256=hashlib.sha256(entries['config.bin']).hexdigest());dump(directory/'receipt.json',receipt);results.append(receipt)
        for p,h in pins.items():assert sha(p)==h,p
    assert results[0]['config_sha256']==results[1]['config_sha256']
    dump(O/'report.json',dict(status='PAIR_READY_FOR_CONSUMER',results=results,contract_sha256=sha(contract)))
    out=R/'prism-b3-binary-consumer-20261028'
    cp=subprocess.run([PY,'-I',str(W/'tools/quality/prism_b3_binary_ev112.py'),str(R),str(contract),str(O),str(reader),str(out)],cwd=W,capture_output=True,timeout=195,creationflags=0x08000000)
    (O/'consumer.stdout.log').write_bytes(cp.stdout);(O/'consumer.stderr.log').write_bytes(cp.stderr)
    completion=dict(consumer_returncode=cp.returncode,inputs_unchanged=all(sha(p)==h for p,h in pins.items()));dump(O/'completion.json',completion)
    if cp.returncode:print(json.dumps(completion));return
    proof=json.loads((out/'report.json').read_bytes());assert proof['status']=='COMPILED_B3_CONDITIONAL' and proof['contract_sha256']==sha(contract)
    package=R/'prism-b3-binary-package-20261028';package.mkdir(exist_ok=False);dst=package/'Addons';dst.mkdir();folder=package/'compiled/baltic_stream_pilot';folder.mkdir(parents=True)
    _,props,before=read_pbo(pbo);after=before.copy();payload=(O/'candidate/saved-odol.p3d').read_bytes();assert hashlib.sha256(payload).hexdigest()==proof['candidate_odol_sha256'];after[gate.NAME]=payload
    gate.old.package_identity(props,before,props,after,payload)
    for name,data in after.items():
        assert Path(name).name==name and '/' not in name and '\\' not in name
        (folder/name).write_bytes(data)
    filebank=Path(pre['tools_root'])/'Bin/PboUtils/FileBank.exe';args=[str(filebank)]
    for k,v in props.items():args+=['-property',k+'='+v]
    execute(args+['-dst',str(dst),str(folder)],W,package/'filebank.log',120)
    packed=dst/'baltic_stream_pilot.pbo';_,actual_props,actual=read_pbo(packed)
    identity=gate.old.package_identity(props,before,actual_props,actual,payload)
    for p,h in pins.items():assert sha(p)==h,p
    dump(package/'report.json',dict(status='EXPERIMENTAL_B3_PACKAGE_CONDITIONAL',identity=identity,pbo_sha256=sha(packed),candidate_odol_sha256=proof['candidate_odol_sha256'],proof_sha256=sha(out/'report.json'),inputs=pins,no_deployment=True))
    print(json.dumps(dict(status='EXPERIMENTAL_B3_PACKAGE_CONDITIONAL',pbo_sha256=sha(packed))))

try:main()
except Exception as e:
    if O.exists():dump(O/'failure.json',dict(status='INCONCLUSIVE_BINARY_EXECUTION',type=type(e).__name__,reason=str(e),details=getattr(e,'details',None)))
    raise
