from pathlib import Path
import ast,hashlib,json,subprocess,sys
if sys.flags.optimize:raise SystemExit('optimized Python refused')
R=Path(__file__).parent;O=R/'kit7-native-data-review-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
S=R/'stage-kit7-fc-20261026';M=R/'river-kit7-merged-byteexact-20261026'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not (O/'accepted.json').exists()
review=read(O/'review-response.json');completion=read(O/'completion.json')
assert not review['is_error'] and completion['exit_code']==0 and completion['inputs_unchanged'] and not review.get('permission_denials')
assert 'claude-fable-5-1' in review['modelUsage']
results=[]
for pattern in ('test_native_height_probe_ev112.py','test_forest_boundary_probe.py','test_forest_boundary_native_booleans.py'):
 p=subprocess.run([sys.executable,'-I','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=W,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
 (O/(pattern+'.log')).write_bytes(p.stdout);results.append(dict(pattern=pattern,exit_code=p.returncode));assert p.returncode==0,p.stdout.decode(errors='replace')
p=subprocess.run([sys.executable,'-O','-I',str(R/'prepare_kit7_native_data.py')],cwd=W,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
assert p.returncode!=0 and b'optimized Python disables preparation gates; refused' in p.stdout
(O/'optimized-python-negative.log').write_bytes(p.stdout)
source=R/'prepare_kit7_native_data.py';tree=ast.parse(source.read_text())
scope=dict(Path=Path,W=W,R=R,B=B,S=S,M=M,__file__=str(source),read=read)
# Read only the literal required-list assignment and its two append statements.
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='required' for t in node.targets):scope['required']=eval(compile(ast.Expression(node.value),str(source),'eval'),scope)
 elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='required':exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope)
paths=scope['required']+[W/'plans/ev112-kit7-native-data-unit-20261026.md',W/'tests/test_native_height_probe_ev112.py',Path(__file__),R/'forest-boundary-full-f/host-identity.json',O/'review-response.json',O/'source-hashes.json',O/'completion.json']
inputs={str(p):sha(p) for p in paths}
fixes=[dict(id=1,fix='Reject optimized interpreter before reading gate; real -O negative returns nonzero.'),dict(id=2,fix='Bind both interpolation and native parser plus WRP reader before use.'),dict(id=3,fix='Correct native SurfaceY tolerance citation to line88.'),dict(id=4,fix='NaN field preserves six columns and reaches numeric validation.'),dict(id=5,fix='Plan preserves partial outputs and forbids blind rerun.'),dict(id=6,fix='Consumer requires deployed init hash to equal bound producer; updated-hash mutant rejected.')]
receipt=dict(status='REVIEW_ACCEPTED_PREPARE_ONLY',review_verdict='SOUND-with-fixes',reviewer='claude-fable-5-1',receiver='Codex',fixes=fixes,tests=results,optimized_python_rejected=True,mode_adjustment='DataServer true, matching F boundary host receipt; no navigation acceptance',inputs=inputs,scope='Preparation and consumer tests only; runtime identity must be checked independently at launch.')
(O/'accepted.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=receipt['status'],bound_inputs=len(inputs),tests=results,optimized_python_rejected=True)))
