from pathlib import Path
import hashlib,json,copy,tempfile
R=Path(__file__).parent;D=R/'kit7-nav8load1-ram-ab-20261027'
packages={f'P:/test/{n}.pbo':str(n)*64 for n in range(1,5)}
fixtures={'result.json':dict(status='PASS_KIT7_NATIVE_GRAPH'),'config-result.json':dict(status='PASS_NATIVE_LOAD1_CONFIG'),'joint-result.json':dict(status='PASS_LOAD1_CONFIG_AND_NATIVE607',config_status='PASS_NATIVE_LOAD1_CONFIG',native_status='PASS_KIT7_NATIVE_GRAPH',run_id='run-a',packages=dict(packages)),'identity-verification.json':dict(status='PASS_BOUND_NATIVE_PROBE_INPUTS',run_id='run-a',packages=dict(packages)),'host-identity.json':dict(run_id='run-a',package_hashes=dict(packages)),'deployment.json':dict(packages=dict(packages))}
checks=[];hashes={}
def reject(fn,label,exceptions=(AssertionError,KeyError)):
 try:fn()
 except exceptions:checks.append(dict(case=label,passed=True))
 else:raise AssertionError('Accepted negative '+label)
for name,ending in [('prepare_nav8load1_ram_pass.py','dep=read('),('finalize_nav8load1_ram_ab.py','loaded=[]')]:
 source=(R/name).read_text();hashes[str(R/name)]=hashlib.sha256((R/name).read_bytes()).hexdigest()
 section=source[source.index("native=R/'kit7-nav8load1-consumer-20261027'"):source.index(ending)]
 def run(values):
  def read(p):
   assert p.parent==R/'kit7-nav8load1-consumer-20261027'
   return values[p.name]
  exec(compile(section,name,'exec'),dict(R=R,Path=Path,read=read,load=read))
 run(fixtures);checks.append(dict(case=name+'_all_required_pass',passed=True))
 for key in ('result.json','config-result.json','joint-result.json','identity-verification.json'):
  for value in ('FAIL','INCONCLUSIVE'):
   changed=copy.deepcopy(fixtures);changed[key]['status']=value
   reject(lambda:run(changed),name+'_'+key+'_'+value)
  changed=copy.deepcopy(fixtures);del changed[key]
  reject(lambda:run(changed),name+'_'+key+'_MISSING')
 for key,field in [('joint-result.json','run_id'),('identity-verification.json','run_id'),('host-identity.json','run_id'),('joint-result.json','config_status'),('joint-result.json','native_status')]:
  changed=copy.deepcopy(fixtures);changed[key][field]='discordant'
  reject(lambda:run(changed),name+'_'+key+'_'+field)
 for key,field in [('joint-result.json','packages'),('identity-verification.json','packages'),('host-identity.json','package_hashes'),('deployment.json','packages')]:
  changed=copy.deepcopy(fixtures);changed[key][field]['P:/test/1.pbo']='wrong'
  reject(lambda:run(changed),name+'_'+key+'_packages')
 admission=source[source.index('gate='):source.index("native=R/'kit7-nav8load1-consumer-20261027'")]
 changed_paths={str(R/n) for n in ('prepare_nav8load1_ram_pass.py','finalize_nav8load1_ram_ab.py','test_nav8load1_joint_gate.py')}|{str(D/'joint-gate-controls.json')}
 reviewed={**{str(R/n):n for n in ('orchestrate.js','finish.py','sampler.ps1','consumer.py')},**{p:'old-'+p for p in changed_paths}}
 required={**reviewed,**{p:'new-'+p for p in changed_paths}}
 review=R/'kit7-nav8load1-ram-review-20261027';followup=R/'kit7-nav8load1-recovery-review-20261027'
 inputs={**required,**{str(folder/n):str(folder/n)+'-digest' for folder in (review,followup) for n in ('source-hashes.json','adjudication.json')}}
 values={str(review/'source-hashes.json'):reviewed,str(review/'adjudication.json'):dict(status='ACCEPTED_AFTER_REVIEW',inputs=required,post_review_changes=sorted(changed_paths)),str(followup/'adjudication.json'):dict(status='ACCEPTED_AFTER_REVIEW',inputs=required),str(D/'accepted.json'):dict(status='ACCEPTED_AFTER_REVIEW',inputs=inputs)}
 def admit(v):
  read=lambda p:v[str(p)]
  sha=lambda p:inputs.get(str(p),'unknown')
  exec(compile(admission,name,'exec'),dict(R=R,D=D,read=read,load=read,sha=sha))
 admit(values);checks.append(dict(case=name+'_complete_review_coverage',passed=True))
 for key in [None,*reviewed,str(review/'adjudication.json'),str(review/'source-hashes.json'),str(followup/'source-hashes.json'),str(followup/'adjudication.json')]:
  changed=copy.deepcopy(values)
  if key is None:changed[str(D/'accepted.json')]['inputs']={}
  else:del changed[str(D/'accepted.json')]['inputs'][key]
  reject(lambda:admit(changed),name+'_missing_review_coverage_'+str(key))
 changed=copy.deepcopy(values);changed[str(review/'source-hashes.json')][str(R/'consumer.py')]='wrong-original-review-hash'
 reject(lambda:admit(changed),name+'_changed_unapproved_review_value')
 changed=copy.deepcopy(values);changed[str(followup/'adjudication.json')]['inputs'][next(iter(changed_paths))]='wrong-followup-value'
 reject(lambda:admit(changed),name+'_changed_followup_review_value')
 changed=copy.deepcopy(values);changed[str(review/'adjudication.json')]['post_review_changes'].append(str(R/'consumer.py'))
 reject(lambda:admit(changed),name+'_expanded_change_allowlist')
source=(R/'prepare_nav8load1_ram_pass.py').read_text();section=source[source.index("attempts=D/'attempt-reservations'"):source.index('out.mkdir();')]
with tempfile.TemporaryDirectory() as folder:
 scope=dict(D=Path(folder),n=1,row={'mission':'fresh'},sha=lambda p:'sealed',json=json)
 exec(section,scope);checks.append(dict(case='exclusive_attempt_first_reservation',passed=True))
 reject(lambda:exec(section,scope),'exclusive_attempt_cannot_repeat_after_pass_folder_removed',(FileExistsError,))
report=dict(status='PASS_LOAD1_NATIVE_ADMISSION_CONTROLS',count=len(checks),checks=checks,inputs=hashes,native_measurement=False,limits=['Actual admission source executed with independent fixtures; not a native or RAM result.'])
(D/'joint-gate-controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],count=len(checks))))
