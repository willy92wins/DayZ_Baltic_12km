from pathlib import Path
import hashlib,json,sys,time
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');O=R/'b3f-package-input-discovery-20261028';O.mkdir(exist_ok=False)
sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();start=time.monotonic()
p=R/'dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo';expected='ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84';assert sha(p)==expected
_,props,entries=read_pbo(p);assert sha(p)==expected
row=dict(status='PACKAGE_INPUTS_DISCOVERED_ONLY',baseline_pbo=str(p),baseline_sha256=expected,entry_count=len(entries),model_count=sum(n.endswith('.p3d') for n in entries),properties=props,target_sha256=hashlib.sha256(entries['cs_kit_118_0000.p3d']).hexdigest(),config_sha256=hashlib.sha256(entries['config.bin']).hexdigest(),seconds=time.monotonic()-start,entries={n:hashlib.sha256(data).hexdigest() for n,data in entries.items()})
assert row['model_count']==201 and row['entry_count']==202 and row['target_sha256']=='351424ab535a3e3eb40fc460a22360ab442776446055b116e10c0ba6134579f5'
(O/'report.json').write_text(json.dumps(row,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in row.items() if k!='entries'}))
