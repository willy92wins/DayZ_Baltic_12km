from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
ref=json.loads((R/'kit7-navv9diag-ram-ab-20261027/pass-06/reference.json').read_text())
p,h=next((Path(p),h) for p,h in ref['packages'].items() if Path(p).name=='worlds_chernarusplus.pbo')
raw,props,entries=read_pbo(p);assert hashlib.sha256(raw).hexdigest()==h
O=R/'chernarus-current-config-20261027'
assert not O.exists() or not any(O.iterdir()),'Only an empty own extraction directory may resume'
O.mkdir(exist_ok=True)
configs=[n for n in entries if n.lower().endswith('config.bin')]
assert configs==['config.bin'],configs
rawconfig=entries[configs[0]];assert rawconfig.startswith(b'\0raP')
(O/'config.bin').write_bytes(rawconfig)
converter=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe')
q=subprocess.run([str(converter),'-txt','-dst',str(O/'config.cpp'),str(O/'config.bin')],capture_output=True,creationflags=0x08000000)
(O/'converter.stdout.log').write_bytes(q.stdout);(O/'converter.stderr.log').write_bytes(q.stderr)
assert q.returncode==0 and (O/'config.cpp').stat().st_size>1000
report=dict(status='CURRENT_MEASURED_WORLD_CONFIG_EXTRACTED_READ_ONLY',package=str(p),package_sha256=h,config_entry=configs[0],config_bin_sha256=hashlib.sha256(rawconfig).hexdigest(),config_cpp_sha256=hashlib.sha256((O/'config.cpp').read_bytes()).hexdigest(),converter_sha256=hashlib.sha256(converter.read_bytes()).hexdigest(),wrp_entries={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),prefix=b[:8].hex()) for n,b in entries.items() if n.lower().endswith('.wrp')},limits=['Extraction only; no generated map, changed parameters or runtime acceptance.'])
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
