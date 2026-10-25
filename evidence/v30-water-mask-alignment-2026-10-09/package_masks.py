from pathlib import Path
import sys,json,hashlib,subprocess,shutil,re
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=json.loads((B/'mask-verification.json').read_text());assert result['status']=='PASS_MASK_ALIGNMENT_SOURCE_AND_COMPILED_INTERIORS'
baseline=Path('P:/Mods/@DayZ_Baltic_TerminalContourV1/Addons/narva_trial.pbo');assert sha(baseline)=='c06f9b52d0b31d5c6e5cd3ec6c8cb14055abbe3ae40163092403b5ac66ca88fe'
raw,props,before=read_pbo(baseline);del raw
stage=B/'package/narva_trial';stage.mkdir(parents=True,exist_ok=False);changes=[];count=0
for name,data in before.items():
 dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True)
 match=re.search(r'(?:^|/)m_\d{3}_\d{3}_lca\.paa$',name,re.I)
 if match:
  replacement=B/'layers'/Path(name).name.lower();assert replacement.exists();candidate=replacement.read_bytes();count+=1
  if candidate!=data:changes.append(name)
  dest.write_bytes(candidate)
 else:dest.write_bytes(data)
assert count==1024 and changes
out=B/'packed';out.mkdir(exist_ok=False)
cmd=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
for k,v in props.items():cmd+=['-property',k+'='+v]
cmd+=['-dst',str(out),str(stage)]
done=subprocess.run(cmd,capture_output=True,text=True);(B/'filebank.log').write_text(done.stdout+'\n'+done.stderr);assert done.returncode==0
pbo=out/'narva_trial.pbo';raw,afterprops,after=read_pbo(pbo);del raw
assert props==afterprops and set(before)==set(after)
actual=sorted(k for k in before if before[k]!=after[k]);assert actual==sorted(changes)
assert all(re.search(r'(?:^|/)m_\d{3}_\d{3}_lca\.paa$',k,re.I) for k in actual)
for k in before:
 if k not in actual:assert before[k]==after[k]
water=Path('P:/Mods/@DayZ_Baltic_TerminalContourV1/Addons/baltic_water_v30.pbo');assert sha(water)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
dest=Path('P:/Mods/@DayZ_Baltic_AlignedMaskV1/Addons');dest.mkdir(parents=True,exist_ok=False)
for source in [pbo,water]:shutil.copyfile(source,dest/source.name);assert sha(source)==sha(dest/source.name)
receipt=dict(status='DEPLOYED_MASK_ONLY_PREVIEW',mod=str(dest.parent),world_sha256=sha(pbo),water_sha256=sha(water),baseline_world_sha256=sha(baseline),changed_mask_entries=len(actual),changed_entries=actual,total_entries=len(before),archive_properties=props,all_other_entries_byte_identical=True,wrp_sha256=hashlib.sha256(after['baltic_trial.wrp']).hexdigest(),terrain_sha256=result['inputs'][str(Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz'))],mask_result_sha256=sha(B/'mask-verification.json'),reuse_scope=['Terrain, config, all water models/instances, materials, satellite, bridges and navmesh are byte-identical to EV16.','EV16 native census and EV18 physical trips remain applicable to unchanged geometry.','New masks still require in-game load/vegetation inspection; no BALTIC016 closure.'])
(B/'deploy-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='changed_entries'},indent=2))
