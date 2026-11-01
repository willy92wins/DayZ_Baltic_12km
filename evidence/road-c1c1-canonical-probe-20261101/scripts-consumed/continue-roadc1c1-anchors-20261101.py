from pathlib import Path
import json,hashlib,os,time,sys,subprocess,stat
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c1-local-author-20261101';started=json.loads((D/'author-start.json').read_bytes())['started']
def dump(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
ps='C:/Users/guill/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe';command=[ps,'-NoProfile','-File',str(D/'conhost-signature.ps1')];t=time.monotonic();r=subprocess.run(command,capture_output=True,timeout=30,creationflags=0x08000000);(D/'signature-r1.stdout').write_bytes(r.stdout);(D/'signature-r1.stderr').write_bytes(r.stderr);assert r.returncode==0;sig=json.loads(r.stdout.decode('utf-8-sig'));assert sig['status']=='Valid' and sig['chainBuilt'] and sig['signer'].startswith('CN=Microsoft Windows,')
dump(D/'signature-receipt.json',{'command':command,'rc':r.returncode,'seconds':time.monotonic()-t,'stdout_sha':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha':hashlib.sha256(r.stderr).hexdigest(),'attestation':'Current host PowerShell7.6.5. Original powershell5.1 module autoload failed, preserved. Explicit chain NoCheck is not revocation attestation.'})
source=(R/'prepare-roadc1c1-anchors-20261101.py').read_text();tail=source[source.index('def pin(p):'):];exec(compile(tail,'anchored-tail','exec'))
