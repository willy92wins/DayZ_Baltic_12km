from pathlib import Path
import shutil
R=Path(__file__).parent;O=R/'kit7-nav8-code-review-20261027';D=R/'nav-kit7-8m-preparation-20261027'
(O/'reviewed-source').mkdir(exist_ok=False)
for p in [R/'orchestrate_kit7_nav8_generation.js',R/'test_kit7_nav8_generation.cjs',D/'launch-inputs.json']:
 shutil.copyfile(p,O/'reviewed-source'/p.name)
p=R/'orchestrate_kit7_nav8_generation.js';s=p.read_text(encoding='utf-8');assert 'let rounds=0;' in s and 'if(rounds>1830)' in s
s=s.replace('let rounds=0;','let rounds=0;const deadline=Date.now()+18300e3;').replace('if(rounds>1830)','if(Date.now()>deadline)');p.write_text(s,encoding='utf-8')
p=R/'test_kit7_nav8_generation.cjs';s=p.read_text(encoding='utf-8')
s=s.replace('let statusFailed=false;','let statusFailed=false,clock=0;')
s=s.replace("pollCount++;if(name==='wrapper_failure'", "pollCount++;clock+=name==='rapid_progress'?1:10000;\n   if(name==='rapid_progress'&&pollCount<=1900)return {session_id:77,output:'progress'};\n   if(name==='elapsed_deadline'&&!cancelled){assert(pollCount<4,'Missing deadline');clock=18300001;return {session_id:77,output:''};}\n   if(name==='wrapper_failure'")
s=s.replace("'notify','setTimeout',code", "'notify','setTimeout','Date',code")
s=s.replace('x=>notifications.push(x),f=>f());','x=>notifications.push(x),f=>f(),{now:()=>clock,parse:Date.parse});')
s=s.replace("name==='success'||name==='physics_mixed_paths'", "name==='success'||name==='rapid_progress'||name==='physics_mixed_paths'")
s=s.replace("['success','physics_mixed_paths','delayed_capture']", "['success','rapid_progress','physics_mixed_paths','delayed_capture']")
s=s.replace("if(name==='delayed_capture')assert.equal(captureCount,4);", "if(name==='delayed_capture')assert.equal(captureCount,4);\n if(name==='rapid_progress')assert.equal(pollCount,1901);\n if(name==='elapsed_deadline'){assert(error.includes('Coordinator duration bound'));assert(cancelled&&closed&&!active);}")
s=s.replace("'success','delayed_capture','wrapper_failure'", "'success','rapid_progress','elapsed_deadline','delayed_capture','wrapper_failure'")
s=s.replace("const mutations=[", "const mutations=[\n ['iteration_counter',source.replace('if(Date.now()>deadline)','if(rounds>1830)'),'rapid_progress'],\n ['deadline_removed',source.replace('if(Date.now()>deadline)','if(false)'),'elapsed_deadline'],")
s=s.replace("/generation-controls.json'", "/generation-controls-deadline.json'")
p.write_text(s,encoding='utf-8')
print('FIXED_WALL_CLOCK_BOUND_REVIEWED_BYTES_PRESERVED')
