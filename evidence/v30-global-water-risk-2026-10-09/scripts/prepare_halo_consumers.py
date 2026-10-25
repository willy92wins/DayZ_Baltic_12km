from pathlib import Path
import json,hashlib,shutil,sys,subprocess,csv
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');V=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'));from v30_common import tri_sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=json.loads((V/'c1r3p-probe-reference.json').read_text());points=ref['points'];assert len(points)==28
src=V/'missions/BalticC1R3PWaterProbeV1.BalticTrial'
old=json.loads((E/'native-anomaly-classification.json').read_text())['points']
micros=[p for p in old if p['reason']=='runtime_water_missing_below_frozen_plane']
dry=[p for p in csv.DictReader((E/'halo-physical-anomalies.csv').open()) if p['cls']=='0']
for kind,rows in [('closed_microgap',micros),('remaining_dry',dry)]:
    for p in rows:
        for offset,dx,dz in [('exact',0,0),('east',.02,0),('west',-.02,0),('north',0,.02),('south',0,-.02)]:
            points.append(dict(id=6000+len(points),x=float(p['x'])+dx,z=float(p['z'])+dz,role='frozen_shallow_failure' if kind=='closed_microgap' else 'diagnostic_remaining_dry',reach='GLOBAL',case=kind,offset=offset))
for p in json.loads((E/'native-fullwater-reference.json').read_text())['points']:
    points.append(dict(id=6000+len(points),x=p['x'],z=p['z'],reach='GLOBAL',role='dry_bank' if p['cls']==0 else 'high_pond_control',case='calibrated_image',offset='exact'))
h=np.load('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')['heights']
ys=tri_sample(h,np.array([p['x'] for p in points]),np.array([p['z'] for p in points]))
for p,y in zip(points,ys):
    if 'expected_ground_m' in p:assert abs(p['expected_ground_m']-y)<1e-5
    p['expected_ground_m']=float(y)
name='BalticHaloConsumersV1.BalticTrial';dest=B/'missions'/name;dest.mkdir(parents=True,exist_ok=False)
code=(src/'init.c').read_text().replace('c1r3p_probe_v1.log','halo_consumers_v1.log').replace('c1r3p_order_v1.log','halo_consumers_order_v1.log')
assert 'm_Rows.Count() == 28' in code
code=code.replace('m_Rows.Count() == 28',f'm_Rows.Count() == {len(points)}').replace('END;62;28',f'END;62;{len(points)}')
(dest/'init.c').write_text(code);(dest/'points.csv').write_text(''.join(f'{p["id"]};{p["x"]:.9f} 0 {p["z"]:.9f}\n' for p in points))
deploy=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name;shutil.copytree(dest,deploy)
ref['files']={p.name:sha(p) for p in dest.iterdir()};assert all(sha(deploy/n)==v for n,v in ref['files'].items())
ref['deployed']={str(p):sha(p) for p in Path('P:/Mods/@DayZ_Baltic_HaloFixV1/Addons').glob('*.pbo')}
ref['original_points']=28;ref['microgap_points']=25;ref['diagnostic_dry_points']=60;ref['calibrated_points']=7
(E/'halo-consumers-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
verify=(V/'verify_c1r3p_probe.py').read_text().replace("E=W/'evidence/v30-valley-smoothing-2026-10-08'","E=W/'evidence/v30-global-water-risk-2026-10-09'")
verify=verify.replace('c1r3p-probe-reference.json','halo-consumers-reference.json').replace('c1r3p_probe_v1.log','halo_consumers_v1.log').replace('c1r3p_order_v1.log','halo_consumers_order_v1.log')
verify=verify.replace('c1r3p-runtime','halo-consumers-runtime').replace('c1r3p-order','halo-consumers-order').replace('PASS_C1R3P_WATER_READBACK','PASS_HALO_CONSUMERS_READBACK')
verify=verify.replace('28 frozen points, calm/storm sample windows; no maximum wave envelope.','28 historical controls plus 25 microgap neighbourhood points, 60 diagnostic remaining dry points and 7 calibrated points. No maximum wave envelope.')
(B/'verify_halo_consumers.py').write_text(verify)
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(dest)],capture_output=True,text=True)
got=json.loads(lint.stdout);assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==1
(E/'halo-consumers-lint.json').write_text(lint.stdout)
print(json.dumps(dict(mission=str(deploy),points=len(points),lint='PASS',pbo=ref['deployed'])))
