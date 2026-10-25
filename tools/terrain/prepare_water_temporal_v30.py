"""Prepare a bounded server-only probe for the 13 frozen shallow-water failures.

No production terrain or prior acceptance criteria are modified. Native declarations:
P:/scripts/3_Game/global/game.c:1162,1174-1187,1510. Their depth/wave semantics
remain hypotheses until this independent time series is read back in the engine.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
MISSION = ROOT / 'missions/BalticV30WaterTemporalV1.BalticTrial'

SCRIPT = r'''// Server owns all measurements; no RPC, player movement, or terrain edits.
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0.1, 0.1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 0);
    weather.GetRain().Set(0, 0, 3600);
    weather.GetFog().SetLimits(0, 0);
    weather.GetFog().Set(0, 0, 3600);
    weather.GetSnowfall().SetLimits(0, 0);
    weather.GetSnowfall().Set(0, 0, 3600);
}

class BalticV30WaterTemporalV1Mission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected float m_Elapsed;
    protected float m_NextSample = 5;
    protected int m_Sample;
    protected bool m_Ready;
    protected bool m_Done;

    void LogRow(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_v30_water_temporal_v1.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle file = OpenFile("$profile:baltic_v30_water_temporal_v1.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_V30_WATER_TEMPORAL_V1;BalticTrial");
        CloseFile(file);
        FileHandle input = OpenFile("$mission:points.csv", FileMode.READ);
        if (!input) { LogRow("FAIL;NO_POINTS"); return; }
        string row;
        while (FGets(input, row) >= 0)
        {
            if (row == "") continue;
            m_Fields.Clear();
            row.Split(";", m_Fields);
            if (m_Fields.Count() != 2) { CloseFile(input); LogRow("FAIL;SCHEMA"); return; }
            m_Rows.Insert(row);
        }
        CloseFile(input);
        m_Ready = m_Rows.Count() == 17;
        LogRow("BEGIN;" + m_Rows.Count() + ";151;2");
    }

    void SampleAll()
    {
        vector pos;
        vector above;
        float ground;
        float noFake;
        float withFake;
        string row;
        int timeMs;
        for (int i = 0; i < m_Rows.Count(); i++)
        {
            m_Fields.Clear();
            m_Rows[i].Split(";", m_Fields);
            pos = m_Fields[1].ToVector();
            ground = GetGame().SurfaceY(pos[0], pos[2]);
            above = Vector(pos[0], ground + 100, pos[2]);
            timeMs = GetGame().GetTime();
            noFake = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            withFake = GetGame().GetWaterSurfaceHeightWithFakeWave(above);
            row = "T;" + m_Sample + ";" + m_Fields[0];
            row = row + ";" + timeMs + ";" + ground;
            row = row + ";" + GetGame().SurfaceIsSea(pos[0], pos[2]);
            row = row + ";" + GetGame().SurfaceIsPond(pos[0], pos[2]);
            row = row + ";" + noFake + ";" + withFake;
            row = row + ";" + GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
            row = row + ";" + GetGame().GetWaterDepth(above);
            row = row + ";" + GetGame().GetWaterDepth(Vector(pos[0], noFake - 1, pos[2]));
            row = row + ";" + GetGame().SurfaceGetSeaLevel();
            row = row + ";" + GetGame().SurfaceGetSeaWaveCurrent();
            row = row + ";" + GetGame().SurfaceGetSeaWaveMax();
            LogRow(row);
        }
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        m_Elapsed = m_Elapsed + timeslice;
        if (m_Elapsed < m_NextSample) return;
        SampleAll();
        m_Sample++;
        // Schedule from the actual tick: never backfill missing temporal samples.
        m_NextSample = m_Elapsed + 2;
        if (m_Sample == 151)
        {
            LogRow("END;151;17");
            m_Done = true;
        }
    }
}
Mission CreateCustomMission(string path) { return new BalticV30WaterTemporalV1Mission(); }
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revision_two(script):
    """Keep V1 immutable; fix its clock mismatch and isolate query ordering."""
    script = script.replace('TemporalV1', 'TemporalV2').replace('temporal_v1', 'temporal_v2').replace('TEMPORAL_V1', 'TEMPORAL_V2')
    script = script.replace('protected float m_Elapsed;\n    protected float m_NextSample = 5;', 'protected int m_NextSampleMs;')
    script = script.replace('m_Ready = m_Rows.Count() == 17;', '''m_Ready = m_Rows.Count() == 17;
        m_NextSampleMs = GetGame().GetTime() + 5000;
        FileHandle orderFile = OpenFile("$profile:baltic_v30_water_order_v2.log", FileMode.WRITE);
        if (!orderFile) { m_Ready = false; return; }
        FPrintln(orderFile, "BALTIC_V30_WATER_ORDER_V2;BalticTrial");
        CloseFile(orderFile);''')
    script = script.replace('float withFake;', 'float withFake;\n        float beforePresence;\n        float afterDepth;\n        float bedDepth;\n        bool sea;\n        bool pond;')
    script = script.replace('noFake = GetGame().GetWaterSurfaceHeightNoFakeWave(above);', '''beforePresence = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            sea = GetGame().SurfaceIsSea(pos[0], pos[2]);
            pond = GetGame().SurfaceIsPond(pos[0], pos[2]);
            noFake = GetGame().GetWaterSurfaceHeightNoFakeWave(above);''')
    script = script.replace('row = row + ";" + GetGame().SurfaceIsSea(pos[0], pos[2]);', 'row = row + ";" + sea;')
    script = script.replace('row = row + ";" + GetGame().SurfaceIsPond(pos[0], pos[2]);', 'row = row + ";" + pond;')
    script = script.replace('row = row + ";" + GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));', '''bedDepth = GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
            afterDepth = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            row = row + ";" + bedDepth;''')
    script = script.replace('            LogRow(row);', '''            LogRow(row);
            FileHandle orderFile = OpenFile("$profile:baltic_v30_water_order_v2.log", FileMode.APPEND);
            if (!orderFile) { m_Done = true; return; }
            string orderRow = "O;" + m_Sample + ";" + m_Fields[0] + ";" + timeMs;
            orderRow = orderRow + ";" + beforePresence + ";" + noFake + ";" + afterDepth;
            FPrintln(orderFile, orderRow);
            CloseFile(orderFile);''')
    script = script.replace('m_Elapsed = m_Elapsed + timeslice;\n        if (m_Elapsed < m_NextSample) return;', 'if (GetGame().GetTime() < m_NextSampleMs) return;')
    script = script.replace('// Schedule from the actual tick: never backfill missing temporal samples.\n        m_NextSample = m_Elapsed + 2;', '// Schedule after the complete batch using the same clock as the recorded samples.\n        m_NextSampleMs = GetGame().GetTime() + 2000;')
    script = script.replace('LogRow("END;151;17");', '''LogRow("END;151;17");
            FileHandle orderFile = OpenFile("$profile:baltic_v30_water_order_v2.log", FileMode.APPEND);
            if (orderFile) { FPrintln(orderFile, "END;151;17"); CloseFile(orderFile); }''')
    assert 'm_Elapsed' not in script and 'm_NextSample =' not in script
    return script


STORM = dict(calm=dict(overcast=0.1, wind_mps=0.1), storm=dict(overcast=1.0, wind_mps=20.0), settle_s=30)


def revision_three(script):
    """Keep V2 immutable; append a storm phase to the same 17 points and cadence.

    Wind API: P:/scripts/3_Game/weather.c:251 SetWindSpeed (minimum 0.1 m/s),
    :264 SetWindMaximumSpeed, :280 SetWindFunctionParams; overcast :49 Set, :74 SetLimits.
    Vanilla storm maximum 20 m/s: P:/scripts/4_World/classes/worlds/chernarusplus.c:110.
    """
    script = revision_two(script)
    for old, new in (('TemporalV2', 'TemporalV3'), ('temporal_v2', 'temporal_v3'), ('TEMPORAL_V2', 'TEMPORAL_V3'),
                     ('order_v2', 'order_v3'), ('ORDER_V2', 'ORDER_V3')):
        script = script.replace(old, new)
    edits = (
        ('    weather.GetSnowfall().Set(0, 0, 3600);\n}',
         '    weather.GetSnowfall().Set(0, 0, 3600);\n    weather.SetWindMaximumSpeed(20);\n'
         '    weather.SetWindFunctionParams(0, 0, 1);\n    weather.SetWindSpeed(0.1);\n}'),
        ('LogRow("BEGIN;" + m_Rows.Count() + ";151;2");', 'LogRow("BEGIN;" + m_Rows.Count() + ";302;2");'),
        ('            row = row + ";" + GetGame().SurfaceGetSeaWaveMax();',
         '            row = row + ";" + GetGame().SurfaceGetSeaWaveMax();\n'
         '            row = row + ";" + GetGame().GetWeather().GetWindSpeed();\n'
         '            row = row + ";" + GetGame().GetWeather().GetOvercast().GetActual();'),
        ('    override void OnUpdate(float timeslice)',
         '    void StartStorm()\n    {\n        Weather weather = GetGame().GetWeather();\n'
         '        weather.GetOvercast().SetLimits(1, 1);\n        weather.GetOvercast().Set(1, 0, 3600);\n'
         '        weather.SetWindFunctionParams(1, 1, 1);\n        weather.SetWindSpeed(20);\n    }\n\n'
         '    override void OnUpdate(float timeslice)'),
        ('        if (m_Sample == 151)\n        {\n            LogRow("END;151;17");',
         '        if (m_Sample == 151)\n        {\n            // Calm phase complete: switch to the storm and let waves settle.\n'
         '            StartStorm();\n            m_NextSampleMs = GetGame().GetTime() + 30000;\n        }\n'
         '        if (m_Sample == 302)\n        {\n            LogRow("END;302;17");'),
        ('FPrintln(orderFile, "END;151;17");', 'FPrintln(orderFile, "END;302;17");'),
    )
    for old, new in edits:
        assert script.count(old) == 1, old[:60]
        script = script.replace(old, new)
    assert 'TemporalV2' not in script and 'END;151;17' not in script
    return script


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--findings', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--revision', type=int, choices=(1, 2, 3), default=1)
    a = ap.parse_args()
    mission = MISSION if a.revision == 1 else MISSION.with_name(f'BalticV30WaterTemporalV{a.revision}.BalticTrial')
    if a.out.exists() or mission.exists():
        raise ValueError('Fresh experiment paths required')
    ref = json.loads(a.reference.read_text())
    failures = json.loads(a.findings.read_text())['shore_failures']
    ids = {p['reference']['id'] for p in failures}
    assert ids == {362,363,416,524,548,642,765,882,1176,1185,1224,1274,1312}
    by_id = {p['id']: p for p in ref['points']}
    high = max((p for p in ref['points'] if p['kind']=='wet' and p['pond_plane_m'] is not None and p['pond_plane_m']-p['expected_ground_m']>1), key=lambda p:p['pond_plane_m'])
    controls = {22:'deep_pond',13:'dry_bank',33:'sea',high['id']:'high_deep_pond'}
    assert len(controls)==4 and not ids.intersection(controls)
    points = [dict(by_id[i],role=controls.get(i,'frozen_shallow_failure')) for i in sorted(ids|controls.keys())]
    mission.mkdir(parents=True)
    script = {1: SCRIPT, 2: revision_two(SCRIPT), 3: revision_three(SCRIPT)}[a.revision]
    (mission/'init.c').write_text(script,encoding='utf-8')
    (mission/'points.csv').write_text(''.join(f'{p["id"]};{p["x"]:.9f} 0 {p["z"]:.9f}\n' for p in points),encoding='ascii')
    a.out.mkdir(parents=True)
    result = dict(status='PREPARED_NOT_EXECUTED',header=f'BALTIC_V30_WATER_TEMPORAL_V{a.revision};BalticTrial',samples=302 if a.revision == 3 else 151,interval_s=2,points=points,mission=str(mission),terrain_sha256=ref['terrain_sha256'],parent_reference_sha256=sha(a.reference),findings_sha256=sha(a.findings),files={p.name:sha(p) for p in mission.iterdir()},limits=['Diagnostic series; does not replace the frozen shore verdict.','No full tidal-cycle or boat/visual/navmesh acceptance.','Depth queries at three Y values discriminate position-dependent API semantics.'])
    if a.revision == 3:
        result.update(fields=17, phases=[dict(name='calm', first=0, count=151, **STORM['calm']),
                                         dict(name='storm', first=151, count=151, **STORM['storm'])],
                      settle_s=STORM['settle_s'])
    (a.out/'reference.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],mission=str(mission),point_count=len(points),controls=controls),indent=2))


if __name__=='__main__':
    main()
