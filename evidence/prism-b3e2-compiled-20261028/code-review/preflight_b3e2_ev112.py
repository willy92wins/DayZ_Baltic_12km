"""Fresh official checks in an isolated stdlib child, with durable phase markers."""
import time
START=time.monotonic()
from pathlib import Path
import argparse,contextlib,importlib.util,json,os,sys,traceback
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import preflight_read_discovery_ev112 as reads
import water_constraint_diagnostic_ev112 as meter
R=reads.ROOT
ORIGINAL='9f8786a5f37b6b2abbd206bce51d4cad44d58536e766b97fd93bae692804c9a7'
ARCHIVED='5fb698727b6c70e8dfa21267963b54cafa60b1ade8b4df3ebfe6b8124e5fc7f2'

def pinned_json(path,expected):
    raw=path.read_bytes();reads.require(__import__('hashlib').sha256(raw).hexdigest()==expected,'receipt_hash:'+str(path));return json.loads(raw)

def run(output):
    emit=reads.Events(output/'events.jsonl');pins={};emit('external_receipts')
    old=pinned_json(reads.RECEIPTS[0][1],reads.RECEIPTS[0][2]);prior=pinned_json(reads.RECEIPTS[1][1],reads.RECEIPTS[1][2])
    for _,p,h in reads.RECEIPTS:pins[str(p)]=h
    src,fixed=reads.SOURCES
    for p,h in [(src,ORIGINAL),(fixed,ARCHIVED)]:
        reads.require(meter.sha(p)==h,'source_hash:'+str(p));pins[str(p)]=h
    a=src.read_text();b=fixed.read_text();reads.require(b.replace("        r'subst P:","        'subst P:")==a,'literal_diff')
    try:compile(a,str(src),'exec');syntax='original_compiles'
    except SyntaxError as e:syntax=f'{type(e).__name__}:line{e.lineno}:{e.msg}'
    emit('import_official');spec=importlib.util.spec_from_file_location('b3e2_official',fixed);pf=importlib.util.module_from_spec(spec);spec.loader.exec_module(pf)
    with (output/'official-checks.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        emit('check_p_drive');reads.require(pf.check_p_drive(),'p_drive');log.flush();os.fsync(log.fileno())
        for name in ('check_dayz_tools','check_dayz_diag','check_vanilla_data','check_workshop_deploy'):
            emit(name);getattr(pf,name)();log.flush();os.fsync(log.fileno())
        emit('validate_p_mods');reads.require(pf.validate_p_mods() is None,'mods_junction')
        emit('find_tools');tools=pf.find_dayz_tools();reads.require(str(tools)==old['tools_root'],'tools_root')
    for p in ('P:/DZ','P:/bin','P:/core','P:/scripts'):
        emit('dependency',path=p);reads.require(Path(p).is_dir(),'dependency:'+p)
    expected=dict(old['tools_sha256'])
    for p in [tools/'Bin/Binarize/Binarize.exe',Path('P:/bin/config.cpp')]:
        key=str(p);reads.require(key in prior['pins'],'missing_prior_pin:'+key);h=prior['pins'][key]
        reads.require(key not in expected or expected[key]==h,'pin_conflict:'+key);expected[key]=h
    for p,h in expected.items():
        emit('tool_hash',path=p);row,_=reads.read_hash(Path(p),p,emit);reads.require(row['sha256']==h,'tool_changed:'+p);pins[p]=h
    emit('recheck_inputs')
    for p,h in pins.items():reads.require(meter.sha(p)==h,'changed_during_preflight:'+p)
    measured=meter.memory();reads.require(measured['seconds']<=60 and max(measured['peak_resident_bytes'],measured['peak_commit_bytes'])<=2*1024**3,'resource_budget')
    return dict(status='FRESH_PREFLIGHT_B3E2',tools_root=str(tools),pins=pins,original_parse=syntax,native_environment_certified=False,installed_skill_modified=False,measurement=measured)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=60;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
    try:r=run(a.output);reads.dump(a.output/'report.json',r);return 0
    except Exception as e:reads.dump(a.output/'report.json',dict(status='INCONCLUSIVE_PREFLIGHT',type=type(e).__name__,reason=str(e),traceback=traceback.format_exc()));return 2
    finally:stop.set()

if __name__=='__main__':raise SystemExit(main())
