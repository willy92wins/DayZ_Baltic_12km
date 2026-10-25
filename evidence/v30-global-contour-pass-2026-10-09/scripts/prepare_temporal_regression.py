"""Keep all EV13 controls and add the newly observed whole-map diagnostics and seams."""
from pathlib import Path
import csv,json,shutil,subprocess,sys
import numpy as np
import shapely
B=Path(__file__).parent;B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
sys.path.insert(0,str(B13));from discover_native_turns import W,sha
sys.path.insert(0,str(W/'tools/terrain'));from v30_common import tri_sample
E=W/'evidence/v30-global-contour-pass-2026-10-09';E13=W/'evidence/v30-native-turn-optimizer-2026-10-09'
oldref=E13/'native-contour-temporal-reference.json';ref=json.loads(oldref.read_text());src=Path(ref['mission'])
assert all(sha(src/k)==v for k,v in ref['files'].items())
deploy=json.loads((B/'deploy.json').read_text());mods=Path(deploy['destination'])/'Addons'
assert all(sha(mods/name)==digest for name,digest in deploy['files'].items())
terrain=B/'candidate-repaired/terrain.npz';h=np.load(terrain)['heights'];delta=[]
for point in ref['points']:
    delta.append(abs(float(tri_sample(h,point['x'],point['z']))-point['expected_ground_m']))
assert max(delta)<1e-6,max(delta)
queries=list(csv.DictReader((E/'global-contour-unflagged-scalar-queries.csv').open(),delimiter=';'))
missing=list(csv.DictReader((E/'global-contour-physical-anomalies.csv').open()))
known={(round(p['x'],6),round(p['z'],6)) for p in ref['points']};additions=[]


def add(x,z,role,case):
    if (round(x,6),round(z,6)) in known:return
    known.add((round(x,6),round(z,6)))
    additions.append(dict(id=40000+len(additions),x=float(x),z=float(z),role=role,reach='GLOBAL',case=case,expected_ground_m=float(tri_sample(h,x,z))))


for label,rows in (('diagnostic_current_scalar',queries),('diagnostic_missing_presence',missing)):
    for row in rows:add(int(row['col'])*6,12282-int(row['row'])*6,label,'global_contour_inventory')
for row in json.loads((B/'seam-authoring.json').read_text())['rows']:
    point=shapely.from_geojson(row['gap_geometry']).representative_point()
    add(point.x,point.y,'diagnostic_new_seam',row['model'])
count_before=len(ref['points']);assert not ({p['id'] for p in additions}&{p['id'] for p in ref['points']})
ref['points'].extend(additions)
name='BalticGlobalContourTemporalV1.BalticTrial';mission=B/'missions'/name;mission.mkdir(parents=True,exist_ok=False)
code=(src/'init.c').read_text().replace('native_contour_temporal_v1','global_contour_temporal_v1').replace('native_contour_temporal_order_v1','global_contour_temporal_order_v1')
assert f'm_Rows.Count() == {count_before}' in code and f'END;62;{count_before}' in code
code=code.replace(f'm_Rows.Count() == {count_before}',f"m_Rows.Count() == {len(ref['points'])}").replace(f'END;62;{count_before}',f"END;62;{len(ref['points'])}")
(mission/'init.c').write_text(code)
(mission/'points.csv').write_text(''.join(f'{p["id"]};{p["x"]:.9f} 0 {p["z"]:.9f}\n' for p in ref['points']))
validator='C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py'
lint=subprocess.run([sys.executable,validator,str(mission)],capture_output=True,text=True);got=json.loads(lint.stdout)
assert lint.returncode==0 and got['info']['files_scanned']==1 and not got['errors'];(B/'native-temporal-lint.json').write_text(lint.stdout)
destination=src.parent/name;shutil.copytree(mission,destination)
ref.update(mission=str(destination),files={p.name:sha(p) for p in mission.iterdir()},terrain_sha256=sha(terrain),pbo=deploy['files'],
           deployed={str(mods/name):digest for name,digest in deploy['files'].items()},source_reference_sha256=sha(oldref))
(E/'global-contour-temporal-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
assert all(sha(destination/name)==digest for name,digest in ref['files'].items())
verifier=(B13/'verify_native_contour_temporal.py').read_text().replace("E=W/'evidence/v30-native-turn-optimizer-2026-10-09'","E=W/'evidence/v30-global-contour-pass-2026-10-09'")
verifier=verifier.replace('native-contour-temporal','global-contour-temporal').replace('native_contour_temporal_v1','global_contour_temporal_v1').replace('native_contour_temporal_order_v1','global_contour_temporal_order_v1')
(B/'verify_global_contour_temporal.py').write_text(verifier)
from collections import Counter
report=dict(status='FRESH_TEMPORAL_REGRESSION_PREPARED',mission=str(destination),points=len(ref['points']),maximum_control_height_change_m=max(delta),
            current_missing_flags=len(missing),scalar_positive_current_points=len(queries),added_points=len(additions),
            added_by_role=dict(Counter(p['role'] for p in additions)),all_current_query_points_in_reference=True,
            limits=['New seam points and scalar disagreements are diagnostics; unchanged controls retain their declared gates.','Compiled full-domain coverage remains the subcell geometric consumer.'])
(B/'temporal-preparation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
