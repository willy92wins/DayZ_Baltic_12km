"""Preserve the junction R2 source world; replace only its height samples."""
from pathlib import Path
import hashlib,json,shutil,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];EV=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/terrain'))
import wrp0wzd
B=Path('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008')
SOURCE=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/world/root/dayz_baltic_12km_dev/tb/narva_trial')
DEST=B/'world/root/dayz_baltic_12km_dev/tb/narva_trial'
assert json.loads((EV/'verification.json').read_text())['status']=='PASS_OFFLINE_NAVIGATION_CONTRACT'
old=wrp0wzd.read(SOURCE/'baltic_trial.wrp')
assert hashlib.sha256((SOURCE/'baltic_trial.wrp').read_bytes()).hexdigest()=='d508356b0c4b191ad4d8e91ce2f0d8e72484c374c7cbb2000a0b37075e4ee92b'
h=np.load(B/'terrain_floor.npz')['heights'][::-1,:]
assert np.count_nonzero(h!=old['heights'])==2
shutil.copytree(SOURCE,DEST,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
wrp0wzd.write(DEST/'baltic_trial.wrp',old['header'],h,old['materials'],[o['bytes'] for o in old['objects']],old['terminator'])
back=wrp0wzd.read(DEST/'baltic_trial.wrp')
assert np.array_equal(back['heights'],h) and back['materials']==old['materials'] and back['header']==old['header']
assert [o['bytes'] for o in back['objects']]==[o['bytes'] for o in old['objects']] and back['terminator']==old['terminator']
report=dict(status='STAGED_TWO_HEIGHTS_ONLY',wrp_sha256=hashlib.sha256((DEST/'baltic_trial.wrp').read_bytes()).hexdigest(),
            unchanged_objects=len(back['objects']),source=str(SOURCE),destination=str(DEST),changed_heights=2)
(EV/'world-source.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=1))
