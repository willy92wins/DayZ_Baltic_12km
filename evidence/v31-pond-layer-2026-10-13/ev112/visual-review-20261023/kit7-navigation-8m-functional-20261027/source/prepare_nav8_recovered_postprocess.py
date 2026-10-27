from pathlib import Path
R=Path(__file__).parent
s=(R/'package_and_deploy_kit7_nav8.py').read_text(encoding='utf-8')
s=s.replace('from verify_c_orderly_close import validate_close,validate_rpt,validate_generation_exit','from verify_c_orderly_close import validate_close,validate_rpt\nfrom verify_nav8_recovered_exit import validate_generation_exit',1)
s=s.replace("[Path(__file__),R/'verify_c_orderly_close.py']","[R/'package_and_deploy_kit7_nav8.py',R/'verify_c_orderly_close.py']",1)
needle="assert {str(p) for p in [R/'package_and_deploy_kit7_nav8.py',R/'verify_c_orderly_close.py']}<=set(gate['inputs'])\n"
assert needle in s
extra="""recovery_gate_path=R/'kit7-nav8-recovered-postprocess-review-20261027/accepted.json'
recovery_gate=read(recovery_gate_path)
assert recovery_gate['status']=='ACCEPTED_AFTER_REVIEW'
assert {str(Path(__file__)),str(R/'verify_nav8_recovered_exit.py'),str(R/'resume_kit7_nav8_generation.js')}<=set(recovery_gate['inputs'])
for p,digest in recovery_gate['inputs'].items():assert sha(p)==digest,p
gate=dict(status=gate['status'],inputs={**gate['inputs'],**recovery_gate['inputs'],str(recovery_gate_path):sha(recovery_gate_path)})
"""
s=s.replace(needle,needle+extra)
needle="assert not any(e['event'] in ('SERVER_EXIT_OBSERVED','GENERATOR_CANCEL_INTENT') for e in events)"
assert s.count(needle)==1
s=s.replace(needle,"assert not any(e['event']=='SERVER_EXIT_OBSERVED' for e in events)  # exact unexecuted cancel intent classified by reviewed recovery verifier above")
p=R/'package_and_deploy_kit7_nav8_recovered.py';assert not p.exists();p.write_text(s,encoding='utf-8')
p=R/'verify_nav8_recovered_exit.py';s=p.read_text(encoding='utf-8').replace('import copy,json,re','import json,re').replace("assert not proof['cancel_file_exists'] and not proof['wrapper_cancel_file_exists']","assert proof['cancel_file_exists'] is False and proof['wrapper_cancel_file_exists'] is False").replace("and gen['returncode']==0","and type(gen['returncode']) is int and gen['returncode']==0");p.write_text(s,encoding='utf-8')
(R/'nav8-recovery-addendum.md').write_text('''# Addendum: same-run navigation generation recovery

Original generation inputs, map, native query contract and tolerances remain immutable. Only the lifecycle evidence classifier changes for run 0db37e43-0bd0-4ac6-8b03-bc85daf9d5b2. The original validator and original packer remain unchanged and will still reject its raw timeline.

An explicit lease_expired interrupted the original coordinator. GENERATOR_CANCEL_INTENT at 2026-10-27T02:34:29.4373005+00:00 was recorded, but the cancel command did not run. Original error receipts are preserved. Native process recapture at 02:59:44Z proves the same generator PID71040, creation time, executable and command hashes, same parentPID59940/creation/command, after that intent. Progress advanced afterward. The same serverPID46288/creation was readopted through MCP; original server observer retained its handle. Resume uses the original absolute time budget and never launches a replacement generator.

Recovered acceptance is conditional on exactly that one intent, absent cancellation and wrapper-cancellation receipts, identical before/after generator identity, advancement after intent, native generation exit0 and complete artifact, successful recovered coordinator completion, and unchanged original observer/close/RPT conditions. Every other cancellation intent, server exit observation, nonzero generator code, changed identity, stale/no progress, bad server exit code, missing/late close is rejected. Raw timeline is preserved; only the fully classified one event is omitted from a derived in-memory view passed to the unchanged exit validator. This does not alter geometric tolerances or native queries.

The recovered packer adds a separately reviewed hash gate and carries both original and recovery evidence into deployment inputs. It must not run before generation and orderly close complete. No PASS is claimed by this addendum. Preparation tests use synthetic future termination only; they are never runtime evidence.
''',encoding='utf-8')
print('RECOVERY_POSTPROCESS_PREPARED_NOT_EXECUTED')
