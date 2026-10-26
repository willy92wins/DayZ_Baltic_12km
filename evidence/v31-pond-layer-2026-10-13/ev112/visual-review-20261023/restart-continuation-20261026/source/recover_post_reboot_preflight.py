from pathlib import Path
import hashlib,json,subprocess,sys,datetime,os
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
out=R/'restart-recovery-20261026'
out.mkdir(exist_ok=False)
src=Path('C:/Users/guill/.agents/skills/dayz-preflight/preflight.py')
raw=src.read_bytes(); text=raw.decode('utf-8-sig')
bad="""        'subst P: "C:\\Users\\guill\\OneDrive\\Documentos\\DayZ Projects"',"""
assert text.count(bad)==1
fixed=text.replace(bad, "        r"+bad.strip(),1)
target=out/'preflight-syntax-only-copy.py'
target.write_text(fixed,encoding='utf-8')
p=subprocess.run([sys.executable,'-I',str(target)],capture_output=True,text=True)
(out/'preflight.stdout.log').write_text(p.stdout,encoding='utf-8')
(out/'preflight.stderr.log').write_text(p.stderr,encoding='utf-8')
h=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
prepared=json.loads((R/'nav-c-data-preparation-20261026/inputs.json').read_text())
check={path:{'expected':digest,'actual':h(path)} for path,digest in prepared['inputs'].items()}
assert src.read_bytes()==raw
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(src),'source_sha256':hashlib.sha256(raw).hexdigest(),'copy_sha256':h(target),'copy_change':'only raw-string prefix on diagnostic subst example; governed source untouched','preflight_exit':p.returncode,'inputs':check,'inputs_unchanged':all(v['expected']==v['actual'] for v in check.values())}
(out/'recovery.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(p.stdout)
print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
assert p.returncode==0 and result['inputs_unchanged']

