"""Derive OnInput comparison from the frozen v1 mission; fail on anchor drift."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[2]
source = root / 'missions/BalticBoatCalibration.BalticTrial'
target = root / 'missions/BalticBoatInput.BalticTrial'
if target.exists():
    raise ValueError('Fresh mission required')
text = (source / 'init.c').read_text(encoding='utf-8-sig')
changes = {
    'baltic_boat_calibration_v1.log': 'baltic_boat_input_v2.log',
    'BALTIC_BOAT_CALIBRATION_V1': 'BALTIC_BOAT_INPUT_V2',
    ';active;authority;proxy"': ';active;authority;proxy;input_calls"',
    '        m_Boat.SetSteering(0);\n        m_Boat.SetThrottle(throttle);':
        '        m_Boat.BalticProbeSetInput(throttle, 0, phase >= 1 && phase <= 4, phase >= 2);',
    '            FPrintln(m_Log, row);':
        '            row = row + ";" + m_Boat.BalticProbeGetCalls();\n            FPrintln(m_Log, row);',
    '            m_Boat.SetThrottle(0);': '            m_Boat.BalticProbeStop();\n            m_Boat.SetThrottle(0);',
}
for old,new in changes.items():
    if text.count(old) != 1:
        raise ValueError('Ambiguous/missing anchor: ' + old)
    text = text.replace(old,new)
if text.count('            m_Boat.SetClutch(0);') != 3:
    raise ValueError('Unexpected clutch calls')
text = text.replace('            m_Boat.SetClutch(0);\n','')
shutil.copytree(source,target,ignore=shutil.ignore_patterns('storage*'))
(target / 'init.c').write_text(text,encoding='utf-8')
print(target)
