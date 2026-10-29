from pathlib import Path
import time,json,hashlib,os,difflib,ast
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c-local-author-20261029';D.mkdir(exist_ok=False);started=time.time()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,o):p.write_bytes((json.dumps(o,indent=2)+'\n').encode());return sha(p)
put(D/'author-start.json',{'started':started,'seconds':600,'role':'Codex executor local','scope':'contract/oracles/wrapper/observer/tests'})
def pin(p):p=Path(p);return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
root=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools');ab=root/'Bin/AddonBuilder'
names=['AddonBuilder.exe','AddonBuilder.exe.config','logger.xml','NDesk.Options.dll','log4net.dll','Utils.dll','SteamLayerWrap.dll','SteamHelper.dll','SharedResources.dll','steam_api.dll','steam_appid.txt','en-US/SharedResources.resources.dll']
files=[dict(dest=n,**pin(ab/n)) for n in names];assert len(files)<=64 and sum(f['bytes'] for f in files)<128*1024**2 and max(f['bytes'] for f in files)<64*1024**2
assert files[0]['sha256']=='c113de9cab5e91d27ca0630e360db0a3eca190ec797e1dcad9cdfa70466b45e1'
tools={k:pin(root/v) for k,v in {'binarize':'Bin/Binarize/binarize.exe','cfgConvert':'Bin/CfgConvert/CfgConvert.exe','fileBank':'Bin/PboUtils/FileBank.exe','dsSignFile':'Bin/DsUtils/DSSignFile.exe','bin_config':'Bin/Binarize/bin/config.cpp','binarize_steam':'Bin/Binarize/steam_api64.dll'}.items()}
pre=Path('C:/Users/guill/.agents/skills/dayz-preflight/preflight.py');raw=pre.read_bytes();(D/'preflight-original.py').write_bytes(raw)
try:compile(raw,str(pre),'exec');fixed=raw;negative=None
except SyntaxError as e:
 assert e.lineno==213
 old=b"        'subst P: \"C:";new=b"        r'subst P: \"C:";assert raw.count(old)==1;fixed=raw.replace(old,new);negative={'type':'SyntaxError','line':e.lineno,'message':e.msg}
ast.parse(fixed);(D/'preflight-local.py').write_bytes(fixed);(D/'preflight.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),fixed.decode().splitlines(True),fromfile='governed-original',tofile='local-operational')),encoding='utf-8');put(D/'preflight-provenance.json',{'original':pin(pre),'copy':pin(D/'preflight-local.py'),'negative':negative,'delta':'one raw prefix on subst literal' if negative else 'none','governed_changed':False})
(D/'include.lst').write_bytes(b'*.paa;*.emat;*.xml;*.nm;*.c;*.csv\n');(D/'exclude.lst').write_bytes(b'')
c1b=R/'road-c1b-local-author-20261029/contract.json';assert sha(c1b)=='b7d335883f33629f8e9fc1f1b98018dadb2cb95541a33a643f6805a3bcb3d1c6'
contract={'schema':'road-c1c-probe.v1','root':str(R/'road-c1c-probe-20261029'),'source_stage':str(R/'road-c1b-stage-20261029'),'c1b':pin(c1b),'c1b_consumer':pin(R/'road-c1b-real-20261029/consumer.json'),'tool_root':str(root),'tool_files':files,'tools':tools,'include':pin(D/'include.lst'),'exclude':pin(D/'exclude.lst'),'preflight':pin(D/'preflight-local.py'),'preflight_original':pin(pre),'profile_roots':[str(Path(os.environ['LOCALAPPDATA'])/n) for n in ['Bohemia_Interactive','Bohemia Interactive']],'caps':{'copy_seconds':180,'preflight_seconds':60,'help_seconds':30,'arm_seconds':300,'observe_seconds':120,'total_seconds':1050,'rss':2147483648,'disk':2147483648,'log':33554432,'wrp':134217728,'metadata':33554432,'drain_seconds':5},'claims':{'build_ready':False,'decoder_verified':False,'map_changed':False,'native_acceptance':False},'prefix':'dayz_baltic_12km_dev/tb/narva_trial'}
h=put(D/'contract.json',contract)
oracle={'schema':'road-c1c-oracle.v1','valid_header_hex':'4f5052572000000001020304','source_header_hex':'30575a442000000001020304','positive_log':'Build Successful\n','negative_logs':['Build failed\n','Build Successful\nERROR: missing texture\n','Build Successful\nFATAL: test\n'],'expected_positive':'ARTIFACT_OBSERVED_ONLY','expected_source_header':'WRP_MAGIC','expected_no_child':'PROBE_INCONCLUSIVE_NOT_OBSERVED','expected_bad_image':'UNEXPECTED_CHILD','expected_nonzero':'PROCESS_REJECTED','expected_timeout':'TIMEOUT','expected_missing_marker':'NO_MARKER','expected_old_log':'LOG_WINDOW','expected_multiple':'WRP_COUNT','expected_changed_source':'SOURCE_CHANGED','expected_changed_work':'WORK_INPUT_MUTATED','expected_co_mutant':'ARTIFACT_PIN','expected_extra_logger_change':'LOGGER_DELTA','candidate_requires':'control.status == ARTIFACT_OBSERVED_ONLY'}
oh=put(D/'oracle.json',oracle);print(json.dumps({'contract_sha256':h,'oracle_sha256':oh,'preflight_negative':negative,'files':len(files),'tool_bytes':sum(f['bytes'] for f in files),'seconds':time.time()-started}))
