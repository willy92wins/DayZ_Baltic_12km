"""Pin loaded reader modules before the unchanged B3E binary consumer."""
from pathlib import Path
import argparse,hashlib,importlib,json,sys,time,traceback
START=time.monotonic();HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from road_asset_catalog_ev112 import READER_PINS
import prism_b3e_compiled_ev112 as gate

def bind_reader(root,pins):
    for name,expected in READER_PINS.items():
        path=root/name
        gate.bind(str(path) in pins and pins[str(path)]==expected and gate.meter.sha(path)==expected,'reader_pin:'+name)
    sys.path.insert(0,str(root));importlib.import_module('odol_reader')
    for name in READER_PINS:
        module=sys.modules.get(Path(name).stem)
        gate.bind(module is not None and Path(module.__file__).resolve()==(root/name).resolve(),'loaded_reader_path:'+name)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['control','candidate']);ap.add_argument('contract',type=Path);ap.add_argument('pair',type=Path);ap.add_argument('reader',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    gate.meter.STARTED=START;gate.meter.MAX_SECONDS=180;gate.meter.MAX_BYTES=2*1024**3;stop=gate.meter.bounded(a.output)
    try:
        c,_=gate.context(a.contract);bind_reader(a.reader,c['pins'])
        r=gate.consume(a.mode,a.contract,a.pair,a.reader,a.output);r['loaded_reader_modules_bound']=True
        gate.meter.dump(a.output/'report.json',r);return 0
    except Exception as e:
        status=gate.failure_status(e);gate.meter.dump(a.output/'report.json',dict(status=status,type=type(e).__name__,reason=str(e),details=getattr(e,'details',None),traceback=traceback.format_exc(),measurement=gate.meter.memory()));return 1 if status=='REJECTED_BINARY' else 2
    finally:stop.set()

if __name__=='__main__':raise SystemExit(main())
