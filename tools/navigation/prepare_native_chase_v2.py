"""Freeze a fresh consumer fixture with target settlement before AI spawn."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = root / 'missions/BalticNativeChase.BalticTrial/init.c'
text = source.read_text()
text = text.replace('BalticNativeChaseMission', 'BalticNativeChaseV2Mission')
text = text.replace('baltic_native_chase_v1.log', 'baltic_native_chase_v2.log')
text = text.replace('BALTIC_NATIVE_CHASE_V1', 'BALTIC_NATIVE_CHASE_V2')
text = text.replace('protected bool m_Started;', 'protected bool m_Started;\n    protected bool m_Preparing;\n    protected float m_PreparedAt;')
text = text.replace('void BeginStage()', 'void PrepareStage()')
needle = '        m_Prey.SetAllowDamage(false);\n        m_Actor ='
replacement = '''        m_Prey.SetAllowDamage(false);
        m_Preparing = true;
        m_PreparedAt = m_Time;
        m_NextSample = m_Time;
        Record("SETTLE_BEGIN");
    }

    void BeginStage()
    {
        float spawnDistance = -80;
        vector orientation = "98.748926 0 0";
        if (m_Stage == 1) spawnDistance = -50;
        if (m_Stage == 2)
        {
            spawnDistance = 50;
            orientation = "-81.251074 0 0";
        }
        m_Preparing = false;
        m_Actor ='''
assert needle in text
text = text.replace(needle, replacement)
needle = '        if (!m_Started)\n        {'
replacement = '''        if (m_Preparing)
        {
            if (m_Time >= m_NextSample)
            {
                Record("SETTLE");
                m_NextSample = m_Time + 0.2;
            }
            if (m_Time - m_PreparedAt >= 20) BeginStage();
            return;
        }
        if (!m_Started)
        {'''
assert needle in text
text = text.replace(needle, replacement)
text = text.replace('            m_Prey = m_NativeTestObservers[0];\n            BeginStage();', '            m_Prey = m_NativeTestObservers[0];\n            PrepareStage();')
target = root / 'missions/BalticNativeChaseV2.BalticTrial/init.c'
if target.exists():
    raise ValueError('Fresh mission required')
target.parent.mkdir(parents=True)
target.write_text(text, encoding='utf-8')
ref = json.loads((root/'evidence/navigation/native-chase-reference-v1.json').read_text())
ref.update(parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), mission_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), target_settlement_s=20)
ref['requirements'].append('Target within2m of goal during last5s of pre-spawn settlement')
(root/'evidence/navigation/native-chase-reference-v2.json').write_text(json.dumps(ref,indent=2)+'\n')
print(ref['mission_sha256'])
