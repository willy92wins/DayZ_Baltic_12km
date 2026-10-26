"""Preserve reviewed v1 sources and produce focused v2 controls after adjudication."""
from pathlib import Path
import hashlib,json
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');O=R/'kit7-nav-postprocess-review-20261026';D=R/'kit7-nav-consumer-20261026'
hashes=json.loads((O/'source-hashes.json').read_text());B=O/'reviewed-source';B.mkdir(exist_ok=False)
sources=[R/'orchestrate_kit7_nav_probe.js',R/'finish_kit7_nav_probe.py',W/'tools/navigation/verify_kit7_nav_ev112.py']
for p in sources:
    s=p.read_text()
    if p.suffix=='.js':s=s.replace('for(let i=0;i<60;i++)','for(let i=0;i<30;i++)')
    elif p.name.startswith('finish_'):
        s=s.replace("assert Path(binding['source']).name==frozen['log_name']\n",'').replace("assert mcp['version']==read(R/'nav-kit7-preparation-20261026/mcp-after.json')['version']\n",'').replace("frozen['inputs'][str(O/'reference.json')]","sha(O/'reference.json')")
    else:
        s=s.replace('LineString,shape,GeometryCollection','LineString,shape').replace("    if reference['max_waypoint_surface_error_m']!=.801:raise ValueError('Original surface tolerance required')\n",'').replace("    full=unary_union(list(dry.values())+[wet])\n",'')
        start=s.index("        expected=LineString(q['centerline']).buffer(2.1)\n");stop=s.index('        v=check_route(',start);s=s[:start]+s[stop:]
    # Existing generated JS/finish files were written by Path.write_text on Windows.
    raw=s.replace('\n','\r\n').encode() if p.parent==R else s.encode()
    if hashlib.sha256(raw).hexdigest()!=hashes[str(p)]:
        raw=s.encode()
    assert hashlib.sha256(raw).hexdigest()==hashes[str(p)],p
    (B/p.name).write_bytes(raw)
s=(R/'test_kit7_nav_consumer.py').read_text().replace("out=D/'synthetic-controls'","out=D/'synthetic-controls-v2'")
anchor="for mode in ('reference','terrain'):"
extra="""bad=copy.deepcopy(ref);bad['max_waypoint_surface_error_m']=.802;control('relaxed_tolerance',bad,text)
bad=copy.deepcopy(ref);bad['queries'][45]['centerline'][0][0]+=.5;control('changed_centerline',bad,text)
from shapely.geometry import mapping,box
bad=copy.deepcopy(ref);bad['corridors'][0]['exterior']=mapping(box(0,0,10,10));control('fake_exterior',bad,text)
bad=copy.deepcopy(ref);bad['corridors'][0]['corridor']=mapping(box(0,0,10,10));control('fake_corridor',bad,text)
"""
assert anchor in s;s=s.replace(anchor,extra+anchor);(R/'test_kit7_nav_consumer_v2.py').write_text(s)
s=(R/'test_kit7_nav_probe_flow.cjs').read_text().replace("'success','queue_timeout'","'success','slow_readiness','readiness_timeout','queue_timeout'").replace('let started=false','let reads=0;let started=false').replace("server_peer:{binding_state:'BOUND'","server_peer:{binding_state:(mode==='readiness_timeout'||(mode==='slow_readiness'&&++reads<=35))?'WAITING':'BOUND'").replace("['success','lease_recovery'].includes(mode)","['success','slow_readiness','lease_recovery'].includes(mode)").replace("mode==='success'?1:2","mode==='lease_recovery'?2:1").replace('coordinator-controls.json','coordinator-controls-v2.json')
(R/'test_kit7_nav_probe_flow_v2.cjs').write_text(s)
s=(R/'test_kit7_nav_probe_command.cjs').read_text().replace('command-flow-controls.json','command-flow-controls-v2.json').replace('tested-command-function.js','tested-command-function-v2.js')
(R/'test_kit7_nav_probe_command_v2.cjs').write_text(s)
print('Reviewed sources preserved; v2 controls prepared')
