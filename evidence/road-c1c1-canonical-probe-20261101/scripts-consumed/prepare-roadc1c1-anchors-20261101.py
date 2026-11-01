from pathlib import Path
import json,hashlib,os,time,sys,subprocess,stat
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c1-local-author-20261101';D.mkdir(exist_ok=False);started=time.time()
def dump(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
dump(D/'author-start.json',{'started':started,'budget_seconds':600,'role':'Codex explicitly assigned local executor','plan':'ev112-road-c1c1-canonical-preflight-probe-20261029.md'})
script="""$ErrorActionPreference='Stop'
$sig=Get-AuthenticodeSignature -LiteralPath 'C:/Windows/System32/conhost.exe'
$chain=[System.Security.Cryptography.X509Certificates.X509Chain]::new()
$chain.ChainPolicy.RevocationMode='NoCheck'
$chain.ChainPolicy.UrlRetrievalTimeout=[TimeSpan]::FromSeconds(3)
$ok=$chain.Build($sig.SignerCertificate)
$rows=@($chain.ChainElements | ForEach-Object { @{subject=$_.Certificate.Subject;issuer=$_.Certificate.Issuer;thumbprint=$_.Certificate.Thumbprint;serial=$_.Certificate.SerialNumber;notBefore=$_.Certificate.NotBefore.ToUniversalTime().ToString('o');notAfter=$_.Certificate.NotAfter.ToUniversalTime().ToString('o')} })
@{path=$sig.Path;status=$sig.Status.ToString();message=$sig.StatusMessage;chainBuilt=$ok;revocationMode='NoCheck';chain=$rows;signer=$sig.SignerCertificate.Subject;signerThumbprint=$sig.SignerCertificate.Thumbprint} | ConvertTo-Json -Depth 8
"""
(D/'conhost-signature.ps1').write_text(script,encoding='utf-8')
command=['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(D/'conhost-signature.ps1')];tick=time.monotonic();r=subprocess.run(command,capture_output=True,timeout=30,creationflags=0x08000000);(D/'signature.stdout').write_bytes(r.stdout);(D/'signature.stderr').write_bytes(r.stderr);assert r.returncode==0;sig=json.loads(r.stdout.decode('utf-8-sig'));assert sig['status']=='Valid' and sig['chainBuilt'] and sig['signer'].startswith('CN=Microsoft Windows,')
dump(D/'signature-receipt.json',{'command':command,'rc':r.returncode,'seconds':time.monotonic()-tick,'stdout_sha':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha':hashlib.sha256(r.stderr).hexdigest(),'attestation':'Authenticode observed now; revocation NoCheck for explicit chain builder'})
def pin(p):
 p=Path(p);s=p.stat();b=p.read_bytes();t=p.stat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]}
old=R/'road-c1c-local-author-20261029';c=json.loads((old/'contract.json').read_bytes());assert hashlib.sha256((old/'contract.json').read_bytes()).hexdigest()=='e88e345a2e88a6c47b05091a40c1bdfbaab34353ad000f7b7b80d52b6104f1b6'
canonical=Path('C:/Users/guill/.claude/skills/dayz-preflight/preflight.py');a=Path('C:/Users/guill/.agents/skills/dayz-preflight');orig=pin(canonical);assert (orig['bytes'],orig['sha256'])==(10743,'9f8786a5f37b6b2abbd206bce51d4cad44d58536e766b97fd93bae692804c9a7');assert a.resolve()==canonical.parent
anc=[]
for p in [canonical,*canonical.parents]:
 s=p.lstat();assert not getattr(s,'st_file_attributes',0)&1024 and not stat.S_ISLNK(s.st_mode);anc.append({'path':str(p),'dev':s.st_dev,'ino':s.st_ino,'attributes':getattr(s,'st_file_attributes',0),'is_dir':p.is_dir()})
link=a.lstat();assert link.st_reparse_tag==2684354563;alias={'path':str(a),'target':os.readlink(a),'dev':link.st_dev,'ino':link.st_ino,'tag':link.st_reparse_tag}
for n in ['preflight-original.py','preflight-local.py','oracle.json','logger-fixture.xml','include.lst','exclude.lst']:(D/n).write_bytes((old/n).read_bytes())
assert pin(D/'preflight-local.py')['sha256']=='812e68aa2744428b3fce1b8016b552252e13244fa37eec7084e42763ab446646'
for p in [*c['tool_files'],*c['tools'].values()]:assert pin(p['path'])['sha256']==p['sha256']
helper=pin('C:/Windows/System32/conhost.exe');helper.update(signature=sig,signature_stdout_sha=hashlib.sha256(r.stdout).hexdigest(),argv_pattern='exact image path (optional NT prefix), followed by one hexadecimal 0x handle; exactly 2 arguments',role='OS_HOST_HELPER')
c.update(schema='road-c1c1-probe.v1',root=str(R/'road-c1c1-probe-20261101'),preflight_original=orig,canonical_preflight={'file':orig,'ancestors':anc,'alias':alias},os_helper=helper,prior_contract=pin(old/'contract.json'))
for k,n in [('preflight','preflight-local.py'),('include','include.lst'),('exclude','exclude.lst')]:c[k]=pin(D/n)
dump(D/'contract.json',c)
o={'schema':'road-c1c1-oracle.v1','canonical_good':'MATCH','changed_alias':'ALIAS_CHANGED','new_reparse':'REPARSE','changed_source':'PIN','before_help':'NOT_LAUNCHED','started_without_close':'INCOMPLETE_PHASE','wrong_helper_parent':'PROCESS_PARENT','wrong_helper_argv':'OS_HELPER_ARGV','helper_is_not_binarize':'PROBE_INCONCLUSIVE_NOT_OBSERVED','logger_before_start':'ORIGINAL','total_seconds':1050,'producer_seconds':930,'observer_seconds':120,'old_literal_oracle_sha':'0a809df80c7766f114a5c330418145fa9a831dab80ccd593486a9e5a84de236b'};dump(D/'oracle-c1c1.json',o)
dump(D/'anchors.json',{'contract_sha':pin(D/'contract.json')['sha256'],'oracle_sha':pin(D/'oracle-c1c1.json')['sha256'],'seconds':time.time()-started,'canonical':orig,'helper':helper,'no_native_tool_run':True})
print(json.dumps({'seconds':time.time()-started,'contract':pin(D/'contract.json')['sha256'],'oracle':pin(D/'oracle-c1c1.json')['sha256']}))
