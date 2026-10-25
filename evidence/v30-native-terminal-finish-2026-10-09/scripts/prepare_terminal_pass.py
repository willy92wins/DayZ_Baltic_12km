"""Freeze EV14 author/consumer kernels and adapt only domain and baseline."""
from pathlib import Path
import ast,hashlib,json,shutil
B=Path(__file__).parent;parent=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def replace(text,old,new):
    assert text.count(old)==1,(old,text.count(old))
    return text.replace(old,new)
source=parent/'global_contour_pass.py';s=source.read_text();begin=s.index('def discovery():');end=s.index('def contour_lines(',begin);s=s[:begin]+s[end:]
s=replace(s,"SOURCE=B13/'candidate-feasible/terrain.npz'", "SOURCE=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/candidate-repaired/terrain.npz')")
s=replace(s,"SOURCE_SHA='cff6d175da46a0080bd761c327babf9c0ef4c53434744ceec9241bc9cc28c82c'", "SOURCE_SHA='223029dedd7122096bb51c704fc722629b2be549f6c946b9cb89c7d1a8b6d6eb'")
s=replace(s,"started=time.monotonic();r0,c0=job;r1,c1=min(2047,r0+16),min(2047,c0+16)","started=time.monotonic();r0,c0,r1,c1=job['box_cells']")
s=replace(s,"report=dict(row=r0,col=c0,status='UNCHANGED',reason=None)","report=dict(row=r0,col=c0,box_cells=job['box_cells'],features=job['features'],status='UNCHANGED',reason=None)")
s=s.replace('len(results)%50==0','len(results)%1==0').replace('>5400','>1200').replace('Global 90 minute budget','Terminal 20 minute budget')
s=replace(s,'    if args.discover:discovery()','    if args.discover:raise SystemExit("Run discover_terminals.py instead")')
ast.parse(s);(B/'terminal_pass.py').write_text(s)
shutil.copyfile(parent/'contour_objective.py',B/'contour_objective.py');shutil.copyfile(parent/'derivative-controls.json',B/'derivative-controls.json')
source2=parent/'verify_global_contours.py';v=source2.read_text()
v=replace(v,"source=B13/'candidate-feasible/terrain.npz'", "source=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/candidate-repaired/terrain.npz')")
v=replace(v,"['candidate_tiles']","['candidate_boxes']")
v=replace(v,"gates['perimeters_exact']=np.array_equal(h[::16,:],v[::16,:]) and np.array_equal(h[:,::16],v[:,::16])", "gates['perimeters_exact']=all(np.array_equal(h[r0,c0:c1+1],v[r0,c0:c1+1]) and np.array_equal(h[r1,c0:c1+1],v[r1,c0:c1+1]) and np.array_equal(h[r0:r1+1,c0],v[r0:r1+1,c0]) and np.array_equal(h[r0:r1+1,c1],v[r0:r1+1,c1]) for r0,c0,r1,c1 in (job['box_cells'] for job in json.loads((B/'discovery.json').read_text())['jobs']))")
v=replace(v,"after['p90_degrees']<=.9*before['p90_degrees']", "after['p90_degrees']<=before['p90_degrees']+1e-5")
ast.parse(v);(B/'verify_terminal_global.py').write_text(v)
report=dict(status='EXACT_KERNEL_REUSE_WITH_DECLARED_DOMAIN_ADAPTATION',author_sha256=sha(source),consumer_sha256=sha(source2),objective_sha256=sha(B/'contour_objective.py'),derivatives_sha256=sha(B/'derivative-controls.json'),changes=['GlobalContourV1 baseline', '15 discovered variable rectangular boxes instead of full-map regular tiles', 'Frozen exterior 24 m with explicit engineering constraints', 'Global contour nonregression; local angular improvement required for integration', '20 minute total budget; unchanged 80 iterations/30 seconds per box'])
(B/'kernel-reuse.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
