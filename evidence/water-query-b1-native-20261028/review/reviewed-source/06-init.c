// Dedicated-server diagnostics only. No RPC, player control, spawning or terrain edits.
// game.c:923,1176-1202; Object.c:287,503. Native linking still needs a real run.
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

class BalticWaterQueryB1Mission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected ref array<Object> m_Objects = new array<Object>;
    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;
    protected ref array<string> m_ObjectRows = new array<string>;
    protected ref array<string> m_SeaRows = new array<string>;
    protected ref array<vector> m_SeaPoints = new array<vector>;
    protected int m_StartMs;
    protected int m_QueryAfter;
    protected int m_Index;
    protected int m_Round;
    protected bool m_Loaded;
    protected bool m_Ready;
    protected bool m_Done;

    void LogRow(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_water_query_b1.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle file = OpenFile("$profile:baltic_water_query_b1.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_WATER_QUERY_B1;BalticTrial");
        CloseFile(file);
        FileHandle input = OpenFile("$mission:points.csv", FileMode.READ);
        if (!input) { LogRow("FAIL;NO_POINTS"); return; }
        string inputRow;
        while (FGets(input, inputRow) >= 0)
        {
            if (inputRow == "") continue;
            m_Fields.Clear();
            inputRow.Split(";", m_Fields);
            if (m_Fields.Count() != 6) { CloseFile(input); LogRow("FAIL;SCHEMA"); return; }
            if ((m_Fields[4] != "0" && m_Fields[4] != "1") || (m_Fields[5] != "0" && m_Fields[5] != "1")) { CloseFile(input); LogRow("FAIL;FLAGS"); return; }
            m_Rows.Insert(inputRow);
        }
        CloseFile(input);
        if (m_Rows.Count() != 115) { LogRow("FAIL;COUNT"); return; }
        m_SeaPoints.Insert("2400 100 7000");
        m_SeaPoints.Insert("2430 100 7020");
        m_SeaPoints.Insert("2410 100 7040");
        m_StartMs = GetGame().GetTime() + 10000;
        m_Ready = true;
        LogRow("BEGIN;115;3");
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        if (GetGame().GetTime() < m_StartMs) return;
        vector pos;
        vector origin0;
        vector origin1;
        vector origin2;
        vector high;
        vector low;
        vector seaPos;
        vector seaDepthPos;
        vector objectPos;
        Object nearby;
        float ground;
        float bed;
        float waterRef;
        float solid;
        float upper;
        float road;
        float nfHigh;
        float fakeHigh;
        float nfLow;
        float fakeLow;
        float depth0;
        float depth1;
        float depth2;
        float waveBefore;
        float waveAfter;
        float seaNf;
        float seaFake;
        float seaDepth;
        bool sea;
        bool pond;
        bool seaFlag;
        bool pondFlag;
        bool lowBelow;
        bool objectValid;
        string shape;
        string row;
        string objectRow;
        string seaRow;
        int startMs;
        int endMs;
        int oi;
        int ri;
        FileHandle file;
        m_Fields.Clear();
        m_Rows[m_Index].Split(";", m_Fields);
        pos = m_Fields[1].ToVector();
        if (!m_Loaded)
        {
            m_Objects.Clear();
            m_Proxies.Clear();
            GetGame().GetObjectsAtPosition(Vector(pos[0], 0, pos[2]), 40.0, m_Objects, m_Proxies);
            m_Loaded = true;
            m_QueryAfter = GetGame().GetTime() + 100;
            return;
        }
        if (GetGame().GetTime() < m_QueryAfter) return;
        m_Objects.Clear();
        m_Proxies.Clear();
        GetGame().GetObjectsAtPosition(Vector(pos[0], 0, pos[2]), 40.0, m_Objects, m_Proxies);
        startMs = GetGame().GetTime();
        waveBefore = GetGame().SurfaceGetSeaWaveCurrent();
        ground = GetGame().SurfaceY(pos[0], pos[2]);
        pos[1] = ground;
        bed = ground;
        if (m_Fields[4] == "1") bed = m_Fields[2].ToFloat();
        waterRef = m_Fields[3].ToFloat();
        solid = ground;
        if (bed > solid) solid = bed;
        upper = solid;
        if (m_Fields[5] == "1" && waterRef > upper) upper = waterRef;
        high = Vector(pos[0], ground + 100, pos[2]);
        low = Vector(pos[0], solid + 2, pos[2]);
        origin0 = Vector(pos[0], ground + 0.01, pos[2]);
        origin1 = Vector(pos[0], solid + 0.01, pos[2]);
        origin2 = Vector(pos[0], upper + 0.25, pos[2]);
        lowBelow = m_Fields[5] == "1" && waterRef > low[1];
        sea = GetGame().SurfaceIsSea(pos[0], pos[2]);
        pond = GetGame().SurfaceIsPond(pos[0], pos[2]);
        nfHigh = GetGame().GetWaterSurfaceHeightNoFakeWave(high);
        fakeHigh = GetGame().GetWaterSurfaceHeightWithFakeWave(high);
        nfLow = GetGame().GetWaterSurfaceHeightNoFakeWave(low);
        fakeLow = GetGame().GetWaterSurfaceHeightWithFakeWave(low);
        depth0 = GetGame().GetWaterDepth(origin0);
        depth1 = GetGame().GetWaterDepth(origin1);
        depth2 = GetGame().GetWaterDepth(origin2);
        road = GetGame().SurfaceRoadY3D(pos[0], ground + 100, pos[2], RoadSurfaceDetection.UNDER);
        m_ObjectRows.Clear();
        for (oi = 0; oi < m_Objects.Count(); oi++)
        {
            nearby = m_Objects[oi];
            objectValid = false;
            shape = "";
            objectPos = "0 0 0";
            if (nearby)
            {
                objectValid = true;
                shape = nearby.GetShapeName();
                objectPos = nearby.GetPosition();
            }
            objectRow = "O;" + m_Round + ";" + m_Fields[0] + ";" + oi + ";" + objectValid + ";" + shape + ";" + objectPos;
            m_ObjectRows.Insert(objectRow);
        }
        m_SeaRows.Clear();
        for (ri = 0; ri < m_SeaPoints.Count(); ri++)
        {
            seaPos = m_SeaPoints[ri];
            seaFlag = GetGame().SurfaceIsSea(seaPos[0], seaPos[2]);
            pondFlag = GetGame().SurfaceIsPond(seaPos[0], seaPos[2]);
            seaNf = GetGame().GetWaterSurfaceHeightNoFakeWave(seaPos);
            seaFake = GetGame().GetWaterSurfaceHeightWithFakeWave(seaPos);
            seaDepthPos = Vector(seaPos[0], seaNf + 0.25, seaPos[2]);
            seaDepth = GetGame().GetWaterDepth(seaDepthPos);
            seaRow = "S;" + m_Round + ";" + m_Fields[0] + ";" + ri + ";" + seaPos + ";" + seaFlag + ";" + pondFlag;
            seaRow = seaRow + ";" + seaNf + ";" + seaFake + ";" + seaDepthPos + ";" + seaDepth;
            m_SeaRows.Insert(seaRow);
        }
        waveAfter = GetGame().SurfaceGetSeaWaveCurrent();
        endMs = GetGame().GetTime();
        row = "Q;" + m_Round + ";" + m_Fields[0] + ";" + startMs + ";" + endMs + ";" + waveBefore + ";" + waveAfter;
        row = row + ";" + pos + ";" + ground + ";" + road + ";" + sea + ";" + pond + ";" + m_Objects.Count();
        row = row + ";" + origin0 + ";" + origin1 + ";" + origin2 + ";" + high + ";" + low;
        row = row + ";" + nfHigh + ";" + fakeHigh + ";" + nfLow + ";" + fakeLow;
        row = row + ";" + depth0 + ";" + depth1 + ";" + depth2 + ";" + lowBelow;
        file = OpenFile("$profile:baltic_water_query_b1.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        for (oi = 0; oi < m_ObjectRows.Count(); oi++) FPrintln(file, m_ObjectRows[oi]);
        for (ri = 0; ri < m_SeaRows.Count(); ri++) FPrintln(file, m_SeaRows[ri]);
        CloseFile(file);
        m_Loaded = false;
        m_Index++;
        if (m_Index == m_Rows.Count())
        {
            m_Index = 0;
            m_Round++;
        }
        if (m_Round == 3)
        {
            LogRow("END;345");
            m_Done = true;
        }
    }
}
Mission CreateCustomMission(string path) { return new BalticWaterQueryB1Mission(); }
