"""Derive the12m postprocess from the already exercised kit7 lifecycle consumer."""
from pathlib import Path
import ast
R=Path(__file__).parent
source=(R/'package_and_deploy_kit7_nav9.py').read_text(encoding='utf-8')
changes={'navmesh-kit7-v9-20261026':'navmesh-kit7-12m-v9-20261027','nav-kit7-preparation-20261026':'nav-kit7-12m-preparation-20261027','package-kit7-nav-v9-20261026':'package-kit7-nav12-v9-20261027','@DayZ_Baltic_EV112_Kit7Overlap':'@DayZ_Baltic_EV112_Kit7Nav12Input','@DayZ_Baltic_EV112_Kit7NavV9':'@DayZ_Baltic_EV112_Kit7Nav12','kit7-nav-consumer-20261026':'kit7-nav12-consumer-20261027','kit7-nav-postprocess-review-20261026':'kit7-nav12-postprocess-review-20261027','10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc':'ed1acb1d993a705996edad1bc3008f14e0b904483ad207d5b903a4d2aee35287',"'--grid','983','983','--tile-width','12.5'":"'--grid','1024','1024','--tile-width','12'",'eb0f131e5fc0f80d81c60b1f332d8ecfa6396cab9e09ffd36cd1c8504885c496':'13e1ab1567740aca2ff94d6607b6f2c6423b9142674878562bf477994597f80b','KIT7_NAV9_DEPLOYED_RUNTIME_PENDING':'KIT7_NAV12_DEPLOYED_RUNTIME_PENDING'}
for a,b in changes.items():assert a in source,a;source=source.replace(a,b)
anchor="assert gen['run_id']==host['run_id']==completion['run_id']==close['close']['run_id']=='57c47974-d29d-4d2c-af5f-65c0a14e1b29'"
assert anchor in source
source=source.replace(anchor,"from uuid import UUID\nassert str(UUID(gen['run_id']))==gen['run_id']\nassert gen['run_id']==host['run_id']==completion['run_id']==close['close']['run_id']\nassert dep['status']=='READY_AFTER_CODE_REVIEW' and dep['generation_seconds']==18000 and dep['observer_seconds']==18300")
target=R/'package_and_deploy_kit7_nav12.py';assert not target.exists();ast.parse(source);target.write_text(source,encoding='utf-8')
for old,new in [('test_kit7_nav_probe_command_v2.cjs','test_kit7_nav12_probe_command.cjs'),('test_kit7_nav_probe_flow_v2.cjs','test_kit7_nav12_probe_flow.cjs')]:
 s=(R/old).read_text(encoding='utf-8')
 for a,b in {'orchestrate_kit7_nav_probe.js':'orchestrate_kit7_nav12_probe.js','probeKit7Nav':'probeKit7Nav12','kit7-nav-consumer-20261026':'kit7-nav12-consumer-20261027','@DayZ_Baltic_EV112_Kit7NavV9':'@DayZ_Baltic_EV112_Kit7Nav12','kit7NavProbe':'kit7Nav12Probe','coordinator-controls-v2.json':'coordinator-controls.json','command-flow-controls-v2.json':'command-flow-controls.json'}.items():s=s.replace(a,b)
 target=R/new;assert not target.exists();target.write_text(s,encoding='utf-8')
print('POSTPROCESS_DERIVED_NOT_REVIEWED_OR_EXECUTED')
