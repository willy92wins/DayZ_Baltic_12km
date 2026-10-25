"""Freeze an explicit current control set without rewriting the old experiment."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OLD = ROOT/'evidence/v30-bug-recheck-2026-10-08'
sys.path[:0] = [str(ROOT/'tools/terrain'), str(ROOT/'tools/playtest')]
from v30_common import tri_sample
from verify_channel_reaches_v30 import retained_pond_surface
from read_water_temporal_v30 import read_series

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
terrain = Path('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')
assert sha(terrain) == 'b363b79dc8b4374a626644da78f110666139d382ee09a38dc7aade46b2e659dc'
ref = copy.deepcopy(json.loads((OLD/'wave-fixed-reference.json').read_text()))
source = ROOT/'missions/BalticBugRecheckWaterV2.BalticTrial'
assert all(sha(source/name)==value for name,value in ref['files'].items())
old = read_series(ref, (OLD/'wave-fixed-runtime.log').read_text(encoding='utf-8-sig'))
assert [p['id'] for p in old['control_gate']['failures']] == [693]
(OUT/'old-controls-recheck.json').write_text(json.dumps(dict(shallow_gate=old['gate'],control_gate=old['control_gate']),indent=2)+'\n')
fit = Path('E:/DayZ-Baltic-Build/v30-v11/24')
manifest = json.loads((fit/'water/pieces.json').read_text())
h = np.load(terrain)['heights'].astype(float)
old_point = next(p for p in ref['points'] if p['id']==693)
plane, hits = retained_pond_surface(fit, manifest, old_point['x'], old_point['z'])
assert plane is not None and tri_sample(h,old_point['x'],old_point['z']) > plane + .5
old_point.update(role='changed_outline_dry_control', current_control_reason='Terrain above retained pond by >0.5 m before this run; historical positive role failed.')
x, z = 5438., 1970.
ground = float(tri_sample(h,x,z))
plane, hits = retained_pond_surface(fit,manifest,x,z)
assert plane is not None and plane > 4.5 and plane-ground > .75
assert 2001 not in {p['id'] for p in ref['points']}
ref['points'].append(dict(id=2001,x=x,z=z,expected_ground_m=ground,role='high_pond_control',
                         pond_plane_m=plane,nominal_depth_m=plane-ground,source_models=hits))
ref['required_control_roles']=['deep_pond','high_pond_control','sea','dry_bank','changed_outline_dry_control']
mission = ROOT/'missions/BalticBugRecheckWaterV3.BalticTrial'
mission.mkdir(exist_ok=False)
code = (source/'init.c').read_text().replace('water_v2.log','water_v3.log').replace('water_order_v2.log','water_order_v3.log')
assert code.count('m_Rows.Count() == 17') == 1 and code.count('END;302;17') == 2
code = code.replace('m_Rows.Count() == 17','m_Rows.Count() == 18').replace('END;302;17','END;302;18')
(mission/'init.c').write_text(code,encoding='utf-8',newline='\n')
(mission/'points.csv').write_text((source/'points.csv').read_text().rstrip()+'\n2001;5438 0 1970\n',encoding='utf-8',newline='\n')
lint = subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],capture_output=True,text=True)
check=json.loads(lint.stdout)
assert lint.returncode==0 and not check['errors'] and check['info']['files_scanned']==1
(OUT/'controls-lint.json').write_text(lint.stdout,encoding='utf-8')
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
shutil.copytree(mission,deployed)
ref.update(status='FROZEN_CURRENT_CONTROLS',mission=str(mission),deployed_mission=str(deployed),
           parent_reference_sha256=sha(OLD/'wave-fixed-reference.json'),files={p.name:sha(p) for p in mission.iterdir()},
           limits=['All 17 original coordinates retained; 693 is explicitly a dry control in this new experiment.',
                   'New high pond control 2001 is selected against actual retained faces before launch.',
                   'Sampled calm/storm conditions do not certify the maximum wave envelope.'])
assert all(sha(deployed/name)==value for name,value in ref['files'].items())
(OUT/'controls-reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(mission=str(deployed),points=len(ref['points']),reference_sha256=sha(OUT/'controls-reference.json'),positive_high_pond=ref['points'][-1]),indent=1))
