from pathlib import Path
import hashlib,json,uuid,subprocess,sys,shutil
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-native-config-types-20261027';D.mkdir(exist_ok=False)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
probe=str(uuid.uuid4());mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticNavConfigTypes.BalticTrial');mission.mkdir(exist_ok=False)
template=W/'missions/BalticNavConfigTypes.BalticTrial/init.c'
(mission/'init.c').write_text(template.read_text().replace('@PROBE_ID@',probe),encoding='ascii')
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
bootstrap='import runpy,sys;sys.path.insert(0,'+repr(str(validator.parent))+');sys.argv='+repr([str(validator),str(mission),'--vanilla-root','P:/scripts'])+';runpy.run_path('+repr(str(validator))+',run_name="__main__")'
p=subprocess.run([sys.executable,'-I','-c',bootstrap],capture_output=True)
(D/'script-validator.json').write_bytes(p.stdout);(D/'script-validator.stderr.log').write_bytes(p.stderr)
static=read(D/'script-validator.json');assert p.returncode==0 and static['status']=='PASS' and static['info']['files_scanned']==1 and not static['errors'] and not static['warnings']
capture=(R/'capture_kit7_nav_log.ps1').read_text().replace('900','120').replace("$rows[-1] -eq 'END;607'", "$rows[-1] -match '^END;[0-9]+$'").replace('607','9')
(R/'capture_kit7_config_types_log.ps1').write_text(capture)
source=(R/'orchestrate_kit7_nav12_probe.js').read_text()
replacements={'probeKit7Nav12':'probeKit7ConfigTypes','kit7-nav12-consumer-20261027':D.name,'BalticKit7Nav12.BalticTrial':mission.name,'baltic_kit7_nav_3325b685-d8cf-42d1-a476-aa2a3fe2e857.log':f'baltic_nav_config_{probe}.log','kit7-nav12-postprocess-review-20261027':'kit7-config-types-code-review-20261027',"extra_mods:['@DayZ_Baltic_EV112_Kit7Nav12']":"extra_mods:['@DayZ_Baltic_EV112_Kit7Nav8']",'kit7Nav12Probe':'kit7ConfigTypesProbe','KIT7_NAV607':'KIT7_CONFIG9','capture_kit7_nav_log.ps1':'capture_kit7_config_types_log.ps1','finish_kit7_nav12_probe.py':'finish_kit7_config_types_probe.py',"workdir:w,yield_time_ms":"workdir:w,login:false,yield_time_ms",'-MaxSeconds 1200':'-MaxSeconds 600'}
for a,b in replacements.items():assert a in source,a;source=source.replace(a,b)
# Inventory checked before launch as well as after capture; no occupancy preflight.
source=source.replace("foreach($v in @($dep.inputs.PSObject.Properties)","$stock=Get-Content -LiteralPath '"+str(D).replace('\\','/')+"/vanilla-packages.json' -Raw|ConvertFrom-Json\\n$actual=@(Get-ChildItem -LiteralPath $stock.directory -Filter '*.pbo' -File|ForEach-Object {$_.FullName.ToLowerInvariant()}|Sort-Object)\\n$expected=@($stock.packages.PSObject.Properties|ForEach-Object {[IO.Path]::GetFullPath($_.Name).ToLowerInvariant()}|Sort-Object)\\nif(Compare-Object $actual $expected){throw 'Vanilla inventory drift'}\\nforeach($v in @($dep.inputs.PSObject.Properties)")
(R/'orchestrate_kit7_config_types_probe.js').write_text(source)
for name in ('flow','command'):
 s=(R/f'test_kit7_nav12_probe_{name}.cjs').read_text()
 for a,b in replacements.items():s=s.replace(a,b)
 s=s.replace('orchestrate_kit7_nav12_probe.js','orchestrate_kit7_config_types_probe.js').replace('native607 remains separate','native config getters remain separate')
 (R/f'test_kit7_config_types_probe_{name}.cjs').write_text(s)
finish=(R/'finish_kit7_nav12_probe.py').read_text().replace('kit7-nav12-consumer-20261027',D.name).replace('==607','==9')
finish=finish.replace("assert mcp['version']==read(R/'nav-kit7-12m-preparation-20261027/mcp-after.json')['version']", "assert mcp['version_state']=='ok'")
begin=finish.index("execute([W/'tools/navigation/verify_kit7_nav_ev112.py'")
finish=finish[:begin]+'''execute([W/'tools/navigation/verify_nav_config_types_ev112.py','--probe-id',frozen['probe_id'],'--log',O/'runtime.log','--out',O/'result.json'],'consumer')
import re
rpt=(O/'server.RPT').read_text(encoding='utf-8-sig',errors='replace').splitlines()
pattern=re.compile(r'filterIsolatedIslands|navmesh|conversion|cannot convert|type mismatch|config.*(?:error|warning)',re.I)
hits=[i for i,line in enumerate(rpt) if pattern.search(line)]
excerpts=[dict(line=i+1,context=[dict(line=j+1,text=rpt[j]) for j in range(max(0,i-2),min(len(rpt),i+3))]) for i in hits]
(O/'rpt-config-observations.json').write_text(json.dumps(dict(status='OBSERVED_LOG_EXCERPTS',rpt_sha256=sha(O/'server.RPT'),total_lines=len(rpt),match_count=len(hits),pattern=pattern.pattern,origin='INCONCLUSIVE_UNLESS_INDIVIDUAL_CONTEXT_IDENTIFIES_PHASE',excerpts=excerpts,limits=['No match is not proof of valid conversion. No claim of warning-free startup. Full RPT retained privately.']),indent=2)+'\\n')
print('CONFIG_READ_DIAGNOSTIC_CONSUMED_NO_HEIGHT_OR_RAM_ACCEPTANCE')
'''
finish=finish.replace("limits=['Exact kit7 NM and packages; no actor or global acceptance.']", "limits=['Exact Nav8 packages; config reads only, no height/RAM/actor acceptance.']")
stockcheck="""stock=read(O/'vanilla-packages.json')
assert set(str(p.resolve()).casefold() for p in Path(stock['directory']).glob('*.pbo'))==set(str(Path(p).resolve()).casefold() for p in stock['packages'])
for path,digest in stock['packages'].items():assert sha(path)==digest,path
"""
finish=finish.replace("host=read(O/'host-identity.json');",stockcheck+"host=read(O/'host-identity.json');")
(R/'finish_kit7_config_types_probe.py').write_text(finish)
stock=read(R/'chernarus-nav-height-reference-20261027/vanilla-packages.json')
assert set(str(p.resolve()).casefold() for p in Path(stock['directory']).glob('*.pbo'))==set(str(Path(p).resolve()).casefold() for p in stock['packages'])
for path,digest in stock['packages'].items():assert sha(path)==digest,path
write(D/'vanilla-packages.json',stock)
packages={str(Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8/Addons')/n):h for n,h in {'narva_trial.pbo':'ac088ccbaff34ef7a5cbfe03b6e016fb6941895b9b253786f99b57578cf6d4ff','baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6','baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}.items()}
packages['P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo']='7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'
for path,digest in packages.items():assert sha(path)==digest,path
write(D/'runtime-preparation.json',dict(status='PREPARED_PENDING_OPERATIONAL_REVIEW',mission=str(mission),log_name=f'baltic_nav_config_{probe}.log',probe_id=probe,expected_count=9,packages=packages))
print(json.dumps(dict(probe_id=probe,script_validator=static['status'],stock_packages=len(stock['packages']))))
