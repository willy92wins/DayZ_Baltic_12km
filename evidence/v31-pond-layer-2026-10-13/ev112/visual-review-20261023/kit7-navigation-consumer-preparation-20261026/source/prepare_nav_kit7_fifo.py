from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'nav-kit7-preparation-20261026'
s=(R/'orchestrate_nav_kit7_v3.js').read_text()
old="let s=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(s.box.occupied||s.self.state!=='none')throw Error('Bank occupied');\n"
assert s.count(old)==1;s=s.replace(old,'')
assert s.count('takeover:false,wait_for_box_s:0,navmesh_data_server:true')==1
s=s.replace('takeover:false,wait_for_box_s:0,navmesh_data_server:true',"takeover:false,on_busy:'queue',wait_for_box_s:600,navmesh_data_server:true")
p=R/'orchestrate_nav_kit7_fifo_v4.js';assert not p.exists();p.write_text(s)
s=(R/'test_nav_kit7_coordinator_v3.cjs').read_text().replace('orchestrate_nav_kit7_v3.js','orchestrate_nav_kit7_fifo_v4.js')
s=s.replace("assert.equal(a.takeover,false);","assert.equal(a.takeover,false);assert.equal(a.on_busy,'queue');assert.equal(a.wait_for_box_s,600);assert(!calls.includes('acquire'),'Lifecycle must queue without preacquired lease');")
s=s.replace("calls.push('launch');assert.equal","assert(!calls.includes('status'),'No pre-launch occupancy polling; lifecycle owns FIFO');calls.push('launch');assert.equal")
s=s.replace('coordinator-control-flow-v3.json','coordinator-control-flow-fifo-v4.json')
p=R/'test_nav_kit7_fifo_v4.cjs';assert not p.exists();p.write_text(s)
(D/'fifo-user-request.json').write_text(json.dumps(dict(status='FIFO_ADAPTATION_NOT_LAUNCHED',user_request='No periodic checks; join MCP lease queue and execute when prior task finishes.',source='orchestrate_nav_kit7_fifo_v4.js',source_sha256=hashlib.sha256((R/'orchestrate_nav_kit7_fifo_v4.js').read_bytes()).hexdigest(),changes=['Remove occupancy polling before launch','Delegate queue and lease acquisition to dayz_test_run on_busy=queue, wait_for_box_s=600, takeover=false'],automation='baltic-navegaci-n-cuando-quede-libre-el-banco PAUSED',generation_budget_unchanged=True),indent=2)+'\n')

