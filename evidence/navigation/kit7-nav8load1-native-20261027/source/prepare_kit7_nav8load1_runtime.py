from pathlib import Path
import hashlib,json,uuid,subprocess,sys,shutil
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav8load1-consumer-20261027';D.mkdir(exist_ok=False)
sys.path[:0]=[str(W/'tools/playtest'),str(W/'tools/navigation')]
from attach_navmesh import read_pbo
from package_nav8_onload_config_ev112 import verify_config_delta

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
old=read(R/'kit7-nav8-consumer-20261027/frozen.json');base_mission=Path(old['mission'])/'init.c'
assert sha(base_mission)==old['inputs'][str(base_mission)]
base=base_mission.read_text();normalized=base.replace(old['probe_id'],'@PROBE_ID@')
function='''// LOAD1_CONFIG_BEGIN: separate diagnostic; graph body stays byte-equivalent after normalization.
bool BalticWriteLoad1Config()
{
    ref array<string> paths = new array<string>;
'''
source=(W/'missions/BalticNavConfigTypes.BalticTrial/init.c').read_text()
function+='\n'.join(line.replace('m_Paths.Insert','paths.Insert') for line in source.splitlines() if 'm_Paths.Insert(' in line)+'\n'
function+='''    FileHandle output = OpenFile("$profile:baltic_nav_config_@PROBE_ID@.log", FileMode.WRITE);
    if (!output) return false;
    string world = GetGame().GetWorldName();
    bool accepted = world == "BalticTrial" && paths.Count() == 9;
    FPrintln(output, "BALTIC_NAV_CONFIG_TYPES_V1;" + world + ";@PROBE_ID@;9");
    Print("BALTIC_NAV_CONFIG_BEGIN_@PROBE_ID@");
    for (int index = 0; index < paths.Count(); index++)
    {
        string path = paths[index];
        bool exists = GetGame().ConfigIsExisting(path);
        int valueType = -1;
        string textValue = "";
        bool textOk = false;
        int integerValue = 0;
        float floatValue = 0;
        if (exists)
        {
            valueType = GetGame().ConfigGetType(path);
            textOk = GetGame().ConfigGetText(path, textValue);
            integerValue = GetGame().ConfigGetInt(path);
            floatValue = GetGame().ConfigGetFloat(path);
        }
        FPrintln(output, "C;" + index + ";" + path + ";" + exists + ";" + valueType + ";" + textOk + ";" + textValue + ";" + integerValue + ";" + floatValue);
        if (index < 8 && !exists) accepted = false;
        if (index == 0 || index == 2 || index == 3)
        {
            if (valueType != 0 || !textOk || textValue != "1" || integerValue != 1 || floatValue != 1) accepted = false;
        }
        if (index == 1 && (valueType != 2 || !textOk || textValue != "true" || integerValue != 0 || floatValue != 0)) accepted = false;
        if (index == 4 && (integerValue != 8 || floatValue != 8)) accepted = false;
        if (index == 5 && (integerValue != 50 || floatValue != 50)) accepted = false;
        if (index == 6 && (!textOk || textValue != "12:00")) accepted = false;
        if (index == 7 && (!textOk || textValue != "Chernarus")) accepted = false;
        if (index == 8 && exists) accepted = false;
    }
    Print("BALTIC_NAV_CONFIG_END_@PROBE_ID@");
    FPrintln(output, "END;9");
    CloseFile(output);
    return accepted;
}
// LOAD1_CONFIG_END
'''
guard='''        if (!BalticWriteLoad1Config())
        {
            FPrintln(output, "FAIL;CONFIG");
            FPrintln(output, "END;0");
            CloseFile(output);
            return;
        }
'''
mission_template=normalized.replace('class BalticKit7NavV1Mission',function+'class BalticKit7NavV1Mission').replace('        FileHandle input = OpenFile',guard+'        FileHandle input = OpenFile')
assert mission_template.count(function)==1 and mission_template.count(guard)==1
assert mission_template.replace(function,'').replace(guard,'')==normalized
source_dir=W/'missions/BalticKit7Nav8Load1.BalticTrial';source_dir.mkdir(exist_ok=False);(source_dir/'init.c').write_text(mission_template)
probe=str(uuid.uuid4());mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticKit7Nav8Load1.BalticTrial');mission.mkdir(exist_ok=False)
(mission/'init.c').write_text(mission_template.replace('@PROBE_ID@',probe),encoding='ascii')
queries=R/'kit7-nav8-consumer-20261027/queries.csv'
assert sha(queries)==old['inputs'][str(queries)]
for dest in (D/'queries.csv',mission/'queries.csv'):shutil.copyfile(queries,dest)
reference=read(R/'kit7-nav8-consumer-20261027/reference.json');prior_ref=dict(reference)
for p,h in reference['inputs'].items():assert sha(p)==h,p
reference.update(probe_id=probe,header='BALTIC_KIT7_NAV_V1;BalticTrial;'+probe,log_name='baltic_kit7_nav_'+probe+'.log')
assert {k:v for k,v in reference.items() if k not in ('probe_id','header','log_name')}=={k:v for k,v in prior_ref.items() if k not in ('probe_id','header','log_name')}
write(D/'reference.json',reference)
write(D/'contract-parity.json',dict(status='EXACT_607_CONTRACT_AND_GRAPH_BODY_PRESERVED',base_mission_sha256=sha(base_mission),new_mission_sha256=sha(mission/'init.c'),queries_sha256=sha(queries),baseline_reference_sha256=sha(R/'kit7-nav8-consumer-20261027/reference.json'),metadata_only_changed=['probe_id','header','log_name'],config_guard_separate=True))
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
bootstrap='import runpy,sys;sys.path.insert(0,'+repr(str(validator.parent))+');sys.argv='+repr([str(validator),str(mission),'--vanilla-root','P:/scripts'])+';runpy.run_path('+repr(str(validator))+',run_name="__main__")'
p=subprocess.run([sys.executable,'-I','-c',bootstrap],capture_output=True)
(D/'script-validator.json').write_bytes(p.stdout);(D/'script-validator.stderr.log').write_bytes(p.stderr)
static=read(D/'script-validator.json');assert p.returncode==0 and static['status']=='PASS' and static['info']['files_scanned']==1 and not static['errors'] and not static['warnings']
# Fresh mod only; preserve all original deployed packages.
B=R/'package-kit7-nav8-onload-20261027';v=read(B/'verification.json');assert v['status']=='PASS_ISOLATED_NAV8_ONLOAD_CONFIG_PACKAGE'
BASE=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8/Addons');DEST=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8Load1/Addons');DEST.mkdir(parents=True,exist_ok=False)
expected={'narva_trial.pbo':'f0e0e6b99da08b48f62ee47fa72b8905a5c9843bee4a30cefa18f517ddb1f603','baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6','baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}
packages={}
for name,digest in expected.items():
 src=(B/'Addons' if name=='narva_trial.pbo' else BASE)/name;assert sha(src)==digest
 shutil.copyfile(src,DEST/name);assert sha(DEST/name)==digest;packages[str(DEST/name)]=digest
assert sha(BASE/'narva_trial.pbo')==v['baseline_sha256']
raw,props,original=read_pbo(BASE/'narva_trial.pbo');del raw
raw,outprops,deployed=read_pbo(DEST/'narva_trial.pbo');del raw
assert props==outprops and set(original)==set(deployed)
assert [k for k in original if original[k]!=deployed[k]]==['config.bin']
assert hashlib.sha256(deployed['navmesh/baltic_trial.nm']).hexdigest()==v['navmesh_sha256'] and hashlib.sha256(deployed['baltic_trial.wrp']).hexdigest()==v['wrp_sha256']
assert deployed['config.bin']==(B/'config.bin').read_bytes()
(D/'deployed-config.bin').write_bytes(deployed['config.bin']);del original,deployed
converter='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe'
p=subprocess.run([converter,'-txt','-dst',str(D/'deployed-config.cpp'),str(D/'deployed-config.bin')],capture_output=True,creationflags=0x08000000)
(D/'decode-deployed.stdout.log').write_bytes(p.stdout);(D/'decode-deployed.stderr.log').write_bytes(p.stderr);assert p.returncode==0
verify_config_delta((B/'original.cpp').read_text(encoding='utf-8-sig'),(D/'deployed-config.cpp').read_text(encoding='utf-8-sig'))
bridge=Path('P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo');assert sha(bridge)=='7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a';packages[str(bridge)]=sha(bridge)
write(D/'deployment-parity.json',dict(status='EXACT_DEPLOYED_CONFIG_ONLY_DELTA',packages=packages,unchanged_entries=6826,wrp_sha256=v['wrp_sha256'],nm_sha256=v['navmesh_sha256'],deployed_config_sha256=sha(D/'deployed-config.bin'),baseline_preserved=True))
shutil.copyfile(R/'kit7-native-config-types-20261027/vanilla-packages.json',D/'vanilla-packages.json')
write(D/'runtime-preparation.json',dict(status='PREPARED_PENDING_OPERATIONAL_REVIEW',mission=str(mission),probe_id=probe,log_name=reference['log_name'],config_log_name='baltic_nav_config_'+probe+'.log',expected_count=607,packages=packages))
print(json.dumps(dict(status='PREPARED_PENDING_OPERATIONAL_REVIEW',probe_id=probe,static='PASS',unchanged_entries=6826)))
