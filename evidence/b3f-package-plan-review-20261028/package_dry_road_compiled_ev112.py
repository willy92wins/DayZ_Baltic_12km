"""Compose an isolated 201-model experimental PBO after the frozen compiled gate."""
from pathlib import Path
import argparse,json,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import compiled_dry_road_gate_ev112 as gate

FILEBANK=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
FILEBANK_SHA='f89aaeb22421b9158fbbf173f75d52b6f3de69986cb462e58956c78da82c4caf'

def compose(root,proof_path,output):
    proof=json.loads(proof_path.read_bytes())
    gate.require(proof['status']=='COMPILED_GEOMETRY_GATE_PASS_METADATA_CONDITIONAL','gate_not_complete')
    gate.require(proof['candidate_odol_sha256']==gate.CANDIDATE_SHA,'wrong_gate_candidate')
    pins=proof['inputs'].copy();gate.require(pins.get(str(Path(gate.__file__).resolve()))==gate.sha(gate.__file__),'gate_code_changed')
    pins.update({str(proof_path):gate.sha(proof_path),str(FILEBANK):FILEBANK_SHA,str(Path(__file__)):gate.sha(__file__)})
    for p,d in pins.items():gate.require(gate.sha(p)==d,'input_changed:'+p)
    baseline=root/'package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo'
    candidate=root/'dry-road-compile-pair-20261028/candidate/saved-odol.p3d'
    gate.require(gate.sha(candidate)==gate.CANDIDATE_SHA and gate.sha(baseline)==gate.ANCHORS[str(baseline.relative_to(root)).replace('\\','/')],'package_anchor')
    _,props,before=gate.read_pbo(baseline);expected=before.copy();expected[gate.NAME]=candidate.read_bytes()
    gate.package_identity(props,before,props,expected,candidate.read_bytes())
    source=output/'compiled/baltic_stream_pilot';source.mkdir(parents=True);dest=output/'Addons';dest.mkdir()
    for name,data in expected.items():
        p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    args=[str(FILEBANK)]
    for key,value in props.items():args+=['-property',key+'='+value]
    started=time.monotonic()
    proc=subprocess.run(args+['-dst',str(dest),str(source)],capture_output=True,timeout=120,creationflags=0x08000000)
    (output/'filebank.log').write_bytes(proc.stdout+proc.stderr);gate.require(proc.returncode==0,'filebank_failed')
    pbo=dest/'baltic_stream_pilot.pbo';_,actual_props,actual=gate.read_pbo(pbo)
    identity=gate.package_identity(props,before,actual_props,actual,candidate.read_bytes())
    for p,d in pins.items():gate.require(gate.sha(p)==d,'input_changed_during_pack:'+p)
    return dict(status='EXPERIMENTAL_PACKAGE_IDENTITY_PASS_METADATA_CONDITIONAL',pbo_sha256=gate.sha(pbo),baseline_sha256=gate.sha(baseline),compiled_gate_sha256=gate.sha(proof_path),identity=identity,seconds=time.monotonic()-started,inputs=pins,limits=proof['limits']+['No deployment or engine run performed.'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('proof',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    try:
        result=compose(a.root,a.proof,a.output);gate.meter.dump(a.output/'report.json',result);print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
    except Exception as exc:gate.meter.dump(a.output/'failure.json',dict(type=type(exc).__name__,error=str(exc)));raise
