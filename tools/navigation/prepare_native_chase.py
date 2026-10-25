"""Adapt the previously executed chase fixture to the accepted 75m native bridge."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[2]
source=root/'missions/BalticChase.BalticTrial/init.c'
text=source.read_text()
text=text.replace('    Hive ce = CreateHive();\n    if (ce) ce.InitOffline();\n','')
text=text.replace('BalticChaseMission','BalticNativeChaseMission').replace('baltic_infected_v1.log','baltic_native_chase_v1.log').replace('BALTIC_INFECTED_V1','BALTIC_NATIVE_CHASE_V1')
text=text.replace('float spawnDistance = -30;', 'float spawnDistance = -80;')
text=text.replace('float goalDistance = -60;', 'float goalDistance = -55;')
text=text.replace('goalDistance = 30;', 'spawnDistance = -50;\n            goalDistance = 60;')
text=text.replace('spawnDistance = 30;\n            goalDistance = -30;', 'spawnDistance = 50;\n            goalDistance = -60;')
text=text.replace('vector orientation = "-81.251074 0 0";', 'vector orientation = "98.748926 0 0";')
text=text.replace('spawnDistance = 50;\n            goalDistance = -60;', 'spawnDistance = 50;\n            goalDistance = -60;\n            orientation = "-81.251074 0 0";')
text=text.replace('m_Stage == 0 && d <= -42', 'm_Stage == 0 && d >= -65')
text=text.replace('m_Stage == 1 && d >= 25', 'm_Stage == 1 && d >= 48')
text=text.replace('m_Stage == 2 && d <= -25', 'm_Stage == 2 && d <= -48')
text=text.replace('protected Man m_Prey;', 'protected Man m_Prey;\n    protected ref array<Man> m_NativeTestObservers = new array<Man>;')
text=text.replace('            array<Man> players = new array<Man>;\n            GetGame().GetPlayers(players);', '            m_NativeTestObservers.Clear();\n            GetGame().GetPlayers(m_NativeTestObservers);')
text=text.replace('players.Count()', 'm_NativeTestObservers.Count()').replace('m_Prey = players[0];', 'm_Prey = m_NativeTestObservers[0];')
text=text.replace('!GetGame().IsServer()', '!GetGame().IsDedicatedServer()')
text=text.replace('        CloseFile(report);\n    }\n\n    void CleanupActor()', '        if (m_Prey) FPrintln(report, "PREY;" + m_Time + ";" + m_Stage + ";" + m_Prey.GetPosition() + ";" + m_Goal);\n        CloseFile(report);\n    }\n\n    void CleanupActor()')
target=root/'missions/BalticNativeChase.BalticTrial/init.c'
if target.exists(): raise ValueError('Fresh mission required')
target.parent.mkdir(parents=True)
target.write_text(text,encoding='utf-8')
out=root/'evidence/navigation/native-chase-reference-v1.json'
out.write_text(json.dumps({'status':'FROZEN_BEFORE_RUNTIME','parent_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'mission_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'stages':[{'spawn_axis_m':-80,'goal_axis_m':-55,'reach_axis_m':-65},{'spawn_axis_m':-50,'goal_axis_m':60,'reach_axis_m':48},{'spawn_axis_m':50,'goal_axis_m':-60,'reach_axis_m':-48}],
    'stage_timeout_s':90,'sample_interval_s':.2,'requirements':['Local stimulus control first','Both crossings beyond +/-48m','No AI movement or position override after spawn','Server health stays positive, no swimming/fall below roadway','Prey position must stay within2m of stated goal','No gaps>1s after settlement, corridor lateral<=4m'],
    'limits':['One infected and one controlled local client; not multiplayer load.','Graph 0.8m mismatch remains recorded independently.']},indent=2)+'\n')
print(hashlib.sha256(target.read_bytes()).hexdigest())
