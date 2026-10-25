"""Reuse the previous physical controls with fresh candidate identities."""
from pathlib import Path
import csv,json,shutil,subprocess,sys
import numpy as np
from discover_native_turns import B,B10,W,sha
E=W/'evidence/v30-native-turn-optimizer-2026-10-09';OLD=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'));from v30_common import tri_sample

oldref=OLD/'scalar-r2-temporal-reference.json';ref=json.loads(oldref.read_text());src=Path(ref['mission'])
assert all(sha(src/k)==v for k,v in ref['files'].items())
deploy=json.loads((B/'deploy.json').read_text());mods=Path(deploy['destination'])/'Addons'
assert all(sha(mods/name)==digest for name,digest in deploy['files'].items())
terrain=B/'candidate-feasible/terrain.npz';h=np.load(terrain)['heights'];delta=[]
for point in ref['points']:
    expected=point.get('expected_ground_m')
    if expected is not None:delta.append(abs(float(tri_sample(h,point['x'],point['z']))-expected))
assert max(delta)<1e-6,max(delta)
before=list(csv.DictReader((OLD/'halo-r3-physical-anomalies.csv').open()))
after=list(csv.DictReader((E/'native-contour-physical-anomalies.csv').open()))
key=lambda r:(int(r['row']),int(r['col']),int(r['cls']))
old_missing={key(r) for r in before};new_missing={key(r) for r in after}
queries=list(csv.DictReader((E/'native-contour-unflagged-scalar-queries.csv').open(),delimiter=';'))
known={(round(p['x'],6),round(p['z'],6)) for p in ref['points']};novel=[]
for row in queries:
    x=int(row['col'])*6;z=12282-int(row['row'])*6
    if (round(x,6),round(z,6)) not in known:novel.append((x,z))
additions=[]
for label,rows in (('diagnostic_current_scalar',queries),('diagnostic_missing_presence',before+after)):
    for row in rows:
        x=int(row['col'])*6;z=12282-int(row['row'])*6;position=(round(x,6),round(z,6))
        if position in known:continue
        known.add(position);ident=30000+len(additions)
        point=dict(id=ident,x=x,z=z,role=label,reach='GLOBAL',case='new_native_inventory',expected_ground_m=float(tri_sample(h,x,z)))
        additions.append(point)
assert not ({p['id'] for p in additions}&{p['id'] for p in ref['points']})
ref['points'].extend(additions)
name='BalticNativeContourTemporalV1.BalticTrial';mission=B/'missions'/name;mission.mkdir(parents=True,exist_ok=False)
code=(src/'init.c').read_text().replace('scalar_temporal_v2','native_contour_temporal_v1').replace('scalar_temporal_order_v2','native_contour_temporal_order_v1')
assert 'm_Rows.Count() == 351' in code and 'END;62;351' in code
code=code.replace('m_Rows.Count() == 351',f"m_Rows.Count() == {len(ref['points'])}").replace('END;62;351',f"END;62;{len(ref['points'])}")
(mission/'init.c').write_text(code)
(mission/'points.csv').write_text(''.join(f'{p["id"]};{p["x"]:.9f} 0 {p["z"]:.9f}\n' for p in ref['points']))
validator='C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py'
lint=subprocess.run([sys.executable,validator,str(mission)],capture_output=True,text=True);got=json.loads(lint.stdout)
assert lint.returncode==0 and got['info']['files_scanned']==1 and not got['errors'];(B/'native-temporal-lint.json').write_text(lint.stdout)
destination=src.parent/name;shutil.copytree(mission,destination)
ref.update(mission=str(destination),files={p.name:sha(p) for p in mission.iterdir()},terrain_sha256=sha(terrain),pbo=deploy['files'],
           deployed={str(mods/name):digest for name,digest in deploy['files'].items()},source_reference_sha256=sha(oldref))
(E/'native-contour-temporal-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
assert all(sha(destination/name)==digest for name,digest in ref['files'].items())
verifier=(B10/'verify_scalar_r2_temporal.py').read_text().replace("E=W/'evidence/v30-global-water-risk-2026-10-09'","E=W/'evidence/v30-native-turn-optimizer-2026-10-09'")
verifier=verifier.replace('scalar-r2-temporal','native-contour-temporal').replace('scalar_temporal_v2','native_contour_temporal_v1').replace('scalar_temporal_order_v2','native_contour_temporal_order_v1')
(B/'verify_native_contour_temporal.py').write_text(verifier)
report=dict(status='FRESH_TEMPORAL_REGRESSION_PREPARED',mission=str(destination),points=len(ref['points']),maximum_control_height_change_m=max(delta),
            native_missing_flag_identities_match_previous=old_missing==new_missing,missing_flag_points=len(after),
            newly_missing_flag_ids=sorted(new_missing-old_missing),no_longer_missing_flag_ids=sorted(old_missing-new_missing),
            added_diagnostic_points=len(additions),novel_scalar_queries=len(novel),
            scalar_positive_current_points=len(queries),all_scalar_positive_points_in_temporal_reference=True,
            explanation='Presence flags alone do not establish missing water. Repeated scalar/depth consumers retain these same exceptions for classification.')
(B/'native-anomaly-regression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
