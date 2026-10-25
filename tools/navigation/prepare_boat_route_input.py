"""Derive one bounded Narva-route comparison from the frozen engine-tested probe."""
from pathlib import Path
import hashlib
import shutil

root=Path(__file__).resolve().parents[2]
source=root/'missions/BalticBoat.BalticTrial'
target=root/'missions/BalticBoatRouteInput.BalticTrial'
raw=(source/'init.c').read_bytes()
if hashlib.sha256(raw).hexdigest()!='37f673890407c01a8a1d2fd17109db033f2d90ba6f0664ffa4b6513a544ff6ca':
    raise ValueError('Frozen baseline mission changed')
if target.exists(): raise ValueError('Fresh mission required')
text=raw.decode('utf-8-sig').replace('\r\n','\n')
changes={
    'baltic_boat_probe_v3.log':'baltic_boat_route_input_v1.log',
    'BALTIC_BOAT_PROBE_V3':'BALTIC_BOAT_ROUTE_INPUT_V1',
    '        float speed = velocity.Length();':'        velocity[1] = 0;\n        float speed = velocity.Length();',
    '            m_Boat.SetSteering(steer);\n            m_Boat.SetThrottle(throttle);':
        '            m_Boat.BalticProbeSetInput(throttle, steer, true, true);',
    '            FPrintln(m_Log, record);':
        '            record = record + ";" + m_Boat.EngineGetRPM() + ";" + m_Boat.PropellerGetAngularVelocity() + ";" + m_Boat.GetNeutralGear();\n'
        '            record = record + ";" + m_Boat.BalticProbeGetCalls() + ";" + RouteDistance(pos) + ";" + steer + ";" + throttle;\n'
        '            FPrintln(m_Log, record);',
    '        else if (targetDistance > 40) Finish("OFF_ROUTE_STOP");':
        '        else if (RouteDistance(pos) > 6) Finish("CHANNEL_DEVIATION_STOP");\n'
        '        else if (targetDistance > 40) Finish("OFF_ROUTE_STOP");',
    '            m_Boat.SetThrottle(0);':'            m_Boat.BalticProbeStop();\n            m_Boat.SetThrottle(0);',
    '    void Finish(string reason)':r'''    float RouteDistance(vector pos)
    {
        float best = 100000;
        int last = m_Route.Count();
        last -= 1;
        for (int index = 0; index < last; index++)
        {
            vector a = m_Route.Get(index);
            vector b = m_Route.Get(index + 1);
            vector d = b - a;
            vector q = pos - a;
            d[1] = 0;
            q[1] = 0;
            float square = d[0]*d[0] + d[2]*d[2];
            if (square <= 0) continue;
            float t = Math.Clamp((q[0]*d[0] + q[2]*d[2])/square, 0, 1);
            vector residual = q - d*t;
            best = Math.Min(best, residual.Length());
        }
        return best;
    }

    void Finish(string reason)''',
}
for old,new in changes.items():
    if text.count(old)!=1: raise ValueError('Missing/ambiguous anchor: '+old)
    text=text.replace(old,new)
shutil.copytree(source,target,ignore=shutil.ignore_patterns('storage*'))
(target/'init.c').write_text(text,encoding='utf-8')
print(target)
print(hashlib.sha256((target/'init.c').read_bytes()).hexdigest())
