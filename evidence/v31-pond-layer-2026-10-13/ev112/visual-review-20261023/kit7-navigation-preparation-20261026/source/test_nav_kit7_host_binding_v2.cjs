const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),cp=require('node:child_process');
const R='E:/DayZ-Baltic-Build/shape-repair-20261025',source=fs.readFileSync(R+'/orchestrate_nav_kit7_v2.js','utf8');
const line=source.split('\n').find(l=>l.startsWith(' await cmd(')&&l.includes('Wrong engine identity/mode'));assert(line);
const expr=line.trim().slice('await cmd('.length,-2);
const root=R+'/nav-kit7-preparation-20261026/host-check-tests';fs.mkdirSync(root);
const base=JSON.parse(fs.readFileSync(R+'/kit7-overlap-native-20261026/calibration/host-identity.json','utf8').replace(/^\uFEFF/,''));
const packages=JSON.parse(fs.readFileSync(R+'/kit7-overlap-native-20261026/calibration/result.json','utf8')).packages;
const cases=[];
for(const name of ['mixed_paths','wrong_hash','missing_package','extra_package','duplicate_alias','wrong_engine','wrong_mode']){
 const host=structuredClone(base),dir=root+'/'+name;fs.mkdirSync(dir);
 const keys=Object.keys(host.package_hashes);
 if(name==='wrong_hash')host.package_hashes[keys[0]]='bad';
 if(name==='missing_package')delete host.package_hashes[keys[0]];
 if(name==='extra_package')host.package_hashes['P:/Mods/foreign.pbo']='bad';
 if(name==='duplicate_alias'){delete host.package_hashes[keys[1]];host.package_hashes[keys[0].replaceAll('\\','/')]=host.package_hashes[keys[0]];}
 if(name==='wrong_engine')host.executable_file_sha256='bad';
 if(name==='wrong_mode')host.navmesh_data_server=false;
 fs.writeFileSync(dir+'/host-identity.json',JSON.stringify(host));
 fs.writeFileSync(dir+'/launch-inputs.json',JSON.stringify({packages}));
 const command=new Function('d','return '+expr)(dir);
 fs.writeFileSync(dir+'/check.ps1',command);
 const result=cp.spawnSync('powershell',['-NoProfile','-ExecutionPolicy','Bypass','-File',dir+'/check.ps1'],{encoding:'utf8',windowsHide:true,timeout:30000});
 assert.equal(result.error,undefined);
 const passed=result.status===0;assert.equal(passed,name==='mixed_paths',name);
 fs.writeFileSync(dir+'/output.log',(result.stdout||'')+(result.stderr||''));
 cases.push({name,expected_pass:name==='mixed_paths',exit_code:result.status,passed:true});
}
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const report={status:'REAL_POWERSHELL_HOST_BINDING_CONTROLS_PASS',coordinator_sha256:sha(source),command_expression_sha256:sha(expr),host_source_sha256:sha(fs.readFileSync(R+'/kit7-overlap-native-20261026/calibration/host-identity.json')),cases,scope:'Actual inline PowerShell executed against retained real host identity and altered fixtures; no processes launched or stopped.'};
fs.writeFileSync(R+'/nav-kit7-preparation-20261026/host-check-controls-v2.json',JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report,null,2));

