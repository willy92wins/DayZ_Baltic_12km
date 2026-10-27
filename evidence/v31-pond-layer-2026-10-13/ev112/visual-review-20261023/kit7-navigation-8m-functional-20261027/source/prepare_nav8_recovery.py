from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'nav-kit7-8m-preparation-20261027'
s=(R/'orchestrate_kit7_nav8_generation.js').read_text(encoding='utf-8')
s=s.replace('async function generateKit7Nav8(){','async function resumeKit7Nav8(){',1)
s=s.replace('let token=null;',"let token=load('nav8RecoveryToken');if(!token)throw Error('Recovery token missing');",1)
s=s.replace("if(token)parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));",'if(token)await beat();',1)
a=s.index('const prepared=');b=s.index('const event=async(name)=>')
s=s[:a]+"const runid='0db37e43-0bd0-4ac6-8b03-bc85daf9d5b2';let p={pid:46288,creation_time_utc:'2026-10-27T01:56:26.504646Z'},genSession=11394,observerSession=39068,genDone=false,problem=null,cleanupProblem=null,close=null,preserveForRecovery=false,generatorFinished=null;\n"+s[b:]
s=s.replace("await event('HEARTBEAT_ERROR');const state=",'const state=',1)
s=s.replace("store('navKit7EightLease',token);","store('nav8RecoveryToken',token);",1)
a=s.index(" await event('LAUNCHED');");b=s.index(' let rounds=0;')
s=s[:a]+" await beat();await snapshot('mcp-recovered.json');\n await cmd(\"$ErrorActionPreference='Stop'\\n$i=Get-Content -LiteralPath '\"+d+\"/launch-inputs.json' -Raw|ConvertFrom-Json\\nforeach($v in $i.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Recovery input drift'}}\");\n await event('LEASE_RECOVERED');let q={session_id:genSession};\n"+s[b:]
s=s.replace('const deadline=Date.now()+18300e3;',"const deadline=Date.parse('2026-10-27T01:59:33.833774Z')+18300e3;",1)
out=R/'resume_kit7_nav8_generation.js';assert not out.exists();out.write_text(s,encoding='utf-8')
for name in ['cleanup.json','completion.json']:
 p=D/name;backup=D/(name.replace('.json','-before-lease-recovery.json'));assert not backup.exists();backup.write_bytes(p.read_bytes())
record=dict(status='RESUME_SAME_LIVE_GENERATION',run_id='0db37e43-0bd0-4ac6-8b03-bc85daf9d5b2',server_pid=46288,generator_pid=71040,generator_session=11394,observer_session=39068,restarted=False,inputs_changed=False,tolerances_changed=False,source_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),reason='Explicit lease_expired caused original coordinator to fail before cancellation could be confirmed. Same original RUNNING_IDLE run re-adopted; server, generator and observer retained. Original error receipts preserved. Command heartbeat now uses recovery helper; recovery claims before recording an event to avoid the expired-heartbeat recursion.')
(D/'lease-recovery.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
