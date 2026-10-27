from pathlib import Path
import hashlib,json,uuid,subprocess,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'chernarus-nav-height-reference-20261027'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
assert not (D/'runtime-preparation.json').exists()
probe=str(uuid.uuid4());mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticChernarusNavHeightRef.ChernarusPlus');mission.mkdir(exist_ok=False)
anchors=read(D/'anchors.json')['anchors']
csv='\n'.join(a['id']+';'+a['shape']+';'+' '.join(f'{v:.6f}' for v in a['historical_position']) for a in anchors)+'\n'
(D/'anchors.csv').write_text(csv);(mission/'anchors.csv').write_text(csv)
template=W/'missions/BalticChernarusNavHeightRef.ChernarusPlus/init.c'
(mission/'init.c').write_text(template.read_text().replace('@PROBE_ID@',probe),encoding='ascii')
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
bootstrap='import runpy,sys;sys.path.insert(0,'+repr(str(validator.parent))+');sys.argv='+repr([str(validator),str(mission),'--vanilla-root','P:/scripts'])+';runpy.run_path('+repr(str(validator))+',run_name="__main__")'
p=subprocess.run([sys.executable,'-I','-c',bootstrap],capture_output=True)
(D/'script-validator.json').write_bytes(p.stdout);(D/'script-validator.stderr.log').write_bytes(p.stderr)
static=read(D/'script-validator.json');assert static['status']=='PASS' and static['info']['files_scanned']==1 and not static['errors'] and not static['warnings']
capture=(R/'capture_kit7_nav_log.ps1').read_text().replace('900','300').replace("$rows[-1] -eq 'END;607'", "$rows[-1] -match '^END;[0-9]+$'").replace('607','49')
(R/'capture_chernarus_nav_height_log.ps1').write_text(capture)
source=(R/'orchestrate_kit7_nav12_probe.js').read_text()
replacements={'probeKit7Nav12':'probeChernarusNavHeight','kit7-nav12-consumer-20261027':D.name,'BalticKit7Nav12.BalticTrial':mission.name,'baltic_kit7_nav_3325b685-d8cf-42d1-a476-aa2a3fe2e857.log':f'chernarus_nav_height_{probe}.log','kit7-nav12-postprocess-review-20261027':'chernarus-nav-height-code-review-20261027',"extra_mods:['@DayZ_Baltic_EV112_Kit7Nav12']":"extra_mods:[]",'kit7Nav12Probe':'chernarusNavHeightProbe','KIT7_NAV607':'CHERNARUS_NAV49','capture_kit7_nav_log.ps1':'capture_chernarus_nav_height_log.ps1','finish_kit7_nav12_probe.py':'finish_chernarus_nav_height_probe.py',"$a.Count -ne 4":"$a.Count -ne 1","Properties).Count -ne 4":"Properties).Count -ne 1","workdir:w,yield_time_ms":"workdir:w,login:false,yield_time_ms"}
for a,b in replacements.items():assert a in source,a;source=source.replace(a,b)
# Vanilla inventory revalidation is completed before launch by seal/guard and again after capture.
(R/'orchestrate_chernarus_nav_height_probe.js').write_text(source)
for name in ('flow','command'):
 s=(R/f'test_kit7_nav12_probe_{name}.cjs').read_text()
 for a,b in replacements.items():s=s.replace(a,b)
 s=s.replace('orchestrate_kit7_nav12_probe.js','orchestrate_chernarus_nav_height_probe.js')
 (R/f'test_chernarus_nav_height_probe_{name}.cjs').write_text(s)
finish=(R/'finish_kit7_nav12_probe.py').read_text()
finish=finish.replace('kit7-nav12-consumer-20261027',D.name).replace("==4","==1").replace('==607','==49')
finish=finish.replace("assert mcp['version']==read(R/'nav-kit7-12m-preparation-20261027/mcp-after.json')['version']", "assert mcp['version_state']=='ok'")
begin=finish.index("execute([W/'tools/navigation/verify_kit7_nav_ev112.py'")
finish=finish[:begin]+'''execute([W/'tools/navigation/verify_chernarus_nav_height_reference.py','--anchors',O/'anchors.json','--probe-id',frozen['probe_id'],'--log',O/'runtime.log','--out',O/'result.json'],'consumer')
print('REFERENCE_CAPTURE_CONSUMED_NO_BALTIC_ACCEPTANCE')
'''
# The accepted review and stock inventory are part of immutable deployment inputs.
finish=finish.replace("limits=['Exact kit7 NM and packages; no actor or global acceptance.']", "limits=['Exact Chernarus reference packages; no Baltic or actor acceptance.']")
stockcheck="""stock=read(O/'vanilla-packages.json')
assert set(str(p.resolve()).casefold() for p in Path(stock['directory']).glob('*.pbo'))==set(str(Path(p).resolve()).casefold() for p in stock['packages'])
for path,digest in stock['packages'].items():assert sha(path)==digest,path
"""
finish=finish.replace("host=read(O/'host-identity.json');",stockcheck+"host=read(O/'host-identity.json');")
(R/'finish_chernarus_nav_height_probe.py').write_text(finish)
packages=read(R/'kit7-navv9diag-ram-ab-20261027/pass-02/reference.json')['packages']
stock={p:h for p,h in packages.items() if '/dayz exp/addons/' in p.replace('\\','/').lower()}
stockdir=Path('E:/SteamLibrary/steamapps/common/DayZ Exp/Addons')
assert set(str(p.resolve()).casefold() for p in stockdir.glob('*.pbo'))==set(str(Path(p).resolve()).casefold() for p in stock)
for path,digest in stock.items():assert sha(path)==digest,path
write(D/'vanilla-packages.json',dict(directory=str(stockdir),packages=stock))
bridge=Path('P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo')
assert sha(bridge)=='7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'
write(D/'runtime-preparation.json',dict(status='PREPARED_PENDING_OPERATIONAL_REVIEW',mission=str(mission),log_name=f'chernarus_nav_height_{probe}.log',probe_id=probe,expected_count=49,packages={str(bridge):sha(bridge)}))
print(json.dumps(dict(probe_id=probe,script_validator=static['status'],stock_packages=len(stock))))
