from pathlib import Path
import hashlib,json,datetime,subprocess,sys
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;kind='full';O=R/'runtime-road-f'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'));from eval_visual_probe_v31 import parse,projected_margin,calibrate
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
assert not (O/'result.json').exists() and not (O/'identity-verification.json').exists()
d=read(O/'deployment.json');host=read(O/'host-identity.json');m=read(O/'mcp-identity.json');b=read(O/'log-binding.json');c=read(O/'cleanup.json')
for path,h in d['inputs'].items():assert sha(path)==h,path
assert host['run_id']==m['run_id']==m['server_run_id'] and m['server_binding']=='BOUND' and m['version_state']=='ok'
assert len(m['processes'])==1 and m['processes'][0]['role']=='server' and m['processes'][0]['pid']==host['pid']==b['pid']
assert host['navmesh_data_server'] and all(x['state']=='not_started' for x in m['client_diagnostics'])
assert Path(host['mission_path'])==Path(d['mission']) and host['mission_sha256']==sha(Path(d['mission'])/'init.c')
assert host['executable_file_sha256']=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
actual={str(Path(p).resolve()).casefold():h for p,h in host['package_hashes'].items()}
expected={**d['deployed'],'P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'}
assert actual=={str(Path(p).resolve()).casefold():h for p,h in expected.items()}
for p,h in expected.items():assert sha(p)==h,p
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
assert abs((utc(host['created_utc'])-utc(m['processes'][0]['creation_time_utc'])).total_seconds())<=.002
assert b['sha256']==sha(O/'runtime.log') and b['expected_end_count']==d['points']
assert utc(b['source_last_write_utc'])>=utc(host['created_utc'])
assert c['close']['run_retired'] and c['self']['state']=='none' and not c['cleanup_degraded'] and c['pending_commands']==0
(O/'identity-verification.json').write_text(json.dumps(dict(status='PASS_BOUND_NATIVE_CONTACT_INPUTS',run_id=host['run_id'],inputs_unchanged=True,points=d['points'],navmesh_data_server=True,client_started=False),indent=2)+'\n')
ref=R/'runtime-t-20261025/calibration-fresh.log';assert sha(ref)=='b72f39c114f0d40e0228f8440ceea66bc45a910d5f76f06ed5599ed08c2c1e20'
if kind=='full':
    for p,h in read(O/'points.json')['inherited_inputs'].items():assert sha(p)==h,p
    args=[sys.executable,'-I',str(W/'tools/water/eval_visual_road_probe_ev112.py'),str(O/'points.json'),str(O/'runtime.log'),str(O/'result.json'),'--collision-reference',str(ref)]
    p=subprocess.run(args,capture_output=True,cwd=W);(O/'consumer.stdout.log').write_bytes(p.stdout);(O/'consumer.stderr.log').write_bytes(p.stderr)
    print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'));raise SystemExit(p.returncode)
margin=calibrate(ref.read_text())['margin_m'];points=read(O/'points.json')['points']
def judge_grid(path):
    rows=parse(path.read_text(),300);assert set(rows)==set(range(300));fail=[]
    for p in points:
        row=rows[p['id']];why=[]
        if not row['rv'] or 'baltic_stream_pilot\\' not in row['rv_shapes']:why.append('RV miss')
        if not row['bullet'] or 'baltic_stream_pilot\\' not in row['bullet_shape']:why.append('Bullet miss')
        if any(abs(row[key][i]-p[axis])>.01 for key in ('rv_pos','bullet_pos') for i,axis in ((0,'x'),(2,'z'))):why.append('ray XZ')
        try:
            if abs(projected_margin(row)-margin)>.01:why.append('margin')
        except AssertionError:why.append('invalid normal')
        if why:fail.append(dict(id=p['id'],original_id=p['original_id'],why=why,measured=row))
    return fail
positive=judge_grid(R/'runtime-u2-20261025/rv-grid.log');negative=judge_grid(R/'runtime-t-20261025/rv-grid.log');assert not positive and negative
failed=judge_grid(O/'runtime.log');result=dict(status='SERVER_GRID_CONTACT_PASS' if not failed else 'FAIL',points=300,failure_count=len(failed),failures=failed,positive_U2_pass=True,negative_T_rejected=True,limits=['Frozen diagnostic grid with RV/Bullet hit, XZ and calibrated margin only; full4749 gate remains separate.'])
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='failures'}));raise SystemExit(bool(failed))
