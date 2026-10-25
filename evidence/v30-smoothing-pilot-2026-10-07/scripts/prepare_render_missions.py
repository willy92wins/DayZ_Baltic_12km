"""Create isolated direct-spawn render controls; never rewrite an existing mission.

APIs checked against P:/scripts/5_mission/mission/missionserver.c:486,
P:/scripts/3_game/global/world.c:19,51 and the live BalticTideProbeV2 mission.
Only spawn position and frozen noon differ from that probe.
"""
from pathlib import Path
import hashlib
import json
import shutil

W = Path(__file__).resolve().parents[3]
M = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
source = M / 'BalticTideProbeV2.BalticTrial/init.c'
original = source.read_text(encoding='utf-8-sig')
out = W / 'evidence/v30-smoothing-pilot-2026-10-07/missions'
entries = []
for name, x, z in [('BalticRenderNavControlV1', 6081, 4966), ('BalticRenderDryControlV1', 6192, 8466)]:
    body = original.replace('BalticTideProbeV2Mission', name + 'Mission')
    body = body.replace('GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);',
                        'GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);\n    GetGame().GetWorld().SetTimeMultiplier(0);')
    anchor = '    protected const string LOG = '
    assert body.count(anchor) == 1
    method = f'''    // Direct initial creation: no post-load teleport.
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {{
        pos = "{x} 0 {z}";
        pos[1] = GetGame().SurfaceY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }}

'''
    body = body.replace(anchor, method + anchor)
    folder = out / (name + '.BalticTrial')
    deployed = M / folder.name
    assert not folder.exists() and not deployed.exists(), 'Preserve existing evidence/mission'
    folder.mkdir(parents=True)
    (folder / 'init.c').write_text(body, encoding='utf-8', newline='\n')
    shutil.copytree(folder, deployed)
    digest = hashlib.sha256((folder / 'init.c').read_bytes()).hexdigest()
    assert hashlib.sha256((deployed / 'init.c').read_bytes()).hexdigest() == digest
    entries.append({'mission': str(deployed), 'sha256': digest, 'spawn_xz': [x,z], 'time_multiplier_requested': 0})
(out / 'receipt.json').write_text(json.dumps({'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'missions': entries}, indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(entries, indent=2))
