// Temporary, bounded player-view inspection. No camera API or terrain changes.
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

class BalticV30ShoreFinishV4HeadlessMission: MissionServer
{
    protected ref array<string> m_BalticSites = new array<string>;
    protected float m_BalticElapsed;
    protected int m_BalticStage = -1;
    protected int m_BalticSampled = -1;
    protected int m_BalticStable = -1;
    protected bool m_BalticReady;
    protected bool m_BalticComplete;
    protected ref array<string> m_BalticQueries = new array<string>;
    protected int m_BalticQueryIndex;
    protected bool m_BalticQueriesDone;
    protected ref array<string> m_BalticParts = new array<string>;
    protected ref array<string> m_BalticFields = new array<string>;
    protected ref array<Man> m_BalticObservers = new array<Man>;

    void LogTour(string row)
    {
        FileHandle output = OpenFile("$profile:baltic_v30_shorefinish_v4_headless.log", FileMode.APPEND);
        if (!output) return;
        FPrintln(output, row);
        CloseFile(output);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle output = OpenFile("$profile:baltic_v30_shorefinish_v4_headless.log", FileMode.WRITE);
        if (!output) return;
        FPrintln(output, "BALTIC_V30_SHOREFINISH_V4_HEADLESS;BalticTrial");
        CloseFile(output);
        FileHandle input = OpenFile("$mission:sites.csv", FileMode.READ);
        if (!input) return;
        string row;
        array<string> fields = new array<string>;
        while (FGets(input, row) >= 0)
        {
            if (row == "") continue;
            fields.Clear(); row.Split(";", fields);
            if (fields.Count() != 5) { CloseFile(input); LogTour("FAIL;SCHEMA"); return; }
            m_BalticSites.Insert(row);
        }
        CloseFile(input);
        FileHandle queries = OpenFile("$mission:queries.csv", FileMode.READ);
        if (!queries) return;
        while (FGets(queries, row) >= 0)
        {
            if (row == "") continue;
            fields.Clear(); row.Split(";", fields);
            if (fields.Count() != 2) { CloseFile(queries); LogTour("FAIL;QUERY_SCHEMA"); return; }
            m_BalticQueries.Insert(row);
        }
        CloseFile(queries);
        LogTour("QBEGIN;" + m_BalticQueries.Count());
        m_BalticReady = m_BalticSites.Count() == 7 && m_BalticQueries.Count() == 1332;
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "2022.00000 0 8364.00000";
        pos[1] = GetGame().SurfaceRoadY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }

    void SamplePoint(string name, string kind, vector pos)
    {
        float ground = GetGame().SurfaceY(pos[0], pos[2]);
        vector above = Vector(pos[0], ground + 100, pos[2]);
        vector bed = Vector(pos[0], ground + 0.01, pos[2]);
        string surface;
        GetGame().SurfaceGetType(pos[0], pos[2], surface);
        string row = "W;" + name + ";" + kind + ";" + pos.ToString() + ";" + ground;
        row = row + ";" + GetGame().SurfaceRoadY(pos[0], pos[2]) + ";" + GetGame().SurfaceIsSea(pos[0], pos[2]);
        row = row + ";" + GetGame().SurfaceIsPond(pos[0], pos[2]) + ";" + GetGame().GetWaterDepth(bed);
        row = row + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(above) + ";" + surface;
        LogTour(row);
    }

    void ReadQueryBatch()
    {
        if (m_BalticQueriesDone) return;
        for (int batch = 0; batch < 16 && m_BalticQueryIndex < m_BalticQueries.Count(); batch++)
        {
            array<string> parts = m_BalticParts;
            parts.Clear();
            m_BalticQueries[m_BalticQueryIndex].Split(";", parts);
            vector pos = parts[1].ToVector();
            float ground = GetGame().SurfaceY(pos[0], pos[2]);
            bool sea = GetGame().SurfaceIsSea(pos[0], pos[2]);
            bool pond = GetGame().SurfaceIsPond(pos[0], pos[2]);
            float noWave = GetGame().GetWaterSurfaceHeightNoFakeWave(Vector(pos[0], ground + 100, pos[2]));
            float depth = GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
            string queryRow = "Q;" + parts[0];
            queryRow = queryRow + ";" + ground;
            queryRow = queryRow + ";" + sea;
            queryRow = queryRow + ";" + pond;
            queryRow = queryRow + ";" + noWave;
            queryRow = queryRow + ";" + depth;
            queryRow = queryRow + ";" + GetGame().SurfaceGetSeaLevelMin();
            queryRow = queryRow + ";" + GetGame().SurfaceGetSeaLevelMax();
            queryRow = queryRow + ";" + GetGame().SurfaceGetSeaLevel();
            LogTour(queryRow);
            m_BalticQueryIndex++;
        }
        if (m_BalticQueryIndex == m_BalticQueries.Count())
        {
            m_BalticQueriesDone = true;
            LogTour("QEND;" + m_BalticQueryIndex);
        }
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_BalticReady || m_BalticComplete) return;
        m_BalticElapsed = m_BalticElapsed + timeslice;
        if (m_BalticElapsed < 3) return;
        ReadQueryBatch();
        if (m_BalticQueriesDone)
        {
            m_BalticComplete = true;
            LogTour("END_READBACK;1332");
        }
    }

}

Mission CreateCustomMission(string path) { return new BalticV30ShoreFinishV4HeadlessMission(); }
