from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).parent;D=R/'nav-kit7-8m-preparation-20261027/release-tests';D.mkdir(exist_ok=False)
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
rows=[]
for pattern in ['test_navmesh*.py','test_nav8*.py','test_server_exit_observer.py']:
 start=time.monotonic();p=subprocess.run([sys.executable,'-I','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=W,capture_output=True)
 label=pattern.replace('*','all').replace('.py','');(D/(label+'.log')).write_bytes(p.stdout+p.stderr)
 assert p.returncode==0,(pattern,p.returncode)
 rows.append(dict(pattern=pattern,returncode=0,seconds=time.monotonic()-start));print(pattern,'PASS',flush=True)
sources=[*W.glob('tools/navigation/*nav8*'),*W.glob('tests/test_navmesh*.py'),W/'tests/test_nav8_config_ev112.py',W/'tests/test_server_exit_observer.py',W/'tools/navigation/generate_navmesh_console.py',W/'tools/navigation/inspect_navmesh_v9_ev112.py',W/'tools/navigation/observe_owned_server_exit.ps1']
(D/'result.json').write_text(json.dumps(dict(status='PASS_PREPUBLICATION_TARGETED_TESTS',runs=rows,sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},native_acceptance=False),indent=2)+'\n')
