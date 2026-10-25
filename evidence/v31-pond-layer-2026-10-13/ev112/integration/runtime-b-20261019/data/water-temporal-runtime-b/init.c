// Server-side probe for the BALTIC-015 bridge rollout (EV109): objects around each point are loaded with
// GetObjectsAtPosition (game.c:922) in the same frame before the water queries (a server without players does not
// stream the kit pieces otherwise); adds SurfaceRoadY3D UNDER (game.c:1164, constants.c:40) from 30 m above ground (decks of bridge_metal_25 stand up to 16 m over the terrain).
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0.1, 0.1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 0);
    weather.GetRain().Set(0, 0, 3600);
    weather.SetWindMaximumSpeed(20);
    weather.SetWindFunctionParams(0, 0, 1);
    weather.GetWindMagnitude().SetLimits(0.1, 0.1);
    weather.GetWindMagnitude().Set(0.1, 0, 3600);
}

class BalticBridgeProbeV2Mission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected ref array<Object> m_Objects = new array<Object>;
    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;
    protected int m_StartMs;
    protected bool m_Ready;
    protected bool m_Done;
    protected int m_Sample;

    void LogRow(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_water_temporal_ev112.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle file = OpenFile("$profile:baltic_water_temporal_ev112.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_WATER_TEMPORAL_EV112;BalticTrial");
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
        m_Ready = m_Rows.Count() > 0;
        m_StartMs = GetGame().GetTime() + 10000;
        LogRow("BEGIN;30;" + m_Rows.Count());
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        if (GetGame().GetTime() < m_StartMs) return;
        vector pos;
        vector above;
        float ground;
        string row;
        for (int i = 0; i < m_Rows.Count(); i++)
        {
            m_Fields.Clear();
            m_Rows[i].Split(";", m_Fields);
            pos = m_Fields[1].ToVector();
            m_Objects.Clear();
            m_Proxies.Clear();
            GetGame().GetObjectsAtPosition(Vector(pos[0], 0, pos[2]), 30.0, m_Objects, m_Proxies);
            ground = GetGame().SurfaceY(pos[0], pos[2]);
            above = Vector(pos[0], ground + 100, pos[2]);
            row = "P;" + m_Sample + ";" + GetGame().GetTime() + ";" + m_Fields[0] + ";" + ground;
            row = row + ";" + GetGame().SurfaceIsSea(pos[0], pos[2]);
            row = row + ";" + GetGame().SurfaceIsPond(pos[0], pos[2]);
            row = row + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            row = row + ";" + GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
            row = row + ";" + GetGame().SurfaceRoadY3D(pos[0], ground + 30.0, pos[2], RoadSurfaceDetection.UNDER);
            row = row + ";" + m_Objects.Count();
            row = row + ";" + GetGame().GetWaterSurfaceHeightWithFakeWave(above);
            row = row + ";" + GetGame().SurfaceGetSeaWaveCurrent();
            LogRow(row);
        }
        m_Sample = m_Sample + 1;
        m_StartMs = GetGame().GetTime() + 2000;
        if (m_Sample >= 30)
        {
            LogRow("END;30;" + m_Rows.Count());
            m_Done = true;
        }
    }
}
Mission CreateCustomMission(string path) { return new BalticBridgeProbeV2Mission(); }
