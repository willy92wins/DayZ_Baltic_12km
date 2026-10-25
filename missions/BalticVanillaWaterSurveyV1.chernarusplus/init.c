// Server-only survey of vanilla Chernarus water pieces: placement and water readback.
// APIs: game.c:922 GetObjectsAtPosition; object.c:311 GetOrientation, :330 GetDirectionUp,
// :509 GetShapeName, :869 ModelToWorld; game.c:1162-1187 water queries.
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
}

class BalticVanillaWaterSurveyV1Mission: MissionServer
{
    protected ref array<Object> m_Objects = new array<Object>;
    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;
    protected ref map<string, bool> m_Seen = new map<string, bool>;
    protected ref array<Object> m_Channel = new array<Object>;
    protected int m_Cell;
    protected int m_Sampled;
    protected bool m_Started;
    protected bool m_Done;
    protected int m_StartMs;

    void LogRow(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_vanilla_water_survey_v1.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer()) return;
        FileHandle file = OpenFile("$profile:baltic_vanilla_water_survey_v1.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_VANILLA_WATER_SURVEY_V1;" + GetGame().GetWorldName());
        CloseFile(file);
        m_Started = true;
        m_StartMs = GetGame().GetTime() + 10000;
    }

    bool IsWaterShape(string shape)
    {
        if (shape.Contains("stream_")) return true;
        if (shape.Contains("river_")) return true;
        if (shape.Contains("streambed")) return true;
        if (shape.Contains("pond_")) return true;
        if (shape.Contains("lake_")) return true;
        return false;
    }

    bool IsChannelShape(string shape)
    {
        if (shape.Contains("stream_")) return true;
        if (shape.Contains("river_")) return true;
        if (shape.Contains("streambed")) return true;
        return false;
    }

    void ScanCell(int cell)
    {
        // 103 x 103 cells of 150 m with 110 m query radius cover the 15360 m world.
        int col = cell % 103;
        int line = cell / 103;
        float x = col * 150.0;
        x = x + 75.0;
        float z = line * 150.0;
        z = z + 75.0;
        m_Objects.Clear();
        m_Proxies.Clear();
        GetGame().GetObjectsAtPosition(Vector(x, 0, z), 110.0, m_Objects, m_Proxies);
        foreach (Object o : m_Objects)
        {
            if (!o) continue;
            string shape = o.GetShapeName();
            shape.ToLower();
            if (!IsWaterShape(shape)) continue;
            vector p = o.GetPosition();
            string key = shape + ";" + Math.Round(p[0] * 10) + ";" + Math.Round(p[2] * 10);
            if (m_Seen.Contains(key)) continue;
            m_Seen.Insert(key, true);
            string row = "O;" + m_Seen.Count() + ";" + shape;
            row = row + ";" + p;
            row = row + ";" + o.GetOrientation();
            row = row + ";" + o.GetDirectionUp();
            LogRow(row);
            if (IsChannelShape(shape)) m_Channel.Insert(o);
        }
    }

    void SamplePoint(int index, string axis, float offset, vector modelPos, Object o)
    {
        vector p = o.ModelToWorld(modelPos);
        float ground = GetGame().SurfaceY(p[0], p[2]);
        vector above = Vector(p[0], ground + 50, p[2]);
        bool sea = GetGame().SurfaceIsSea(p[0], p[2]);
        bool pond = GetGame().SurfaceIsPond(p[0], p[2]);
        float plane = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
        float depth = GetGame().GetWaterDepth(Vector(p[0], ground + 0.01, p[2]));
        string row = "W;" + index + ";" + axis + ";" + offset;
        row = row + ";" + p[0] + ";" + p[1] + ";" + p[2];
        row = row + ";" + ground + ";" + sea + ";" + pond;
        row = row + ";" + plane + ";" + depth;
        LogRow(row);
    }

    void SampleChannel(int index)
    {
        Object o = m_Channel[index];
        if (!o) return;
        for (int k = -2; k <= 2; k++)
        {
            float d = k * 6;
            SamplePoint(index, "z", d, Vector(0, 0, d), o);
            SamplePoint(index, "x", d, Vector(d, 0, 0), o);
        }
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Started || m_Done) return;
        if (GetGame().GetTime() < m_StartMs) return;
        int cells = 10609;
        if (m_Cell < cells)
        {
            for (int i = 0; i < 12 && m_Cell < cells; i++)
            {
                ScanCell(m_Cell);
                m_Cell++;
            }
            if (m_Cell >= cells) LogRow("SCAN_END;" + m_Seen.Count() + ";" + m_Channel.Count());
            return;
        }
        for (int j = 0; j < 40 && m_Sampled < m_Channel.Count(); j++)
        {
            SampleChannel(m_Sampled);
            m_Sampled++;
        }
        if (m_Sampled >= m_Channel.Count())
        {
            LogRow("END;" + m_Seen.Count() + ";" + m_Channel.Count());
            m_Done = true;
        }
    }
}

Mission CreateCustomMission(string path) { return new BalticVanillaWaterSurveyV1Mission(); }
