from pathlib import Path
import hashlib,json,re
B=Path(__file__).parent
p=Path('P:/DayZ_MCP_dev/_server/profiles/DayZDiag_x64_2026-10-10_05-20-01.RPT')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
t=p.read_text(errors='replace');lines=t.splitlines()
assert '-mission=C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZServer\\mpmissions\\BalticIncrementalBankFullWaterV1.BalticTrial' in t
assert '-mod=P:\\Mods\\@DayZ_MCP;P:\\Mods\\@DayZ_Baltic_IncrementalBankPreviewV1' in t
assert '-filePatching' not in '\n'.join(lines[:12])
ends=[(i+1,s) for i,s in enumerate(lines) if '--- Termination successfully completed ---' in s]
assert ends
deployment=json.loads((B/'deploy.json').read_text())
actual={name:sha(Path(deployment['mod'])/'Addons'/name) for name in deployment['files']}
assert actual==deployment['files']
source=B/'missions/BalticIncrementalBankFullWaterV1.BalticTrial'
ref=json.loads((B/'native-reference.json').read_text())
for name,digest in ref['files'].items():
    assert sha(source/name)==sha(Path(ref['mission'])/name)==digest
stats={key:sum(bool(re.search(pattern,s,re.I)) for s in lines) for key,pattern in {
    'script_errors':'SCRIPT.*\\(E\\)',
    'exceptions':'exception',
    'plugin_item_diagnostic_mentions':'PluginItemDiagnostic',
    'resource_errors':'RESOURCES.*\\(E\\)'
}.items()}
report=dict(status='PASS_RUNTIME_ARTIFACT_IDENTITY_AND_ORDERLY_TERMINATION',path=str(p),sha256=sha(p),bytes=p.stat().st_size,lines=len(lines),termination=ends,log_counts=stats,actual_deployed=actual,mission_files=ref['files'],limits=['RPT retains environment/resource and script diagnostics; this does not certify a clean log or render.','Server-only run 2d06c106-f70d-48ea-aff5-ab17fb42c8f9, version 1.29.163709.'])
(B/'runtime-rpt-identity.json').write_text(json.dumps(report,indent=2)+'\n')
(B/'runtime-rpt-excerpt.log').write_text('\n'.join(lines[:50]+['...']+lines[-6:])+'\n')
print(json.dumps(report,indent=2))
