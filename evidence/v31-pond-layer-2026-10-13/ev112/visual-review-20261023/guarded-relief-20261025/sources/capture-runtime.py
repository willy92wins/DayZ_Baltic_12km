from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
out=R/'runtime-guarded-d';log=Path('C:/temp/DayZ_MCP_130_dev/_server/profiles-130/baltic_visual_probe_v1.log')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for attempt in range(10):
    data=log.read_bytes()
    if data.rstrip().endswith(b'END;4292'):break
    time.sleep(5)
else:raise SystemExit('Probe still incomplete; nothing accepted')
doc=json.loads((out/'points.json').read_text())
for p,h in doc['inputs'].items():assert sha(Path(p))==h,('input drift',p)
reference=R/'runtime-t-20261025/calibration-fresh.log';assert sha(reference)=='b72f39c114f0d40e0228f8440ceea66bc45a910d5f76f06ed5599ed08c2c1e20'
(out/'runtime.log').write_bytes(data)
result=subprocess.run([sys.executable,'-I',str(W/'tools/water/eval_visual_probe_v31.py'),str(out/'points.json'),str(out/'runtime.log'),str(out/'result.json'),'--collision-reference',str(reference)],cwd=W)
(out/'identity.json').write_text(json.dumps(dict(run_id='7b9c50cf-3ca6-4ec4-a1e3-4652a8929738',pid=41352,created_utc='2026-10-25T17:17:42.852318Z',server_version='12~1.30.164200.56',server_binding='BOUND',mission='BalticGuardedD.BalticTrial',source_log=str(log),runtime_sha256=sha(out/'runtime.log'),all_inputs_unchanged=True,navmesh_data_server=True,client_started=False),indent=2)+'\n')
raise SystemExit(result.returncode)
