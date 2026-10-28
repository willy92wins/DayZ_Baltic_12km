"""Compose and independently consume the one approved ODOL replacement in 201 models."""
import time
START=time.monotonic()
from pathlib import Path
import argparse,hashlib,json,struct,sys,traceback
HERE=Path(__file__).resolve().parent;W=HERE.parent.parent;sys.path.insert(0,str(HERE))
import build_prism_b3e2_ev112 as runtime
import preflight_b3f_ev112 as flight
from compiled_dry_road_gate_ev112 import package_identity
gate=runtime.gate;R=runtime.R;meter=gate.meter;sha=meter.sha;dump=meter.dump
NAME='cs_kit_118_0000.p3d';PAIR=R/'prism-b3e2-pair-20261028'
BASE=R/'dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo';BASE_SHA='ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84'
CANDIDATE=PAIR/'candidate/saved-odol.p3d';CANDIDATE_SHA='2581a99ff60f5a6242af55483cce6dd1aa3556cbc36e8a2f1c1488fa08c93545';CONTROL_SHA='351424ab535a3e3eb40fc460a22360ab442776446055b116e10c0ba6134579f5';CONFIG_SHA='57d0d0ae31a33fa329598ce2c17df43fbb8451fd3acc0844467b87fec3a239ca'
ANCHORS={BASE:BASE_SHA,CANDIDATE:CANDIDATE_SHA,PAIR/'contract.json':'c3709a1929214e1372fb2026b8d84c8ae83466aa83e033da968fa196a598f8e4',PAIR/'candidate-gate/report.json':'9a541c82274a9cad75c337d734db2d3ab62120a5e8694c3502fc09f9dd841884',PAIR/'control-gate/census.json':'a895ab0375d1c5838c37775e296d393c2f46807481af61f0a91d8b9705c5deea',PAIR/'candidate-gate/census.json':'1ad63bfc09f0a1ff537225028911ceacae45954a8655ffadef17d9b7c8c2467e',W/'evidence/prism-b3e2-compiled-20261028/report.json':'f850319aaae07f415af179235efe9fd52c3c1d879a3546925b938cb85dce3c06'}
HELPERS={**runtime.HELPERS,HERE/'build_prism_b3e2_ev112.py':'b131794d75a2748f40dfdd87e5e01389cf6434ca2f9b160253f70f241f538cbb',HERE/'preflight_b3e2_ev112.py':'7b9f2a7191099f7cbc6570954ef1810fbaf890904f291601625d961574a1c447',HERE/'compiled_dry_road_gate_ev112.py':'00a68cabe86628ae9e659bfb6b6779f6efa2ab1fdb184b7731f8e493c7831c6c'}

class Rejected(Exception):pass
class Inconclusive(Exception):pass
def require(ok,reason):
    if not ok:raise Rejected(reason)
def bind(ok,reason):
    if not ok:raise Inconclusive(reason)
digest=lambda data:hashlib.sha256(data).hexdigest()
def pins_check(pins):
    for p,h in pins.items():bind(sha(p)==h,'pin_changed:'+str(p))

def header(data):
    """Independent ordered header guard before the shared body reader collapses dicts."""
    offset=0;props=[];names=[];sizes=[];seen_props=set();seen_names=set();extensions=0
    def string():
        nonlocal offset
        end=data.index(b'\0',offset);s=data[offset:end].decode('utf-8');offset=end+1;return s
    while True:
        name=string();mime,original,reserved,stamp,size=struct.unpack_from('<5I',data,offset);offset+=20
        if not name:
            if mime==0x56657273:
                extensions+=1;require(extensions==1 and not names,'property_header_position')
                while True:
                    k=string()
                    if not k:break
                    v=string();require(k not in seen_props,'duplicate_property');seen_props.add(k);props.append((k,v))
                continue
            require(mime==0 and original==0 and reserved==0 and stamp==0 and size==0,'terminator');break
        require(mime==0,'compressed_entry');name=name.replace('\\','/')
        require(not name.startswith('/') and ':' not in name and all(s not in ('','.','..') for s in name.split('/')),'unsafe_name')
        require(name.lower() not in seen_names,'duplicate_entry');seen_names.add(name.lower());names.append(name);sizes.append(size)
    require(extensions==1 and offset+sum(sizes)<=len(data),'truncated_or_missing_header')
    rest=len(data)-(offset+sum(sizes));require(rest in (0,21),'trailer_length')
    if rest:require(data[-21]==0 and hashlib.sha1(data[:-21]).digest()==data[-20:],'trailer_checksum')
    return props,names,sizes

def read_package(path):
    data=path.read_bytes();props,names,sizes=header(data)
    raw,decoded,entries=gate.old.read_pbo(path)
    bind(raw==data and decoded==dict(props) and list(entries)==names and [len(v) for v in entries.values()]==sizes,'reader_disagreement')
    return props,entries

def compare(before_props,before,after_props,after,candidate):
    require(before_props==after_props,'property_sequence')
    try:identity=package_identity(dict(before_props),before,dict(after_props),after,candidate)
    except ValueError as e:raise Rejected(str(e)) from e
    return identity

def census_check(row):
    bind(row['status']=='EXACT_CENSUS' and row['compared_components']==row['visited_components']==row['expected_components']==row['observed_components']==1520 and not row['global_errors'] and not row['geometric_failures'] and row['structural_failures']==0,'census_incomplete')

def output_universe(folder):
    require(sorted(p.name for p in folder.iterdir())==['baltic_stream_pilot.pbo'],'output_universe')
    require((folder/'baltic_stream_pilot.pbo').is_file() and not (folder/'baltic_stream_pilot.pbo').is_symlink(),'output_not_regular')

def consumer_identity(report,receipt,image,image_sha):
    rows=[v for k,v in receipt['observed_processes'].items() if k.startswith(str(report['measurement']['pid'])+'@')]
    bind(len(rows)==1 and rows[0]['executable'] is not None and Path(rows[0]['executable']).resolve()==Path(image).resolve() and rows[0]['sha256']==image_sha,'consumer_identity')

def context():
    pins={str(p):h for p,h in {**ANCHORS,**HELPERS}.items()};pins_check(pins)
    j=lambda p:json.loads(p.read_bytes())
    old,_=gate.context(PAIR/'contract.json');pins.update(old['pins']);pins_check(pins)
    proof=j(PAIR/'candidate-gate/report.json');summary=j(W/'evidence/prism-b3e2-compiled-20261028/report.json')
    bind(proof['status']==summary['status']=='COMPILED_B3E_CONDITIONAL','proof_status')
    bind(proof['contract_sha256']==summary['contract_sha256']==ANCHORS[PAIR/'contract.json'] and summary['proof_sha256']==ANCHORS[PAIR/'candidate-gate/report.json'] and summary['candidate_odol_sha256']==CANDIDATE_SHA and summary['control_odol_sha256']==CONTROL_SHA,'proof_links')
    bind(proof['outputs'].get(str(CANDIDATE))==CANDIDATE_SHA,'proof_output')
    for side in ('control','candidate'):
        path=PAIR/(side+'-gate/census.json');row=j(path)
        census_check(row)
    bind(proof['census_sha256']==ANCHORS[PAIR/'candidate-gate/census.json'],'census_proof')
    props,entries=read_package(BASE)
    bind(digest(entries[NAME])==CONTROL_SHA and digest(entries['config.bin'])==CONFIG_SHA,'baseline_control_config')
    candidate=CANDIDATE.read_bytes();bind(digest(candidate)==CANDIDATE_SHA,'candidate_bytes')
    expected=entries.copy();expected[NAME]=candidate;compare(props,entries,props,expected,candidate)
    return pins,props,entries,candidate

def source_check(folder,expected):
    paths=[p for p in folder.rglob('*')]
    require(all(not p.is_symlink() and not p.is_junction() for p in paths),'source_link')
    actual={p.relative_to(folder).as_posix():p.read_bytes() for p in paths if p.is_file()}
    require(list(sorted(actual))==list(sorted(expected)) and actual==expected,'source_bytes')

def approval(path,output):
    a=json.loads(path.read_bytes());bind(a['schema']=='B3F_EXECUTION_V1' and a['status']=='REVIEW_ADJUDICATED_TESTS_PASS' and Path(a['output']).resolve()==output.resolve(),'approval')
    required=[Path(__file__).resolve(),HERE/'preflight_b3f_ev112.py',HERE/'test_prism_b3f_ev112.py',W/'plans/ev112-b3f-package-composition-20261028.md']
    bind(all(str(p) in a['pins'] for p in required),'approval_sources');pins_check(a['pins']);pins_check({str(p):h for p,h in HELPERS.items()})
    bind(a['review_adjudication'] in a['pins'] and a['tests'] in a['pins'],'approval_receipts');suite=json.loads(Path(a['tests']).read_bytes())
    bind(suite['status']=='TESTS_PASS' and suite['tests']>0 and suite['seconds']<=120 and all(suite['postimages'].get(str(p))==a['pins'][str(p)] for p in required[:-1]),'suite')
    return a

def consume(execution,output):
    pins,props,before,candidate=context();manifest=json.loads((execution/'manifest.json').read_bytes());pins_check(manifest['pins'])
    bind(manifest['schema']=='B3F_COMPOSITION_V1' and all(manifest['pins'].get(p)==h for p,h in pins.items()),'manifest_transitive')
    output_universe(execution/'Addons')
    expected=before.copy();expected[NAME]=candidate;source_check(execution/'compiled/baltic_stream_pilot',expected)
    actual_props,after=read_package(execution/'Addons/baltic_stream_pilot.pbo');identity=compare(props,before,actual_props,after,candidate)
    bind(manifest['preflight'] in manifest['pins'],'preflight_unpinned')
    pre=json.loads(Path(manifest['preflight']).read_bytes());bind(pre['status']=='FRESH_B3F_PREFLIGHT','preflight_status');bind(flight.inventory(flight.FILEBANK.parent)==pre['pboutils'],'tool_inventory_changed');pins_check(manifest['pins'])
    return dict(status='EXPERIMENTAL_B3F_PACKAGE_IDENTITY_PASS_CONDITIONAL',identity=identity,properties=actual_props,pbo_sha256=sha(execution/'Addons/baltic_stream_pilot.pbo'),candidate_sha256=digest(after[NAME]),baseline_sha256=BASE_SHA,config201_sha256=digest(after['config.bin']),manifest_sha256=sha(execution/'manifest.json'),compiled_proof_sha256=ANCHORS[PAIR/'candidate-gate/report.json'],entries={n:digest(v) for n,v in after.items()},measurement=meter.memory(),limits=['No DayZ, deployment, native contact or global acceptance.','Shared read_pbo for bodies; independent header and synthetic writer do not constitute a second full parser.','Installed tool directory identity is not loaded DLL attestation.'])

def execute(approval_path,output):
    a=approval(approval_path,output);output.mkdir(exist_ok=False);phase='preflight';emit=runtime.reads.Events(output/'events.jsonl');started=time.monotonic()
    try:
        image=runtime.reads.interpreter_image();image_sha=sha(image)
        emit(phase);runtime.run_process([str(image),'-I','-S',str(HERE/'preflight_b3f_ev112.py'),str(output/'preflight')],output/'preflight-driver.log',60)
        pre_path=output/'preflight/report.json';pre=json.loads(pre_path.read_bytes());identity=json.loads((output/'preflight-driver.running.json').read_bytes());bind(pre['status']=='FRESH_B3F_PREFLIGHT' and pre['measurement']['pid']==identity['pid'],'preflight_identity')
        approval(approval_path,output);pins,props,before,candidate=context();pins.update(a['pins']);pins.update(pre['pins']);pins[str(pre_path)]=sha(pre_path);pins[str(approval_path)]=sha(approval_path);pins[str(image)]=image_sha
        pins_check(pins);expected=before.copy();expected[NAME]=candidate;folder=output/'compiled/baltic_stream_pilot';folder.mkdir(parents=True);dest=output/'Addons';dest.mkdir()
        for name,data in expected.items():p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        source_check(folder,expected);bind(flight.inventory(flight.FILEBANK.parent)==pre['pboutils'],'tools_before_pack')
        manifest=output/'manifest.json';dump(manifest,dict(schema='B3F_COMPOSITION_V1',pins=pins,preflight=str(pre_path),runtime_image=str(image)));manifest_sha=sha(manifest)
        bind(time.monotonic()-started<=60,'preparation_deadline');measured=meter.memory();bind(max(measured['peak_resident_bytes'],measured['peak_commit_bytes'])<=2*1024**3,'preparation_memory')
        args=[str(flight.FILEBANK)]
        for key,value in props:args+=['-property',key+'='+value]
        phase='pack';emit(phase);receipt=runtime.run_process(args+['-dst',str(dest),str(folder)],output/'pack.log',120)
        source_check(folder,expected);pins_check(pins);bind(sha(manifest)==manifest_sha,'manifest_changed');bind(flight.inventory(flight.FILEBANK.parent)==pre['pboutils'],'tools_after_pack')
        phase='consumer';emit(phase);child_receipt=runtime.run_process([sys.executable,'-I',str(Path(__file__).resolve()),'consume',str(output),str(output/'consumer')],output/'consumer.log',120)
        result=json.loads((output/'consumer/report.json').read_bytes());consumer_identity(result,child_receipt,image,image_sha);bind(result['status']=='EXPERIMENTAL_B3F_PACKAGE_IDENTITY_PASS_CONDITIONAL' and result['manifest_sha256']==manifest_sha,'consumer_status');pins_check(pins)
        dump(output/'completion.json',dict(status=result['status'],pbo_sha256=result['pbo_sha256'],proof_sha256=sha(output/'consumer/report.json'),manifest_sha256=manifest_sha,pack=receipt,no_deployment_or_dayz=True))
    except Exception as e:runtime.linked_failure(output,e,phase);raise

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['execute','consume']);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    if a.mode=='execute':execute(a.input,a.output);return 0
    a.output.mkdir(exist_ok=False);meter.STARTED=START;meter.MAX_SECONDS=120;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
    try:dump(a.output/'report.json',consume(a.input,a.output));return 0
    except Exception as e:
        status='REJECTED_PACKAGE' if isinstance(e,Rejected) else 'INCONCLUSIVE_PACKAGE';dump(a.output/'report.json',dict(status=status,type=type(e).__name__,reason=str(e),traceback=traceback.format_exc()));return 1 if status=='REJECTED_PACKAGE' else 2
    finally:stop.set()

if __name__=='__main__':raise SystemExit(main())
